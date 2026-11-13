"""Retarget extracted ISL motion onto the avatar in Blender and bake one clip per sign.

Runs inside Blender 4.2 or newer (background mode is fine). The maths lives in
retarget_math.py, which is unit-tested outside Blender.

1. List the avatar's bones (to fill in a bone map):
   blender avatar/avatar_source.blend --background --python tools/retarget_blender.py -- --list-bones

2. Bake a sign (only motion whose quality check passed is accepted):
   blender avatar/avatar_source.blend --background --python tools/retarget_blender.py -- \
       --motion motion/magnet.json --bone-map tools/bone_maps/mixamo.json --save

3. Export every baked sign into the web player's model:
   blender avatar/avatar_source.blend --background --python tools/retarget_blender.py -- \
       --export avatar/avatar.glb

Each sign becomes an NLA track named after its sign_id, on the armature and (if the
motion has face blendshapes) on the face mesh. The glTF exporter merges tracks with
the same name into one animation, which the player plays by sign_id.

What this script does NOT do: change the sign. It keys exactly the tracked frames,
with linear interpolation (no overshoot), and leaves any untracked frame unkeyed.
"""

import argparse
import json
import os
import math
import sys
from pathlib import Path

import bpy
from mathutils import Quaternion

sys.path.insert(0, str(Path(__file__).resolve().parent))
import retarget_math as rm  # noqa: E402


def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser(description='Retarget ISL motion onto the avatar and bake clips.')
    p.add_argument('--list-bones', action='store_true', help='print bone names and exit')
    p.add_argument('--motion', help='motion/<sign_id>.json from extract_landmarks.py')
    p.add_argument('--bone-map', help='JSON map from logical joints to this rig\'s bone names')
    p.add_argument('--armature', help='armature object name (default: the only armature)')
    p.add_argument('--no-smooth', action='store_true', help='key the raw tracked motion')
    p.add_argument('--qc-exception', metavar='REASON',
                   help='bake although the quality check failed, for a team-approved exception '
                        '(record it as motion_qc = pass_exception in registry/signs.csv)')
    p.add_argument('--save', action='store_true', help='save the .blend after baking')
    p.add_argument('--export', help='write a GLB with every baked sign, e.g. avatar/avatar.glb')
    p.add_argument('--make-idle', action='store_true',
                   help='make the "idle" clip in the natural rest pose (tools/rest_pose.py); needs --bone-map')
    return p.parse_args(argv)


def find_armature(name):
    if name:
        return bpy.data.objects[name]
    armatures = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    if len(armatures) != 1:
        raise SystemExit(f'Found {len(armatures)} armatures; pass --armature <name>')
    return armatures[0]


def as_rows(m):
    return [[m[i][j] for j in range(3)] for i in range(3)]


def skeleton_of(arm):
    bones = sorted(arm.data.bones, key=lambda b: len(b.parent_recursive))   # parents first
    return [{'name': b.name, 'parent': b.parent.name if b.parent else None,
             'rest': as_rows(b.matrix_local.to_3x3())} for b in bones]


def rest_hand_points(arm, bone_map, side):
    """The avatar's 21 hand points (MediaPipe order) in the rest pose, armature space."""
    pts = []
    for logical, end in rm.HAND_POINT_BONES:
        bone = arm.data.bones[bone_map[f'{side}_{logical}']]
        pts.append(list(bone.head_local if end == 'head' else bone.tail_local))
    return pts


def load_config():
    path = Path(__file__).resolve().parent / 'retarget_config.json'
    config = json.loads(path.read_text(encoding='utf-8'))
    # hands.finger_fit (ISL_FINGER_FIT=0/1 overrides it, for side-by-side experiments)
    fit = os.environ.get('ISL_FINGER_FIT')
    rm.FINGER_FIT = bool(int(fit)) if fit is not None else bool(config.get('hands', {}).get('finger_fit', False))
    return config


