"""Tests for tools/retarget_math.py. Run: python -m unittest discover tests"""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
import retarget_math as rm  # noqa: E402


def close(test, a, b, places=6):
    for x, y in zip(a, b):
        if isinstance(x, list):
            close(test, x, y, places)
        else:
            test.assertAlmostEqual(x, y, places=places)


def quat_to_mat(q):
    w, x, y, z = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


UP = rm.frame_from([0, 0, 1], [1, 0, 0])      # a bone pointing up, armature space
LEFT = rm.frame_from([1, 0, 0], [0, -1, 0])   # a bone pointing to the avatar's left


def posed_from_basis(skeleton, basis):
    """Rebuild armature-space rotations the way Blender does: parent pose x rest offset x basis."""
    rest = {b['name']: b['rest'] for b in skeleton}
    pose = {}
    for b in skeleton:
        local = basis.get(b['name'], rm.IDENTITY)
        if b['parent'] is None:
            pose[b['name']] = rm.mat_mul(b['rest'], local)
        else:
            offset = rm.mat_mul(rm.transpose(rest[b['parent']]), b['rest'])
            pose[b['name']] = rm.mat_mul(rm.mat_mul(pose[b['parent']], offset), local)
    return pose


class VectorTest(unittest.TestCase):
    def test_axis_conversion_is_a_proper_rotation(self):
        # right stays right, image-down becomes down, towards-camera becomes towards the viewer (-Y)
        self.assertEqual(rm.mp_to_blender([1, 0, 0]), [1, 0, 0])
        self.assertEqual(rm.mp_to_blender([0, 1, 0]), [0, 0, -1])
        self.assertEqual(rm.mp_to_blender([0, 0, -1]), [0, -1, 0])

    def test_rotation_between(self):
        for a, b in [([0, 0, 1], [1, 0, 0]), ([1, 2, 3], [-3, 1, 0.5]), ([0, 1, 0], [0, -1, 0]), ([1, 0, 0], [1, 0, 0])]:
            r = rm.rotation_between(a, b)
            got = [sum(r[i][k] * rm.norm(a)[k] for k in range(3)) for i in range(3)]
            close(self, got, rm.norm(b))
            close(self, rm.mat_mul(r, rm.transpose(r)), rm.IDENTITY)

    def test_frame_is_orthonormal_and_right_handed(self):
        f = rm.frame_from([0.2, 0.1, 1], [1, 0.3, 0])
        close(self, rm.mat_mul(rm.transpose(f), f), rm.IDENTITY)
        close(self, rm.cross(rm.column(f, 0), rm.column(f, 1)), rm.column(f, 2))

    def test_quaternion_round_trip(self):
        for axis, angle in [([0, 0, 1], 0.3), ([1, 1, 0], 2.0), ([0, 1, 0], math.pi - 0.01), ([1, -2, 3], 3.1)]:
            m = rm.axis_angle(axis, angle)
            close(self, quat_to_mat(rm.mat_to_quat(m)), m)


class SolveTest(unittest.TestCase):
    def setUp(self):
        self.skeleton = [
            {'name': 'shoulder', 'parent': None, 'rest': LEFT},
            {'name': 'upper', 'parent': 'shoulder', 'rest': LEFT},
            {'name': 'lower', 'parent': 'upper', 'rest': LEFT},
        ]

    def test_dir_targets_point_bones_where_asked(self):
        targets = {'upper': ('dir', [0, 0, -1]), 'lower': ('dir', [0, -1, 0])}
        pose = posed_from_basis(self.skeleton, rm.solve_frame(self.skeleton, targets))
        close(self, rm.column(pose['upper'], 1), [0, 0, -1])
        close(self, rm.column(pose['lower'], 1), [0, -1, 0])
        close(self, pose['shoulder'], LEFT)   # untouched bone keeps its rest pose

    def test_child_follows_parent_when_not_targeted(self):
        targets = {'upper': ('dir', [0, 0, -1])}
        pose = posed_from_basis(self.skeleton, rm.solve_frame(self.skeleton, targets))
        close(self, rm.column(pose['lower'], 1), [0, 0, -1])

    def test_abs_target_sets_orientation_regardless_of_parent(self):
        turn = rm.axis_angle([0, 0, 1], 0.7)
        targets = {'upper': ('dir', [0, 0, -1]), 'lower': ('abs', turn)}
        pose = posed_from_basis(self.skeleton, rm.solve_frame(self.skeleton, targets))
        close(self, pose['lower'], rm.mat_mul(turn, LEFT))

    def test_rest_targets_give_identity_basis(self):
        targets = {'upper': ('dir', [1, 0, 0]), 'lower': ('abs', rm.IDENTITY)}
        for basis in rm.solve_frame(self.skeleton, targets).values():
            close(self, basis, rm.IDENTITY)


