"""Geometric comparison of a source ISL signer and the reconstructed avatar (pure Python).

Everything is compared in body-relative terms so different cameras, body sizes and
positions do not matter:

- finger joint angles (flexion at every finger joint, thumb included) and finger spread,
  which do not depend on where the hand is;
- palm orientation relative to the chest;
- wrist / elbow position relative to the middle of the shoulders, in shoulder widths;
- wrist speed profile and fingertip contact events;
- dynamic time warping (DTW) as a diagnostic only: the original timing stays the reference.

These numbers measure geometric similarity. They say nothing about whether the signing is
correct ISL: only a qualified interpreter can decide that.
"""

import math

from retarget_math import (cross, dot, frame_from, length, mat_mul, mid, norm, palm_frame, rotation_angle, sub,
                           transpose)

# Flexion angles: (name, previous joint, joint, next joint) on the 21-point MediaPipe hand.
FLEXION_JOINTS = [
    ('thumb_cmc', 0, 1, 2), ('thumb_mcp', 1, 2, 3), ('thumb_ip', 2, 3, 4),
    ('index_mcp', 0, 5, 6), ('index_pip', 5, 6, 7), ('index_dip', 6, 7, 8),
    ('middle_mcp', 0, 9, 10), ('middle_pip', 9, 10, 11), ('middle_dip', 10, 11, 12),
    ('ring_mcp', 0, 13, 14), ('ring_pip', 13, 14, 15), ('ring_dip', 14, 15, 16),
    ('pinky_mcp', 0, 17, 18), ('pinky_pip', 17, 18, 19), ('pinky_dip', 18, 19, 20),
]
# Finger spread: angle between neighbouring fingers' first segments, seen on the palm plane.
SPREAD_PAIRS = [('thumb_index', (1, 2), (5, 6)), ('index_middle', (5, 6), (9, 10)),
                ('middle_ring', (9, 10), (13, 14)), ('ring_pinky', (13, 14), (17, 18))]
FINGERTIPS = (4, 8, 12, 16, 20)
CONTACT_THRESHOLD = 0.10      # fingertips closer than 10% of shoulder width = touching


def angle_deg(u, v):
    lu, lv = length(u), length(v)
    if lu < 1e-12 or lv < 1e-12:
        return None
    return math.degrees(math.acos(max(-1.0, min(1.0, dot(u, v) / (lu * lv)))))


def flexion_angles(pts):
    """Bend at each finger joint in degrees: 0 = straight, larger = more curled."""
    out = {}
    for name, a, b, c in FLEXION_JOINTS:
        inner = angle_deg(sub(pts[a], pts[b]), sub(pts[c], pts[b]))
        out[name] = None if inner is None else 180.0 - inner
    return out


def spread_angles(pts):
    """Angle between neighbouring fingers on the palm plane (abduction / adduction)."""
    normal = cross(sub(pts[5], pts[0]), sub(pts[17], pts[0]))
    if length(normal) < 1e-12:
        return {name: None for name, _, _ in SPREAD_PAIRS}
    n = norm(normal)
    out = {}
    for name, (a1, b1), (a2, b2) in SPREAD_PAIRS:
        u, v = sub(pts[b1], pts[a1]), sub(pts[b2], pts[a2])
        u = sub(u, [x * dot(u, n) for x in n])
        v = sub(v, [x * dot(v, n) for x in n])
        out[name] = angle_deg(u, v)
    return out


def chest_frame(l_shoulder, r_shoulder, up=(0.0, 0.0, 1.0)):
    """Body frame: Y up, X towards the person's left (the shoulder line, levelled)."""
    across = sub(l_shoulder, r_shoulder)
    return frame_from(list(up), [across[0], across[1], 0.0])


def palm_relative_to_chest(pts, chest):
    """Palm orientation expressed in the body frame (so body turning does not count)."""
    return mat_mul(transpose(chest), palm_frame(pts[0], pts[5], pts[9], pts[17]))


