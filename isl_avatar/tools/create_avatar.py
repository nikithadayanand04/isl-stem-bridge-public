"""Build the interpreter avatar with MPFB (MakeHuman for Blender) and save avatar/avatar_source.blend.

Needs Blender 4.2+ with the MPFB extension and these CC0 asset packs installed in MPFB:
makehuman_system_assets, skins02, eyebrows01, eyelashes01, hair01, system_hair_materials01, shirts01,
faceunits01 (ARKit-style face shapes, needed for facial grammar).

    blender --background --python tools/create_avatar.py

Change the look in LOOK below and run again. The rig is MPFB's built-in Mixamo rig, so
tools/bone_maps/mixamo.json works unchanged.
"""

import importlib
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'avatar' / 'avatar_source.blend'


def mpfb(module, name):
    return getattr(importlib.import_module(f'bl_ext.user_default.mpfb.services.{module}'), name)


HumanService = mpfb('humanservice', 'HumanService')
AssetService = mpfb('assetservice', 'AssetService')
FaceService = mpfb('faceservice', 'FaceService')
TargetService = mpfb('targetservice', 'TargetService')

# A young woman with fair skin. Hair is tied back in a ponytail so it never hides the
# face (facial grammar) or the hands.
LOOK = {
    'macros': {'gender': 0.0, 'age': 0.45, 'muscle': 0.5, 'weight': 0.5, 'proportions': 0.6, 'height': 0.5,
               'cupsize': 0.5, 'firmness': 0.5,
               'race': {'asian': 0.30, 'caucasian': 0.60, 'african': 0.10}},
    'skin': 'young_caucasian_female.mhmat',
    'assets': [('eyes', 'high-poly.mhclo'), ('eyebrows', 'eyebrow010.mhclo'), ('eyelashes', 'eyelashes02.mhclo'),
               ('teeth', 'teeth_base.mhclo'), ('tongue', 'tongue01.mhclo'), ('hair', 'ponytail01.mhclo'),
               # trousers first, so the T-shirt is fitted over them and hangs on top
               ('clothes', 'toigo_wool_pants.mhclo'), ('clothes', 'joepal_crude_t-shirt_female.mhclo')],
    # Alternative materials, keyed by the asset's uuid, path relative to the asset folder.
    'materials': {'2c12f43b-1303-432c-b7ce-d78346baf2e6': 'materials/brown.mhmat',                        # eyes
                  '44e0340e-c7a6-4d22-814c-0632968d2dde':
                      'ponytail01/dariush086_ponytail01_black/dariush086_ponytail01_black.mhmat'},   # hair
    # Plain, dark top so the hands stand out (like the ISLRTC interpreters' black polo).
    # Same colour for both, as interpreters dress, which also hides where the waistband
    # rises above the T-shirt hem on this body shape.
    'flat_colours': {'joepal_crude_t-shirt_female': (0.02, 0.02, 0.025, 1.0),
                     'toigo_wool_pants': (0.02, 0.02, 0.025, 1.0)},
}


# Strands need their alpha texture; the eyes have a clear cornea over the iris.
TRANSPARENT_PARTS = ('ponytail01', 'eyebrow010', 'eyelashes02', 'high-poly')


def make_opaque(obj):
    """Solid surfaces must not use alpha, or the web export marks them see-through."""
    for slot in obj.material_slots:
        tree = slot.material.node_tree
        for node in tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                for link in list(node.inputs['Alpha'].links):
                    tree.links.remove(link)
                node.inputs['Alpha'].default_value = 1.0


def delete_helpers(basemesh):
    """Remove MPFB's helper geometry (hair/clothes guides). A mask hides it in Blender,
    but the web export ignores masks, so it must actually be deleted. Shape keys survive."""
    import bmesh
    body_group = basemesh.vertex_groups['body'].index
    bm = bmesh.new()
    bm.from_mesh(basemesh.data)
    deform = bm.verts.layers.deform.verify()
    doomed = [v for v in bm.verts if v[deform].get(body_group, 0.0) <= 0.0]
    bmesh.ops.delete(bm, geom=doomed, context='VERTS')
    bm.to_mesh(basemesh.data)
    bm.free()
    for mod in list(basemesh.modifiers):
        if mod.type == 'MASK':
            basemesh.modifiers.remove(mod)
    return len(doomed)


def flatten_colour(obj, rgba):
    """Replace the base-colour texture with one plain colour (exports cleanly to glTF)."""
    for slot in obj.material_slots:
        tree = slot.material.node_tree
        for node in tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                socket = node.inputs['Base Color']
                for link in list(socket.links):
                    tree.links.remove(link)
                socket.default_value = rgba
                node.inputs['Roughness'].default_value = 0.9   # matte cotton, no shine


def find(subdir, name, kind):
    for f in AssetService.find_asset_files_matching_pattern(AssetService.get_asset_roots(subdir), '*.' + kind):
        if f.name == name:
            return str(f)
    raise SystemExit(f'Asset not found: {subdir}/{name} (is its asset pack installed in MPFB?)')


def main():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    basemesh = HumanService.create_human(macro_detail_dict=LOOK['macros'])
    basemesh.name = 'Interpreter'
    TargetService.bake_targets(basemesh)   # freeze body shape so only face shapes remain as shape keys

    # The rig must exist BEFORE clothes, hair and eyes are added: MPFB only binds an asset
    # to the skeleton if there is one when the asset is loaded.
    rig = HumanService.add_builtin_rig(basemesh, 'mixamo')
    rig.name = 'InterpreterRig'

    HumanService.set_character_skin(find('skins', LOOK['skin'], 'mhmat'), basemesh, skin_type='GAMEENGINE')
    for subdir, name in LOOK['assets']:
        HumanService.add_mhclo_asset(find(subdir, name, 'mhclo'), basemesh, asset_type=subdir, subdiv_levels=0,
                                     material_type='GAMEENGINE', alternative_materials=LOOK['materials'])
    for obj in bpy.data.objects:
        for asset, rgba in LOOK['flat_colours'].items():
            if obj.name.endswith('.' + asset):
                flatten_colour(obj, rgba)

    if not FaceService.is_faceunits01_installed(force_recheck=True):
        raise SystemExit('faceunits01 pack missing: facial grammar would be impossible')
    FaceService.load_targets(basemesh, load_microsoft_visemes=False, load_arkit_faceunits=True)
    FaceService.interpolate_targets(basemesh)

    removed = delete_helpers(basemesh)
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and not obj.name.endswith(TRANSPARENT_PARTS):
            make_opaque(obj)

    unbound = [o.name for o in bpy.data.objects
               if o.type == 'MESH' and not any(m.type == 'ARMATURE' and m.object == rig for m in o.modifiers)]
    if unbound:
        raise SystemExit(f'Not attached to the skeleton (would not move): {unbound}')

    OUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
    keys = basemesh.data.shape_keys.key_blocks.keys() if basemesh.data.shape_keys else []
    print(f'Saved {OUT}: {len(rig.data.bones)} bones, {len(keys)} face shape keys, {removed} helper vertices removed, '
          f'meshes: {[o.name for o in bpy.data.objects if o.type == "MESH"]}')


main()
