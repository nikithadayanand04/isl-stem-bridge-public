"""Tests for tools/motion_qc.py. Run: python -m unittest discover tests"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
from motion_qc import longest_gap, qc_report  # noqa: E402

P = [[0, 0, 0]]  # stand-in for a list of landmarks


def clip(n=60, right=None, left=None, pose=True, face=True):
    """right/left: set of frame indexes where that hand is tracked (None = never)."""
    return {'frames': [{
        'pose_world': P if pose else None,
        'face': P if face else None,
        'right_hand': P if right is not None and i in right else None,
        'left_hand': P if left is not None and i in left else None,
    } for i in range(n)]}


class MotionQcTest(unittest.TestCase):
    def test_longest_gap_ignores_edges(self):
        self.assertEqual(longest_gap([False, True, True, False, False, True, False, False, False]), 2)
        self.assertEqual(longest_gap([False, False]), 0)

    def test_clean_one_handed_sign_passes(self):
        report = qc_report(clip(right=set(range(10, 50))))
        self.assertEqual(report['result'], 'pass', report['problems'])
        self.assertFalse(report['hands']['left_hand']['signing'])

    def test_short_dropout_is_allowed(self):
        right = set(range(10, 50)) - {20, 21, 22}
        self.assertEqual(qc_report(clip(right=right))['result'], 'pass')

    def test_long_dropout_fails_instead_of_being_filled(self):
        right = set(range(10, 50)) - {20, 21, 22, 23}
        report = qc_report(clip(right=right))
        self.assertEqual(report['result'], 'fail')
        self.assertIn('right_hand lost for 4 frames', report['problems'][0])

    def test_two_handed_sign_checks_both_hands(self):
        report = qc_report(clip(right=set(range(60)), left=set(range(30)) | set(range(40, 60))))
        self.assertEqual(report['result'], 'fail')

    def test_resting_hand_is_not_a_lost_hand(self):
        # Image pose: shoulders at y=0.3 (x 0.4/0.6), hips at y=0.7 (x 0.45/0.55).
        def pose(left_wrist):
            p = [[0.5, 0.5, 0.0, 1.0] for _ in range(33)]
            p[11], p[12] = [0.6, 0.3, 0, 1], [0.4, 0.3, 0, 1]
            p[23], p[24] = [0.55, 0.7, 0, 1], [0.45, 0.7, 0, 1]
            p[15], p[16] = left_wrist + [0, 1], [0.45, 0.4, 0, 1]
            return p
        resting = pose([0.75, 0.72])      # hanging at the side, low
        signing = pose([0.52, 0.45])      # in front of the chest
        frames = []
        for i in range(60):
            lost = 20 <= i < 40
            frames.append({'pose_world': P, 'face': P, 'right_hand': P,
                           'left_hand': None if lost else P,
                           'pose': resting if lost else signing})
        self.assertEqual(qc_report({'frames': frames})['result'], 'pass')
        for f in frames[20:40]:
            f['pose'] = signing            # same gap, but the hand is in the signing space
        self.assertEqual(qc_report({'frames': frames})['result'], 'fail')

    def test_low_hand_in_front_of_body_is_still_signing(self):
        from motion_qc import hand_resting
        p = [[0.5, 0.5, 0.0, 1.0] for _ in range(33)]
        p[11], p[12], p[23], p[24] = [0.6, 0.3, 0, 1], [0.4, 0.3, 0, 1], [0.55, 0.7, 0, 1], [0.45, 0.7, 0, 1]
        p[15] = [0.52, 0.68, 0, 1]        # low, but centred: e.g. a sign at the stomach
        self.assertFalse(hand_resting({'pose': p}, 'left_hand'))
        p[15] = [0.5, 1.05, 0, 1]         # below the picture
        self.assertTrue(hand_resting({'pose': p}, 'left_hand'))

    def test_missing_face_or_body_fails(self):
        self.assertEqual(qc_report(clip(right=set(range(60)), face=False))['result'], 'fail')
        self.assertEqual(qc_report(clip(right=set(range(60)), pose=False))['result'], 'fail')

    def test_no_hands_fails(self):
        self.assertEqual(qc_report(clip())['result'], 'fail')
        self.assertEqual(qc_report({'frames': []})['result'], 'fail')


if __name__ == '__main__':
    unittest.main()


class DepthFlipTest(unittest.TestCase):
    """A hand mirrored front-to-back for a couple of frames is wrong data and counts as lost."""

    @staticmethod
    def hand(flip=False):
        pts = [[0.0, 0.0, 0.0]] + [[0.0, 0.0, 0.0]] * 20
        pts = [list(p) for p in pts]
        pts[5] = [0.03, -0.08, 0.0]
        pts[17] = [-0.03, -0.07, 0.0]
        pts[9] = [0.0, -0.09, 0.0]
        if flip:                       # mirror image: the palm normal points the other way
            pts[5], pts[17] = [-0.03, -0.08, 0.0], [0.03, -0.07, 0.0]
        return pts

    def frames(self, flipped):
        return [{'right_hand_world': self.hand(i in flipped)} for i in range(20)]

    def test_short_flip_is_found(self):
        import retarget_math as rm
        self.assertEqual(rm.depth_flip_frames(self.frames({8, 9}), 'right'), {8, 9})

    def test_no_flip_no_frames(self):
        import retarget_math as rm
        self.assertEqual(rm.depth_flip_frames(self.frames(set()), 'right'), set())

    def test_long_stretch_is_not_guessed(self):
        import retarget_math as rm
        # Ten frames each way: both stretches are long, so neither is marked.
        self.assertEqual(rm.depth_flip_frames(self.frames(set(range(10, 20))), 'right'), set())