class TargetsTest(unittest.TestCase):
    def test_palm_frame_matches_between_video_and_avatar(self):
        # The same hand shape seen in the video and in the avatar's rest pose -> no rotation.
        wrist, index, middle, pinky = [0, 0, 0], [0.3, 0, 1], [0, 0, 1.1], [-0.3, 0, 0.9]
        rest = rm.palm_frame(wrist, index, middle, pinky)
        turn = rm.axis_angle([0, 1, 0], 0.5)
        moved = [[sum(turn[i][k] * p[k] for k in range(3)) for i in range(3)] for p in (wrist, index, middle, pinky)]
        target = rm.palm_frame(*moved)
        close(self, rm.mat_mul(target, rm.transpose(rest)), turn)

    def test_missing_parts_produce_no_targets(self):
        rest_frames = {k: rm.IDENTITY for k in ('left_hand', 'right_hand', 'head', 'chest')}
        targets = rm.frame_targets({'pose_world': None, 'left_hand': None, 'right_hand': None, 'face': None},
                                   640, 480, rest_frames)
        self.assertEqual(targets, {})

    def test_hand_targets_cover_all_fingers(self):
        rest_frames = {k: rm.IDENTITY for k in ('left_hand', 'right_hand', 'head', 'chest')}
        hand = [[0.5 + 0.01 * i, 0.5 - 0.02 * i + (0.01 if i % 4 == 0 else 0), 0.001 * i] for i in range(21)]
        targets = rm.frame_targets({'right_hand': hand}, 640, 480, rest_frames)
        self.assertIn('right_hand', targets)
        self.assertEqual(len([k for k in targets if k.startswith('right_') and k != 'right_hand']), 15)