def rest_frames(arm, bone_map):
    def head(logical):
        return list(arm.data.bones[bone_map[logical]].head_local)

    frames = {}
    for side in ('left', 'right'):
        frames[f'{side}_hand'] = rm.palm_frame(head(f'{side}_hand'), head(f'{side}_index1'),
                                               head(f'{side}_middle1'), head(f'{side}_pinky1'))
        # Rest orientation of the palm and every finger bone, built from the same 21
        # anatomical points as the signer's hand (rig-independent finger retargeting).
        frames[f'{side}_hand_bones'] = rm.rest_hand_frames(rest_hand_points(arm, bone_map, side))
    # The avatar's rest pose is assumed to stand upright, facing the viewer (-Y).
    neutral = rm.upright_frame([0, 0, 1], [1, 0, 0])
    frames['head'] = neutral
    frames['chest'] = neutral
    return frames


def avatar_mouth(arm):
    """The avatar's mouth (armature space, rest pose): centre of the lip vertices, i.e. those the
    mouthPucker shape moves most on the face mesh."""
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.data.shape_keys and o.parent == arm]
    if not meshes:
        return None
    face = max(meshes, key=lambda o: len(o.data.shape_keys.key_blocks))
    keys = face.data.shape_keys.key_blocks
    if 'mouthPucker' not in keys:
        return None
    basis, shape = keys[0].data, keys['mouthPucker'].data
    moved = sorted(range(len(basis)), key=lambda i: -(shape[i].co - basis[i].co).length)[:40]
    to_arm = arm.matrix_world.inverted() @ face.matrix_world
    pts = [to_arm @ basis[i].co for i in moved]
    return list(sum(pts, pts[0] * 0) / len(pts))


def body_measurements(arm, bone_map, frames):
    """Avatar shoulder positions and arm lengths, plus the signer's arm length, for arm IK."""
    def head(logical):
        return arm.data.bones[bone_map[logical]].head_local

    body = {'chest_pivot': list(head('chest')), 'video_arm': rm.video_arm_lengths(frames),
            'video_sizes': rm.video_body_sizes(frames), 'video_segments': rm.video_segment_lengths(frames),
            'image_anchor': load_config().get('arms', {}).get('image_anchor', True),
            'hand_anchor': load_config().get('hands', {}).get('image_anchor', True),
            'hand_segments': {s: rm.hand_segment_lengths(frames, s) for s in ('left', 'right')}}
    for side, s in (('left', 'l'), ('right', 'r')):
        shoulder, elbow, wrist = head(f'{side}_upper_arm'), head(f'{side}_forearm'), head(f'{side}_hand')
        body[f'{s}_shoulder'] = list(shoulder)
        body[f'{s}_upper'] = (elbow - shoulder).length
        body[f'{s}_fore'] = (wrist - elbow).length
    body['shoulder_width'] = (head('left_upper_arm') - head('right_upper_arm')).length
    if 'left_upper_leg' in bone_map and 'right_upper_leg' in bone_map:
        shoulders_z = (head('left_upper_arm').z + head('right_upper_arm').z) / 2
        hips_z = (head('left_upper_leg').z + head('right_upper_leg').z) / 2
        body['torso'] = shoulders_z - hips_z
    # Collarbones, for shoulder shrugs: the shoulder joint rides on them.
    if 'left_clavicle' in bone_map and 'right_clavicle' in bone_map:
        body['l_clavicle'] = list(head('left_clavicle'))
        body['r_clavicle'] = list(head('right_clavicle'))
        body['shoulder_neutral'] = rm.video_shoulder_neutral(frames)
    mouth = avatar_mouth(arm)
    if mouth is not None:
        body['mouth'] = mouth
    if None in body['video_arm'].values():
        return None   # body never tracked: fall back to copying directions
    return body


def replace_track(anim_data, name, action):
    for track in list(anim_data.nla_tracks):
        if track.name == name:
            anim_data.nla_tracks.remove(track)
    track = anim_data.nla_tracks.new()
    track.name = name
    track.strips.new(name, 1, action)
    anim_data.action = None


def fresh_action(name):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    return action


