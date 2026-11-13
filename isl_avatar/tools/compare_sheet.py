"""Side-by-side sheet: for each sign, a row of source frames above the same moments on the avatar.

    .venv/bin/python tools/compare_sheet.py --out previews/compare_v3.jpg \
        electricity magnet magnet_sign_2 food photosynthesis

Avatar frames come from reports/visual_loop/<sign>/render.mp4 (rendered framed like the source,
frame i = the same moment as source frame i). Five key frames per sign, spread evenly over the
sign's movement (player/clip_timing.json), are shown in the same layout as docs_avatar_compare.jpg.
"""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def frame_at(video, i):
    cap = cv2.VideoCapture(str(video))
    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
    ok, img = cap.read()
    cap.release()
    return img if ok else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('signs', nargs='+')
    ap.add_argument('--out', required=True)
    ap.add_argument('--frames', type=int, default=5)
    ap.add_argument('--tile-height', type=int, default=240)
    ap.add_argument('--loop-dir', default=str(ROOT / 'reports' / 'visual_loop'))
    args = ap.parse_args()
    timing = json.loads((ROOT / 'player' / 'clip_timing.json').read_text(encoding='utf-8'))
    blocks = []
    for sign in args.signs:
        motion = json.loads((ROOT / 'motion' / 'v2' / f'{sign}.json').read_text(encoding='utf-8'))
        fps, n = motion['fps'], len(motion['frames'])
        span = timing.get(sign, {'start': 0, 'end': (n - 1) / fps})
        first, last = round(span['start'] * fps), round(span['end'] * fps)
        picks = [round(first + (last - first) * k / (args.frames - 1)) for k in range(args.frames)]
        rows = []
        for video in (ROOT / motion['source_video'], Path(args.loop_dir) / sign / 'render.mp4'):
            tiles = []
            for i in picks:
                img = frame_at(video, min(i, n - 1))
                h = args.tile_height
                img = cv2.resize(img, (int(img.shape[1] * h / img.shape[0]), h))
                tiles.append(img)
            rows.append(np.hstack(tiles))
        width = max(r.shape[1] for r in rows)
        rows = [cv2.copyMakeBorder(r, 0, 0, 0, width - r.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for r in rows]
        label = np.full((34, width, 3), 255, np.uint8)
        cv2.putText(label, f'{sign}: ISLRTC source (top) / avatar (bottom), frames {", ".join(map(str, picks))}',
                    (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        blocks.append(np.vstack([label] + rows + [np.full((10, width, 3), 255, np.uint8)]))
    width = max(b.shape[1] for b in blocks)
    blocks = [cv2.copyMakeBorder(b, 0, 0, 0, width - b.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for b in blocks]
    sheet = np.vstack(blocks)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(f'Wrote {out} ({sheet.shape[1]}x{sheet.shape[0]})')


if __name__ == '__main__':
    main()