class ArmIkTest(unittest.TestCase):
    def test_wrist_lands_on_target_and_bone_lengths_hold(self):
        shoulder, target = [0.2, 0, 1.4], [0.05, -0.3, 1.2]
        elbow, wrist = rm.two_bone_ik(shoulder, target, 0.28, 0.26, [0.3, 0.0, 1.1])
        close(self, wrist, target)
        self.assertAlmostEqual(rm.length(rm.sub(elbow, shoulder)), 0.28)
        self.assertAlmostEqual(rm.length(rm.sub(wrist, elbow)), 0.26)

    def test_elbow_bends_towards_the_hint(self):
        shoulder, target = [0, 0, 0], [0, 0, -0.4]
        out, _ = rm.two_bone_ik(shoulder, target, 0.28, 0.26, [0.5, 0, -0.2])
        back, _ = rm.two_bone_ik(shoulder, target, 0.28, 0.26, [0, 0.5, -0.2])
        self.assertGreater(out[0], 0.1)
        self.assertGreater(back[1], 0.1)

    def test_out_of_reach_target_gives_straight_arm(self):
        elbow, wrist = rm.two_bone_ik([0, 0, 0], [1.0, 0, 0], 0.28, 0.26, [0, 0, -1])
        self.assertAlmostEqual(rm.length(wrist), 0.54, places=4)
        self.assertAlmostEqual(elbow[0], 0.28, places=2)

    def _body(self, shoulder_half_width):
        return {'chest_pivot': [0, 0, 1.3], 'l_shoulder': [shoulder_half_width, 0, 1.4],
                'r_shoulder': [-shoulder_half_width, 0, 1.4],
                'l_upper': 0.28, 'l_fore': 0.26, 'r_upper': 0.28, 'r_fore': 0.26,
                'video_arm': {'left': 0.6, 'right': 0.6}}

    def _pose(self):
        # Signer with hands touching in front of the chest (wrists meet at x = 0).
        return {'l_shoulder': [0.2, 0, 1.4], 'r_shoulder': [-0.2, 0, 1.4],
                'l_elbow': [0.25, -0.1, 1.15], 'r_elbow': [-0.25, -0.1, 1.15],
                'l_wrist': [0.0, -0.3, 1.25], 'r_wrist': [0.0, -0.3, 1.25]}

    def test_touching_hands_still_touch_on_a_narrower_avatar(self):
        body = self._body(0.15)            # avatar shoulders narrower than the signer's
        targets = rm.arm_ik_targets(self._pose(), rm.IDENTITY, body)
        wrists = {}
        for side, s in (('left', 'l'), ('right', 'r')):
            sh = body[f'{s}_shoulder']
            elbow = rm.add(sh, rm.scale(rm.norm(targets[f'{side}_upper_arm'][1]), body[f'{s}_upper']))
            wrists[side] = rm.add(elbow, rm.scale(rm.norm(targets[f'{side}_forearm'][1]), body[f'{s}_fore']))
        self.assertLess(rm.length(rm.sub(wrists['left'], wrists['right'])), 0.01)

    def test_chest_level_stays_chest_level_on_a_shorter_torso(self):
        body = self._body(0.15)
        body.update(torso=0.30, shoulder_width=0.30,
                    video_sizes={'torso': 0.45, 'shoulder_width': 0.40})
        s = rm.body_scales(body)
        # Signer's hand 40% of the way down the torso -> 40% down the avatar's torso.
        self.assertAlmostEqual(rm.to_avatar([0, 0, -0.18], s)[2] / 0.30, -0.18 / 0.45)
        # Above the shoulders and in depth: arm-length scale (as before).
        self.assertAlmostEqual(rm.to_avatar([0, -0.2, 0.1], s)[2], 0.1 * s['up'])
        self.assertAlmostEqual(s['up'], s['depth'])

    def test_frame_targets_without_body_keep_direction_copying(self):
        rest = {k: rm.IDENTITY for k in ('left_hand', 'right_hand', 'head', 'chest')}
        world = [[0.0, 0.0, 0.0, 1.0]] * 33
        world = [list(p) for p in world]
        for idx, pt in {11: [0.2, -1.4, 0], 12: [-0.2, -1.4, 0], 13: [0.25, -1.15, 0], 14: [-0.25, -1.15, 0],
                        15: [0.3, -0.9, 0], 16: [-0.3, -0.9, 0], 23: [0.1, 0, 0], 24: [-0.1, 0, 0]}.items():
            world[idx] = pt + [1.0]
        targets = rm.frame_targets({'pose_world': world}, 640, 480, rest)
        self.assertEqual(targets['left_upper_arm'][0], 'dir')


class SmoothingTest(unittest.TestCase):
    def test_constant_signal_unchanged_and_gaps_stay_empty(self):
        frames = [{'h': [[1.0, 2.0, 3.0]]}, {'h': None}, {'h': [[1.0, 2.0, 3.0]]}]
        rm.smooth_track(frames, 'h', fps=30)
        self.assertIsNone(frames[1]['h'])
        close(self, frames[2]['h'][0], [1.0, 2.0, 3.0])

    def test_jitter_is_reduced(self):
        f = rm.OneEuro(fps=60)
        noisy = [0.5 + (0.01 if i % 2 else -0.01) for i in range(60)]
        out = [f(x) for x in noisy]
        self.assertLess(max(out[30:]) - min(out[30:]), 0.02)


if __name__ == '__main__':
    unittest.main()