def resample_action(action, src_fps, out_fps, frame_count):
    """Re-key an action, keyed at source frames 1..frame_count, at out_fps through a smooth
    Catmull-Rom curve (tools/smoothing.resample). Bone rotations are resampled as quaternions
    (four curves together); every other curve on its own, shape-key values clamped to 0..1.
    Untracked gaps between keys are bridged by the same smooth curve."""
    import smoothing
    duration = (frame_count - 1) / src_fps
    out_times = [k / out_fps for k in range(math.ceil(duration * out_fps - 1e-6) + 1)]   # covers the last source frame
    groups = {}
    for fc in action.fcurves:
        groups.setdefault(fc.data_path, {})[fc.array_index] = fc

    def keys(fc):
        return [((kp.co[0] - 1) / src_fps, kp.co[1]) for kp in fc.keyframe_points]

    def write(fc, values):
        fc.keyframe_points.clear()
        fc.keyframe_points.add(len(values))
        flat = []
        for k, v in enumerate(values):
            flat += [1 + k, v]
        fc.keyframe_points.foreach_set('co', flat)
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        fc.update()

    for path, curves in groups.items():
        if path.endswith('rotation_quaternion') and len(curves) == 4:
            per = [dict(keys(curves[i])) for i in range(4)]
            times = sorted(set(per[0]) & set(per[1]) & set(per[2]) & set(per[3]))
            if not times:
                continue
            quats = [[per[i][t] for i in range(4)] for t in times]
            new = smoothing.resample(times, quats, out_times, quaternion=True)
            for i in range(4):
                write(curves[i], [q[i] for q in new])
        else:
            clamp = (0.0, 1.0) if path.startswith('key_blocks') else None
            for fc in curves.values():
                pts = keys(fc)
                if pts:
                    write(fc, smoothing.resample([p[0] for p in pts], [p[1] for p in pts], out_times, clamp=clamp))
    return len(out_times)


def make_linear(action):
    for fcurve in action.fcurves:
        for key in fcurve.keyframe_points:
            key.interpolation = 'LINEAR'


