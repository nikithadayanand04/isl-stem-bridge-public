"""Offline smoothing, resampling and smoothness measures. Pure Python (unit-tested).

The bake is offline, so it can use zero-phase filters: run a low-pass filter forwards and then
backwards. That removes jitter with no lag and without flattening peaks the way a causal filter
(the One Euro filter used before) does. Only the in-memory working copy is filtered; motion
files on disk stay raw.
"""

import math

# ---------- zero-phase Butterworth ----------


def butterworth2(cutoff_hz, fs):
    """Second-order low-pass Butterworth coefficients (b, a) by the bilinear transform."""
    k = math.tan(math.pi * min(cutoff_hz, 0.45 * fs) / fs)
    norm = 1 / (1 + math.sqrt(2) * k + k * k)
    b0 = k * k * norm
    return (b0, 2 * b0, b0), (1.0, 2 * (k * k - 1) * norm, (1 - math.sqrt(2) * k + k * k) * norm)


def _lfilter(b, a, x):
    """Direct form I, started in steady state at x[0] (no start-up transient)."""
    y = []
    x1 = x2 = x[0]
    y1 = y2 = x[0]
    for v in x:
        out = b[0] * v + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2
        x2, x1 = x1, v
        y2, y1 = y1, out
        y.append(out)
    return y


PAD = 9


def filtfilt(x, cutoff_hz, fs):
    """Zero-phase low-pass of one sequence. Ends are padded by odd reflection so the filter does
    not pull the first and last frames towards zero. Sequences shorter than 2 * PAD + 1 are
    returned unchanged (too short to filter honestly)."""
    n = len(x)
    if n < 2 * PAD + 1:
        return list(x)
    b, a = butterworth2(cutoff_hz, fs)
    head = [2 * x[0] - x[i] for i in range(PAD, 0, -1)]
    tail = [2 * x[-1] - x[n - 1 - i] for i in range(1, PAD + 1)]
    y = _lfilter(b, a, head + list(x) + tail)
    y = _lfilter(b, a, y[::-1])[::-1]
    return y[PAD:PAD + n]


def runs(present):
    """(start, end) index pairs of consecutive True values."""
    out, start = [], None
    for i, p in enumerate(present + [False]):
        if p and start is None:
            start = i
        elif not p and start is not None:
            out.append((start, i - 1))
            start = None
    return out


def zero_phase_track(frames, key, fps, cutoff_hz):
    """Filter every coordinate of every landmark of frames[i][key] over time, in place.

    Each tracked stretch is filtered on its own (gaps are never filled here); stretches too
    short to filter stay raw. A 4th value per landmark (visibility) is left as it is."""
    present = [f.get(key) is not None for f in frames]
    for start, end in runs(present):
        seq = [frames[i][key] for i in range(start, end + 1)]
        points, dims = len(seq[0]), min(3, len(seq[0][0]))
        new = [[list(p) for p in fr] for fr in seq]
        for j in range(points):
            for d in range(dims):
                smoothed = filtfilt([fr[j][d] for fr in seq], cutoff_hz, fps)
                for t, v in enumerate(smoothed):
                    new[t][j][d] = v
        for t, i in enumerate(range(start, end + 1)):
            frames[i][key] = new[t]


# ---------- detector switches ----------


