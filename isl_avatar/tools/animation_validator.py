"""Sample a baked sign on the avatar, frame by frame, for comparison with the source signer.

Runs in Blender. Records, per frame, in armature space (metres): shoulders, elbows, wrists,
the 21 points of each hand (MediaPipe order), the head orientation and the value of every
face shape key. tools/motion_report.py compares this with the source landmarks.

    blender avatar/avatar_source.blend --background --python tools/animation_validator.py -- \
        --track food --bone-map tools/bone_maps/mixamo.json --out reports/food/avatar_samples.json
"""

import argparse
import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import retarget_math as rm  # noqa: E402


def parse_args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument('--track', required=True, help='sign_id of the baked clip')
    p.add_argument('--bone-map', required=True)
    p.add_argument('--armature', default=None)
    p.add_argument('--out', required=True)
    p.add_argument('--source-fps', type=float, help='sample at the source video\'s frame times '
                   '(needed when the clip is keyed at another rate, e.g. 60 fps)')
    return p.parse_args(argv)


def solo_track(name):
    """Mute every other clip (body and face) so only this sign plays."""
    found = False
    for obj in bpy.data.objects:
        keys = obj.data.shape_keys if obj.type == 'MESH' and obj.data.shape_keys else None
        for owner in (obj, keys):
            if owner is not None and owner.animation_data:
                for t in owner.animation_data.nla_tracks:
                    t.mute = t.name != name
                    found |= t.name == name
    if not found:
        raise SystemExit(f'No baked clip named "{name}"')


def main():
    args = parse_args()
    bone_map = json.loads(Path(args.bone_map).read_text(encoding='utf-8'))
    arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    arm = bpy.data.objects[args.armature] if args.armature else arms[0]
    solo_track(args.track)
    track = arm.animation_data.nla_tracks[args.track]
    last = int(max(s.frame_end for s in track.strips))
    face_mesh = max((o for o in bpy.data.objects if o.type == 'MESH' and o.data.shape_keys),
                    key=lambda o: len(o.data.shape_keys.key_blocks), default=None)

    def pos(logical, end='head'):
        pb = arm.pose.bones[bone_map[logical]]
        return [round(v, 5) for v in (pb.head if end == 'head' else pb.tail)]

    frames = []
    scene = bpy.context.scene
    fps = scene.render.fps / scene.render.fps_base
    if args.source_fps:
        count = int((last - 1) / fps * args.source_fps + 1e-3) + 1
        times = [1 + i * fps / args.source_fps for i in range(count)]
    else:
        times = list(range(1, last + 1))
    for f in times:
        whole = int(f)
        scene.frame_set(whole, subframe=f - whole)
        sample = {'frame': f}
        for side, s in (('left', 'l'), ('right', 'r')):
            sample[f'{s}_shoulder'] = pos(f'{side}_upper_arm')
            sample[f'{s}_elbow'] = pos(f'{side}_forearm')
            sample[f'{s}_wrist'] = pos(f'{side}_hand')
            if f'{side}_upper_leg' in bone_map:
                sample[f'{s}_hip'] = pos(f'{side}_upper_leg')
            sample[f'{side}_hand_points'] = [pos(f'{side}_{logical}', end) for logical, end in rm.HAND_POINT_BONES]
        head = arm.pose.bones[bone_map['head']].matrix.to_3x3()
        sample['head_rotation'] = [[round(head[i][j], 5) for j in range(3)] for i in range(3)]
        if face_mesh is not None:
            sample['face'] = {k.name: round(k.value, 4) for k in face_mesh.data.shape_keys.key_blocks[1:]}
        frames.append(sample)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'track': args.track, 'fps': args.source_fps or fps,
                               'frames': frames}), encoding='utf-8')
    print(f'Sampled {len(frames)} frames of "{args.track}" -> {out}')


main()