def bake_body(arm, motion, bone_map, sign_id, contact_flags, contact_cfg, collision_cfg=None, rest_cfg=None):
    skeleton = skeleton_of(arm)
    names = {b['name'] for b in skeleton}
    missing = sorted(v for v in bone_map.values() if v not in names)
    if missing:
        raise SystemExit(f'Bone map names bones this rig does not have: {", ".join(missing)}')

    frames_rest = rest_frames(arm, bone_map)
    body = body_measurements(arm, bone_map, motion['frames'])
    if body:
        print(f'Arm IK on: avatar arms {body["l_upper"] + body["l_fore"]:.3f} m, '
              f'signer arms {body["video_arm"]["left"]:.3f} m (left) / {body["video_arm"]["right"]:.3f} m (right)')
    arm.animation_data_create()
    action = fresh_action(sign_id)
    arm.animation_data.action = action
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = (1, 0, 0, 0)

    world_only = rm.world_only_sides(motion['frames'])
    skipped = {s: sum(1 for f in motion['frames'] if f.get(f'{s}_hand') is not None and f.get(f'{s}_hand_world') is None)
               for s in world_only}
    if world_only:
        print(f'Hand shape from metric world points only ({", ".join(world_only)}); image-only frames '
              f'interpolated instead of mixed in: {skipped}')
    flips = {s: rm.depth_flip_frames(motion['frames'], s) for s in ('left', 'right')}
    if any(flips.values()):
        print('Depth-flipped hand frames left out (interpolated): '
              + ', '.join(f'{s} {sorted(v)}' for s, v in flips.items() if v))
    tip_bones = {side: [bone_map[f'{side}_{finger}3'] for finger in ('thumb', 'index', 'middle', 'ring', 'pinky')]
                 for side in ('left', 'right')}

    def solve(frame, shift=None, index=None):
        if body is not None:
            body['wrist_shift'] = shift
        skip = tuple(s for s in ('left', 'right') if index in flips[s])
        logical = rm.frame_targets(frame, motion['width'], motion['height'], frames_rest, body, world_only, skip)
        targets = {bone_map[k]: v for k, v in logical.items() if k in bone_map}
        return rm.solve_frame(skeleton, targets)

    def fingertip_gap(basis):
        """Pose the avatar with this solution; return (gap vector left->right, its length)."""
        for bone_name, rotation in basis.items():
            arm.pose.bones[bone_name].rotation_quaternion = Quaternion(rm.mat_to_quat(rotation))
        bpy.context.view_layer.update()
        tips = {side: [arm.pose.bones[b].tail.copy() for b in names] for side, names in tip_bones.items()}
        a, b = min(((a, b) for a in tips['left'] for b in tips['right']), key=lambda ab: (ab[1] - ab[0]).length)
        return list(b - a), (b - a).length

    frames = motion['frames']
    # Pass 1: in frames where the signer's fingertips touch, find the wrist shift that makes
    # the avatar's fingertips touch too.
    shifts = {}
    if body is not None:
        for i, frame in enumerate(frames):
            if not contact_flags[i]:
                continue
            shift = {'left': [0.0, 0.0, 0.0], 'right': [0.0, 0.0, 0.0]}
            basis = solve(frame, index=i)
            for _ in range(contact_cfg['max_iterations']):
                gap, distance = fingertip_gap(basis)
                if distance < contact_cfg['stop_distance_m']:
                    break
                shift['left'] = rm.add(shift['left'], rm.scale(gap, 0.5))
                shift['right'] = rm.sub(shift['right'], rm.scale(gap, 0.5))
                basis = solve(frame, shift, i)
            shifts[i] = shift

    # Ease the shift in and out over EASE frames around each touch, so the hands glide together
    # instead of snapping. Only frames next to real contact in the video are affected.
    EASE = contact_cfg['ease_frames']

    def eased_shift(i):
        if i in shifts:
            return shifts[i]
        near = [j for j in shifts if abs(j - i) <= EASE]
        if not near:
            return None
        j = min(near, key=lambda j: abs(j - i))
        w = rm.smoothstep(1 - abs(j - i) / (EASE + 1))      # no visible start or stop of the glide
        return {side: rm.scale(v, w) for side, v in shifts[j].items()}

    previous = {}
    contacts = []
    for i, frame in enumerate(frames):
        basis = solve(frame, eased_shift(i), i)
        if i in shifts:
            contacts.append(round(fingertip_gap(basis)[1] * 100, 1))
        for bone_name, rotation in basis.items():
            q = Quaternion(rm.mat_to_quat(rotation))
            if bone_name in previous and previous[bone_name].dot(q) < 0:
                q.negate()   # same rotation, but stops the next frame spinning the long way round
            previous[bone_name] = q
            pb = arm.pose.bones[bone_name]
            pb.rotation_quaternion = q
            pb.keyframe_insert('rotation_quaternion', frame=i + 1, group=bone_name)

    if body is not None:
        body['wrist_shift'] = None
    if contacts:
        print(f'Hand contact in {len(contacts)} frames; avatar fingertip gap after correction: '
              f'max {max(contacts)} cm, median {sorted(contacts)[len(contacts) // 2]} cm')
    if rest_cfg and rest_cfg.get('enabled', True):
        blend_to_rest(arm, action, bone_map, motion, rest_cfg)
    if collision_cfg and collision_cfg.get('enabled', True):
        correct_thumbs(arm, action, bone_map, len(frames), collision_cfg)
    out_fps = load_config().get('output_fps')
    if out_fps:
        n = resample_action(action, motion['fps'], out_fps, len(frames))
        print(f'Resampled body keys to {out_fps} fps: {n} frames')
    make_linear(action)
    replace_track(arm.animation_data, sign_id, action)