def blend_detector_switches(frames, side, blend_frames=4):
    """Crossfade the image hand between its two detectors where the source switches.

    {side}_hand is Holistic's hand, or the hand model's when Holistic missed it
    ({side}_hand_source). The two detectors place the same hand slightly differently, so a
    hard switch is a jump. Around each switch, where both detections exist, the two are mixed
    with a smoothstep over blend_frames frames, ending on the source used after the switch.
    Returns the number of switches blended."""
    key, src = f'{side}_hand', f'{side}_hand_source'
    blended = 0
    for i in range(1, len(frames)):
        a, b = frames[i - 1].get(src), frames[i].get(src)
        if not a or not b or a == b:
            continue
        new_key = f'{side}_hand_holistic' if b == 'holistic' else f'{side}_hand_model'
        old_key = f'{side}_hand_holistic' if a == 'holistic' else f'{side}_hand_model'
        span = range(max(0, i - blend_frames // 2), min(len(frames), i + blend_frames - blend_frames // 2))
        touched = False
        for n, k in enumerate(span):
            # Only frames where both detectors saw the hand can be mixed; the others keep the
            # one detection there is (never invented).
            if not (frames[k].get(old_key) and frames[k].get(new_key)):
                continue
            w = smoothstep((n + 1) / (len(span) + 1))
            old, new = frames[k][old_key], frames[k][new_key]
            frames[k][key] = [[(1 - w) * o[d] + w * q[d] for d in range(min(len(o), len(q)))] for o, q in zip(old, new)]
            touched = True
        blended += touched
    return blended


def smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ---------- resampling ----------


def _align(qs):
    out = [list(qs[0])]
    for q in qs[1:]:
        q = list(q)
        if sum(a * b for a, b in zip(q, out[-1])) < 0:
            q = [-v for v in q]
        out.append(q)
    return out


def _catmull_rom(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return [0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3)
            for a, b, c, d in zip(p0, p1, p2, p3)]


def resample(times, values, out_times, quaternion=False, clamp=None):
    """Catmull-Rom resampling of keyed values (a smooth curve through every key, continuous
    velocity, so slow playback has no corners at the original frames). Quaternions are brought
    into one hemisphere first and normalised after. Outside the keyed range the end value holds.
    Gaps between keys (frames left untracked) are bridged by the same smooth curve."""
    if not times:
        return []
    vals = _align(values) if quaternion else [list(v) if isinstance(v, (list, tuple)) else [v] for v in values]
    out = []
    j = 0
    for t in out_times:
        if t <= times[0]:
            v = vals[0]
        elif t >= times[-1]:
            v = vals[-1]
        else:
            while times[j + 1] < t:
                j += 1
            u = (t - times[j]) / (times[j + 1] - times[j])
            v = _catmull_rom(vals[max(j - 1, 0)], vals[j], vals[j + 1], vals[min(j + 2, len(vals) - 1)], u)
        if quaternion:
            n = math.sqrt(sum(c * c for c in v)) or 1.0
            v = [c / n for c in v]
        if clamp:
            v = [max(clamp[0], min(clamp[1], c)) for c in v]
        out.append(v if quaternion or isinstance(values[0], (list, tuple)) else v[0])
    return out


# ---------- smoothness measures ----------


def angular_speeds(directions, fps):
    """Degrees per second between consecutive unit directions (None where a frame is missing)."""
    out = []
    for a, b in zip(directions, directions[1:]):
        if a is None or b is None:
            out.append(None)
            continue
        la, lb = math.sqrt(sum(c * c for c in a)), math.sqrt(sum(c * c for c in b))
        if la < 1e-9 or lb < 1e-9:
            out.append(None)
            continue
        c = max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b)) / (la * lb)))
        out.append(math.degrees(math.acos(c)) * fps)
    return out


SPIKE_FACTOR = 3.0
SPIKE_MIN_DEG_S = 60.0     # below this a "spike" is too slow to see


def smoothness(directions, fps):
    """Median and p95 angular speed (deg/s), mean jerk (deg/s^3, third difference of the angle
    along the path) and spike frames (speed above SPIKE_FACTOR x the clip's median and above
    SPIKE_MIN_DEG_S) for one moving segment."""
    v = angular_speeds(directions, fps)
    known = sorted(x for x in v if x is not None)
    if len(known) < 4:
        return {'n': len(known)}
    median = known[len(known) // 2]
    spikes = sum(1 for x in v if x is not None and x > max(SPIKE_FACTOR * median, SPIKE_MIN_DEG_S))
    jerk = []
    for i in range(len(v) - 2):
        a, b, c = v[i], v[i + 1], v[i + 2]
        if None not in (a, b, c):
            jerk.append(abs(c - 2 * b + a) * fps * fps)
    return {'n': len(known), 'median_deg_s': round(median, 1), 'p95_deg_s': round(known[int(len(known) * 0.95)], 1),
            'mean_jerk_deg_s3': round(sum(jerk) / len(jerk), 0) if jerk else None, 'spike_frames': spikes}
