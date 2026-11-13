"""2D image-space comparison of a sign: the source video's landmarks against the landmarks the same
tracker finds on a render of the avatar. Pure Python (unit-tested); used by visual_loop_check.py.

Why 2D and why from a render: the 3D geometric check (motion_report.py) measures the avatar with the
same body-relative scaling the retargeting uses, so an error in that scaling or in the arm IK cannot
show up there. Here nothing is shared with the retargeting: both pictures go through the same
tracker (its bias cancels), and every frame is normalised only by what is visible in that frame:
centred on the shoulder midpoint and divided by the shoulder width, both in pixels.
Coordinates: x to the image right, y DOWN (as in the picture), in shoulder widths.
"""

import math

POSE = {'nose': 0, 'l_shoulder': 11, 'r_shoulder': 12, 'l_elbow': 13, 'r_elbow': 14,
        'l_wrist': 15, 'r_wrist': 16}
FINGERTIPS = (4, 8, 12, 16, 20)
MIN_VISIBILITY = 0.5          # the tracker's own confidence that a body point is in view

# Limits, set before any fix was made and not to be loosened (see MOTION_VALIDATION.md).
VISUAL_LIMITS = {
    'wrist_median': 0.15,         # shoulder widths
    'wrist_p90': 0.30,
    'elbow_median': 0.20,
    'peak_height': 0.20,          # highest wrist point reached during the sign
    'handshape_median': 0.30,     # fingertip layout, in hand lengths (wrist to middle knuckle)
}


def _pt(lm, w, h):
    return (lm[0] * w, lm[1] * h)


def body_frame(pose, w, h):
    """(centre, scale) for one frame: shoulder midpoint and shoulder width in pixels, or None."""
    if pose is None:
        return None
    ls, rs = _pt(pose[POSE['l_shoulder']], w, h), _pt(pose[POSE['r_shoulder']], w, h)
    width = math.dist(ls, rs)
    if width < 1e-6:
        return None
    return ((ls[0] + rs[0]) / 2, (ls[1] + rs[1]) / 2), width


def normalised(point_px, frame):
    (cx, cy), s = frame
    return ((point_px[0] - cx) / s, (point_px[1] - cy) / s)


def body_point(pose, name, w, h):
    """Normalised position of a pose point, or None if not visible enough or no body frame."""
    frame = body_frame(pose, w, h)
    if frame is None:
        return None
    lm = pose[POSE[name]]
    if len(lm) > 3 and lm[3] < MIN_VISIBILITY:
        return None
    return normalised(_pt(lm, w, h), frame)


def fingertip_layout(hand, w, h):
    """Fingertips relative to the wrist, in hand lengths (wrist to middle knuckle), 2D."""
    if hand is None:
        return None
    wrist = _pt(hand[0], w, h)
    span = math.dist(wrist, _pt(hand[9], w, h))
    if span < 1e-6:
        return None
    return [((x - wrist[0]) / span, (y - wrist[1]) / span) for x, y in (_pt(hand[i], w, h) for i in FINGERTIPS)]


def summary(values):
    v = sorted(x for x in values if x is not None)
    if not v:
        return {'n': 0}
    return {'n': len(v), 'median': round(v[len(v) // 2], 3), 'p90': round(v[min(len(v) - 1, int(len(v) * 0.9))], 3),
            'max': round(v[-1], 3)}


def compare(src, av):
    """src, av: dicts with 'width', 'height', 'frames' (each frame: 'pose', 'left_hand', 'right_hand').
    Frame i of each is the same moment. Returns per-side measures and the pass/fail of each limit."""
    n = min(len(src['frames']), len(av['frames']))
    sw, sh, aw, ah = src['width'], src['height'], av['width'], av['height']
    out = {'frames_compared': n}
    for side, s in (('left', 'l'), ('right', 'r')):
        wrist_err, height_err, side_err, elbow_err, nose_err, hand_err = [], [], [], [], [], []
        src_heights, av_heights = [], []
        for i in range(n):
            fs, fa = src['frames'][i], av['frames'][i]
            ws, wa = body_point(fs.get('pose'), f'{s}_wrist', sw, sh), body_point(fa.get('pose'), f'{s}_wrist', aw, ah)
            if ws is not None:
                src_heights.append(ws[1])
            if wa is not None:
                av_heights.append(wa[1])
            if ws is not None and wa is not None:
                wrist_err.append(math.dist(ws, wa))
                height_err.append(wa[1] - ws[1])          # + = avatar hand lower than the signer's
                side_err.append(wa[0] - ws[0])
                ns, na = body_point(fs.get('pose'), 'nose', sw, sh), body_point(fa.get('pose'), 'nose', aw, ah)
                if ns is not None and na is not None:
                    nose_err.append((wa[1] - na[1]) - (ws[1] - ns[1]))
            es, ea = body_point(fs.get('pose'), f'{s}_elbow', sw, sh), body_point(fa.get('pose'), f'{s}_elbow', aw, ah)
            if es is not None and ea is not None:
                elbow_err.append(abs(ea[1] - es[1]))
            hs, ha = fingertip_layout(fs.get(f'{side}_hand'), sw, sh), fingertip_layout(fa.get(f'{side}_hand'), aw, ah)
            if hs is not None and ha is not None:
                hand_err.append(sum(math.dist(p, q) for p, q in zip(hs, ha)) / len(FINGERTIPS))
        if not wrist_err:
            continue
        peak_src, peak_av = min(src_heights), min(av_heights)     # smallest y = highest point
        out[side] = {
            'wrist_error': summary(wrist_err),
            'wrist_height_error_signed': summary(height_err),
            'wrist_sideways_error_signed': summary(side_err),
            'wrist_height_vs_nose_error_signed': summary(nose_err),
            'elbow_height_error': summary(elbow_err),
            'handshape_error': summary(hand_err),
            'peak_height': {'source': round(peak_src, 3), 'avatar': round(peak_av, 3),
                            'error': round(abs(peak_av - peak_src), 3)},
        }
    out['visual_check'] = verdict(out)
    return out


def verdict(result, limits=VISUAL_LIMITS):
    checks = []

    def check(name, value, limit):
        if value is not None:
            checks.append({'check': name, 'value': value, 'limit': limit, 'passed': value <= limit})

    for side in ('left', 'right'):
        r = result.get(side)
        if not r:
            continue
        check(f'{side} wrist error median', r['wrist_error'].get('median'), limits['wrist_median'])
        check(f'{side} wrist error p90', r['wrist_error'].get('p90'), limits['wrist_p90'])
        check(f'{side} elbow height error median', r['elbow_height_error'].get('median'), limits['elbow_median'])
        check(f'{side} peak height error', r['peak_height']['error'], limits['peak_height'])
        check(f'{side} handshape error median', r['handshape_error'].get('median'), limits['handshape_median'])
    if not checks:
        return {'result': 'fail', 'checks': [], 'note': 'nothing to compare'}
    return {'result': 'pass' if all(c['passed'] for c in checks) else 'fail', 'checks': checks}