def correct_thumbs(arm, action, bone_map, frame_count, cfg):
    """Remove thumb-in-finger overlap from the freshly keyed clip (see tools/hand_collision.py).

    Pass 1 poses every frame, turns the thumb at its base until no more than target_depth_mm is
    left inside any finger, and records that turn. Pass 2 keys the original thumb rotation times
    the turn, eased in and out over ease_frames around each corrected frame."""
    import hand_collision as hc
    body = hc.body_mesh(arm)
    scene = bpy.context.scene
    target = cfg['target_depth_mm'] / 1000.0
    report = []
    # Only this clip may move the rig while it is measured: other signs' tracks (and idle)
    # would otherwise blend into the pose.
    muted = {t.name: t.mute for t in arm.animation_data.nla_tracks}
    for t in arm.animation_data.nla_tracks:
        t.mute = True
    for p in arm.pose.bones:
        p.rotation_mode = 'QUATERNION'
        p.rotation_quaternion = (1, 0, 0, 0)
    animated = {fc.data_path.split('"')[1] for fc in action.fcurves if '"' in fc.data_path}
    for side in ('left', 'right'):
        chain = [(f'thumb{j}', bone_map[f'{side}_thumb{j}']) for j in (1, 2)]
        if any(bone not in animated for _, bone in chain):
            report.append(f'{side}: hand not animated in this sign')
            continue
        segments = hc.phalanx_vertices(body, arm, bone_map, side)
        original = {bone: {} for _, bone in chain}
        deltas, depths = {}, []
        for f in range(frame_count):
            arm.animation_data.action = action
            scene.frame_set(f + 1)
            for _, bone in chain:
                original[bone][f] = arm.pose.bones[bone].rotation_quaternion.copy()
            arm.animation_data.action = None          # so the manual turn is not overwritten
            delta, before, after, turned = hc.resolve_thumb(
                arm, body, segments, chain, target, cfg['max_iterations'], cfg['max_correction_deg'])
            if before > target:
                deltas[f] = delta
                depths.append((before, after, turned))
        arm.animation_data.action = action
        if not deltas:
            report.append(f'{side}: no overlap')
            continue
        for f, (src, w) in rm.ease_weights(deltas, frame_count, cfg['ease_frames'], 'smoothstep').items():
            for _, bone in chain:
                d = deltas[src].get(bone, Quaternion())
                pb = arm.pose.bones[bone]
                pb.rotation_quaternion = original[bone][f] @ Quaternion().slerp(d, w)
                pb.keyframe_insert('rotation_quaternion', frame=f + 1, group=bone)
        worst = max(depths, key=lambda d: d[0])
        report.append(f'{side}: {len(deltas)} frames corrected, deepest {worst[0] * 1000:.1f} mm -> '
                      f'{worst[1] * 1000:.1f} mm, largest turn {max(d[2] for d in depths):.1f} deg, '
                      f'left over {max(d[1] for d in depths) * 1000:.1f} mm max, '
                      f'{sum(1 for d in depths if d[1] > 0.002)} frames still over 2 mm')
    for t in arm.animation_data.nla_tracks:
        if t.name in muted:
            t.mute = muted[t.name]
    print('Thumb overlap correction: ' + '; '.join(report))


def bake_face(motion, sign_id, face_cfg):
    frames = motion['frames']
    if not any(f.get('blendshapes') for f in frames):
        print('No face blendshapes in this motion file: facial grammar NOT baked. '
              'Re-run extraction with --face-model before interpreter review.')
        return 0
    names = set()
    for f in frames:
        names.update((f.get('blendshapes') or {}).keys())
    neutral = {}
    if face_cfg.get('calibration', 'neutral') == 'neutral':
        import motion_qc
        resting = [all(f.get(f'{s}_hand') is None or motion_qc.hand_resting(f, f'{s}_hand') for s in ('left', 'right'))
                   for f in frames]
        neutral, method = rm.face_neutral(frames, resting)
        strong = {k: round(v, 2) for k, v in sorted(neutral.items(), key=lambda kv: -kv[1])[:5]}
        print(f'Face neutral from {method}: strongest resting scores {strong}')

    baked = 0
    for obj in bpy.data.objects:
        keys = obj.data.shape_keys if obj.type == 'MESH' else None
        if not keys:
            continue
        present = sorted(n for n in names if n in keys.key_blocks)
        if not present:
            continue
        keys.animation_data_create()
        action = fresh_action(f'{sign_id}__{obj.name}')
        keys.animation_data.action = action
        for i, f in enumerate(frames):
            scores = f.get('blendshapes')
            if not scores:
                continue          # face not tracked: no key, never a guess
            for n in present:
                block = keys.key_blocks[n]
                gain = face_cfg['gains'].get(n, face_cfg['default_gain'])
                value = rm.calibrate_score(scores.get(n, 0.0), neutral.get(n, 0.0)) if neutral else scores.get(n, 0.0)
                block.value = max(0.0, min(1.0, value * gain))
                block.keyframe_insert('value', frame=i + 1)
        if load_config().get('output_fps'):
            resample_action(action, motion['fps'], load_config()['output_fps'], len(frames))
        make_linear(action)
        replace_track(keys.animation_data, sign_id, action)
        baked += len(present)
    if not baked:
        print('No mesh has ARKit-named shape keys: facial grammar NOT baked.')
    return baked


