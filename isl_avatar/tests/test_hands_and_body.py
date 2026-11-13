"""Tests for hand, thumb, shoulder and head retargeting (tools/retarget_math.py).
Run: python -m unittest discover tests"""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
import retarget_math as rm  # noqa: E402
import motion_metrics as mm  # noqa: E402


def close(test, a, b, places=5):
    for x, y in zip(a, b):
        if isinstance(x, list):
            close(test, x, y, places)
        else:
            test.assertAlmostEqual(x, y, places=places)


def flat_hand(scale=1.0, spread=1.0):
    """A straight hand in its own frame: wrist at origin, fingers along +Y, thumb out to +X."""
    pts = [[0.0, 0.0, 0.0]]
    pts += [[0.02 * scale, 0.02 * scale, 0], [0.04 * scale, 0.04 * scale, 0], [0.055 * scale, 0.06 * scale, 0],
            [0.07 * scale, 0.08 * scale, 0]]
    for i, x in enumerate((0.025, 0.008, -0.008, -0.024)):
        x *= scale * spread
        for j, y in enumerate((0.09, 0.13, 0.155, 0.175)):
            pts.append([x, y * scale, 0.0])
    return pts


def curl(pts, joints, angle_deg):
    """Bend a finger at the given joint indices about the X axis (towards -Z, the palm side)."""
    pts = [p[:] for p in pts]
    for j in joints:
        rot = rm.axis_angle([1, 0, 0], -math.radians(angle_deg))
        pivot = pts[j]
        chain = range(j + 1, (j // 4 + 1) * 4 + 1)
        for k in chain:
            rel = rm.sub(pts[k], pivot)
            pts[k] = rm.add(pivot, [sum(rot[r][c] * rel[c] for c in range(3)) for r in range(3)])
    return pts


def pose_hand(skeleton_rest_pts, basis):
    """Rebuild the avatar hand's finger directions from solved basis rotations (Blender-style)."""
    return basis


class FingerFrameTest(unittest.TestCase):
    def test_same_shape_gives_identity_rotations(self):
        rest = rm.rest_hand_frames(flat_hand())
        targets = rm.hand_targets(flat_hand(), 'right', rest)
        for name, (kind, rot) in targets.items():
            self.assertEqual(kind, 'abs')
            close(self, rot, rm.IDENTITY)

    def test_rotation_is_independent_of_hand_size_and_position(self):
        rest = rm.rest_hand_frames(flat_hand(scale=1.0))
        turn = rm.axis_angle([0.3, 1, 0.2], 0.8)
        signer = [rm.add([sum(turn[r][c] * p[c] for c in range(3)) for r in range(3)], [0.4, -0.2, 1.1])
                  for p in flat_hand(scale=1.3)]
        for name, (_, rot) in rm.hand_targets(signer, 'left', rest).items():
            close(self, rot, turn, places=4)

    def test_curled_finger_is_reproduced_and_measured(self):
        rest = rm.rest_hand_frames(flat_hand())
        signer = curl(flat_hand(), [6], 70)                    # index PIP bent 70 degrees
        targets = rm.hand_targets(signer, 'right', rest)
        self.assertAlmostEqual(rm.rotation_angle(targets['right_index2'][1]), 70, places=3)
        self.assertAlmostEqual(rm.rotation_angle(targets['right_index1'][1]), 0, places=3)
        self.assertAlmostEqual(mm.flexion_angles(signer)['index_pip'], 70, places=3)

    def test_impossible_bend_is_limited_and_logged(self):
        rest = rm.rest_hand_frames(flat_hand())
        rm.CLAMP_LOG.clear()
        signer = curl(flat_hand(), [6], 170)                   # index PIP folded far past its range
        t = rm.hand_targets(signer, 'right', rest)
        rel = rm.mat_mul(rm.transpose(t['right_index1'][1]), t['right_index2'][1])
        self.assertAlmostEqual(rm.rotation_angle(rel), rm.FINGER_JOINT_LIMITS['finger2'], places=3)
        self.assertEqual(rm.CLAMP_LOG[0][:2], ('right', 'index2'))
        # Within range: untouched, nothing logged.
        rm.CLAMP_LOG.clear()
        t = rm.hand_targets(curl(flat_hand(), [6], 70), 'right', rest)
        self.assertAlmostEqual(rm.rotation_angle(t['right_index2'][1]), 70, places=3)
        self.assertEqual(rm.CLAMP_LOG, [])

    def test_limits_can_be_switched_off(self):
        rest = rm.rest_hand_frames(flat_hand())
        t = rm.hand_targets(curl(flat_hand(), [6], 170), 'right', rest, limits=None)
        self.assertAlmostEqual(rm.rotation_angle(t['right_index2'][1]), 170, places=2)

    def test_thumb_roll_is_captured(self):
        # Rolling the thumb about its own axis (opposition) changes its frame, not just direction.
        rest = rm.rest_hand_frames(flat_hand())
        pts = flat_hand()
        axis = rm.sub(pts[2], pts[1])
        roll = rm.axis_angle(axis, math.radians(40))
        rolled = [p[:] for p in pts]
        for k in range(5, 21):                                 # move the knuckles around the thumb axis
            rel = rm.sub(pts[k], pts[1])
            rolled[k] = rm.add(pts[1], [sum(roll[r][c] * rel[c] for c in range(3)) for r in range(3)])
        t = rm.hand_targets(rolled, 'right', rest)
        self.assertGreater(rm.rotation_angle(t['right_thumb1'][1]), 1.0)

    def test_thumb_follows_tracked_direction_without_flipping(self):
        # Thumb swung across the palm towards the index knuckle (the pose where the old roll
        # reference lined up with the bone): every thumb bone must point where the signer's does.
        rest_pts = flat_hand()
        rest = rm.rest_hand_frames(rest_pts)
        pts = [p[:] for p in rest_pts]
        pts[2], pts[3], pts[4] = [0.03, 0.05, 0.01], [0.022, 0.075, 0.012], [0.015, 0.09, 0.012]
        t = rm.hand_targets(pts, 'right', rest)
        for j, (a, b) in ((1, (1, 2)), (2, (2, 3)), (3, (3, 4))):
            rest_dir = rm.norm(rm.sub(rest_pts[b], rest_pts[a]))
            got = rm.norm(rm.mat_vec(t[f'right_thumb{j}'][1], rest_dir))
            want = rm.norm(rm.sub(pts[b], pts[a]))
            self.assertGreater(rm.dot(got, want), 0.9999)

    def test_spread_angles_detect_abduction(self):
        narrow, wide = mm.spread_angles(flat_hand(spread=0.5)), mm.spread_angles(curl(flat_hand(), [], 0))
        self.assertLess(narrow['index_middle'], 1e-6 + wide['index_middle'] + 1e-9)


class ShoulderAndHeadTest(unittest.TestCase):
    def pose(self, lift_left=0.0, lift_right=0.0):
        return {'l_shoulder': [0.18, 0, 0.5 + lift_left], 'r_shoulder': [-0.18, 0, 0.5 + lift_right],
                'l_hip': [0.1, 0, 0.0], 'r_hip': [-0.1, 0, 0.0], 'l_elbow': [0.2, 0, 0.2], 'r_elbow': [-0.2, 0, 0.2],
                'l_wrist': [0.2, 0, 0.0], 'r_wrist': [-0.2, 0, 0.0]}

    def test_no_shrug_at_neutral(self):
        neutral = {'left': 0.5, 'right': 0.5, 'width': 0.36}
        for rot in rm.shrug_rotations(self.pose(), rm.IDENTITY, neutral).values():
            self.assertAlmostEqual(rm.rotation_angle(rot), 0, places=6)

    def test_raised_shoulder_lifts_the_collarbone_end(self):
        neutral = {'left': 0.5, 'right': 0.5, 'width': 0.36}
        rots = rm.shrug_rotations(self.pose(lift_left=0.04), rm.IDENTITY, neutral)
        lateral_end = [sum(rots['left'][r][c] * v for c, v in enumerate([1, 0, 0])) for r in range(3)]
        self.assertGreater(lateral_end[2], 0.05)                # the left (+X) end goes up
        self.assertAlmostEqual(rm.rotation_angle(rots['right']), 0, places=6)

    def test_shrug_is_limited(self):
        neutral = {'left': 0.5, 'right': 0.5, 'width': 0.36}
        rots = rm.shrug_rotations(self.pose(lift_left=1.0), rm.IDENTITY, neutral)
        self.assertAlmostEqual(rm.rotation_angle(rots['left']), rm.SHRUG_LIMITS[1], places=4)

    def test_neck_takes_its_share_of_a_head_turn(self):
        turn = rm.axis_angle([0, 0, 1], math.radians(50))
        self.assertAlmostEqual(rm.rotation_angle(rm.partial_rotation(turn, 0.4)), 20, places=4)

    def test_slerp_halfway_and_shortest_path(self):
        q0 = rm.mat_to_quat(rm.IDENTITY)
        q1 = rm.mat_to_quat(rm.axis_angle([0, 1, 0], math.radians(90)))
        half = rm.quat_to_mat(rm.slerp(q0, q1, 0.5))
        self.assertAlmostEqual(rm.rotation_angle(half), 45, places=4)
        neg = [-v for v in q1]
        self.assertAlmostEqual(rm.rotation_angle(rm.quat_to_mat(rm.slerp(q0, neg, 0.5))), 45, places=4)

    def test_arm_ik_shoulder_rides_on_shrug(self):
        body = {'chest_pivot': [0, 0, 1.3], 'l_shoulder': [0.15, 0, 1.4], 'r_shoulder': [-0.15, 0, 1.4],
                'l_clavicle': [0.02, 0, 1.4], 'r_clavicle': [-0.02, 0, 1.4],
                'l_upper': 0.28, 'l_fore': 0.26, 'r_upper': 0.28, 'r_fore': 0.26,
                'video_arm': {'left': 0.54, 'right': 0.54}}
        p = {'l_shoulder': [0.15, 0, 1.4], 'r_shoulder': [-0.15, 0, 1.4], 'l_elbow': [0.2, -0.1, 1.15],
             'r_elbow': [-0.2, -0.1, 1.15], 'l_wrist': [0.1, -0.3, 1.2], 'r_wrist': [-0.1, -0.3, 1.2]}
        lift = {'left': rm.axis_angle([0, 1, 0], math.radians(-15))}
        plain = rm.arm_ik_targets(p, rm.IDENTITY, body)
        shrugged = rm.arm_ik_targets(p, rm.IDENTITY, body, lift)
        self.assertNotEqual(plain['left_upper_arm'][1], shrugged['left_upper_arm'][1])
        self.assertEqual(plain['right_upper_arm'][1], shrugged['right_upper_arm'][1])


class MetricsTest(unittest.TestCase):
    def test_straight_hand_has_no_flexion(self):
        # PIP and DIP are straight; MCP is measured from the wrist, so side fingers read their
        # splay there (the same definition is used for source and avatar).
        for name, value in mm.flexion_angles(flat_hand()).items():
            if name.endswith(('_pip', '_dip')):
                self.assertAlmostEqual(value, 0, places=6)

    def test_orientation_error_and_body_offset(self):
        turn = rm.axis_angle([0, 0, 1], math.radians(30))
        self.assertAlmostEqual(mm.orientation_error(rm.IDENTITY, turn), 30, places=4)
        chest = mm.chest_frame([0.2, 0, 0], [-0.2, 0, 0])
        off = mm.body_offset([0.2, -0.2, -0.4], [0.2, 0, 0], [-0.2, 0, 0], chest)
        close(self, off, [0.5, -1.0, 0.5])    # [left, up, forward] in shoulder widths

    def test_dtw_finds_a_time_shift(self):
        a = [math.sin(i / 3) for i in range(40)]
        b = [0.0] * 3 + a[:-3]
        aligned, path = mm.dtw(a, b, lambda x, y: abs(x - y))
        direct = sum(abs(x - y) for x, y in zip(a, b)) / len(a)
        self.assertLess(aligned, direct)

    def test_contact_and_correlation(self):
        left = flat_hand()
        right = [rm.add(p, [0.0, 0.0, 0.001]) for p in flat_hand()]
        self.assertLess(mm.contact(left, right, 0.36), mm.CONTACT_THRESHOLD)
        self.assertAlmostEqual(mm.correlation([1, 2, 3, 4], [2, 4, 6, 8]), 1.0)
        self.assertEqual(mm.summarise([None, None]), {'n': 0})


if __name__ == '__main__':
    unittest.main()


class FaceCalibrationTest(unittest.TestCase):
    def test_neutral_from_rest_frames_and_rescale(self):
        frames = [{'blendshapes': {'eyeSquintLeft': 0.25, 'browInnerUp': 0.0}}] * 4 + \
                 [{'blendshapes': {'eyeSquintLeft': 0.25, 'browInnerUp': 0.9}}] * 6
        resting = [True] * 4 + [False] * 6
        neutral, method = rm.face_neutral(frames, resting)
        self.assertEqual(method, 'rest_frames')
        self.assertAlmostEqual(neutral['eyeSquintLeft'], 0.25)
        self.assertAlmostEqual(rm.calibrate_score(0.25, neutral['eyeSquintLeft']), 0.0)   # relaxed face -> 0
        self.assertAlmostEqual(rm.calibrate_score(1.0, 0.25), 1.0)                         # full stays full
        self.assertAlmostEqual(rm.calibrate_score(0.9, neutral['browInnerUp']), 0.9)       # real expression kept

    def test_falls_back_to_percentile_without_rest(self):
        frames = [{'blendshapes': {'jawOpen': v / 10}} for v in range(10)]
        neutral, method = rm.face_neutral(frames, [False] * 10)
        self.assertEqual(method, 'percentile')
        self.assertAlmostEqual(neutral['jawOpen'], 0.1)


class EaseWeightsTest(unittest.TestCase):
    def test_corrected_frames_full_and_neighbours_faded(self):
        w = rm.ease_weights({5: 'x'}, 12, 2)
        self.assertEqual(w[5], (5, 1.0))
        self.assertEqual(w[4], (5, 1 - 1 / 3))
        self.assertEqual(w[7], (5, 1 - 2 / 3))
        self.assertNotIn(8, w)
        self.assertNotIn(2, w)

    def test_nearest_correction_wins_and_bounds(self):
        w = rm.ease_weights([0, 6], 8, 2)
        self.assertEqual(w[1][0], 0)
        self.assertEqual(w[5][0], 6)
        self.assertEqual(w[7], (6, 1 - 1 / 3))
        self.assertEqual(rm.ease_weights([], 5, 2), {})


class RestWeightsTest(unittest.TestCase):
    def test_smoothstep_ends_flat(self):
        self.assertEqual(rm.smoothstep(0), 0)
        self.assertEqual(rm.smoothstep(1), 1)
        self.assertAlmostEqual(rm.smoothstep(0.5), 0.5)
        self.assertLess(rm.smoothstep(0.1), 0.1)          # slow start, no jump

    def test_rest_weights_ramp_inside_resting_stretch(self):
        resting = [True] * 8 + [False] * 10 + [True] * 8
        w = rm.rest_weights(resting, 3)
        self.assertEqual(w[:4], [1.0] * 4)                    # clip starts at rest: fully at rest
        self.assertTrue(1 > w[5] > w[6] > w[7] > 0)           # eases out before the hand leaves
        self.assertTrue(all(v == 0.0 for v in w[8:18]))       # while signing: pure tracking
        self.assertTrue(0 < w[18] < w[19] < w[20] < 1)        # eases in after the hand arrives
        self.assertEqual(w[-1], 1.0)                          # clip ends at rest
        self.assertEqual(rm.rest_weights([False] * 4, 3), [0.0] * 4)
        mid = rm.rest_weights([False, True, True, False], 3)
        self.assertTrue(0 < mid[1] < 1 and mid[0] == 0 and mid[3] == 0)


class ImageAnchoredHandTest(unittest.TestCase):
    """The 3D hand flattens a claw; the picture shows it. Anchoring recovers the curl."""

    @staticmethod
    def upright(pts):
        # flat_hand lies in the X-Y plane with fingers along +Y; stand it up facing the camera:
        # fingers up (+Z), depth along Y (the camera looks along +Y).
        return [[p[0], p[2], p[1]] for p in pts]

    def project(self, pts):
        return [[0.5 + p[0], 0.5 - p[2]] for p in pts]                    # 1 x 1 picture, metres

    def test_curled_fingers_recovered_from_the_picture(self):
        flat = self.upright(flat_hand())
        side = 'right'
        n = rm.scale(rm.cross(rm.sub(flat[5], flat[0]), rm.sub(flat[17], flat[0])), rm.PALM_SIGN[side])
        palm_dir = rm.norm(n)
        curled = [p[:] for p in flat]
        for chain in rm.FINGER_CHAINS.values():
            for j in chain[:3]:                     # bend MCP, PIP, DIP by 50 deg towards the palm
                axis = rm.norm(rm.cross(rm.sub(curled[j + 1], curled[j]), palm_dir))
                rot = rm.axis_angle(axis, math.radians(50))
                for k in range(j + 1, chain[3] + 1):
                    rel = rm.sub(curled[k], curled[j])
                    curled[k] = rm.add(curled[j], [sum(rot[r][c] * rel[c] for c in range(3)) for r in range(3)])
        segs = {(a, b): rm.length(rm.sub(flat[b], flat[a])) for ch in rm.FINGER_CHAINS.values()
                for a, b in zip(ch, ch[1:])}
        fixed = rm.image_anchored_hand(flat, self.project(curled), 1, 1, side, segs)
        want = mm.flexion_angles(curled)
        got = mm.flexion_angles(fixed)
        before = mm.flexion_angles(flat)
        for joint in ('index_pip', 'middle_pip', 'ring_dip'):
            self.assertLess(abs(got[joint] - want[joint]), 3.0, joint)
            self.assertGreater(abs(before[joint] - want[joint]), 40.0, joint)

    def test_straight_hand_stays_straight(self):
        flat = self.upright(flat_hand())
        segs = {(a, b): rm.length(rm.sub(flat[b], flat[a])) for ch in rm.FINGER_CHAINS.values()
                for a, b in zip(ch, ch[1:])}
        fixed = rm.image_anchored_hand(flat, self.project(flat), 1, 1, 'right', segs)
        for joint, v in mm.flexion_angles(fixed).items():
            if joint.endswith(('_pip', '_dip')):
                self.assertAlmostEqual(v, 0.0, places=4)


class PalmFitTest(unittest.TestCase):
    def test_palm_turn_recovered_from_its_outline(self):
        hand = ImageAnchoredHandTest.upright(flat_hand())
        turn = rm.mat_mul(rm.axis_angle([0, 0, 1], math.radians(35)), rm.axis_angle([1, 0, 0], math.radians(-25)))
        c = hand[9]
        seen = [rm.add(c, rm.mat_vec(turn, rm.sub(p, c))) for p in hand]
        image = [[0.5 + p[0], 0.5 - p[2]] for p in seen]
        fitted, resid = rm.image_fitted_palm(hand, image, 1, 1)
        self.assertLess(resid, 0.02)
        n_fit = rm.norm(rm.cross(rm.sub(fitted[5], fitted[0]), rm.sub(fitted[17], fitted[0])))
        n_true = rm.norm(rm.cross(rm.sub(seen[5], seen[0]), rm.sub(seen[17], seen[0])))
        self.assertGreater(abs(rm.dot(n_fit, n_true)), 0.99)

    def test_untouched_when_already_matching(self):
        hand = ImageAnchoredHandTest.upright(flat_hand())
        image = [[0.5 + p[0], 0.5 - p[2]] for p in hand]
        fitted, resid = rm.image_fitted_palm(hand, image, 1, 1)
        close(self, fitted, hand, places=6)


class PalmFitScaleTest(unittest.TestCase):
    def test_residual_in_palm_lengths_at_pixel_scale(self):
        # A 1920 x 1080 picture: the residual must still be a small fraction of a palm length.
        hand = ImageAnchoredHandTest.upright(flat_hand())
        turn = rm.axis_angle([0, 0, 1], math.radians(30))
        c = hand[9]
        seen = [rm.add(c, rm.mat_vec(turn, rm.sub(p, c))) for p in hand]
        image = [[(960 + p[0] * 3000) / 1920, (540 - p[2] * 3000) / 1080] for p in seen]
        fitted, resid = rm.image_fitted_palm(hand, image, 1920, 1080)
        self.assertLess(resid, 0.02)
        self.assertLess(resid, rm.PALM_FIT_MAX_RESIDUAL)

    def test_palm_fit_is_switched_off_in_the_pipeline(self):
        # Measured to make handshapes worse (AUDIT_REPORT.md); the fit itself stays tested above.
        self.assertFalse(rm.PALM_FIT)


class WristInFrontTest(unittest.TestCase):
    def test_hand_in_front_of_belly_never_goes_behind(self):
        # Shoulders 0.4 apart at height 1.4; the picture shows the left wrist in front of the belly.
        p = {'l_shoulder': [0.2, 0.0, 1.4], 'r_shoulder': [-0.2, 0.0, 1.4],
             'l_elbow': [0.25, 0.02, 1.15], 'r_elbow': [-0.25, 0.0, 1.15],
             'l_wrist': [0.05, 0.01, 1.05], 'r_wrist': [-0.25, 0.0, 0.9]}      # 3D: wrist slightly BEHIND
        W = H = 1000
        pose = [[0.5, 0.5, 0, 1.0] for _ in range(33)]
        for name, i in rm.POSE.items():
            if name in p:                       # the same points as seen in a 1000 x 1000 picture
                pose[i] = [0.5 + p[name][0] / 2, 1.0 - p[name][2] / 2, 0, 1.0]
        frame = {'pose': pose}
        segs = {'left': (0.26, 0.24), 'right': (0.26, 0.24)}
        out = rm.image_anchored_arms(frame, W, H, p, 0.4, segs)
        self.assertLess(out['l_wrist'][1], out['l_elbow'][1])                # in front of the elbow (-Y)


class FaceShiftTest(unittest.TestCase):
    def setUp(self):
        self.p = {'l_shoulder': [0.2, 0, 1.4], 'r_shoulder': [-0.2, 0, 1.4], 'mouth': [0, 0, 1.6],
                  'l_wrist': [0.2, -0.2, 1.0], 'r_wrist': [0.0, -0.1, 1.6]}
        self.body = {'mouth': [0.0, -0.08, 1.65]}
        self.scales = {'x': 1, 'depth': 1, 'up': 1, 'down': 1}

    def test_hand_at_mouth_moves_to_avatar_mouth(self):
        shift = rm.face_shift(self.p, 'r', self.body, [0, 0, 1.4], [0, 0, 1.4], self.scales, lambda q: q)
        self.assertAlmostEqual(shift[2], 0.05)          # avatar mouth 5 cm higher
        self.assertEqual(shift[1], 0.0)                  # depth untouched

    def test_hand_far_from_face_unchanged(self):
        shift = rm.face_shift(self.p, 'l', self.body, [0, 0, 1.4], [0, 0, 1.4], self.scales, lambda q: q)
        self.assertEqual(shift, [0.0, 0.0, 0.0])


class FingerFitTest(unittest.TestCase):
    """fitted_finger_hand: anatomically possible fingers that match the picture (12 Nov 2026)."""

    def hand(self, bends):
        """A right hand in armature axes, seen from the side: knuckles spread along Y (depth), so
        the palm faces along X and finger bends show in the X/Z picture plane. Fingers bent by `bends`."""
        import retarget_math as rm
        wrist = [0.0, 0.0, 0.0]
        knuckles = {5: [0.0, -0.03, 0.09], 9: [0.0, -0.01, 0.095], 13: [0.0, 0.01, 0.09], 17: [0.0, 0.03, 0.08]}
        pts = [list(wrist)] + [[0.0, 0.0, 0.0]] * 20
        pts[1], pts[2], pts[3], pts[4] = [0, -0.03, 0.02], [0, -0.045, 0.04], [0, -0.055, 0.06], [0, -0.06, 0.075]
        normal = rm.norm(rm.scale(rm.cross(rm.sub(knuckles[5], wrist), rm.sub(knuckles[17], wrist)), rm.PALM_SIGN['right']))
        lengths = (0.04, 0.025, 0.02)
        for chain in rm.FINGER_CHAINS.values():
            base = knuckles[chain[0]]
            pts[chain[0]] = base
            for j, p in zip(chain[1:], rm._finger_chain_points(base, [0, 0, 1], normal, lengths, bends)):
                pts[j] = p
        segs = {(a, b): l for chain in rm.FINGER_CHAINS.values() for (a, b), l in zip(zip(chain, chain[1:]), lengths)}
        return pts, normal, segs

    def test_recovers_a_neat_fold_from_the_picture(self):
        import retarget_math as rm
        truth, normal, segs = self.hand((45.0, 80.0, 54.0))
        flat, _, _ = self.hand((10.0, 20.0, 10.0))          # what a flattening 3D tracker reports
        # The picture: the true hand seen along Y (x right, z up), as normalised image landmarks.
        W = H = 1000
        image = [[0.5 + p[0] * 2, 0.5 - p[2] * 2, 0.0] for p in truth]
        fit = rm.fitted_finger_hand(flat, image, W, H, 'right', segs)
        for chain in rm.FINGER_CHAINS.values():
            for j in chain[1:]:
                self.assertLess(rm.length(rm.sub(fit[j], truth[j])), 0.01)   # within 1 cm

    def test_never_beyond_the_limits(self):
        import retarget_math as rm
        flat, _, segs = self.hand((0.0, 0.0, 0.0))
        # A picture that asks for an impossible fold: fingertips drawn back at the wrist.
        image = [[0.5 + p[0] * 2, 0.5 - p[2] * 2, 0.0] for p in flat]
        for chain in rm.FINGER_CHAINS.values():
            for j in chain[1:]:
                image[j] = [0.5, 0.5, 0.0]
        fit = rm.fitted_finger_hand(flat, image, 1000, 1000, 'right', segs)
        for chain in rm.FINGER_CHAINS.values():
            a, b, c, d = chain
            bends = [rm._angle([0, 0, 1], rm.sub(fit[b], fit[a])), rm._angle(rm.sub(fit[b], fit[a]), rm.sub(fit[c], fit[b])),
                     rm._angle(rm.sub(fit[c], fit[b]), rm.sub(fit[d], fit[c]))]
            for got, lim in zip(bends, rm.FIT_LIMITS):
                self.assertLessEqual(got, lim + 0.5)
