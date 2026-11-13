"""Audit the avatar's facial blendshapes and the baked facial animation. Runs in Blender;
writes only the report and renders.

    blender -b avatar/avatar_source.blend --python tools/facial_validator.py -- \
        --out reports/face [--renders]

Checks
1. All 52 ARKit blendshapes exist on the face mesh; which of them the secondary meshes
   (eyebrows, eyelashes, eyes, teeth, tongue, hair) also carry.
2. Each blendshape at 1.0: how far it moves the skin (mm) and where (brow / eye / nose /
   cheek / mouth / jaw region). A shape that barely moves, or moves the wrong region,
   is flagged.
3. Left/right pairs: similar size, and "Left" moves the signer's left side (ARKit naming).
4. Eye gaze: the rig has no eye bones, so gaze must come from the eyeLook* shapes. Checks
   that they move the eyeballs, not only the lids.
5. Secondary meshes follow the face: brows and lashes move with the skin under them.
6. Baked signs: the face clip of every sign starts and ends with the body clip (one
   timeline), which shapes are used, and how strongly.
"""

import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ARKIT = [
    'browDownLeft', 'browDownRight', 'browInnerUp', 'browOuterUpLeft', 'browOuterUpRight', 'cheekPuff',
    'cheekSquintLeft', 'cheekSquintRight', 'eyeBlinkLeft', 'eyeBlinkRight', 'eyeLookDownLeft', 'eyeLookDownRight',
    'eyeLookInLeft', 'eyeLookInRight', 'eyeLookOutLeft', 'eyeLookOutRight', 'eyeLookUpLeft', 'eyeLookUpRight',
    'eyeSquintLeft', 'eyeSquintRight', 'eyeWideLeft', 'eyeWideRight', 'jawForward', 'jawLeft', 'jawOpen', 'jawRight',
    'mouthClose', 'mouthDimpleLeft', 'mouthDimpleRight', 'mouthFrownLeft', 'mouthFrownRight', 'mouthFunnel',
    'mouthLeft', 'mouthLowerDownLeft', 'mouthLowerDownRight', 'mouthPressLeft', 'mouthPressRight', 'mouthPucker',
    'mouthRight', 'mouthRollLower', 'mouthRollUpper', 'mouthShrugLower', 'mouthShrugUpper', 'mouthSmileLeft',
    'mouthSmileRight', 'mouthStretchLeft', 'mouthStretchRight', 'mouthUpperUpLeft', 'mouthUpperUpRight',
    'noseSneerLeft', 'noseSneerRight', 'tongueOut',
]
# Expected region of each shape family (checked against where the skin actually moves).
REGION = {'brow': 'brow', 'eyeBlink': 'eye', 'eyeLook': 'eye', 'eyeSquint': 'eye', 'eyeWide': 'eye',
          'cheek': 'cheek', 'nose': 'nose', 'jaw': 'jaw', 'mouth': 'mouth', 'tongue': 'mouth'}
MIN_MOVE_MM = 0.5          # less than this at full strength = the shape does nothing visible
PAIR_RATIO = (0.67, 1.5)   # left/right size within this ratio


def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--out', required=True)
    p.add_argument('--renders', action='store_true')
    p.add_argument('--size', type=int, default=260)
    return p.parse_args(argv)


ARGS = parse_args()
OUT = Path(ARGS.out)
OUT.mkdir(parents=True, exist_ok=True)
ARM = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
MESHES = [o for o in bpy.data.objects if o.type == 'MESH' and o.data.shape_keys]
FACE = max(MESHES, key=lambda o: len(o.data.shape_keys.key_blocks))
HEAD = ARM.matrix_world @ ARM.data.bones[next(b.name for b in ARM.data.bones if b.name.endswith('Head'))].head_local


def mute_all():
    for obj in bpy.data.objects:
        keys = obj.data.shape_keys if obj.type == 'MESH' and obj.data.shape_keys else None
        for owner in (obj, keys):
            if owner is not None and owner.animation_data:
                owner.animation_data.action = None
                for t in owner.animation_data.nla_tracks:
                    t.mute = True
    for o in MESHES:
        for k in o.data.shape_keys.key_blocks[1:]:
            k.value = 0.0