def orientation_error(r_source, r_avatar):
    """Angle (degrees) of the rotation between two orientations."""
    return rotation_angle(mat_mul(transpose(r_source), r_avatar))


def body_offset(point, l_shoulder, r_shoulder, chest):
    """Position relative to the middle of the shoulders, in the body frame, in shoulder widths."""
    width = length(sub(l_shoulder, r_shoulder))
    rel = sub(point, mid(l_shoulder, r_shoulder))
    local = [dot([chest[0][i], chest[1][i], chest[2][i]], rel) for i in range(3)]
    return [v / width for v in local]


def contact(left_pts, right_pts, shoulder_width):
    """Smallest fingertip-to-fingertip distance between the hands, in shoulder widths."""
    gap = min(length(sub(left_pts[a], right_pts[b])) for a in FINGERTIPS for b in FINGERTIPS)
    return gap / shoulder_width


def speeds(track, fps):
    """Frame-to-frame speed of a position track (None where a point is missing)."""
    out = [None]
    for prev, cur in zip(track, track[1:]):
        out.append(None if prev is None or cur is None else length(sub(cur, prev)) * fps)
    return out


def correlation(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 3:
        return None
    mx = sum(p[0] for p in pairs) / len(pairs)
    my = sum(p[1] for p in pairs) / len(pairs)
    sxy = sum((x - mx) * (y - my) for x, y in pairs)
    sxx = sum((x - mx) ** 2 for x, _ in pairs)
    syy = sum((y - my) ** 2 for _, y in pairs)
    return None if sxx < 1e-12 or syy < 1e-12 else sxy / math.sqrt(sxx * syy)


def dtw(a, b, dist):
    """Dynamic time warping. Returns (mean aligned distance, path). Diagnostic only."""
    n, m = len(a), len(b)
    inf = float('inf')
    cost = [[inf] * (m + 1) for _ in range(n + 1)]
    cost[0][0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d = dist(a[i - 1], b[j - 1])
            cost[i][j] = d + min(cost[i - 1][j], cost[i][j - 1], cost[i - 1][j - 1])
    path, i, j = [], n, m
    while i > 0 and j > 0:
        path.append((i - 1, j - 1))
        step = min((cost[i - 1][j - 1], i - 1, j - 1), (cost[i - 1][j], i - 1, j), (cost[i][j - 1], i, j - 1))
        i, j = step[1], step[2]
    path.reverse()
    return cost[n][m] / len(path), path


def summarise(values):
    """Mean, median, 90th percentile and count of a list (missing values ignored)."""
    v = sorted(x for x in values if x is not None)
    if not v:
        return {'n': 0}
    return {'n': len(v), 'mean': round(sum(v) / len(v), 3), 'median': round(v[len(v) // 2], 3),
            'p90': round(v[min(len(v) - 1, int(0.9 * len(v)))], 3), 'max': round(v[-1], 3)}


# Largest bend a healthy hand reaches at each joint, in degrees (published active range of
# motion, rounded up). flexion_angles is unsigned, so bending back too far also counts.
ANATOMICAL_LIMITS = {
    'thumb_cmc': 70, 'thumb_mcp': 70, 'thumb_ip': 90,
    'index_mcp': 100, 'index_pip': 115, 'index_dip': 90,
    'middle_mcp': 100, 'middle_pip': 115, 'middle_dip': 90,
    'ring_mcp': 100, 'ring_pip': 115, 'ring_dip': 90,
    'pinky_mcp': 100, 'pinky_pip': 115, 'pinky_dip': 90,
}
# MCP is measured from the wrist, so a side finger reads its natural splay (~15 deg) even when
# straight; allow that on top of the limit.
MCP_BASELINE = 20


def over_limit(angles):
    """Joints whose bend is beyond the anatomical range: {joint: degrees}."""
    out = {}
    for joint, v in angles.items():
        limit = ANATOMICAL_LIMITS[joint] + (MCP_BASELINE if joint.endswith('_mcp') else 0)
        if v is not None and v > limit:
            out[joint] = v
    return out
