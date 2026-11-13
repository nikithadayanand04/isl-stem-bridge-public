"""NOT USED since 13 Nov 2026: the player no longer applies voice-driven lip-sync (school feedback:
the lesson is for Deaf students; the avatar keeps the ISLRTC signer's own face). Kept for reference.

Mouth movement from a narration audio file. Pure Python + numpy (unit-tested).

Language-independent on purpose: no phoneme recogniser exists offline for Kannada, so the mouth is
driven by the sound itself, per 1/60 s:
  loudness           -> how far the jaw opens (jawOpen)
  low, dark sound    -> rounded lips (mouthFunnel, mouthPucker), as in o / u
  bright, hissy sound-> spread lips (mouthStretch), as in i / e / s
  silence            -> mouth closed
The curves are smoothed forwards and backwards (no lag), so the mouth moves with the voice.

NOTE (project decision, 11 Nov 2026): the player applies this lip-sync on top of everything,
including while the avatar signs. That replaces the ISLRTC signer's own mouth movements (mouthing
and mouth gestures, which are part of ISL) during narration. See AUDIT_REPORT.md.
"""

import math

import numpy as np

FPS = 60
SILENCE = 0.06          # loudness below this fraction of the voice's loud level = closed mouth
MAX_JAW = 0.35          # speaking-sized: at 0.65 the mouth gaped and the lower lip and tongue showed
                        # (checked in the player, 11 Nov 2026)


def _filtfilt(x, cutoff_hz, fs):
    import smoothing
    return smoothing.filtfilt(list(x), cutoff_hz, fs)


def frames(samples, rate, fps=FPS):
    """(loudness, spectral centroid Hz) per animation frame. samples: mono floats in -1..1."""
    hop = rate / fps
    n = int(round(len(samples) / hop))
    win = int(hop * 2)
    loud, centroid = [], []
    window = np.hanning(win)
    freqs = np.fft.rfftfreq(win, 1 / rate)
    for i in range(n):
        a = int(i * hop)
        chunk = samples[a:a + win]
        if len(chunk) < win:
            chunk = np.pad(chunk, (0, win - len(chunk)))
        loud.append(float(np.sqrt(np.mean(chunk ** 2))))
        spec = np.abs(np.fft.rfft(chunk * window))
        total = spec.sum()
        centroid.append(float((freqs * spec).sum() / total) if total > 1e-9 else 0.0)
    return loud, centroid


def visemes(loud, centroid, fps=FPS):
    """Mouth shape weights per frame: {'jawOpen': [...], 'mouthFunnel': [...], ...} in 0..1."""
    if not loud:
        return {}
    ref = sorted(loud)[int(len(loud) * 0.95)] or 1e-9          # the voice's loud level
    jaw, rnd, wide = [], [], []
    for l, c in zip(loud, centroid):
        level = l / ref
        open_ = 0.0 if level < SILENCE else min(1.0, (level - SILENCE) / (1 - SILENCE)) ** 0.8
        jaw.append(MAX_JAW * open_)
        rnd.append(open_ * max(0.0, min(1.0, (1600 - c) / 900)))
        wide.append(open_ * max(0.0, min(1.0, (c - 2600) / 2400)))
    out = {}
    for name, curve, scale in (('jawOpen', jaw, 1.0), ('mouthFunnel', rnd, 0.45), ('mouthPucker', rnd, 0.3),
                               ('mouthStretchLeft', wide, 0.35), ('mouthStretchRight', wide, 0.35)):
        # (No mouthClose: in the ARKit set it is meant only together with an open jaw.)
        smoothed = _filtfilt(curve, 9.0, fps) if len(curve) > 20 else curve
        top = MAX_JAW if name == 'jawOpen' else 1.0              # smoothing may overshoot a little
        out[name] = [round(max(0.0, min(top, v * scale)), 3) for v in smoothed]
    return out


def from_wav(path):
    """Read a 16-bit PCM WAV (mono or stereo) and return its viseme curves at FPS."""
    import wave
    with wave.open(str(path), 'rb') as w:
        rate, ch, width, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(n)
    if width != 2:
        raise ValueError('expected 16-bit PCM')
    data = np.frombuffer(raw, dtype='<i2').astype(np.float64) / 32768.0
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    loud, cent = frames(data, rate)
    return {'fps': FPS, 'duration': round(len(data) / rate, 3), 'shapes': visemes(loud, cent)}
