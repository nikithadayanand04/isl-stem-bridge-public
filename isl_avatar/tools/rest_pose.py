"""A fixed, natural rest pose for the avatar's arms and hands. Runs in Blender.

Why: the idle pose used to be frame 1 of a tracked sign. In the ISLRTC videos resting hands are at
the bottom edge of the picture or outside it, so the tracker guesses: the avatar stood with one
hand buried in the hip and the other bent at the wrist in a half fist (render, 10 Nov 2026).
Resting hands carry no meaning in a sign, so they now go to this pose instead of tracked data:
arms hanging where the ISLRTC signers' hands hang at rest (measured), wrists straight, palms
towards the thighs, fingers lightly curled. Built from the rig's own geometry, so it works on any rig with
the bone map.
"""

import math

import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import retarget_math as rm  # noqa: E402

# Where the ISLRTC signers' wrists hang at rest, measured on the source videos (10 Nov 2026:
# median over 171 resting frames with the wrist in view, all signs), from the shoulder midpoint in
# shoulder widths: 0.62 out to the side, 1.42 down. (Hands below the picture cannot be measured,
# so if anything the true resting hand is a little lower.) The wrist is placed there by two-bone
# IK, slightly in front of the body; elbows bend backwards and out like a relaxed arm.
REST = {
    'wrist_side_sw': 0.62,
    'wrist_down_sw': 1.42,
    'wrist_forward_m': 0.04,
    'finger_curl': (12.0, 16.0, 10.0),   # MCP, PIP, DIP, degrees
    'thumb_curl': (4.0, 10.0, 8.0),
}
FINGERS = ('index', 'middle', 'ring', 'pinky')


def _update():
    bpy.context.view_layer.update()


def _rotate_world(arm, pb, rotation):
    """Apply an armature-space rotation to a pose bone about its head."""
    _update()
    current = pb.matrix.to_3x3().normalized()
    delta = current.inverted() @ rotation @ current
    pb.rotation_quaternion = (pb.rotation_quaternion.to_matrix() @ delta).to_quaternion()
    _update()


def _direction(pb):
    return (pb.tail - pb.head).normalized()


def _turn_to(arm, pb, target):
    _rotate_world(arm, pb, _direction(pb).rotation_difference(target.normalized()).to_matrix())


def _palm_normal(arm, bone_map, side):
    """Out of the palm. The sign of the knuckle cross product differs between the mirror-image
    hands; tools/rig_validator.py measured it from real finger flexion: + for the right, - for the
    left (reports/rig/rig_report.json, palm_side)."""
    b = arm.pose.bones
    wrist = b[bone_map[f'{side}_hand']].head
    index = b[bone_map[f'{side}_index1']].head
    pinky = b[bone_map[f'{side}_pinky1']].head
    n = (index - wrist).cross(pinky - wrist).normalized()
    return n if side == 'right' else -n


def natural_rest_pose(arm, bone_map):
    """{bone name: local rotation quaternion} for both arms and hands. Other bones: identity.
    Leaves the armature in that pose."""
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion()
    _update()
    b = arm.pose.bones
    for side, sign in (('left', 1.0), ('right', -1.0)):       # +X is the avatar's left
        upper, fore, hand = b[bone_map[f'{side}_upper_arm']], b[bone_map[f'{side}_forearm']], b[bone_map[f'{side}_hand']]
        ls, rs = b[bone_map['left_upper_arm']].head, b[bone_map['right_upper_arm']].head
        width = (ls - rs).length
        middle = (ls + rs) / 2
        target = middle + Vector((sign * REST['wrist_side_sw'] * width, -REST['wrist_forward_m'],
                                  -REST['wrist_down_sw'] * width))
        shoulder = upper.head.copy()
        upper_len = (fore.head - upper.head).length
        fore_len = (hand.head - fore.head).length
        hint = shoulder + Vector((sign * 0.08, 0.10, -0.15))          # elbow back and out
        elbow, wrist = rm.two_bone_ik(list(shoulder), list(target), upper_len, fore_len, list(hint))
        _turn_to(arm, upper, Vector(elbow) - shoulder)
        _turn_to(arm, fore, Vector(wrist) - Vector(elbow))
        # Wrist straight: the hand continues the forearm ...
        knuckles = (b[bone_map[f'{side}_middle1']].head - hand.head).normalized()
        _rotate_world(arm, hand, knuckles.rotation_difference(_direction(fore)).to_matrix())
        # ... and is turned about the forearm so the palm faces the thigh (towards the body's middle).
        axis = _direction(fore)
        medial = Vector((-sign, 0, 0))
        n = _palm_normal(arm, bone_map, side)
        n_flat = (n - axis * n.dot(axis)).normalized()
        m_flat = (medial - axis * medial.dot(axis)).normalized()
        angle = math.atan2(axis.dot(n_flat.cross(m_flat)), n_flat.dot(m_flat))
        _rotate_world(arm, hand, Matrix.Rotation(angle, 3, axis))
        # Fingers lightly curled towards the palm.
        for finger, curls in [(f, REST['finger_curl']) for f in FINGERS] + [('thumb', REST['thumb_curl'])]:
            for j, deg in zip((1, 2, 3), curls):
                pb = b[bone_map[f'{side}_{finger}{j}']]
                n = _palm_normal(arm, bone_map, side)
                _rotate_world(arm, pb, Matrix.Rotation(math.radians(deg), 3, _direction(pb).cross(n)))
    return {pb.name: pb.rotation_quaternion.copy() for pb in arm.pose.bones}


def rest_bones(bone_map, side):
    """The bones a resting arm drives: upper arm, forearm, hand and all finger bones."""
    names = [f'{side}_upper_arm', f'{side}_forearm', f'{side}_hand']
    names += [f'{side}_{f}{j}' for f in FINGERS + ('thumb',) for j in (1, 2, 3)]
    return [bone_map[n] for n in names if n in bone_map]