def displacement(obj, name):
    """Per-vertex movement (world, metres) of one shape at 1.0, from the shape data itself."""
    kb = obj.data.shape_keys.key_blocks
    basis = kb[0].data
    shape = kb[name].data
    mw = obj.matrix_world.to_3x3()
    return [(mw @ (shape[i].co - basis[i].co)).length for i in range(len(basis))], basis


def region_of(point, eye_z, mouth_z):
    """Coarse facial region of a world point (character faces -Y, Z up)."""
    if point.z > eye_z + 0.018:
        return 'brow'
    if point.z > eye_z - 0.012:
        return 'eye'
    if point.z > mouth_z + 0.014:
        return 'nose' if abs(point.x - HEAD.x) < 0.018 else 'cheek'
    if point.z > mouth_z - 0.022:
        return 'mouth'
    return 'jaw'


def analyse_face():
    mw = FACE.matrix_world
    # Eye and mouth heights from the shapes themselves: where blinking and jaw opening move skin.
    def centroid(name, top_fraction=0.2):
        d, basis = displacement(FACE, name)
        idx = sorted(range(len(d)), key=lambda i: -d[i])[:max(10, int(len(d) * 0.002))]
        pts = [mw @ basis[i].co for i in idx]
        return sum(pts, Vector()) / len(pts), max(d)
    eye_c, _ = centroid('eyeBlinkLeft')
    eye_c2, _ = centroid('eyeBlinkRight')
    mouth_c, _ = centroid('mouthPucker')
    eye_z, mouth_z = (eye_c.z + eye_c2.z) / 2, mouth_c.z

    shapes, problems = {}, []
    present = {k.name for k in FACE.data.shape_keys.key_blocks}
    tongue = next((o for o in MESHES if 'tongue' in o.name.lower()), None)
    for name in ARKIT:
        if name not in present:
            problems.append(f'{name}: missing on the face mesh')
            continue
        if name == 'tongueOut' and tongue is not None and 'tongueOut' in tongue.data.shape_keys.key_blocks:
            # The tongue is its own mesh; the face skin is not supposed to move for this shape.
            d, _ = displacement(tongue, name)
            shapes[name] = {'max_mm': round(max(d) * 1000, 2), 'mesh': tongue.name, 'region': 'mouth',
                            'expected_region': 'mouth', 'centroid_side_x': 0.0, 'vertices_moved': sum(1 for x in d if x > 0.0002)}
            if max(d) * 1000 < MIN_MOVE_MM:
                problems.append(f'tongueOut: the tongue moves only {shapes[name]["max_mm"]} mm')
            continue
        d, basis = displacement(FACE, name)
        peak = max(d)
        moved = [i for i in range(len(d)) if d[i] > max(peak * 0.5, 1e-6)]
        c = sum((mw @ basis[i].co for i in moved), Vector()) / max(1, len(moved))
        region = region_of(c, eye_z, mouth_z)
        family = next(v for k, v in REGION.items() if name.startswith(k))
        entry = {'max_mm': round(peak * 1000, 2), 'vertices_moved': sum(1 for x in d if x > 0.0002),
                 'centroid_side_x': round(c.x - HEAD.x, 4), 'region': region, 'expected_region': family}
        if peak * 1000 < MIN_MOVE_MM:
            problems.append(f'{name}: moves the skin only {entry["max_mm"]} mm at full strength')
        # Eye-look shapes move the lids a little; lids sit on the eye/brow border, so accept either.
        # Regions are cut by height, so neighbours overlap: brow shapes pull the upper lid (eye
        # band), squints raise the lower lid and cheek, and so on.
        ok_regions = {family} | ({'brow'} if family == 'eye' else set()) | ({'eye'} if family == 'brow' else set()) \
            | ({'cheek'} if family == 'eye' else set()) | ({'jaw', 'cheek'} if family == 'mouth' else set()) \
            | ({'mouth'} if family in ('jaw', 'cheek') else set()) | ({'cheek', 'eye'} if family == 'nose' else set()) \
            | ({'eye', 'nose'} if family == 'cheek' else set())
        if region not in ok_regions:
            problems.append(f'{name}: moves the {region} region, expected {family}')
        shapes[name] = entry

    pairs = {}
    for name in ARKIT:
        if name.endswith('Left') and name in shapes and name[:-4] + 'Right' in shapes:
            l, r = shapes[name], shapes[name[:-4] + 'Right']
            ratio = round(l['max_mm'] / r['max_mm'], 2) if r['max_mm'] else None
            # The character faces -Y, so the signer's left is +X.
            sides_ok = (l['centroid_side_x'] > 0 > r['centroid_side_x']) if not name.startswith(('jaw', 'mouthLeft')) else True
            pairs[name[:-4]] = {'ratio_left_right': ratio, 'left_is_signers_left': sides_ok}
            if ratio is None or not (PAIR_RATIO[0] <= ratio <= PAIR_RATIO[1]):
                problems.append(f'{name[:-4]}Left/Right: sizes differ (ratio {ratio})')
            if not sides_ok:
                problems.append(f'{name[:-4]}Left/Right: "Left" does not move the signer\'s left side')
    return shapes, pairs, problems


