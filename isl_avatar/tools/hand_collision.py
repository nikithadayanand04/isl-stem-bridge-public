"""Finger interpenetration on the deformed skin, and a thumb correction that removes it.
Runs in Blender. Used by tools/retarget_blender.py (bake) and tools/rig_validator.py (check).

Measuring: skin vertices are grouped by the finger segment (bone) that moves them most. A
finger segment is close to convex, so each is replaced by its convex hull; a vertex of another
finger inside that hull is inside the finger, and its depth is the distance to the nearest hull
face (exact for convex shapes). Segments of the same finger are not compared (they share skin
at the joint), nor is the palm (its hollow is not convex).

Correcting: when the signer's thumb touches a finger, copying the directions onto a hand with
different proportions can leave the avatar's thumb partly inside that finger (measured 7 Nov
2026: 5-9 mm deep in most signing frames of several signs). The correction turns the whole thumb
at its base, by the smallest angle that brings the deepest point back to the finger's surface,
and repeats until what is left is skin contact. The touch is kept; only the overlap is removed.
"""

import math

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

FINGERS = ('thumb', 'index', 'middle', 'ring', 'pinky')


def body_mesh(arm):
    """The skinned body: the largest mesh parented to the armature."""
    return max((o for o in bpy.data.objects if o.type == 'MESH' and o.parent == arm),
               key=lambda o: len(o.data.vertices))


def phalanx_vertices(body, arm, bone_map, side):
    """Vertex indices per finger segment ('index2', ...): the bone that moves each vertex most.
    Only groups that are bones count (MPFB also leaves helper groups such as "Right")."""
    names = {bone_map[f'{side}_{f}{j}']: f'{f}{j}' for f in FINGERS for j in (1, 2, 3)}
    bone_groups = {g.index: g.name for g in body.vertex_groups if g.name in arm.data.bones}
    out = {}
    for v in body.data.vertices:
        best = max(((g.weight, bone_groups[g.group]) for g in v.groups if g.group in bone_groups), default=None)
        if best and best[1] in names:
            out.setdefault(names[best[1]], []).append(v.index)
    return {k: v for k, v in out.items() if len(v) >= 8}


