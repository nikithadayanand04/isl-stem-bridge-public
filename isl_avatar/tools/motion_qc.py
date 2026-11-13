"""Quality check for extracted sign motion.

The rule: we never invent missing movement. If tracking loses a hand for more
than MAX_GAP_FRAMES in a row while that hand is signing, the clip fails and the
sign must be re-recorded (or a better reference found) - it is not patched up.

Usage:
    python tools/motion_qc.py motion/magnet.json
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import retarget_math as rm  # noqa: E402  (pure Python: depth-flip detection)

MAX_GAP_FRAMES = 3          # longest allowed run of lost frames inside a hand's active span
MIN_POSE_COVERAGE = 0.95    # body must be tracked in at least 95% of frames
MIN_FACE_COVERAGE = 0.90    # face must be tracked in 90% of frames (non-manual features)
MIN_HAND_PRESENCE = 0.20    # a hand present in fewer frames than this is treated as not signing


REST_DEPTH = 0.80   # wrist below 80% of the way from shoulders to hips...
REST_SIDE = 0.80    # ...and out to the side (beyond 80% of half the shoulder width) = hand resting


def longest_gap(present, resting=None):
    """Longest run of lost frames between the first and last tracked frame.

    Frames where the hand is resting (see hand_resting) do not count as lost and end a run:
    a hand hanging at the side while the other hand signs is not missing data.
    """
    if True not in present:
        return 0
    resting = resting or [False] * len(present)
    first = present.index(True)
    last = len(present) - 1 - present[::-1].index(True)
    longest = run = 0
    for p, rest in zip(present[first:last + 1], resting[first:last + 1]):
        run = 0 if (p or rest) else run + 1
        longest = max(longest, run)
    return longest


def hand_resting(frame, side):
    """True when the body tracker puts this wrist low at the side or out of the picture.

    Uses the body pose (tracked even when the hand detector loses the hand), in image
    coordinates. Signs made low in front of the body stay "signing": the wrist must be
    both low AND out to the side, or below the bottom of the frame.
    """
    pose = frame.get('pose')
    if pose is None:
        return False
    wrist = pose[15 if side == 'left_hand' else 16]
    if wrist[1] > 1.0:
        return True                                   # below the bottom of the picture
    shoulder_y = (pose[11][1] + pose[12][1]) / 2
    hip_y = (pose[23][1] + pose[24][1]) / 2
    mid_x = (pose[11][0] + pose[12][0]) / 2
    half_width = abs(pose[11][0] - pose[12][0]) / 2
    low = wrist[1] > shoulder_y + REST_DEPTH * (hip_y - shoulder_y)
    to_side = abs(wrist[0] - mid_x) > REST_SIDE * half_width
    return low and to_side


MIN_FPS = 24                # below this, fast handshape changes are lost between frames
MIN_HAND_SHARPNESS = 60     # Laplacian variance of the hand crop; below = motion blur
HOLD_SPEED = 0.6            # wrist speed (shoulder widths / second) below which a hand is "holding"


def lost_runs(present, resting):
    """(start, end) of every run of lost, non-resting frames inside the hand's active span."""
    if True not in present:
        return []
    first = present.index(True)
    last = len(present) - 1 - present[::-1].index(True)
    runs, start = [], None
    for i in range(first, last + 1):
        lost = not present[i] and not resting[i]
        if lost and start is None:
            start = i
        if not lost and start is not None:
            runs.append((start, i - 1))
            start = None
    return runs


def gap_severity(frames, side, run, fps):
    """'critical' if the wrist is nearly still around the gap (a held handshape),
    'transition' if it is moving fast (the hand travelling between positions)."""
    a, b = max(run[0] - 1, 0), min(run[1] + 1, len(frames) - 1)
    pa, pb = frames[a].get('pose'), frames[b].get('pose')
    if not pa or not pb:
        return 'unknown'
    w = 15 if side == 'left_hand' else 16
    shoulder = abs(pa[11][0] - pa[12][0]) or 1e-6
    dist = ((pa[w][0] - pb[w][0]) ** 2 + (pa[w][1] - pb[w][1]) ** 2) ** 0.5 / shoulder
    speed = dist / max((b - a) / fps, 1e-6)
    return 'critical' if speed < HOLD_SPEED else 'transition'