def secondary_meshes():
    """Which ARKit shapes each secondary mesh carries, and whether it moves with the face."""
    out = {}
    for o in MESHES:
        if o is FACE:
            continue
        names = [k.name for k in o.data.shape_keys.key_blocks[1:] if k.name in ARKIT]
        moves = {}
        for n in names:
            d, _ = displacement(o, n)
            moves[n] = round(max(d) * 1000, 2) if d else 0.0
        out[o.name] = {'arkit_shapes': len(names), 'max_mm': moves}
    return out


def gaze_check(sec):
    """No eye bones: gaze must come from eyeLook* shapes moving the eyeball mesh."""
    eye_bones = [b.name for b in ARM.data.bones if 'eye' in b.name.lower()]
    look = [n for n in ARKIT if n.startswith('eyeLook')]
    eyeball = next((name for name, s in sec.items() if any(n in s['max_mm'] for n in look)
                    and 'lash' not in name.lower() and 'brow' not in name.lower()), None)
    moving = {n: sec[eyeball]['max_mm'].get(n, 0.0) for n in look} if eyeball else {}
    problems = []
    if not eye_bones and not eyeball:
        problems.append('no eye bones and no eyeball mesh with eyeLook shapes: the eyes cannot look around')
    elif eyeball:
        still = [n for n, mm in moving.items() if mm < MIN_MOVE_MM]
        if still:
            problems.append(f'eyeball mesh "{eyeball}" does not move for: {", ".join(still)}')
    return {'eye_bones': eye_bones, 'eyeball_mesh': eyeball, 'eyeball_max_mm': moving}, problems


def follow_check(sec):
    """Brows and lashes must move with the skin right under them, or they float off it.

    For every shape that moves the skin under a brow/lash mesh by at least 1 mm, compare the
    mesh's movement with the movement of the nearest skin vertices (not the face's maximum:
    a smile should not move the eyebrows)."""
    from mathutils.kdtree import KDTree
    basis = FACE.data.shape_keys.key_blocks[0].data
    mw = FACE.matrix_world
    tree = KDTree(len(basis))
    for i, v in enumerate(basis):
        tree.insert(mw @ v.co, i)
    tree.balance()
    problems, ratios = [], {}
    for o in MESHES:
        kind = 'brow' if 'brow' in o.name.lower() else 'lash' if 'lash' in o.name.lower() else None
        if not kind:
            continue
        ob = o.data.shape_keys.key_blocks[0].data
        nearest = sorted({tree.find(o.matrix_world @ v.co)[1] for v in ob})
        for shape, mm in sec[o.name]['max_mm'].items():
            skin_d, _ = displacement(FACE, shape)
            under = max(skin_d[i] for i in nearest) * 1000
            if under < 1.0:
                continue
            r = round(mm / under, 2)
            ratios[f'{o.name}:{shape}'] = r
            if r < 0.5 or r > 2.0:
                problems.append(f'{o.name} moves {mm} mm for {shape} while the skin under it moves {under:.1f} mm')
    return ratios, problems