def bake(args):
    motion = json.loads(Path(args.motion).read_text(encoding='utf-8'))
    # Re-run the quality check with today's rules; the result stored at extraction time may be older.
    import motion_qc
    report = motion_qc.qc_report(motion)
    qc = report['result']
    if qc != 'pass' and not args.qc_exception:
        raise SystemExit(f'Motion quality check is {qc!r} ({"; ".join(report["problems"])}), not "pass". '
                         'Find a clearer recording instead of baking this one.')
    if qc != 'pass':
        print(f'QC EXCEPTION used: {args.qc_exception} | problems: {"; ".join(report["problems"])}')
    bone_map = json.loads(Path(args.bone_map).read_text(encoding='utf-8'))
    sign_id = motion['sign_id']
    arm = find_armature(args.armature)

    # Decide where the hands touch from the RAW tracking, before smoothing moves them.
    contact_flags = [rm.fingertip_contact(f, motion['width'], motion['height']) for f in motion['frames']]

    # Smooth a working copy only (the motion file on disk stays raw). Per-stream settings
    # come from tools/retarget_config.json and were chosen by measurement.
    config = load_config()
    if not args.no_smooth:
        import smoothing
        switches = {s: smoothing.blend_detector_switches(motion['frames'], s, config.get('detector_blend_frames', 4))
                    for s in ('left', 'right')}
        print(f'Detector switches crossfaded: {switches}')
        for key, params in config['smoothing'].items():
            if key.startswith('_'):
                continue
            if 'cutoff_hz' in params:          # zero-phase (offline) filter
                smoothing.zero_phase_track(motion['frames'], key, motion['fps'], params['cutoff_hz'])
            else:
                rm.smooth_track(motion['frames'], key, motion['fps'], **params)

    scene = bpy.context.scene
    scene.render.fps = round(motion['fps'])
    scene.render.fps_base = scene.render.fps / motion['fps']
    scene.frame_start, scene.frame_end = 1, len(motion['frames'])

    limits = {k: v for k, v in config.get('finger_joint_limits', {}).items() if not k.startswith('_')}
    rm.FINGER_JOINT_LIMITS.update(limits)
    rm.CLAMP_LOG.clear()
    bake_body(arm, motion, bone_map, sign_id, contact_flags, config['contact'], config.get('thumb_collision'),
              config.get('rest_pose'))
    if rm.CLAMP_LOG:
        worst = max(rm.CLAMP_LOG, key=lambda c: c[2] - c[3])
        print(f'Finger joint limits applied {len(rm.CLAMP_LOG)} times (bone-frames); worst: {worst[0]} {worst[1]} '
              f'asked {worst[2]} deg, allowed {worst[3]} deg. The tracking was impossible there; check those frames.')
    else:
        print('Finger joint limits: no frame needed limiting.')
    shapes = bake_face(motion, sign_id, config['face'])
    if config.get('output_fps'):
        # Every clip is keyed at output_fps; the scene (and the GLB export) runs at that rate.
        scene.render.fps, scene.render.fps_base = int(config['output_fps']), 1.0
        scene.frame_end = 1 + math.ceil((len(motion['frames']) - 1) / motion['fps'] * config['output_fps'] - 1e-6)

    untracked = {k: sum(f.get(k) is None for f in motion['frames']) for k in ('left_hand', 'right_hand', 'face')}
    print(f'Baked "{sign_id}": {len(motion["frames"])} frames at {motion["fps"]:.2f} fps, '
          f'{shapes} face shape keys. Untracked frames left unkeyed: {untracked}')
    print('Next: interpreter compares this clip with the reference video, side by side, before anything is VERIFIED.')