def recording_quality(motion):
    """Frame rate, resolution, brightness and hand sharpness, with plain warnings."""
    frames = motion['frames']
    warnings = []
    fps = motion.get('fps', 0)
    if fps < MIN_FPS:
        warnings.append(f'frame rate {fps:.0f} fps is low (use 50-60 fps for new recordings)')
    if min(motion.get('width', 0), motion.get('height', 0)) < 720:
        warnings.append(f'resolution {motion.get("width")}x{motion.get("height")} is low (use at least 1280x720)')
    q = [f.get('quality') for f in frames if f.get('quality')]
    out = {'fps': round(fps, 3), 'width': motion.get('width'), 'height': motion.get('height'), 'warnings': warnings}
    if not q:
        return out
    bright = sorted(x['brightness'] for x in q)
    out['median_brightness'] = bright[len(bright) // 2]
    if out['median_brightness'] < 60:
        warnings.append('the video is dark (median brightness below 60/255)')
    for side in ('left', 'right'):
        values = sorted(x[f'{side}_sharpness'] for x in q if x.get(f'{side}_sharpness') is not None)
        if values:
            out[f'{side}_median_sharpness'] = values[len(values) // 2]
            blurred = sum(v < MIN_HAND_SHARPNESS for v in values) / len(values)
            out[f'{side}_blurred_fraction'] = round(blurred, 3)
            if blurred > 0.25:
                # Laplacian variance is an absolute measure: a soft or upscaled source reads low
                # even without motion. Treat this as "look at it", not as proof of blur.
                warnings.append(f'{side} hand has low sharpness in {blurred:.0%} of its frames '
                                f'(motion blur or a soft source; check visually)')
    return out


def qc_report(motion):
    frames = motion['frames']
    n = len(frames)
    if n == 0:
        return {'result': 'fail', 'problems': ['no frames'], 'frames': 0}

    def track(key):
        return [f.get(key) is not None for f in frames]

    problems = []
    pose_cov = sum(track('pose_world')) / n
    face_cov = sum(track('face')) / n
    if pose_cov < MIN_POSE_COVERAGE:
        problems.append(f'body tracked in {pose_cov:.0%} of frames (need {MIN_POSE_COVERAGE:.0%})')
    if face_cov < MIN_FACE_COVERAGE:
        problems.append(f'face tracked in {face_cov:.0%} of frames (need {MIN_FACE_COVERAGE:.0%})')

    hands = {}
    for key in ('left_hand', 'right_hand'):
        # A depth-flipped frame (hand mirrored front-to-back by the tracker) is wrong data:
        # it counts as lost, exactly like a frame where the hand was not found.
        flipped = rm.depth_flip_frames(frames, key.split('_')[0])
        present = [p and i not in flipped for i, p in enumerate(track(key))]
        resting = [hand_resting(f, key) for f in frames]
        presence = sum(present) / n
        active = presence >= MIN_HAND_PRESENCE
        gap = longest_gap(present, resting) if active else 0
        rest_frames = sum(1 for p, r in zip(present, resting) if r and not p)
        runs = lost_runs(present, resting) if active else []
        gaps = [{'start': a, 'end': b, 'frames': b - a + 1,
                 'severity': gap_severity(frames, key, (a, b), motion.get('fps') or 25)} for a, b in runs]
        hands[key] = {'presence': round(presence, 3), 'signing': active, 'longest_gap_frames': gap,
                      'depth_flip_frames': sorted(flipped),
                      'untracked_but_resting_frames': rest_frames, 'gaps': gaps,
                      'critical_gap_frames': sum(g['frames'] for g in gaps if g['severity'] == 'critical')}
        if active and gap > MAX_GAP_FRAMES:
            problems.append(f'{key} lost for {gap} frames in a row while signing (max {MAX_GAP_FRAMES})')
    if not any(h['signing'] for h in hands.values()):
        problems.append('no hand tracked in enough frames to count as signing')

    return {
        'result': 'fail' if problems else 'pass',
        'problems': problems,
        'frames': n,
        'pose_coverage': round(pose_cov, 3),
        'face_coverage': round(face_cov, 3),
        'hands': hands,
        'recording': recording_quality(motion),
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python tools/motion_qc.py motion/<sign_id>.json')
    with open(sys.argv[1], encoding='utf-8') as f:
        report = qc_report(json.load(f))
    print(json.dumps(report, indent=2))
    print(f'\nmotion_qc = {report["result"]}  (copy this into registry/signs.csv)')
    sys.exit(0 if report['result'] == 'pass' else 1)


if __name__ == '__main__':
    main()
