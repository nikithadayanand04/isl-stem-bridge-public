"""Render one baked sign as a frame sequence, framed like its ISLRTC source video. Runs in Blender.

Used by tools/visual_loop_check.py, which then runs the same landmark tracker on the render as
on the source video. The camera is placed so the avatar's shoulder centre and hip height land
where the source signer's median shoulder centre and hip height are in the source picture, at
the source's aspect ratio. Frame i of the output shows the avatar at source time i / source_fps.

    blender -b avatar/avatar_source.blend --python tools/render_sign_video.py -- \
        --track electricity --out DIR --frames 82 --source-fps 25 \
        --frame-json '{"width": 1920, "height": 1080, "shoulder_u": 0.51, "shoulder_v": 0.48, "hip_v": 0.99}'
"""

import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

p = argparse.ArgumentParser()
p.add_argument('--track', required=True)
p.add_argument('--out', required=True, help='output folder for frame_0000.png ...')
p.add_argument('--frames', type=int, required=True, help='number of source frames')
p.add_argument('--source-fps', type=float, required=True)
p.add_argument('--frame-json', required=True, help='source framing (see visual_loop_check.py)')
p.add_argument('--render-width', type=int, default=960)
p.add_argument('--distance', type=float, default=3.5, help='camera distance in metres')
args = p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
frame = json.loads(args.frame_json)

# Only this sign plays (body and face); other clips and idle are muted.
found = False
for obj in bpy.data.objects:
    keys = obj.data.shape_keys if obj.type == 'MESH' and obj.data.shape_keys else None
    for owner in (obj, keys):
        if owner is not None and owner.animation_data:
            owner.animation_data.action = None
            for t in owner.animation_data.nla_tracks:
                t.mute = t.name != args.track
                found |= t.name == args.track
if not found:
    raise SystemExit(f'No baked clip "{args.track}"')

rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for pb in rig.pose.bones:
    pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = (1, 0, 0, 0)


def bone_head(suffix):
    b = next(b for b in rig.data.bones if b.name.endswith(suffix))
    return rig.matrix_world @ b.head_local


shoulder = (bone_head('LeftArm') + bone_head('RightArm')) / 2
hip = (bone_head('LeftUpLeg') + bone_head('RightUpLeg')) / 2

scene = bpy.context.scene
W = args.render_width
H = round(W * frame['height'] / frame['width'])
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x, scene.render.resolution_y = W, H
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.world = scene.world or bpy.data.worlds.new('loop')
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.5, 0.5, 0.52, 1)       # plain grey, like the ISLRTC backdrop
bg.inputs[1].default_value = 0.6
for name, loc, energy in (('key', (1.5, -3, 2.6), 260), ('fill', (-2, -2.5, 1.8), 120)):
    light = bpy.data.lights.new(name, 'AREA')
    light.energy, light.size = energy, 2
    obj = bpy.data.objects.new(name, light)
    obj.location = loc
    obj.rotation_euler = (Vector((0, 0, shoulder.z)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.collection.objects.link(obj)

# Pinhole camera looking straight along +Y. With s = focal / sensor width and depth D:
#   u = 0.5 + s * (X - cx) / D        v = 0.5 - s * (W / H) * (Z - cz) / D    (v from the top)
# Solve s from the shoulder-to-hip height in the source picture, then cx, cz.
cam_data = bpy.data.cameras.new('loop_cam')
cam_data.sensor_fit = 'HORIZONTAL'
cam = bpy.data.objects.new('loop_cam', cam_data)
D = args.distance
aspect = W / H
s = (frame['hip_v'] - frame['shoulder_v']) * D / (aspect * (shoulder.z - hip.z))
cx = shoulder.x - (frame['shoulder_u'] - 0.5) * D / s
cz = shoulder.z - (0.5 - frame['shoulder_v']) * D / (s * aspect)
cam_data.lens = s * cam_data.sensor_width
cam.location = (cx, shoulder.y - D, cz)
cam.rotation_euler = (1.5707963, 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam

out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)
fps = scene.render.fps / scene.render.fps_base
for i in range(args.frames):
    t = 1 + i * fps / args.source_fps                 # baked clips start at frame 1
    whole = int(t)
    scene.frame_set(whole, subframe=t - whole)
    scene.render.filepath = str(out / f'frame_{i:04d}.png')
    bpy.ops.render.render(write_still=True)
print(f'Rendered {args.frames} frames of "{args.track}" to {out} (lens {cam_data.lens:.1f} mm)')
