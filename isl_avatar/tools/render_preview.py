"""Render still images of the avatar, for checking a baked sign against its reference video.

    # chest-up portrait in the rest pose
    blender --background avatar/avatar_source.blend --python tools/render_preview.py -- --out previews/portrait
    # frames 11, 26 and 36 of the "electricity" clip
    blender --background avatar/avatar_source.blend --python tools/render_preview.py -- \
        --out previews/electricity --track electricity --frames 11 26 36

Then tools/compare_frames.py puts the renders under the matching video frames.
"""

import argparse
import sys

import bpy
from mathutils import Vector

p = argparse.ArgumentParser()
p.add_argument('--out', required=True, help='output path prefix (frame number and .png are added)')
p.add_argument('--track', help='sign_id whose baked clip to show (default: rest pose)')
p.add_argument('--frames', type=int, nargs='*', default=[1])
p.add_argument('--size', type=int, default=500)
p.add_argument('--focus', help='bone name to frame in close-up (e.g. mixamorig:RightHand), followed every frame')
p.add_argument('--distance', type=float, default=0.55, help='close-up camera distance in metres (with --focus)')
args = p.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])

# Show only the chosen sign's clip (body and face); with no track, the rest pose.
for obj in bpy.data.objects:
    keys = obj.data.shape_keys if obj.type == 'MESH' and obj.data.shape_keys else None
    for owner in (obj, keys):
        if owner is not None and owner.animation_data:
            for t in owner.animation_data.nla_tracks:
                t.mute = t.name != args.track

rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
head = rig.matrix_world @ next(b for b in rig.data.bones if b.name.endswith('Head')).head_local

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = scene.render.resolution_y = args.size
scene.world = scene.world or bpy.data.worlds.new('preview')
scene.world.use_nodes = True
background = scene.world.node_tree.nodes['Background']
background.inputs[0].default_value = (0.55, 0.55, 0.58, 1)
background.inputs[1].default_value = 0.35
for name, loc, energy in (('key', (1.5, -3, 2.6), 260), ('fill', (-2, -2.5, 1.8), 110)):
    light = bpy.data.lights.new(name, 'AREA')
    light.energy, light.size = energy, 2
    obj = bpy.data.objects.new(name, light)
    obj.location = loc
    obj.rotation_euler = (Vector((0, 0, head.z - 0.2)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.collection.objects.link(obj)
cam = bpy.data.objects.new('preview_cam', bpy.data.cameras.new('preview_cam'))
cam.data.lens = 70
cam.location = (0, -2.4, head.z - 0.3)        # chest-up, signing space included
cam.rotation_euler = (1.5708, 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam

for f in args.frames:
    scene.frame_set(f)
    if args.focus:
        # Close-up that follows the bone: camera in front, slightly above, looking at it.
        target = rig.matrix_world @ rig.pose.bones[args.focus].head
        cam.location = (target.x, target.y - args.distance, target.z + 0.08 * args.distance / 0.55)
        cam.rotation_euler = (Vector(target) - Vector(cam.location)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = f'{args.out}_{f:04d}.png'
    bpy.ops.render.render(write_still=True)
    print('rendered', scene.render.filepath)