def baked_tracks():
    """Each sign's face clip against its body clip: same frames (one timeline)."""
    out, problems = {}, []
    body = {t.name: (min(s.frame_start for s in t.strips), max(s.frame_end for s in t.strips))
            for t in ARM.animation_data.nla_tracks} if ARM.animation_data else {}
    keys = FACE.data.shape_keys
    face = {t.name: t for t in keys.animation_data.nla_tracks} if keys.animation_data else {}
    for name, (b0, b1) in sorted(body.items()):
        if name == 'idle':
            continue
        t = face.get(name)
        if not t:
            out[name] = {'face_clip': False}
            problems.append(f'{name}: body clip has no face clip (no facial grammar)')
            continue
        f0 = min(s.frame_start for s in t.strips)
        f1 = max(s.frame_end for s in t.strips)
        action = t.strips[0].action
        peaks = {}
        for fc in action.fcurves:
            shape = fc.data_path.split('"')[1] if '"' in fc.data_path else fc.data_path
            peaks[shape] = round(max(k.co[1] for k in fc.keyframe_points), 3) if fc.keyframe_points else 0
        top = sorted(peaks.items(), key=lambda kv: -kv[1])[:6]
        out[name] = {'face_clip': True, 'body_frames': [b0, b1], 'face_frames': [f0, f1],
                     'in_sync': abs(f0 - b0) <= 1 and abs(f1 - b1) <= 1, 'shapes_animated': len(peaks),
                     'strongest': dict(top)}
        if not out[name]['in_sync']:
            problems.append(f'{name}: face clip frames {f0}-{f1} do not match body clip {b0}-{b1}')
    return out, problems


def render_sheet():
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.render.resolution_x = scene.render.resolution_y = ARGS.size
    scene.world = scene.world or bpy.data.worlds.new('face')
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes['Background']
    bg.inputs[0].default_value = (0.62, 0.62, 0.65, 1)
    bg.inputs[1].default_value = 1.0
    cam = bpy.data.objects.new('face_cam', bpy.data.cameras.new('face_cam'))
    cam.data.lens = 85
    target = HEAD + Vector((0, 0, 0.07))
    cam.location = target + Vector((0, -0.62, 0.02))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.collection.objects.link(cam)
    scene.camera = cam
    light = bpy.data.objects.new('face_key', bpy.data.lights.new('face_key', 'AREA'))
    light.data.energy, light.data.size = 60, 1.0
    light.location = target + Vector((0.4, -0.8, 0.3))
    light.rotation_euler = (target - light.location).to_track_quat('-Z', 'Y').to_euler()
    scene.collection.objects.link(light)
    renders = {}
    for name in ['neutral'] + ARKIT:
        for o in MESHES:
            for k in o.data.shape_keys.key_blocks[1:]:
                k.value = 1.0 if k.name == name else 0.0
        bpy.context.view_layer.update()
        path = OUT / f'shape_{name}.png'
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        renders[name] = path.name
    for o in MESHES:
        for k in o.data.shape_keys.key_blocks[1:]:
            k.value = 0.0
    return renders


def main():
    mute_all()
    shapes, pairs, problems = analyse_face()
    sec = secondary_meshes()
    gaze, gp = gaze_check(sec)
    follow, fp = follow_check(sec)
    tracks, tp = baked_tracks()
    report = {'face_mesh': FACE.name, 'arkit_present': sum(n in shapes for n in ARKIT), 'arkit_expected': len(ARKIT),
              'shapes': shapes, 'left_right_pairs': pairs, 'secondary_meshes': sec, 'gaze': gaze,
              'secondary_follow_ratio': follow, 'baked_tracks': tracks,
              'problems': problems + gp + fp + tp}
    if ARGS.renders:
        report['renders'] = render_sheet()
    (OUT / 'face_report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f'ARKit shapes present: {report["arkit_present"]}/{len(ARKIT)}')
    for p in report['problems']:
        print('  problem:', p)
    print(f'Wrote {OUT / "face_report.json"}')


main()