def make_idle(arm, bone_map):
    """Bake a still 'idle' clip in the natural rest pose (tools/rest_pose.py).

    It used to be frame 1 of a tracked sign; resting hands are at the edge of or outside the
    ISLRTC picture, so that frame had a hand buried in the hip and a bent wrist.
    """
    import rest_pose
    tracks = arm.animation_data.nla_tracks
    muted = {t.name: t.mute for t in tracks}
    for t in tracks:
        t.mute = True
    arm.animation_data.action = None
    pose = rest_pose.natural_rest_pose(arm, bone_map)
    for t in tracks:
        t.mute = muted[t.name]
    action = fresh_action('idle')
    arm.animation_data.action = action
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = pose[pb.name]
        for frame in (1, 50):
            pb.keyframe_insert('rotation_quaternion', frame=frame, group=pb.name)
    replace_track(arm.animation_data, 'idle', action)
    print('Made "idle" from the natural rest pose')


def blend_to_rest(arm, action, bone_map, motion, cfg):
    """Resting hands go to the natural rest pose, not to tracked data (see tools/rest_pose.py).

    A hand counts as resting where motion_qc.hand_resting says so (wrist low at the side, or below
    the picture). The arm and hand bones of that side blend to the rest pose with a smoothstep
    over cfg['ease_frames'] frames before and after each resting stretch."""
    import motion_qc
    import rest_pose
    scene = bpy.context.scene
    frames = motion['frames']
    muted = {t.name: t.mute for t in arm.animation_data.nla_tracks}
    for t in arm.animation_data.nla_tracks:
        t.mute = True
    arm.animation_data.action = None
    pose = rest_pose.natural_rest_pose(arm, bone_map)
    arm.animation_data.action = action
    report = []
    for side in ('left', 'right'):
        resting = [motion_qc.hand_resting(f, f'{side}_hand') for f in frames]
        weights = rm.rest_weights(resting, cfg['ease_frames'])
        bones = rest_pose.rest_bones(bone_map, side)
        current = {}
        for i, w in enumerate(weights):
            if w > 0:
                scene.frame_set(i + 1)
                current[i] = {b: arm.pose.bones[b].rotation_quaternion.copy() for b in bones}
        for i, q in current.items():
            for b in bones:
                pb = arm.pose.bones[b]
                target = pose[b].copy()
                if q[b].dot(target) < 0:
                    target.negate()
                pb.rotation_quaternion = q[b].slerp(target, weights[i])
                pb.keyframe_insert('rotation_quaternion', frame=i + 1, group=b)
        report.append(f'{side}: {sum(resting)} resting frames, {len(current)} frames blended')
    for t in arm.animation_data.nla_tracks:
        if t.name in muted:
            t.mute = muted[t.name]
    print('Rest pose: ' + '; '.join(report))


def main():
    args = parse_args()
    if args.make_idle:
        make_idle(find_armature(args.armature), json.loads(Path(args.bone_map).read_text(encoding='utf-8')))
        if args.save:
            bpy.ops.wm.save_mainfile()
    if args.list_bones:
        arm = find_armature(args.armature)
        for b in sorted(arm.data.bones, key=lambda b: len(b.parent_recursive)):
            print(b.name)
        return
    if args.motion:
        if not args.bone_map:
            raise SystemExit('--bone-map is required with --motion')
        bake(args)
        if args.save:
            bpy.ops.wm.save_mainfile()
    if args.export:
        bpy.ops.export_scene.gltf(filepath=str(Path(args.export).resolve()), export_format='GLB',
                                  export_animations=True, export_animation_mode='NLA_TRACKS',
                                  export_morph=True, export_skins=True)
        print(f'Exported {args.export}')


main()
