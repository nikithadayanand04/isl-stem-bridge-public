"""Where each sign's movement starts and ends, for the player: player/clip_timing.json.

The ISLRTC clips begin and end with the signer standing at rest. The player skips most of that
(so the sign does not start late) but keeps the blend into and out of the rest pose that the bake
adds (retarget_config.json: rest_pose.ease_frames), so the clip starts and ends in the same pose
as the idle clip and the crossfade has nothing to hide.

    python3 tools/clip_timing.py            # every sign with a motion/v2 file and a bake
"""

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import motion_qc  # noqa: E402


def hand_active(frame, side):
    """The hand is signing: not resting, and seen (hand tracked, or its wrist visible)."""
    if motion_qc.hand_resting(frame, f'{side}_hand'):
        return False
    pose = frame.get('pose')
    wrist_seen = bool(pose) and pose[15 if side == 'left' else 16][3] >= 0.5
    return frame.get(f'{side}_hand') is not None or wrist_seen


def active_span(frames):
    """First and last frame where either hand is signing (indices), or None."""
    idx = [i for i, f in enumerate(frames) if hand_active(f, 'left') or hand_active(f, 'right')]
    return (idx[0], idx[-1]) if idx else None


def timing(motion, ease):
    span = active_span(motion['frames'])
    n, fps = len(motion['frames']), motion['fps']
    if span is None:
        return {'start': 0.0, 'end': round((n - 1) / fps, 3)}
    start = max(0, span[0] - ease)
    end = min(n - 1, span[1] + ease)
    return {'start': round(start / fps, 3), 'end': round(end / fps, 3)}


def main():
    config = json.loads((ROOT / 'tools' / 'retarget_config.json').read_text(encoding='utf-8'))
    ease = config.get('rest_pose', {}).get('ease_frames', 6)
    out = {}
    for r in csv.DictReader(open(ROOT / 'registry' / 'signs.csv', encoding='utf-8')):
        path = ROOT / r['motion_file'] if r['motion_file'] else None
        if r['retarget_check'] == 'pass' and path and path.exists():
            out[r['sign_id']] = timing(json.loads(path.read_text(encoding='utf-8')), ease)
    (ROOT / 'player' / 'clip_timing.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    for k, v in out.items():
        print(f'{k:24} play {v["start"]:.2f}s - {v["end"]:.2f}s')


if __name__ == '__main__':
    main()
