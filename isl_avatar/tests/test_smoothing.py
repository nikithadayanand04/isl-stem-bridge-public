"""Tests for tools/smoothing.py and tools/visual_metrics.py. Run: python -m unittest discover tests"""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
import smoothing as sm  # noqa: E402
import visual_metrics as vm  # noqa: E402


class FiltFiltTest(unittest.TestCase):
    def test_no_lag_and_peak_kept(self):
        fs = 25.0
        x = [math.sin(2 * math.pi * 1.0 * i / fs) for i in range(100)]     # 1 Hz movement
        y = sm.filtfilt(x, 6.0, fs)
        peak_x = max(range(20, 42), key=lambda i: x[i])        # one period only
        peak_y = max(range(20, 42), key=lambda i: y[i])
        self.assertEqual(peak_x, peak_y)                     # zero phase: no delay
        self.assertGreater(max(y[20:80]), 0.97)              # the peak is not flattened

    def test_removes_jitter(self):
        fs = 25.0
        x = [(-1) ** i * 0.1 for i in range(60)]             # pure frame-to-frame jitter
        y = sm.filtfilt(x, 4.0, fs)
        self.assertLess(max(abs(v) for v in y[10:50]), 0.02)

    def test_constant_and_short_sequences(self):
        self.assertTrue(all(abs(v - 3) < 1e-9 for v in sm.filtfilt([3.0] * 40, 5, 25)))
        self.assertEqual(sm.filtfilt([1.0, 5.0, 2.0], 5, 25), [1.0, 5.0, 2.0])

    def test_track_filters_runs_and_keeps_gaps(self):
        frames = [{'k': [[float(i % 2), 0.0, 0.0, 0.9]]} for i in range(30)] + [{}] + \
                 [{'k': [[1.0, 0.0, 0.0, 0.9]]} for _ in range(5)]
        sm.zero_phase_track(frames, 'k', 25.0, 3.0)
        self.assertNotIn('k', frames[30])
        self.assertAlmostEqual(frames[15]['k'][0][0], 0.5, delta=0.1)
        self.assertEqual(frames[15]['k'][0][3], 0.9)          # visibility untouched
        self.assertEqual(frames[33]['k'][0][0], 1.0)          # short stretch left raw


class DetectorSwitchTest(unittest.TestCase):
    def test_switch_is_crossfaded(self):
        hol, mod = [[0.0, 0.0, 0.0]], [[1.0, 0.0, 0.0]]
        frames = []
        for i in range(10):
            src = 'holistic' if i < 5 else 'hand_model'
            frames.append({'right_hand_holistic': hol, 'right_hand_model': mod,
                           'right_hand': hol if src == 'holistic' else mod, 'right_hand_source': src})
        self.assertEqual(sm.blend_detector_switches(frames, 'right', 4), 1)
        xs = [f['right_hand'][0][0] for f in frames]
        self.assertEqual(xs[0], 0.0)
        self.assertEqual(xs[-1], 1.0)
        self.assertTrue(all(b >= a for a, b in zip(xs, xs[1:])))
        self.assertTrue(all(abs(b - a) < 0.5 for a, b in zip(xs, xs[1:])))   # no hard jump


class ResampleTest(unittest.TestCase):
    def test_passes_through_keys_and_fills_gap_smoothly(self):
        times = [0, 1, 2, 5, 6]
        values = [0.0, 1.0, 2.0, 5.0, 6.0]                    # a straight line with a gap
        out = sm.resample(times, values, [0, 1, 3.5, 6])
        self.assertAlmostEqual(out[0], 0.0)
        self.assertAlmostEqual(out[1], 1.0)
        self.assertAlmostEqual(out[3], 6.0)
        self.assertTrue(2.0 < out[2] < 5.0)

    def test_quaternions_stay_unit_and_hemisphere(self):
        q0, q1 = [1, 0, 0, 0], [-math.cos(0.2), -math.sin(0.2), 0, 0]   # same side after alignment
        out = sm.resample([0, 1], [q0, q1], [0.5], quaternion=True)[0]
        self.assertAlmostEqual(sum(c * c for c in out), 1.0)
        self.assertGreater(out[0], 0.9)


class SmoothnessTest(unittest.TestCase):
    def test_spikes_counted(self):
        dirs = []
        for i in range(50):
            a = math.radians(i * 2 + (40 if i == 25 else 0))
            dirs.append([math.cos(a), math.sin(a), 0.0])
        s = sm.smoothness(dirs, 25.0)
        self.assertEqual(s['spike_frames'], 2)                # into and out of the jump
        self.assertAlmostEqual(s['median_deg_s'], 50.0, delta=1)


class VisualMetricsTest(unittest.TestCase):
    @staticmethod
    def pose(wrist_y):
        p = [[0.5, 0.5, 0, 1.0] for _ in range(33)]
        p[11], p[12] = [0.6, 0.5, 0, 1.0], [0.4, 0.5, 0, 1.0]
        p[0] = [0.5, 0.3, 0, 1.0]
        p[13], p[14] = [0.65, 0.6, 0, 1.0], [0.35, 0.6, 0, 1.0]
        p[15], p[16] = [0.65, wrist_y, 0, 1.0], [0.35, wrist_y, 0, 1.0]
        return p

    def clip(self, wrist_ys, size=(100, 100)):
        return {'width': size[0], 'height': size[1], 'frames': [{'pose': self.pose(y)} for y in wrist_ys]}

    def test_identical_passes_and_scale_invariant(self):
        a = self.clip([0.7, 0.4, 0.2])
        b = self.clip([0.7, 0.4, 0.2], size=(200, 200))       # same picture, other resolution
        r = vm.compare(a, b)
        self.assertEqual(r['visual_check']['result'], 'pass')
        self.assertAlmostEqual(r['left']['wrist_error']['median'], 0.0)

    def test_low_hand_fails_and_sign_says_lower(self):
        src = self.clip([0.7, 0.3, 0.1])
        av = self.clip([0.75, 0.4, 0.2])                       # avatar's hands 0.5 shoulder widths lower
        r = vm.compare(src, av)
        self.assertEqual(r['visual_check']['result'], 'fail')
        self.assertGreater(r['right']['wrist_height_error_signed']['median'], 0.4)
        self.assertAlmostEqual(r['right']['peak_height']['error'], 0.5, places=3)

    def test_invisible_points_are_skipped(self):
        src = self.clip([0.7, 0.4])
        for f in src['frames']:
            f['pose'][15][3] = 0.1                             # signer's left wrist out of view
        r = vm.compare(src, self.clip([0.7, 0.4]))
        self.assertNotIn('left', r)
        self.assertIn('right', r)


if __name__ == '__main__':
    unittest.main()
