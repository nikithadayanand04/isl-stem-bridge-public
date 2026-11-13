"""Tests for tools/lipsync.py. Run: python -m unittest discover tests  (needs numpy: use .venv)"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))

try:
    import numpy as np
    import lipsync as ls
except ImportError:          # system python without numpy: skip, the venv runs these
    np = None


@unittest.skipIf(np is None, 'numpy not available')
class LipSyncTest(unittest.TestCase):
    rate = 16000

    def tone(self, hz, seconds, amp=0.5):
        t = np.arange(int(self.rate * seconds)) / self.rate
        return amp * np.sin(2 * np.pi * hz * t)

    def test_silence_closes_and_sound_opens(self):
        x = np.concatenate([np.zeros(self.rate // 2), self.tone(300, 0.5), np.zeros(self.rate // 2)])
        loud, cent = ls.frames(x, self.rate)
        v = ls.visemes(loud, cent)
        jaw = v['jawOpen']
        self.assertLess(max(jaw[:20]), 0.05)                 # silent start: closed
        self.assertGreater(max(jaw[35:55]), 0.8 * ls.MAX_JAW)  # voice: open (to the speaking-sized cap)
        self.assertLess(max(jaw[-15:]), 0.05)               # silent end: closed
        self.assertLessEqual(max(jaw), ls.MAX_JAW + 1e-9)

    def test_dark_sound_rounds_bright_sound_spreads(self):
        low = ls.visemes(*ls.frames(self.tone(400, 0.6), self.rate))
        high = ls.visemes(*ls.frames(self.tone(4500, 0.6), self.rate))
        mid = slice(10, 26)
        self.assertGreater(np.mean(low['mouthFunnel'][mid]), np.mean(high['mouthFunnel'][mid]))
        self.assertGreater(np.mean(high['mouthStretchLeft'][mid]), np.mean(low['mouthStretchLeft'][mid]))

    def test_frame_rate(self):
        loud, _ = ls.frames(self.tone(300, 1.0), self.rate)
        self.assertEqual(len(loud), ls.FPS)


if __name__ == '__main__':
    unittest.main()


class VoiceGenderTest(unittest.TestCase):
    def test_only_female_voices_accepted(self):
        import make_narration as mn
        self.assertIn('Lekha', mn.FEMALE_VOICES)
        self.assertNotIn('Rishi', mn.FEMALE_VOICES)
        self.assertTrue(mn.MALE_VOICES.isdisjoint(mn.FEMALE_VOICES))
