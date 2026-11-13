"""Pure-Python maths for retargeting MediaPipe motion onto an avatar skeleton.

No Blender needed, so it can be unit-tested anywhere. retarget_blender.py reads
the avatar's rest pose, calls solve_frame() for every video frame, and keys the
returned bone rotations.

Conventions
- Rotations are 3x3 matrices as lists of rows. Column 1 of a bone's matrix is the
  direction the bone points (Blender bones point along their local +Y).
- "Armature space": Blender's axes, +X = avatar's left, -Y = towards the viewer, +Z = up.
- MediaPipe's camera axes (x right, y down, z away from camera) are converted with
  mp_to_blender(). Image-space points (hands, face) are first scaled to pixels so
  x and y have the same units.
"""

import math

# ---------- vectors ----------


def sub(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def add(a, b):
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def scale(a, s):
    return [a[0] * s, a[1] * s, a[2] * s]


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def norm(a):
    length = math.sqrt(dot(a, a))
    if length < 1e-9:
        raise ValueError('zero-length vector')
    return scale(a, 1 / length)


def mid(a, b):
    return scale(add(a, b), 0.5)


def mp_to_blender(p):
    """MediaPipe camera axes (x right, y down, z away) -> armature axes (x, -y up, z towards -Y)."""
    return [p[0], p[2], -p[1]]


def image_point(p, width, height):
    """Normalised image landmark -> pixel-scaled point (MediaPipe z uses the x scale)."""
    return [p[0] * width, p[1] * height, p[2] * width]


# ---------- 3x3 matrices ----------

IDENTITY = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def transpose(m):
    return [[m[j][i] for j in range(3)] for i in range(3)]


def column(m, j):
    return [m[0][j], m[1][j], m[2][j]]


def from_columns(x, y, z):
    return [[x[0], y[0], z[0]], [x[1], y[1], z[1]], [x[2], y[2], z[2]]]


def axis_angle(axis, angle):
    x, y, z = norm(axis)
    c, s, t = math.cos(angle), math.sin(angle), 1 - math.cos(angle)
    return [[t * x * x + c, t * x * y - s * z, t * x * z + s * y],
            [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c]]


def rotation_between(a, b):
    """Smallest rotation that turns direction a into direction b."""
    a, b = norm(a), norm(b)
    c = max(-1.0, min(1.0, dot(a, b)))
    axis = cross(a, b)
    if math.sqrt(dot(axis, axis)) < 1e-9:
        if c > 0:
            return [row[:] for row in IDENTITY]
        # opposite directions: turn 180 degrees about any axis perpendicular to a
        helper = [1.0, 0.0, 0.0] if abs(a[0]) < 0.9 else [0.0, 1.0, 0.0]
        return axis_angle(cross(a, helper), math.pi)
    return axis_angle(axis, math.acos(c))


def frame_from(y_dir, x_hint):
    """Orthonormal frame whose Y is y_dir and whose X is as close as possible to x_hint."""
    y = norm(y_dir)
    x = norm(sub(x_hint, scale(y, dot(x_hint, y))))
    z = cross(x, y)
    return from_columns(x, y, z)


def mat_to_quat(m):
    """Rotation matrix -> quaternion (w, x, y, z), the order Blender uses."""
    trace = m[0][0] + m[1][1] + m[2][2]
    if trace > 0:
        s = 2 * math.sqrt(trace + 1)
        w, x, y, z = 0.25 * s, (m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s, (m[1][0] - m[0][1]) / s
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = 2 * math.sqrt(1 + m[0][0] - m[1][1] - m[2][2])
        w, x, y, z = (m[2][1] - m[1][2]) / s, 0.25 * s, (m[0][1] + m[1][0]) / s, (m[0][2] + m[2][0]) / s
    elif m[1][1] > m[2][2]:
        s = 2 * math.sqrt(1 + m[1][1] - m[0][0] - m[2][2])
        w, x, y, z = (m[0][2] - m[2][0]) / s, (m[0][1] + m[1][0]) / s, 0.25 * s, (m[1][2] + m[2][1]) / s
    else:
        s = 2 * math.sqrt(1 + m[2][2] - m[0][0] - m[1][1])
        w, x, y, z = (m[1][0] - m[0][1]) / s, (m[0][2] + m[2][0]) / s, (m[1][2] + m[2][1]) / s, 0.25 * s
    q = [w, x, y, z]
    length = math.sqrt(sum(v * v for v in q))
    return [v / length for v in q]


# ---------- palm and head frames ----------


def palm_frame(wrist, index_base, middle_base, pinky_base):
    """Frame of a hand: Y from wrist to the middle finger's base, X across the knuckles.

    The same four points exist on the video hand (MediaPipe 0, 5, 9, 17) and on the
    avatar's rest pose (hand bone and finger base bones), so the two frames can be
    compared whatever the rig's own bone axes are.
    """
    return frame_from(sub(middle_base, wrist), sub(index_base, pinky_base))


def upright_frame(up, toward_left):
    """Frame for head or chest: Y = up, X = towards the person's left."""
    return frame_from(up, toward_left)


# ---------- quaternions (for blending rotations without Euler-angle problems) ----------


def quat_to_mat(q):
    w, x, y, z = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def slerp(q0, q1, t):
    """Spherical interpolation between unit quaternions (shortest path)."""
    d = sum(a * b for a, b in zip(q0, q1))
    if d < 0:
        q1, d = [-v for v in q1], -d
    if d > 0.9995:
        q = [a + t * (b - a) for a, b in zip(q0, q1)]
    else:
        theta = math.acos(d)
        s0, s1 = math.sin((1 - t) * theta) / math.sin(theta), math.sin(t * theta) / math.sin(theta)
        q = [s0 * a + s1 * b for a, b in zip(q0, q1)]
    n = math.sqrt(sum(v * v for v in q))
    return [v / n for v in q]


def partial_rotation(m, t):
    """The fraction t of rotation m (e.g. how much of a head turn the neck takes)."""
    return quat_to_mat(slerp([1.0, 0.0, 0.0, 0.0], mat_to_quat(m), t))


def rotation_angle(m):
    """Angle of a rotation matrix, in degrees."""
    c = max(-1.0, min(1.0, (m[0][0] + m[1][1] + m[2][2] - 1) / 2))
    return math.degrees(math.acos(c))


# ---------- hand shapes ----------

def finger_bone_frame(pts, a, b, finger):
    """Orientation frame of one finger bone from 21 hand points (any coordinate system).

    Y = along the bone (joint a -> joint b). X = the roll reference: for the four fingers,
    the direction across the knuckles (index base -> pinky base), which stays roughly at right
    angles to the finger. (The thumb is handled by thumb_targets: no such direction exists for it.)
    The same construction is used on the signer's hand and on the avatar's rest hand, so their
    difference is the bone's rotation, independent of how the rig's bone axes are set up.
    """
    along = sub(pts[b], pts[a])
    hint = sub(pts[5], pts[a]) if finger == 'thumb' else sub(pts[5], pts[17])
    if length(cross(along, hint)) < 1e-9 * max(length(along), 1e-9):
        hint = sub(pts[9], pts[0])           # degenerate: fall back to the palm's long axis
    return frame_from(along, hint)


def thumb_targets(pts, side, rest_hand, hand_rotation):
    """Thumb rotations by swinging down the chain: each bone starts from its parent's rotation
    and turns by the smallest rotation that points it along the tracked thumb.

    No roll reference is needed, so the roll cannot flip. Any reference built from 21 points
    lines up with the thumb in some poses (measured: cos up to 0.99 with the index knuckle;
    a blend with the palm normal could cancel), which flipped the thumb by up to 179 degrees
    between frames. The thumb's twist therefore follows the hand; its direction at every
    joint follows the signer (so opposition across the palm is kept)."""
    out = {}
    parent = hand_rotation
    for j, (a, b) in ((1, (1, 2)), (2, (2, 3)), (3, (3, 4))):
        rest_dir = column(rest_hand[f'thumb{j}'], 1)
        predicted = mat_vec(parent, rest_dir)
        now = sub(pts[b], pts[a])
        if length(now) < 1e-9:
            rotation = parent
        else:
            rotation = mat_mul(rotation_between(predicted, now), parent)
        out[f'{side}_thumb{j}'] = ('abs', rotation)
        parent = rotation
    return out


FINGER_CHAINS = {'index': (5, 6, 7, 8), 'middle': (9, 10, 11, 12), 'ring': (13, 14, 15, 16), 'pinky': (17, 18, 19, 20)}
PALM_POINTS = (0, 5, 9, 13, 17)
# Which way the palm faces relative to cross(index knuckle - wrist, pinky knuckle - wrist), in
# armature axes: measured from real finger flexion by tools/rig_validator.py (palm_side).
PALM_SIGN = {'right': 1.0, 'left': -1.0}
PALM_FIT_MAX_RESIDUAL = 0.15    # palm lengths: a worse fit means the outline is not a palm (occluded)


def hand_segment_lengths(frames, side):
    """Median length of each finger segment (world points, metres): {(a, b): length}."""
    values = {}
    for f in frames:
        w = f.get(f'{side}_hand_world')
        if w is None:
            continue
        for chain in FINGER_CHAINS.values():
            for a, b in zip(chain, chain[1:]):
                values.setdefault((a, b), []).append(length(sub(w[b], w[a])))
    return {k: sorted(v)[len(v) // 2] for k, v in values.items()}


def image_fitted_palm(world, image, width, height):
    """Turn the whole 3D hand so its palm's outline matches the picture.

    The palm (wrist and the four knuckles) is close to flat, and its outline in the picture fixes
    its 3D orientation up to one mirror ambiguity (tilted towards or away from the camera). That
    ambiguity is settled by the 3D points (whichever answer is closer to them). Measured 10 Nov 2026
    in magnet: the 3D palm faced down while the picture shows the backs of the hands to the camera.
    Returns (points, residual): the 21 points turned about the palm's centre, and the fit's mean
    error in palm lengths; the input unchanged if the outline cannot be fitted."""
    ids = PALM_POINTS
    P = [world[i] for i in ids]
    c3 = [sum(p[d] for p in P) / len(P) for d in range(3)]
    img = [(image[i][0] * width, -image[i][1] * height) for i in ids]
    c2 = [sum(q[d] for q in img) / len(img) for d in range(2)]
    # Palm-plane basis from the 3D points.
    u = norm(sub(world[9], world[0]))
    n = cross(sub(world[5], world[0]), sub(world[17], world[0]))
    if length(n) < 1e-12:
        return [list(p) for p in world], None
    n = norm(n)
    v = cross(n, u)
    uv = [(dot(sub(p, c3), u), dot(sub(p, c3), v)) for p in P]
    q = [(x - c2[0], z - c2[1]) for x, z in img]
    # Least-squares 2x2 map from palm-plane coordinates to the picture: q = A @ uv.
    suu = sum(a * a for a, _ in uv); svv = sum(b * b for _, b in uv); suv = sum(a * b for a, b in uv)
    det = suu * svv - suv * suv
    if abs(det) < 1e-18:
        return [list(p) for p in world], None
    inv = [[svv / det, -suv / det], [-suv / det, suu / det]]
    rows = []
    for d in range(2):
        su = sum(qq[d] * a for qq, (a, _) in zip(q, uv)); sv = sum(qq[d] * b for qq, (_, b) in zip(q, uv))
        rows.append([su * inv[0][0] + sv * inv[1][0], su * inv[0][1] + sv * inv[1][1]])
    a1 = [rows[0][0], rows[1][0]]                       # picture image of the palm's u axis (X, Z)
    a2 = [rows[0][1], rows[1][1]]
    s1, s2, cc = a1[0] ** 2 + a1[1] ** 2, a2[0] ** 2 + a2[1] ** 2, a1[0] * a2[0] + a1[1] * a2[1]
    # Scale 1/k^2 = x from: (1 - s1 x)(1 - s2 x) = cc^2 x^2  (unit, orthogonal axes in 3D).
    qa, qb, qc = s1 * s2 - cc * cc, -(s1 + s2), 1.0
    if abs(qa) < 1e-18:
        x = 1.0 / (s1 + s2) if s1 + s2 > 0 else None
    else:
        disc = qb * qb - 4 * qa * qc
        if disc < 0:
            return [list(p) for p in world], None
        roots = sorted(r for r in ((-qb - math.sqrt(disc)) / (2 * qa), (-qb + math.sqrt(disc)) / (2 * qa)) if r > 0)
        x = next((r for r in roots if r <= 1.0 / max(s1, s2) + 1e-12), None)
    if x is None:
        return [list(p) for p in world], None
    k = 1 / math.sqrt(x)
    d1 = math.sqrt(max(0.0, 1 - s1 * x))
    d2 = math.sqrt(max(0.0, 1 - s2 * x))
    if d1 * d2 > 1e-9 and cc * x > 0:
        d2 = -d2                                         # orthogonality fixes the relative sign
    best = None
    for sgn in (1.0, -1.0):                             # the mirror ambiguity
        fu = [a1[0] / k, sgn * d1, a1[1] / k]           # armature axes: X, depth (Y), Z
        fv = [a2[0] / k, sgn * d2, a2[1] / k]
        if length(fu) < 1e-9 or length(fv) < 1e-9:
            continue
        fu, fv = norm(fu), norm(fv)
        fn = cross(fu, fv)
        R = mat_mul(from_columns(fu, fv, fn), transpose(from_columns(u, v, n)))
        closeness = rotation_angle(R)
        if best is None or closeness < best[0]:
            best = (closeness, R)
    if best is None:
        return [list(p) for p in world], None
    R = best[1]
    turned = [add(c3, mat_vec(R, sub(p, c3))) for p in world]
    # k is pixels per metre: project the turned palm back into the picture and compare.
    proj = [((t_[0] - c3[0]) * k, (t_[2] - c3[2]) * k) for t_ in (turned[i] for i in ids)]
    palm_len = length(sub(world[9], world[0])) * k
    resid = sum(math.dist(pp, qq) for pp, qq in zip(proj, q)) / len(ids) / max(palm_len, 1e-9)
    return turned, resid


# Finger fit (12 Nov 2026). image_anchored_hand reads each finger segment from the picture on its
# own. Measured on water (right hand, frames 29-31): it put the whole fold into the middle joint
# (PIP 130-149 deg, beyond what a finger can do) and left the knuckle almost straight (MCP 10-34);
# the joint limit then cut the PIP to 115, so the avatar showed a flat knuckle with a hooked tip
# where the signer has a neat fold (3D tracker: MCP 33-49, PIP 78-101). The fit below instead
# chooses, per finger, three bends that a real finger can make (each within its limit, the tip
# joint following the middle joint as in real fingers) whose picture best matches the video.
FINGER_FIT = False              # set from retarget_config.json hands.finger_fit
FIT_LIMITS = (95.0, 110.0, 80.0)            # MCP, PIP, DIP flexion, degrees (inside FINGER_JOINT_LIMITS)
FIT_DIP_RATIO = 0.67            # DIP ~ 2/3 PIP in active flexion (tendon coupling)
FIT_DIP_WEIGHT = 0.15           # how strongly that coupling is preferred (picture distance units)
FIT_WORLD_WEIGHT = 0.05         # weak pull towards the 3D tracker's bends (breaks ties the picture cannot)


def _finger_chain_points(base, d0, n, lengths, angles):
    pts, p, total = [], base, 0.0
    for seg, ang in zip(lengths, angles):
        total += math.radians(ang)
        d = add(scale(d0, math.cos(total)), scale(n, math.sin(total)))
        p = add(p, scale(d, seg))
        pts.append(p)
    return pts


def fitted_finger_hand(world, image, width, height, side, segments):
    """Hand points whose four fingers are the anatomically possible fingers that best match the
    picture (see FINGER_FIT above). Palm and thumb keep the 3D points; each finger keeps its 3D
    sideways spread. world: 21 points in armature axes; image: 21 normalised image landmarks."""
    img = [(lm[0] * width, -lm[1] * height) for lm in image]
    wp = [(p[0], p[2]) for p in world]
    ci = [sum(img[i][d] for i in PALM_POINTS) / len(PALM_POINTS) for d in (0, 1)]
    cw = [sum(wp[i][d] for i in PALM_POINTS) / len(PALM_POINTS) for d in (0, 1)]
    num = sum((wp[i][0] - cw[0]) ** 2 + (wp[i][1] - cw[1]) ** 2 for i in PALM_POINTS)
    den = sum((img[i][0] - ci[0]) ** 2 + (img[i][1] - ci[1]) ** 2 for i in PALM_POINTS)
    out = [list(p) for p in world]
    if den < 1e-9 or num < 1e-12:
        return out
    k = math.sqrt(num / den)
    planar = [(cw[0] + (x - ci[0]) * k, cw[1] + (z - ci[1]) * k) for x, z in img]
    normal = scale(cross(sub(world[5], world[0]), sub(world[17], world[0])), PALM_SIGN[side])
    if length(normal) < 1e-12:
        return out
    normal = norm(normal)
    palm_len = max(length(sub(world[9], world[0])), 1e-6)
    for chain in FINGER_CHAINS.values():
        lengths = [segments.get((a, b)) or length(sub(world[b], world[a])) for a, b in zip(chain, chain[1:])]
        base = out[chain[0]]
        # Zero-bend direction: the 3D proximal segment laid into the palm plane (keeps the spread).
        prox = sub(world[chain[1]], world[chain[0]])
        d0 = sub(prox, scale(normal, dot(prox, normal)))
        if length(d0) < 1e-9:
            continue
        d0 = norm(d0)
        wa = [_angle(sub(world[b], world[a]), sub(world[c], world[b])) for a, b, c in zip(chain, chain[1:], chain[2:])]
        wa = [_angle(d0, prox)] + wa
        targets = [planar[j] for j in chain[1:]]

        def cost(angles):
            pts = _finger_chain_points(base, d0, normal, lengths, angles)
            c = sum((p[0] - t[0]) ** 2 + (p[2] - t[1]) ** 2 for p, t in zip(pts, targets)) / (palm_len ** 2)
            c += FIT_DIP_WEIGHT * ((angles[2] - FIT_DIP_RATIO * angles[1]) / 90.0) ** 2
            c += FIT_WORLD_WEIGHT * sum(((a - b) / 90.0) ** 2 for a, b in zip(angles, wa))
            return c

        best, best_c = None, None
        for step, span in ((10.0, None), (3.0, 10.0), (1.0, 3.0)):
            grids = []
            for j, lim in enumerate(FIT_LIMITS):
                lo, hi = (0.0, lim) if span is None else (max(0.0, best[j] - span), min(lim, best[j] + span))
                n_ = int((hi - lo) / step) + 1
                grids.append([lo + i * step for i in range(n_)] + ([hi] if lo + (n_ - 1) * step < hi else []))
            for a1 in grids[0]:
                for a2 in grids[1]:
                    for a3 in grids[2]:
                        c = cost((a1, a2, a3))
                        if best_c is None or c < best_c:
                            best, best_c = (a1, a2, a3), c
        for j, p in zip(chain[1:], _finger_chain_points(base, d0, normal, lengths, best)):
            out[j] = p
    return out


def image_anchored_hand(world, image, width, height, side, segments):
    """Hand points with the four fingers' joints placed from the picture.

    Measured 10 Nov 2026: MediaPipe's 3D hand flattens fingers that curl towards or away from
    the camera. In magnet the signer's fingers form a tight claw, but the 3D points are nearly
    straight, so the avatar's fingers were straight (2D fingertip layout error 0.41 hand lengths).
    The picture shows the curl (fingertips project near the knuckles). So, like the arms:
    sideways and vertical positions of the finger joints come from the image (scaled to metres by
    matching the palm's projection), depth from the 3D points, sized so every finger segment keeps
    its measured length; the depth goes to the side that bends the finger towards the palm
    (fingers essentially never bend backwards). The palm and the thumb keep the 3D points.
    Known limit: a fist seen from behind hides its fingertips, and the picture then reads the
    fingers straighter than the 3D model does (make, left hand).
    world: 21 points in armature axes; image: 21 normalised image landmarks."""
    img = [(lm[0] * width, -lm[1] * height) for lm in image]                 # (X, Z) in pixels
    wp = [(p[0], p[2]) for p in world]
    ci = [sum(img[i][d] for i in PALM_POINTS) / len(PALM_POINTS) for d in (0, 1)]
    cw = [sum(wp[i][d] for i in PALM_POINTS) / len(PALM_POINTS) for d in (0, 1)]
    num = sum((wp[i][0] - cw[0]) ** 2 + (wp[i][1] - cw[1]) ** 2 for i in PALM_POINTS)
    den = sum((img[i][0] - ci[0]) ** 2 + (img[i][1] - ci[1]) ** 2 for i in PALM_POINTS)
    if den < 1e-9 or num < 1e-12:
        return [list(p) for p in world]
    k = math.sqrt(num / den)
    planar = [(cw[0] + (x - ci[0]) * k, cw[1] + (z - ci[1]) * k) for x, z in img]
    out = [list(p) for p in world]
    normal = scale(cross(sub(world[5], world[0]), sub(world[17], world[0])), PALM_SIGN[side])
    n_len = length(normal)
    if n_len < 1e-12:
        return out
    normal = scale(normal, 1 / n_len)
    for chain in FINGER_CHAINS.values():
        pictured = [list(p) for p in out]
        for a, b in zip(chain, chain[1:]):
            seg = segments.get((a, b))
            x, z = planar[b]
            dx, dz = x - pictured[a][0], z - pictured[a][2]
            flat = math.hypot(dx, dz)
            if not seg or flat >= seg:
                depth_options = [0.0]
            else:
                d = math.sqrt(seg * seg - flat * flat)
                depth_options = [d, -d]
            # The depth goes to the side that bends the finger towards the palm.
            best = max(([dx, dy, dz] for dy in depth_options), key=lambda c: dot(norm(c), normal))
            pictured[b] = add(pictured[a], best)
        # Tried 10 Nov 2026 and rejected by the visual loop check: keeping, per finger, whichever
        # reading (picture or 3D) curls more. It scored worse on the fingertip layout in the
        # picture (magnet 0.37 vs 0.35, computer right 0.42 vs 0.33), so the picture's reading is used.
        for j in chain[1:]:
            out[j] = pictured[j]
    return out


# image_fitted_palm: measured 10 Nov 2026 to make handshapes worse in the picture (make left
# 0.53 -> 0.97 fingertip-layout error), probably the wrong side of its mirror ambiguity in
# occluded poses. Kept, tested, and switched off.
PALM_FIT = False


def hand_points(frame, side, width, height, world_only=False, segments=None):
    """21 hand points in armature axes: the metric 3D hand shape when available
    (keeps finger depth), otherwise the image landmarks (flatter, older behaviour).
    world_only: never fall back to image points. The two are different shapes (metric vs
    flattened), so switching between them inside one sign makes the fingers jump; a frame
    without world points is then left untracked and filled by interpolation."""
    world = frame.get(f'{side}_hand_world')
    if world is not None:
        pts = [mp_to_blender(p) for p in world]
        image = frame.get(f'{side}_hand')
        if segments and image is not None:
            if PALM_FIT:
                fitted, resid = image_fitted_palm(pts, image, width, height)
                if resid is not None and resid < PALM_FIT_MAX_RESIDUAL:
                    pts = fitted
            if FINGER_FIT:
                pts = fitted_finger_hand(pts, image, width, height, side, segments)
            else:
                pts = image_anchored_hand(pts, image, width, height, side, segments)
        return pts, 'world'
    if world_only:
        return None, None
    image = frame.get(f'{side}_hand')
    if image is not None:
        return [mp_to_blender(image_point(p, width, height)) for p in image], 'image'
    return None, None


# ---------- solving a pose ----------


def solve_frame(skeleton, targets):
    """Bone rotations for one frame.

    skeleton: list of bones, parents before children, each
        {'name', 'parent' (name or None), 'rest' (3x3 armature-space rest rotation)}
    targets: {bone name: ('dir', direction) | ('abs', rotation)}
        'dir' turns the bone (as carried by its parent) to point along direction.
        'abs' applies rotation to the bone's rest orientation in armature space.
    Returns {bone name: basis rotation} for targeted bones; Blender keys these as quaternions.
    """
    rest = {b['name']: b['rest'] for b in skeleton}
    pose = {}
    basis = {}
    for bone in skeleton:
        name, parent = bone['name'], bone['parent']
        rest_rot = rest[name]
        # Where the bone would be if only its parents moved.
        if parent is None:
            carried = rest_rot
        else:
            carried = mat_mul(mat_mul(pose[parent], transpose(rest[parent])), rest_rot)

        target = targets.get(name)
        if target is None:
            pose[name] = carried
            continue
        kind, value = target
        if kind == 'dir':
            posed = mat_mul(rotation_between(column(carried, 1), value), carried)
        elif kind == 'abs':
            posed = mat_mul(value, rest_rot)
        else:
            raise ValueError(f'unknown target kind {kind!r} for {name}')
        pose[name] = posed

        # basis = what Blender stores on the pose bone (rotation relative to rest and parent)
        if parent is None:
            basis[name] = mat_mul(transpose(rest_rot), posed)
        else:
            basis[name] = mat_mul(mat_mul(mat_mul(transpose(rest_rot), rest[parent]), transpose(pose[parent])), posed)
    return basis


# ---------- smoothing ----------


class OneEuro:
    """One Euro filter (Casiez et al. 2012): removes jitter, keeps fast movement sharp.

    Only smooths values that exist. It never produces a value for a frame where
    tracking found nothing.
    """

    def __init__(self, fps, min_cutoff=1.5, beta=0.3, d_cutoff=1.0):
        self.fps, self.min_cutoff, self.beta, self.d_cutoff = fps, min_cutoff, beta, d_cutoff
        self.prev = None
        self.prev_d = 0.0

    def _alpha(self, cutoff):
        tau = 1 / (2 * math.pi * cutoff)
        return 1 / (1 + tau * self.fps)

    def __call__(self, x):
        if self.prev is None:
            self.prev = x
            return x
        d = (x - self.prev) * self.fps
        a_d = self._alpha(self.d_cutoff)
        self.prev_d = a_d * d + (1 - a_d) * self.prev_d
        a = self._alpha(self.min_cutoff + self.beta * abs(self.prev_d))
        self.prev = a * x + (1 - a) * self.prev
        return self.prev


def smooth_track(frames, key, fps, **params):
    """Smooth one landmark stream (e.g. 'right_hand') in place; missing frames stay None."""
    filters = {}
    for frame in frames:
        points = frame.get(key)
        if points is None:
            continue
        for i, p in enumerate(points):
            for axis in range(3):
                f = filters.setdefault((i, axis), OneEuro(fps, **params))
                p[axis] = f(p[axis])


# ---------- MediaPipe landmarks -> targets ----------

# Finger bones in order, with the MediaPipe hand landmarks at each end.
FINGER_BONES = {
    'thumb1': (1, 2), 'thumb2': (2, 3), 'thumb3': (3, 4),
    'index1': (5, 6), 'index2': (6, 7), 'index3': (7, 8),
    'middle1': (9, 10), 'middle2': (10, 11), 'middle3': (11, 12),
    'ring1': (13, 14), 'ring2': (14, 15), 'ring3': (15, 16),
    'pinky1': (17, 18), 'pinky2': (18, 19), 'pinky3': (19, 20),
}
# MediaPipe pose ids (the signer's own left/right).
POSE = {'l_shoulder': 11, 'r_shoulder': 12, 'l_elbow': 13, 'r_elbow': 14,
        'l_wrist': 15, 'r_wrist': 16, 'l_hip': 23, 'r_hip': 24}
# Face mesh ids: outer eye corners, forehead, chin.
FACE = {'r_eye': 33, 'l_eye': 263, 'forehead': 10, 'chin': 152}


def mat_vec(m, v):
    return [sum(m[i][k] * v[k] for k in range(3)) for i in range(3)]


def length(v):
    return math.sqrt(dot(v, v))


def two_bone_ik(shoulder, target, upper_len, fore_len, elbow_hint):
    """Elbow position for an arm reaching from shoulder towards target.

    The wrist lands exactly on target when it is in reach (otherwise as close as the arm
    allows, fully straight). The elbow bends towards elbow_hint, i.e. the side the
    signer's own elbow was on. Returns (elbow, wrist).
    """
    to_target = sub(target, shoulder)
    d = length(to_target)
    reach = upper_len + fore_len
    d = min(max(d, abs(upper_len - fore_len) + 1e-6), reach - 1e-6)
    u = norm(to_target) if length(to_target) > 1e-9 else [0.0, 0.0, -1.0]
    wrist = add(shoulder, scale(u, d))

    # Law of cosines: how far along the shoulder-wrist line the elbow sits, and how far off it.
    along = (upper_len ** 2 + d ** 2 - fore_len ** 2) / (2 * d)
    off = math.sqrt(max(upper_len ** 2 - along ** 2, 0.0))
    hint = sub(elbow_hint, shoulder)
    sideways = sub(hint, scale(u, dot(hint, u)))
    if length(sideways) < 1e-6:                 # hint on the line: bend downwards
        sideways = sub([0.0, 0.0, -1.0], scale(u, -u[2]))
        if length(sideways) < 1e-6:
            sideways = [0.0, -1.0, 0.0]
    elbow = add(add(shoulder, scale(u, along)), scale(norm(sideways), off))
    return elbow, wrist


def video_arm_lengths(frames):
    """Median shoulder-elbow-wrist length per side in the video (metres), for scaling."""
    sides = {'left': ('l_shoulder', 'l_elbow', 'l_wrist'), 'right': ('r_shoulder', 'r_elbow', 'r_wrist')}
    out = {}
    for side, (s, e, w) in sides.items():
        values = []
        for f in frames:
            world = f.get('pose_world')
            if world is None:
                continue
            ps, pe, pw = (world[POSE[k]][:3] for k in (s, e, w))
            values.append(length(sub(pe, ps)) + length(sub(pw, pe)))
        values.sort()
        out[side] = values[len(values) // 2] if values else None
    return out


def video_segment_lengths(frames):
    """Median upper-arm and forearm length per side in the video (metres, world landmarks)."""
    out = {}
    for side, (s, e, w) in (('left', ('l_shoulder', 'l_elbow', 'l_wrist')), ('right', ('r_shoulder', 'r_elbow', 'r_wrist'))):
        ups, fores = [], []
        for f in frames:
            world = f.get('pose_world')
            if world is None:
                continue
            ps, pe, pw = (world[POSE[k]][:3] for k in (s, e, w))
            ups.append(length(sub(pe, ps)))
            fores.append(length(sub(pw, pe)))
        median = lambda v: sorted(v)[len(v) // 2] if v else None
        out[side] = (median(ups), median(fores))
    return out


IMAGE_ANCHOR_MIN_VISIBILITY = 0.5
TORSO_HALF_WIDTH = 1.3      # the torso's outline, in shoulder half-widths (a hand held at the side of
                            # the belly is still in front of the body: oxygen_sign_2, measured)
TORSO_DEPTH = 0.35          # shoulder widths in front of the shoulder plane: the front of the torso
MOUTH = (9, 10)             # MediaPipe pose: mouth corners
FACE_ANCHOR = (0.5, 0.8)    # wrist-to-mouth distance in the picture plane, shoulder widths: full
                            # face-relative placement within the first, none beyond the second.
                            # When the fingertips touch the mouth the wrist is a hand length lower
                            # (measured in food: 0.47 shoulder widths).


def image_anchored_arms(frame, width, height, p, shoulder_width_m, segments):
    """Arm points with height and sideways position taken from the picture.

    Measured 10 Nov 2026: MediaPipe's 3D (world) pose puts the wrists 0.13-0.32 shoulder widths
    lower than they appear in the picture, in every sign, and shortens a raised arm (electricity:
    0.35 m instead of its usual 0.49 m), so the avatar's overhead hand stopped at the temple.
    The picture itself is reliable in x and height. So: x and height come from the image landmarks,
    in metres via this signer's shoulder width (world median / this frame's shoulder width in
    pixels), relative to the shoulder midpoint; depth comes from the world pose, with its size set
    so the upper arm and forearm keep their measured lengths (sign from the world pose).
    p: world points in armature axes (mp_to_blender). Returns a copy with shoulders, elbows and
    wrists replaced where the image shows them; other points unchanged."""
    image = frame.get('pose')
    if image is None or not shoulder_width_m:
        return p
    def px(i):
        return image[i][0] * width, image[i][1] * height
    ls, rs = px(POSE['l_shoulder']), px(POSE['r_shoulder'])
    sw_px = math.dist(ls, rs)
    if sw_px < 1e-6:
        return p
    k = shoulder_width_m / sw_px
    mid_px = ((ls[0] + rs[0]) / 2, (ls[1] + rs[1]) / 2)
    mid_w = mid(p['l_shoulder'], p['r_shoulder'])
    out = dict(p)

    def planar(i):
        x, y = px(i)
        return mid_w[0] + (x - mid_px[0]) * k, mid_w[2] - (y - mid_px[1]) * k

    def in_front_of_torso_at(x, z):
        return abs(x - mid_w[0]) < TORSO_HALF_WIDTH * shoulder_width_m / 2 and z < mid_w[2]

    mouth_vis = min(image[i][3] if len(image[i]) > 3 else 1.0 for i in MOUTH)
    if mouth_vis >= IMAGE_ANCHOR_MIN_VISIBILITY:
        mx = [planar(i) for i in MOUTH]
        out['mouth'] = [(mx[0][0] + mx[1][0]) / 2, mid_w[1], (mx[0][1] + mx[1][1]) / 2]
    for side, s in (('left', 'l'), ('right', 'r')):
        sx, sz = planar(POSE[f'{s}_shoulder'])
        out[f'{s}_shoulder'] = [sx, p[f'{s}_shoulder'][1], sz]
        parent = out[f'{s}_shoulder']
        world_parent = p[f'{s}_shoulder']
        for joint, seg in (('elbow', 0), ('wrist', 1)):
            name = f'{s}_{joint}'
            lm = image[POSE[name]]
            if len(lm) > 3 and lm[3] < IMAGE_ANCHOR_MIN_VISIBILITY:
                break                                  # not in the picture: keep the world points
            x, z = planar(POSE[name])
            seg_len = (segments.get(side) or (None, None))[seg]
            flat = math.hypot(x - parent[0], z - parent[2])
            world_depth = p[name][1] - world_parent[1]
            if seg_len and flat < seg_len:
                d = math.sqrt(seg_len ** 2 - flat ** 2)
                sign = math.copysign(1.0, world_depth) if world_depth else -1.0
                # A wrist seen inside the torso's outline, below the shoulders, would be inside the
                # body if it were behind: it is in front. Measured 10 Nov 2026 in oxygen_sign_2 and
                # carbon_dioxide_sign_2: the 3D pose put the passive hand, held at the belly, behind
                # the elbow, so the avatar stood with a hand on the hip.
                if joint == 'wrist' and in_front_of_torso_at(x, z):
                    sign = -1.0
                depth = sign * d
            else:
                depth = 0.0                            # the picture shows the full length: no depth left
            world_parent = p[name]
            y = parent[1] + depth
            if joint == 'wrist' and in_front_of_torso_at(x, z):
                # Never inside the body: at least a torso's depth in front of the shoulder plane.
                # (oxygen_sign_2: the picture showed the full arm length, so no depth was left,
                # and the passive hand at the belly was placed inside the torso.)
                y = min(y, mid_w[1] - TORSO_DEPTH * shoulder_width_m)
            out[name] = [x, y, z]
            parent = out[name]
    return out


def video_body_sizes(frames):
    """Median shoulder width and shoulder-to-hip height of the signer (metres)."""
    widths, torsos = [], []
    for f in frames:
        world = f.get('pose_world')
        if world is None:
            continue
        p = {k: mp_to_blender(world[i][:3]) for k, i in POSE.items()}
        widths.append(length(sub(p['l_shoulder'], p['r_shoulder'])))
        torsos.append(mid(p['l_shoulder'], p['r_shoulder'])[2] - mid(p['l_hip'], p['r_hip'])[2])
    median = lambda v: sorted(v)[len(v) // 2] if v else None
    return {'shoulder_width': median(widths), 'torso': median(torsos)}


def body_scales(body):
    """Per-direction scale from the signer's body to the avatar's.

    Location on the body is part of a sign, so heights below the shoulders scale with the
    torso (chest stays chest, waist stays waist), sideways offsets with shoulder width, and
    depth and heights above the shoulders with arm length. ONE set of scales for both hands,
    so hands that touch in the video still touch. Missing measurements fall back to arm length.
    """
    avatar_arm = (body['l_upper'] + body['l_fore'] + body['r_upper'] + body['r_fore']) / 2
    k = avatar_arm / ((body['video_arm']['left'] + body['video_arm']['right']) / 2)
    sizes = body.get('video_sizes') or {}
    sideways = (body['shoulder_width'] / sizes['shoulder_width']
                if sizes.get('shoulder_width') and body.get('shoulder_width') else k)
    down = body['torso'] / sizes['torso'] if sizes.get('torso') and body.get('torso') else k
    return {'x': sideways, 'depth': k, 'up': k, 'down': down}


def to_avatar(offset, s):
    """Map an offset from the signer's shoulder-middle onto the avatar (see body_scales)."""
    return [offset[0] * s['x'], offset[1] * s['depth'], offset[2] * (s['up'] if offset[2] >= 0 else s['down'])]


def arm_ik_targets(p, chest_rotation, body, shrugs=None):
    """Upper-arm and forearm directions that put the avatar's wrists where the signer's were.

    Wrist and elbow positions are measured from the middle of the signer's shoulders and
    scaled by (avatar arm length / signer arm length), so contact between the hands and
    the height of a hand relative to the head survive different body proportions.

    p: this frame's MediaPipe pose points in armature axes.
    chest_rotation: the chest's armature-space rotation this frame (shoulders move with it).
    body: avatar rest measurements from Blender: chest_pivot, l_shoulder, r_shoulder,
          l_upper, l_fore, r_upper, r_fore (lengths), video_arm (from video_arm_lengths).
    """
    def posed(point):
        return add(body['chest_pivot'], mat_vec(chest_rotation, sub(point, body['chest_pivot'])))

    def posed_shoulder(side, s):
        # With a shrug, the shoulder joint rides on the rotated collarbone.
        clav = body.get(f'{s}_clavicle')
        if shrugs and side in shrugs and clav is not None:
            return add(posed(clav), mat_vec(shrugs[side], sub(body[f'{s}_shoulder'], clav)))
        return posed(body[f'{s}_shoulder'])

    shoulders = {'left': posed_shoulder('left', 'l'), 'right': posed_shoulder('right', 'r')}
    # Hand targets are measured from the shoulders WITHOUT the shrug, so one shoulder lifting
    # never moves the other hand; each arm then reaches from its own (shrugged) shoulder.
    avatar_mid = mid(posed(body['l_shoulder']), posed(body['r_shoulder']))
    video_mid = mid(p['l_shoulder'], p['r_shoulder'])

    # The same scales for both arms: MediaPipe's depth noise can make the signer's two arms
    # look very different in length, and scaling each side separately would pull touching hands apart.
    scales = body_scales(body)
    shift = body.get('wrist_shift') or {}

    targets = {}
    for side, s in (('left', 'l'), ('right', 'r')):
        upper, fore = body[f'{s}_upper'], body[f'{s}_fore']
        wrist_goal = add(avatar_mid, to_avatar(sub(p[f'{s}_wrist'], video_mid), scales))
        wrist_goal = add(wrist_goal, face_shift(p, s, body, avatar_mid, video_mid, scales, posed))
        if side in shift:   # contact correction from the bake (see fingertip_contact), avatar space
            wrist_goal = add(wrist_goal, shift[side])
        elbow_hint = add(avatar_mid, to_avatar(sub(p[f'{s}_elbow'], video_mid), scales))
        elbow, wrist = two_bone_ik(shoulders[side], wrist_goal, upper, fore, elbow_hint)
        targets[f'{side}_upper_arm'] = ('dir', sub(elbow, shoulders[side]))
        targets[f'{side}_forearm'] = ('dir', sub(wrist, elbow))
    return targets


def face_shift(p, s, body, avatar_mid, video_mid, scales, posed):
    """Where a hand is at the signer's mouth, put it at the avatar's mouth.

    Location on the body is part of a sign. The shoulder-relative mapping lands a hand that is at
    the signer's mouth wherever the signer's mouth maps to, which is not the avatar's mouth when
    faces sit at different heights above the shoulders (measured 10 Nov 2026: food, mouth 0.40
    shoulder widths above the shoulders on the signer, 0.49 on the avatar; the avatar's fingers
    landed on the chin). Near the mouth the target moves by (avatar mouth - mapped signer mouth),
    sideways and vertically only, fully within FACE_ANCHOR[0] shoulder widths of the mouth and
    fading out by FACE_ANCHOR[1]."""
    if 'mouth' not in p or 'mouth' not in body:
        return [0.0, 0.0, 0.0]
    sw = length(sub(p['l_shoulder'], p['r_shoulder']))
    if sw < 1e-9:
        return [0.0, 0.0, 0.0]
    # In the picture plane only: the mouth's depth is not measured.
    d = math.hypot(p[f'{s}_wrist'][0] - p['mouth'][0], p[f'{s}_wrist'][2] - p['mouth'][2]) / sw
    near, far = FACE_ANCHOR
    w = smoothstep((far - d) / (far - near))
    if w <= 0:
        return [0.0, 0.0, 0.0]
    mapped = add(avatar_mid, to_avatar(sub(p['mouth'], video_mid), scales))
    delta = sub(posed(body['mouth']), mapped)
    return [delta[0] * w, 0.0, delta[2] * w]


FINGERTIPS = (4, 8, 12, 16, 20)
CONTACT_GAP = 0.10   # fingertips closer than 10% of shoulder width count as touching


def fingertip_contact(frame, width, height):
    """True when the signer's two hands touch at the fingertips in this video frame.

    Measured in the image (MediaPipe's per-hand depth is unreliable), relative to shoulder
    width so it works at any distance from the camera. Only real contact in the video
    triggers the bake's contact correction; it is never added where the video has none.
    """
    left, right, pose = frame.get('left_hand'), frame.get('right_hand'), frame.get('pose')
    if left is None or right is None or pose is None:
        return False
    L = [image_point(p, width, height) for p in left]
    R = [image_point(p, width, height) for p in right]
    shoulders = length(sub(image_point(pose[11][:3], width, height), image_point(pose[12][:3], width, height))[:2] + [0])
    gap = min(length(sub(L[a], R[b])[:2] + [0]) for a in FINGERTIPS for b in FINGERTIPS)
    return shoulders > 0 and gap / shoulders < CONTACT_GAP


# Where each of the 21 MediaPipe hand points sits on the avatar's skeleton:
# (logical bone, 'head' or 'tail'). Used for the rest hand and by the validator.
HAND_POINT_BONES = [('hand', 'head')]
for _finger in ('thumb', 'index', 'middle', 'ring', 'pinky'):
    HAND_POINT_BONES += [(f'{_finger}1', 'head'), (f'{_finger}2', 'head'), (f'{_finger}3', 'head'), (f'{_finger}3', 'tail')]


def rest_hand_frames(rest_pts):
    """Palm frame and every finger-bone frame of the avatar's rest hand (21 points)."""
    frames = {'palm': palm_frame(rest_pts[0], rest_pts[5], rest_pts[9], rest_pts[17])}
    for bone, (a, b) in FINGER_BONES.items():
        frames[bone] = finger_bone_frame(rest_pts, a, b, bone.rstrip('123'))
    return frames


# Largest change from the rest pose, in degrees, that each finger joint may make relative to
# its parent bone (anatomical active range of motion, rounded up). Hand tracking sometimes
# returns impossible shapes when fingers hide each other or blur (e.g. a finger folded back
# 170 degrees); those frames are limited instead of copied. Set to None to switch off.
FINGER_JOINT_LIMITS = {'thumb1': 70.0, 'thumb2': 70.0, 'thumb3': 90.0,
                       'finger1': 105.0, 'finger2': 115.0, 'finger3': 90.0}
CLAMP_LOG = []                  # (side, bone, degrees asked, degrees allowed); read and cleared by the baker
WORLD_ONLY_SHARE = 0.8          # use world hand points only, when they cover this share of a hand's frames


FLIP_DEG = 100.0                # palm normal turning more than this between tracked frames = depth flip
FLIP_MAX_RUN = 5                # a flipped stretch longer than this is treated as real (cannot tell)


def _angle(u, v):
    lu, lv = length(u), length(v)
    if lu < 1e-12 or lv < 1e-12:
        return 0.0
    return math.degrees(math.acos(max(-1.0, min(1.0, dot(u, v) / (lu * lv)))))


def depth_flip_frames(frames, side):
    """Frames where the metric hand is mirrored front-to-back (single-camera depth ambiguity).

    A real palm cannot turn ~160 degrees between two frames. The tracked frames are split at
    every jump of the palm normal larger than FLIP_DEG. Stretches longer than FLIP_MAX_RUN are
    trusted ("anchors"); a short stretch whose palm faces away from the nearest anchor is a
    flip. Returns the set of frame indices. Without any anchor nothing is marked."""
    normals = []
    for i, f in enumerate(frames):
        w = f.get(f'{side}_hand_world')
        if w is not None:
            p = [mp_to_blender(q) for q in w]
            normals.append((i, cross(sub(p[5], p[0]), sub(p[17], p[0]))))
    segments, current = [], []
    for k, (i, n) in enumerate(normals):
        if current and _angle(n, normals[k - 1][1]) > FLIP_DEG:
            segments.append(current)
            current = []
        current.append((i, n))
    if current:
        segments.append(current)
    anchors = [s for s in segments if len(s) > FLIP_MAX_RUN]
    flipped = set()
    if not anchors:
        return flipped
    for s in segments:
        if len(s) > FLIP_MAX_RUN:
            continue
        before = [a for a in anchors if a[-1][0] < s[0][0]]
        after = [a for a in anchors if a[0][0] > s[-1][0]]
        ref = before[-1][-1][1] if before else after[0][0][1]
        if _angle(s[0][1], ref) > FLIP_DEG:
            flipped.update(i for i, _ in s)
    return flipped


def world_only_sides(frames):
    """Sides whose hand has metric world points in most tracked frames (see hand_points)."""
    sides = []
    for side in ('left', 'right'):
        tracked = sum(1 for f in frames if f.get(f'{side}_hand') is not None or f.get(f'{side}_hand_world') is not None)
        world = sum(1 for f in frames if f.get(f'{side}_hand_world') is not None)
        if tracked and world / tracked >= WORLD_ONLY_SHARE:
            sides.append(side)
    return tuple(sides)


def clamp_hand(targets, side, limits=FINGER_JOINT_LIMITS):
    """Limit each finger bone's rotation relative to its parent; children keep their own bend."""
    if not limits:
        return targets
    for finger in ('thumb', 'index', 'middle', 'ring', 'pinky'):
        parent_old = parent_new = targets[f'{side}_hand'][1]
        for j in (1, 2, 3):
            key = f'{side}_{finger}{j}'
            child_old = targets[key][1]
            rel = mat_mul(transpose(parent_old), child_old)
            angle = rotation_angle(rel)
            limit = limits[f'thumb{j}' if finger == 'thumb' else f'finger{j}']
            if angle > limit:
                rel = partial_rotation(rel, limit / angle)
                CLAMP_LOG.append((side, f'{finger}{j}', round(angle, 1), limit))
            child_new = mat_mul(parent_new, rel)
            targets[key] = ('abs', child_new)
            parent_old, parent_new = child_old, child_new
    return targets


def hand_targets(pts, side, rest_hand, limits=FINGER_JOINT_LIMITS):
    """Absolute rotations for the hand and its 15 finger bones from 21 signer hand points,
    limited to the anatomical range (see FINGER_JOINT_LIMITS)."""
    targets = {}
    palm = palm_frame(pts[0], pts[5], pts[9], pts[17])
    hand_rotation = mat_mul(palm, transpose(rest_hand['palm']))
    targets[f'{side}_hand'] = ('abs', hand_rotation)
    for bone, (a, b) in FINGER_BONES.items():
        if bone.startswith('thumb'):
            continue
        frame = finger_bone_frame(pts, a, b, bone.rstrip('123'))
        targets[f'{side}_{bone}'] = ('abs', mat_mul(frame, transpose(rest_hand[bone])))
    targets.update(thumb_targets(pts, side, rest_hand, hand_rotation))
    return clamp_hand(targets, side, limits)


# ---------- shoulders (shrugs) ----------

SHRUG_LIMITS = (-10.0, 25.0)    # degrees of collarbone rotation: down / up


def shoulder_lifts(p):
    """Height of each shoulder above the middle of the hips (metres, armature axes)."""
    hips = mid(p['l_hip'], p['r_hip'])[2]
    return {'left': p['l_shoulder'][2] - hips, 'right': p['r_shoulder'][2] - hips}


def video_shoulder_neutral(frames):
    """The signer's median shoulder heights and width: the 'no shrug' reference."""
    lifts = {'left': [], 'right': []}
    widths = []
    for f in frames:
        world = f.get('pose_world')
        if world is None:
            continue
        p = {k: mp_to_blender(world[i][:3]) for k, i in POSE.items()}
        for side, v in shoulder_lifts(p).items():
            lifts[side].append(v)
        widths.append(length(sub(p['l_shoulder'], p['r_shoulder'])))
    median = lambda v: sorted(v)[len(v) // 2] if v else None
    return {'left': median(lifts['left']), 'right': median(lifts['right']), 'width': median(widths)}


def shrug_rotations(p, chest_rotation, neutral):
    """Collarbone rotations (armature space) from how far each shoulder is raised above the
    signer's own neutral height. Rotation is about the chest's forward axis only."""
    out = {}
    if not neutral or neutral.get('width') is None:
        return out
    axis = mat_vec(chest_rotation, [0.0, 1.0, 0.0])
    half = neutral['width'] / 2
    for side, lift in shoulder_lifts(p).items():
        if neutral.get(side) is None:
            continue
        delta = math.degrees(math.atan2(lift - neutral[side], half))
        delta = max(SHRUG_LIMITS[0], min(SHRUG_LIMITS[1], delta))
        # +X is the avatar's left: a positive turn about +Y lowers the left end and lifts the right.
        angle = -delta if side == 'left' else delta
        out[side] = mat_mul(axis_angle(axis, math.radians(angle)), chest_rotation)
    return out


def frame_targets(frame, width, height, rest_frames, body=None, world_only_hands=(), skip_hands=()):
    """Targets for one frame, keyed by logical joint names (see bone maps).

    rest_frames: the avatar's rest frames for 'left_hand', 'right_hand', 'head', 'chest'
    (computed in Blender from the rest pose with palm_frame / upright_frame).
    body: optional avatar measurements (see arm_ik_targets). With it, arms are placed by
    wrist position (keeps hand contact); without it, arms copy the signer's bone directions.
    Parts not tracked in this frame are simply left out.
    """
    targets = {}

    world = frame.get('pose_world')
    if world is not None:
        p = {k: mp_to_blender(world[i][:3]) for k, i in POSE.items()}
        # Raising one arm lifts that shoulder; that is not the torso leaning. So the chest's
        # left-right direction uses the shoulder line with its height difference removed
        # (keeps the body turning, drops the false tilt). Hips are too noisy in depth to use.
        across = sub(p['l_shoulder'], p['r_shoulder'])
        chest = upright_frame([0.0, 0.0, 1.0], [across[0], across[1], 0.0])
        chest_rotation = mat_mul(chest, transpose(rest_frames['chest']))
        targets['chest'] = ('abs', chest_rotation)
        shrugs = shrug_rotations(p, chest_rotation, body.get('shoulder_neutral')) if body else {}
        for side, rotation in shrugs.items():
            targets[f'{side}_clavicle'] = ('abs', rotation)
        if body is not None:
            arm_points = p
            if body.get('image_anchor', True) and body.get('video_segments'):
                arm_points = image_anchored_arms(frame, width, height, p,
                                                 (body.get('video_sizes') or {}).get('shoulder_width'),
                                                 body['video_segments'])
            targets.update(arm_ik_targets(arm_points, chest_rotation, body, shrugs))
        else:
            targets['left_upper_arm'] = ('dir', sub(p['l_elbow'], p['l_shoulder']))
            targets['left_forearm'] = ('dir', sub(p['l_wrist'], p['l_elbow']))
            targets['right_upper_arm'] = ('dir', sub(p['r_elbow'], p['r_shoulder']))
            targets['right_forearm'] = ('dir', sub(p['r_wrist'], p['r_elbow']))

    for side in ('left', 'right'):
        rest_hand = rest_frames.get(f'{side}_hand_bones')
        if rest_hand is not None:
            if side in skip_hands:
                continue                     # depth-flipped frame: interpolated, never copied
            segs = (body or {}).get('hand_segments', {}).get(side) if (body or {}).get('hand_anchor') else None
            pts, _kind = hand_points(frame, side, width, height, world_only=side in world_only_hands, segments=segs)
            if pts is not None:
                targets.update(hand_targets(pts, side, rest_hand))
            continue
        # Older behaviour (no rest finger frames given): palm frame + finger directions.
        hand = frame.get(f'{side}_hand')
        if hand is None:
            continue
        h = [mp_to_blender(image_point(pt, width, height)) for pt in hand]
        palm = palm_frame(h[0], h[5], h[9], h[17])
        targets[f'{side}_hand'] = ('abs', mat_mul(palm, transpose(rest_frames[f'{side}_hand'])))
        for bone, (a, b) in FINGER_BONES.items():
            targets[f'{side}_{bone}'] = ('dir', sub(h[b], h[a]))

    face = frame.get('face')
    if face is not None:
        f = {k: mp_to_blender(image_point(face[i], width, height)) for k, i in FACE.items()}
        head = upright_frame(sub(f['forehead'], f['chin']), sub(f['l_eye'], f['r_eye']))
        head_rotation = mat_mul(head, transpose(rest_frames['head']))
        targets['head'] = ('abs', head_rotation)
        # The neck carries part of every head turn, as in a real body.
        targets['neck'] = ('abs', partial_rotation(head_rotation, NECK_SHARE))

    return targets


NECK_SHARE = 0.4


# ---------- face calibration ----------

NEUTRAL_MIN_FRAMES = 3


def face_neutral(frames, resting):
    """The signer's neutral face for one clip: the median score of every blendshape over the
    frames where both hands are at rest (before and after the sign), else the 10th percentile.

    MediaPipe reads a relaxed face as partly squinting, frowning or smiling for some people
    (measured: squint 0.24, brow-down 0.36, smile 0.31 on a neutral ISLRTC signer), which made
    the avatar's eyes look half closed. resting: one bool per frame.
    Returns ({shape: neutral score}, 'rest_frames' | 'percentile')."""
    scored = [f.get('blendshapes') for f in frames]
    at_rest = [s for s, r in zip(scored, resting) if s and r]
    method = 'rest_frames'
    if len(at_rest) < NEUTRAL_MIN_FRAMES:
        at_rest, method = [s for s in scored if s], 'percentile'
    names = sorted({k for s in at_rest for k in s})
    neutral = {}
    for n in names:
        values = sorted(s.get(n, 0.0) for s in at_rest)
        neutral[n] = values[len(values) // 2] if method == 'rest_frames' else values[int(len(values) * 0.1)]
    return neutral, method


def calibrate_score(value, neutral):
    """Neutral -> 0, full -> 1, linear in between; never below 0."""
    if neutral >= 0.999:
        return 0.0
    return max(0.0, min(1.0, (value - neutral) / (1.0 - neutral)))


# ---------- easing a per-frame correction ----------

def ease_weights(corrected, frame_count, ease, curve='linear'):
    """Where to apply a per-frame correction, and how strongly.

    corrected: frames (0-based) that needed a correction. Those get their own correction at
    full strength; frames up to `ease` away from one get the nearest correction, faded out
    (linearly, or with a smoothstep: zero slope at both ends), so the movement glides into and
    out of the correction instead of jumping.
    Returns {frame: (frame whose correction to use, weight 0..1)}."""
    corrected = sorted(set(corrected))
    out = {f: (f, 1.0) for f in corrected}
    for f in range(frame_count):
        if f in out or not corrected:
            continue
        j = min(corrected, key=lambda c: (abs(c - f), c))
        gap = abs(j - f)
        if gap <= ease:
            w = 1.0 - gap / (ease + 1)
            out[f] = (j, smoothstep(w) if curve == 'smoothstep' else w)
    return out


def smoothstep(x):
    """0 -> 0, 1 -> 1, with zero slope at both ends (no visible start or stop of a blend)."""
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def rest_weights(resting, ease):
    """Blend weight towards the rest pose per frame. The blend happens INSIDE each resting
    stretch: 0 at its first and last frame, rising with a smoothstep over `ease` frames, 1 in the
    middle. So the avatar follows the signer until the hand really is at rest, then settles; it
    never heads for the rest pose while the signer's hand is still moving (measured 10 Nov 2026:
    a blend that started before the resting stretch put the avatar's hand up to 0.9 shoulder widths
    below the signer's for 3-4 frames at the start and end of electricity and magnet).
    A stretch that touches the start or end of the clip is at rest from that end.
    resting: one bool per frame."""
    n = len(resting)
    out = [0.0] * n
    for start, end in _runs(resting):
        for i in range(start, end + 1):
            d_in = i - start + 1 if start > 0 else ease + 1
            d_out = end - i + 1 if end < n - 1 else ease + 1
            out[i] = smoothstep(min(d_in, d_out) / (ease + 1))
    return out


def _runs(flags):
    out, start = [], None
    for i, f in enumerate(list(flags) + [False]):
        if f and start is None:
            start = i
        elif not f and start is not None:
            out.append((start, i - 1))
            start = None
    return out