def deformed_points(body, segments):
    """World positions of the segments' vertices on the posed (deformed) skin."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    mw = body.matrix_world
    out = {name: [mw @ mesh.vertices[i].co for i in idx] for name, idx in segments.items()}
    evaluated.to_mesh_clear()
    return out


def hull_planes(points):
    """Outward face planes (unit normal, offset) of the convex hull of these points."""
    bm = bmesh.new()
    for p in points:
        bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    bm.normal_update()
    centre = sum(points, Vector()) / len(points)
    planes = []
    for f in bm.faces:
        n = f.normal.copy()
        if n.length < 1e-9:
            continue
        d = n.dot(f.verts[0].co)
        if n.dot(centre) - d > 0:          # make the normal point outwards
            n, d = -n, -d
        planes.append((n, d))
    bm.free()
    return planes


def _box(points):
    return (Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points))),
            Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points))))


def _boxes_touch(a, b):
    (la, ha), (lb, hb) = a, b
    return not any(ha[k] < lb[k] or hb[k] < la[k] for k in range(3))


def _deepest_inside(points, planes):
    """(depth, point, outward normal of the nearest hull face) of the deepest point inside."""
    best = (0.0, None, None)
    for p in points:
        worst, normal = None, None
        for n, d in planes:
            gap = d - n.dot(p)               # > 0 on the inner side of this face
            if gap <= 0:
                worst = None
                break
            if worst is None or gap < worst:
                worst, normal = gap, n
        if worst is not None and worst > best[0]:
            best = (worst, p, normal)
    return best


def overlaps(points):
    """{"index-thumb": depth_mm, ...} for every pair of fingers whose skins overlap."""
    boxes = {k: _box(v) for k, v in points.items()}
    hulls, hits = {}, {}
    names = sorted(points)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            fa, fb = a.rstrip('123'), b.rstrip('123')
            if fa == fb or not _boxes_touch(boxes[a], boxes[b]):
                continue
            depth = 0.0
            for inside, other in ((a, b), (b, a)):
                if other not in hulls:
                    hulls[other] = hull_planes(points[other])
                depth = max(depth, _deepest_inside(points[inside], hulls[other])[0])
            if depth > 0:
                key = '-'.join(sorted((fa, fb)))
                hits[key] = max(hits.get(key, 0.0), round(depth * 1000, 1))
    return hits


def thumb_penetrations(points):
    """Every thumb/finger overlap: a list of (depth m, point, push direction for the thumb,
    thumb segment), one per overlapping pair of segments and direction (thumb skin in a
    finger, or finger skin in the thumb)."""
    boxes = {k: _box(v) for k, v in points.items()}
    found = []
    thumb = [k for k in points if k.startswith('thumb')]
    others = [k for k in points if not k.startswith('thumb')]
    hulls = {}
    for t in thumb:
        for o in others:
            if not _boxes_touch(boxes[t], boxes[o]):
                continue
            if o not in hulls:
                hulls[o] = hull_planes(points[o])
            if t not in hulls:
                hulls[t] = hull_planes(points[t])
            depth, p, n = _deepest_inside(points[t], hulls[o])        # thumb skin inside a finger
            if depth > 0:
                found.append((depth, p, n, t))                        # push the thumb out along n
            depth, p, n = _deepest_inside(points[o], hulls[t])        # finger skin inside the thumb
            if depth > 0:
                found.append((depth, p, -n, t))                       # move the thumb away from it
    return found


def thumb_penetration(points):
    """The deepest thumb/finger overlap: (depth m, point, push), or (0, None, None)."""
    found = thumb_penetrations(points)
    return max(found, key=lambda f: f[0])[:3] if found else (0.0, None, None)


def resolve_thumb(arm, body, segments, thumb_bones, target_m, max_iterations, max_deg):
    """Turn the thumb until it is no deeper than target_m inside any finger.

    thumb_bones: [(segment name, bone name)] from the base outwards, e.g. thumb1 then thumb2.
    The base is turned first (moves the whole thumb, keeps its shape); if overlap is left, the
    next joint is bent, which moves only the outer part. Each bone turns at most max_deg.

    The armature must already be in the pose to correct, with no active action (so manual
    rotations stick). The best pose found for each bone is kept, even if the target is not
    reached. Returns ({bone: delta quaternion in its local basis}, depth before m, depth after m,
    largest turn in degrees)."""
    deltas = {}
    before = None
    depth = 0.0
    largest = 0.0
    for segment, bone in thumb_bones:
        level = int(segment[-1])
        movable = {f'thumb{j}' for j in range(level, 4)}     # this bone carries itself and all outer segments
        pb = arm.pose.bones[bone]
        pb.rotation_mode = 'QUATERNION'
        start = pb.rotation_quaternion.copy()
        turned = 0.0
        best = (None, start.copy())
        for _ in range(max_iterations + 1):
            found = thumb_penetrations(deformed_points(body, segments))
            depth = max((f[0] for f in found), default=0.0)
            if before is None:
                before = depth
            if best[0] is None or depth < best[0]:
                best = (depth, pb.rotation_quaternion.copy())
            push = [f for f in found if f[3] in movable]
            if depth <= target_m or turned >= max_deg or not push:
                break
            # A thumb tip pressed between two fingers is pushed both ways; one push at a time
            # makes it bounce between them (measured). Every overlap pushes at once, in
            # proportion to its depth, so the thumb leaves the gap in the direction that clears
            # all of them.
            pivot = arm.matrix_world @ pb.head
            axis = Vector()
            for d, p, n, _ in push:
                axis += (p - pivot).cross(n) * d
            weight = sum(f[0] for f in push)
            lever = sum((f[1] - pivot).length * f[0] for f in push) / weight
            if axis.length < 1e-12 or lever < 1e-6:
                break
            angle = min(math.degrees((max(f[0] for f in push) - target_m * 0.5) / lever), max_deg - turned)
            world = Matrix.Rotation(math.radians(angle), 3, (arm.matrix_world.to_3x3().inverted() @ axis).normalized())
            current = pb.matrix.to_3x3().normalized()
            pb.rotation_quaternion = pb.rotation_quaternion @ (current.inverted() @ world @ current).to_quaternion()
            bpy.context.view_layer.update()
            turned += abs(angle)
        # Keep the best pose seen (a step can overshoot into another finger).
        depth = best[0]
        pb.rotation_quaternion = best[1]
        bpy.context.view_layer.update()
        deltas[bone] = start.inverted() @ best[1]
        largest = max(largest, 2 * math.degrees(math.acos(min(1.0, abs(deltas[bone].w)))))
        if depth <= target_m:
            break
    return deltas, before or 0.0, depth, largest
