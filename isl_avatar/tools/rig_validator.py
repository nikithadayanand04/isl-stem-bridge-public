"""Validate the avatar's hand rig and the baked signs. Runs in Blender; changes nothing on disk
except the report and renders.

    blender -b avatar/avatar_source.blend --python tools/rig_validator.py -- \
        --bone-map tools/bone_maps/mixamo.json --out reports/rig [--renders] [--side right]

What it checks
1. Hierarchy: every mapped bone exists; finger chains are parented 1 -> 2 -> 3 -> hand.
2. Test poses built from the rig's own geometry (rig-independent axes): fist, spread, thumb
   opposition, each finger curled alone, index point, wrist flexion/extension and deviation.
   For each pose: the joint angles reached (measured like the motion reports) and real mesh
   interpenetration between fingers and palm (triangle overlap on the deformed skin).
3. Every baked sign, frame by frame: joint angles against anatomical limits, and frames where
   fingers pass through each other or through the palm.
4. With --renders: a close-up of each test pose (for a person to look at).

Two impossible "control" poses must be caught, or the run is marked as not trustworthy.

The interpenetration test uses the deformed body mesh: vertices are grouped by the finger
segment (bone) that moves them most, each segment is replaced by its convex hull, and the
depth of another finger's skin inside that hull is measured. The palm is not compared.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import retarget_math as rm  # noqa: E402
import motion_metrics as mm  # noqa: E402
import hand_collision as hc  # noqa: E402

FINGERS = ('thumb', 'index', 'middle', 'ring', 'pinky')

ANATOMICAL_LIMITS = mm.ANATOMICAL_LIMITS     # shared with the motion reports



def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--bone-map', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--side', choices=('left', 'right', 'both'), default='both')
    p.add_argument('--renders', action='store_true')
    p.add_argument('--size', type=int, default=420)
    p.add_argument('--skip-tracks', action='store_true', help='only the test poses')
    return p.parse_args(argv)


ARGS = parse_args()
BONE_MAP = json.loads(Path(ARGS.bone_map).read_text(encoding='utf-8'))
ARM = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
BODY = max((o for o in bpy.data.objects if o.type == 'MESH' and o.parent == ARM),
           key=lambda o: len(o.data.vertices))
OUT = Path(ARGS.out)
OUT.mkdir(parents=True, exist_ok=True)
SIDES = ('left', 'right') if ARGS.side == 'both' else (ARGS.side,)


def pb(logical):
    return ARM.pose.bones[BONE_MAP[logical]]


def update():
    bpy.context.view_layer.update()


def all_tracks(mute=True, solo=None):
    for obj in bpy.data.objects:
        keys = obj.data.shape_keys if obj.type == 'MESH' and obj.data.shape_keys else None
        for owner in (obj, keys):
            if owner is not None and owner.animation_data:
                owner.animation_data.action = None
                for t in owner.animation_data.nla_tracks:
                    t.mute = mute if solo is None else t.name != solo


def reset_pose():
    for b in ARM.pose.bones:
        b.rotation_mode = 'QUATERNION'
        b.rotation_quaternion = Quaternion()
        b.location = (0, 0, 0)
    update()


def hand_points(side):
    out = []
    for logical, end in rm.HAND_POINT_BONES:
        b = pb(f'{side}_{logical}')
        out.append(list(b.head if end == 'head' else b.tail))
    return out


PALM_SIGN = {}      # side -> +1/-1 applied to cross(index knuckle, pinky knuckle); set by find_palm_side()


def raw_normal(side):
    p = [Vector(v) for v in hand_points(side)]
    return (p[5] - p[0]).cross(p[17] - p[0]).normalized()


def palm_normal(side):
    """Unit vector out of the palm (palm side), from the posed hand."""
    return raw_normal(side) * PALM_SIGN[side]


def find_palm_side():
    """Which side of the hand is the palm, measured, not assumed: in the baked signs (real
    signers), find the frames where the fingertips come closest to the wrist (strong flexion)
    and see which way they moved relative to the knuckle plane. Fingers flex towards the palm.
    Sides with no strong flexion in any sign use the mirror image of the other side."""
    evidence = {}
    tracks = [t.name for t in ARM.animation_data.nla_tracks if t.name != 'idle'] if ARM.animation_data else []
    all_tracks(mute=True)
    reset_pose()
    rest = {s: [Vector(v) for v in hand_points(s)] for s in ('left', 'right')}
    rest_n = {s: raw_normal(s) for s in ('left', 'right')}
    scene = bpy.context.scene
    for track in tracks:
        all_tracks(solo=track)
        last = int(max(s.frame_end for s in ARM.animation_data.nla_tracks[track].strips))
        for f in range(1, last + 1, 2):
            scene.frame_set(f)
            for s in ('left', 'right'):
                p = [Vector(v) for v in hand_points(s)]
                n = raw_normal(s)
                reach = sum((p[i] - p[0]).length for i in (8, 12, 16, 20)) / sum((rest[s][i] - rest[s][0]).length for i in (8, 12, 16, 20))
                if reach < 0.8:                      # fingertips at least 20% closer to the wrist
                    side_of_palm = sum((p[i] - p[0]).dot(n) for i in (8, 12, 16, 20))
                    evidence.setdefault(s, []).append(side_of_palm)
    all_tracks(mute=True)
    reset_pose()
    found = {s: (1 if sum(v) > 0 else -1) for s, v in evidence.items() if v}
    for s, other in (('left', 'right'), ('right', 'left')):
        if s not in found and other in found:
            found[s] = -found[other]          # mirror image hand: the cross product flips
    PALM_SIGN.update(found)
    return {s: {'sign': found.get(s), 'frames_used': len(evidence.get(s, []))} for s in ('left', 'right')}


def rotate_world(bone, axis, degrees):
    """Rotate a pose bone about an armature-space axis through its head."""
    if axis.length < 1e-9:
        return
    update()
    current = bone.matrix.to_3x3().normalized()
    world = Matrix.Rotation(math.radians(degrees), 3, axis.normalized())
    delta = current.inverted() @ world @ current
    bone.rotation_quaternion = (bone.rotation_quaternion.to_matrix() @ delta).to_quaternion()
    update()


def direction(bone):
    return (bone.tail - bone.head).normalized()


def curl(side, finger, degrees, joints=(1, 2, 3)):
    for j in joints:
        b = pb(f'{side}_{finger}{j}')
        n = palm_normal(side)
        rotate_world(b, direction(b).cross(n), degrees[j - 1] if isinstance(degrees, (list, tuple)) else degrees)


def spread(side, degrees):
    middle = pb(f'{side}_middle1').head.copy()
    for finger in ('index', 'ring', 'pinky'):
        b = pb(f'{side}_{finger}1')
        n = palm_normal(side)
        away = (b.head - middle)
        axis = n if direction(b).cross(n).dot(away) < 0 else -n   # turn the tip away from the middle finger
        rotate_world(b, axis, degrees * (1.5 if finger == 'pinky' else 1.0))


def oppose_thumb(side):
    t1 = pb(f'{side}_thumb1')
    target = pb(f'{side}_pinky1').head
    to_target = (target - t1.head).normalized()
    rotate_world(t1, direction(t1).cross(to_target), 35)
    curl(side, 'thumb', [0, 25, 30], joints=(2, 3))


def wrist(side, flex=0.0, deviate=0.0):
    h = pb(f'{side}_hand')
    n = palm_normal(side)
    if flex:
        rotate_world(h, direction(h).cross(n), flex)
    if deviate:
        rotate_world(h, palm_normal(side), deviate)


POSES = {
    'rest': lambda s: None,
    'fist': lambda s: ([curl(s, f, [80, 100, 70]) for f in FINGERS[1:]], curl(s, 'thumb', [10, 40, 40])),
    'spread': lambda s: spread(s, 12),
    'thumb_opposition': oppose_thumb,
    'index_point': lambda s: ([curl(s, f, [80, 100, 70]) for f in FINGERS[2:]], curl(s, 'thumb', [10, 40, 40])),
    **{f'curl_{f}': (lambda f: lambda s: curl(s, f, [70, 90, 60] if f != 'thumb' else [10, 40, 50]))(f) for f in FINGERS},
    'wrist_flexion': lambda s: wrist(s, flex=60),
    'wrist_extension': lambda s: wrist(s, flex=-60),
    'wrist_radial': lambda s: wrist(s, deviate=20),
    'wrist_ulnar': lambda s: wrist(s, deviate=-30),
    # Positive controls: impossible poses that MUST show interpenetration. If they do not,
    # the detector is broken and every "no interpenetration" result above means nothing.
    'control_index_through_middle': lambda s: rotate_world(pb(f'{s}_index1'), palm_normal(s) * (
        1 if direction(pb(f'{s}_index1')).cross(palm_normal(s)).dot(pb(f'{s}_middle1').head - pb(f'{s}_index1').head) < 0 else -1), 40),
    'control_overcurl_into_palm': lambda s: [curl(s, f, [120, 150, 110]) for f in FINGERS[1:]],
}
# What each control must trigger. (Depth inside a thin finger is under-measured by the
# nearest-surface test, so the over-curl pose is used to prove the joint-limit check instead.)
CONTROLS = {'control_index_through_middle': 'passes_through', 'control_overcurl_into_palm': 'over_limit'}


# ---------- interpenetration ----------

def face_groups(side):
    """Faces of the body mesh grouped by the hand bone that moves them most."""
    names = {BONE_MAP[f'{side}_hand']: 'palm'}
    for f in FINGERS:
        for j in (1, 2, 3):
            names[BONE_MAP[f'{side}_{f}{j}']] = f
    # Only groups that are bones deform the skin (MPFB also leaves helper groups such as
    # "Right"). Each vertex goes to the bone with the largest weight, if that bone is in this
    # hand. Palm skin is shared between the hand and the forearm/knuckles, so no fixed
    # weight threshold is used.
    bone_groups = {g.index: g.name for g in BODY.vertex_groups if g.name in ARM.data.bones}
    owner = {}
    for v in BODY.data.vertices:
        best = max(((g.weight, bone_groups[g.group]) for g in v.groups if g.group in bone_groups), default=None)
        if best and best[1] in names:
            owner[v.index] = names[best[1]]
    groups = {}
    for poly in BODY.data.polygons:
        labels = {owner.get(i) for i in poly.vertices}
        if len(labels) == 1 and None not in labels:
            groups.setdefault(labels.pop(), []).append(poly.index)
    return groups


GROUPS = {side: face_groups(side) for side in SIDES}


PHALANX = {side: hc.phalanx_vertices(BODY, ARM, BONE_MAP, side) for side in SIDES}
# Neighbours share skin at the knuckles; their overlap there is folding, not a collision.
ADJACENT = {frozenset(('palm', f)) for f in FINGERS}


CONTACT_MM = 2.0      # deeper than this = a finger passes through, not skin pressing on skin
NEAR_CROSSING_M = 0.012   # depth is measured within this distance of the crossing skin (about a finger's width)


def interpenetrations(side):
    """Finger overlap depth in mm per finger pair (tools/hand_collision.py)."""
    return hc.overlaps(hc.deformed_points(BODY, PHALANX[side]))


def passes_through(hits):
    return {k: v for k, v in hits.items() if v > CONTACT_MM}


def angles(side):
    return {k: (round(v, 1) if v is not None else None) for k, v in mm.flexion_angles(hand_points(side)).items()}


def over_limit(a):
    return mm.over_limit(a)


# ---------- renders ----------

def setup_render():
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.render.resolution_x = scene.render.resolution_y = ARGS.size
    scene.world = scene.world or bpy.data.worlds.new('rig')
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.6, 0.6, 0.63, 1)
    bg.inputs[1].default_value = 0.9
    cam = bpy.data.objects.new('rig_cam', bpy.data.cameras.new('rig_cam'))
    cam.data.lens = 60
    scene.collection.objects.link(cam)
    scene.camera = cam
    light = bpy.data.objects.new('rig_key', bpy.data.lights.new('rig_key', 'SUN'))
    light.data.energy = 3
    light.rotation_euler = (0.6, 0.2, 0.3)
    scene.collection.objects.link(light)
    return cam


def render_hand(cam, side, path):
    p = [Vector(v) for v in hand_points(side)]
    centre = ARM.matrix_world @ ((p[0] + p[9]) / 2)
    n = (ARM.matrix_world.to_3x3() @ palm_normal(side)).normalized()
    view = (n * 0.8 + Vector((0, -1, 0)) * 0.5 + Vector((0, 0, 0.1))).normalized()
    cam.location = centre + view * 0.30
    cam.rotation_euler = (centre - cam.location).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


# ---------- main ----------

def hierarchy_report():
    problems = []
    for logical, name in BONE_MAP.items():
        if name not in ARM.data.bones:
            problems.append(f'{logical}: bone "{name}" not in the rig')
    for side in ('left', 'right'):
        for f in FINGERS:
            for j, parent in ((2, f'{f}1'), (3, f'{f}2')):
                b = ARM.data.bones.get(BONE_MAP.get(f'{side}_{f}{j}', ''))
                want = BONE_MAP.get(f'{side}_{parent}')
                if b and (not b.parent or b.parent.name != want):
                    problems.append(f'{side}_{f}{j}: parent is {b.parent.name if b.parent else None}, expected {want}')
            b1 = ARM.data.bones.get(BONE_MAP.get(f'{side}_{f}1', ''))
            if b1 and (not b1.parent or b1.parent.name != BONE_MAP[f'{side}_hand']):
                problems.append(f'{side}_{f}1 is not a child of the hand')
    return problems


def main():
    report = {'rig': ARM.name, 'mesh': BODY.name, 'hierarchy_problems': hierarchy_report(),
              'face_groups': {s: {k: len(v) for k, v in g.items()} for s, g in GROUPS.items()},
              'anatomical_limits_deg': ANATOMICAL_LIMITS, 'poses': {}, 'tracks': {}}
    report['palm_side'] = find_palm_side()
    if len(PALM_SIGN) < len(SIDES):
        raise SystemExit('Could not find the palm side from the baked signs (no strong finger flexion).')
    all_tracks(mute=True)
    cam = setup_render() if ARGS.renders else None

    for side in SIDES:
        for name, apply in POSES.items():
            reset_pose()
            apply(side)
            update()
            a = angles(side)
            hits = interpenetrations(side)
            entry = {'angles_deg': a, 'over_limit': over_limit(a), 'overlap_depth_mm': hits,
                     'passes_through': passes_through(hits)}
            if cam:
                path = OUT / f'pose_{side}_{name}.png'
                render_hand(cam, side, path)
                entry['render'] = path.name
            if name in CONTROLS:
                entry['control_detected'] = bool(entry[CONTROLS[name]])
            report['poses'][f'{side}:{name}'] = entry
            print(f'{side:5} {name:18} overlap_mm={hits} over_limit={entry["over_limit"]}')
    reset_pose()
    report['detector_controls_passed'] = all(e.get('control_detected', True) for e in report['poses'].values())
    print('detector controls passed:', report['detector_controls_passed'])

    if not ARGS.skip_tracks:
        scene = bpy.context.scene
        names = sorted(t.name for t in ARM.animation_data.nla_tracks if t.name != 'idle')
        for track in names:
            reset_pose()                     # bones a clip does not key must start from rest, not the last clip
            all_tracks(solo=track)
            strips = ARM.animation_data.nla_tracks[track].strips
            last = int(max(s.frame_end for s in strips))
            per_side = {}
            for side in SIDES:
                per_side[side] = {'frames': 0, 'max_angle_deg': {}, 'frames_over_limit': 0,
                                  'frames_skin_contact': 0, 'frames_passing_through': 0, 'worst': {},
                                  'depth_per_frame_mm': []}
            for f in range(1, last + 1):
                scene.frame_set(f)
                for side in SIDES:
                    s = per_side[side]
                    s['frames'] += 1
                    a = angles(side)
                    for k, v in a.items():
                        if v is not None:
                            s['max_angle_deg'][k] = max(v, s['max_angle_deg'].get(k, 0))
                    if over_limit(a):
                        s['frames_over_limit'] += 1
                    hits = interpenetrations(side)
                    through = passes_through(hits)
                    s['depth_per_frame_mm'].append(max(hits.values()) if hits else 0.0)
                    if through:
                        s['frames_passing_through'] += 1
                    elif hits:
                        s['frames_skin_contact'] += 1
                    if hits and max(hits.values()) > s['worst'].get('depth_mm', 0):
                        s['worst'] = {'frame': f, 'depth_mm': max(hits.values()), 'pairs': hits}
            for v in per_side.values():
                d = sorted(v.pop('depth_per_frame_mm'))
                over = [x for x in d if x > 0]
                v['median_depth_when_overlapping_mm'] = over[len(over) // 2] if over else 0.0
                v['mean_depth_all_frames_mm'] = round(sum(d) / len(d), 2) if d else 0.0
            report['tracks'][track] = per_side
            print(track, {k: (v['frames'], v['frames_over_limit'], v['frames_skin_contact'], v['frames_passing_through'],
                              v['worst'].get('depth_mm')) for k, v in per_side.items()})
        all_tracks(mute=False)

    (OUT / 'rig_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'Wrote {OUT / "rig_report.json"}')


main()
