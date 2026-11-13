"""Put avatar renders under the matching reference-video frames, for interpreter review.

    python tools/compare_frames.py references/cislr_electricity.mp4 previews/electricity 11 26 36 46 61 \
        --out previews/electricity_compare.jpg

Frame numbers are Blender's (video frame index + 1), as given to render_preview.py.
"""

import argparse

import cv2
import numpy as np

p = argparse.ArgumentParser()
p.add_argument('video')
p.add_argument('renders', help='render prefix used with render_preview.py --out')
p.add_argument('frames', type=int, nargs='+')
p.add_argument('--out', required=True)
p.add_argument('--tile', type=int, default=240)
args = p.parse_args()

wanted = {f - 1 for f in args.frames}
video = {}
cap = cv2.VideoCapture(args.video)
i = 0
while True:
    ok, img = cap.read()
    if not ok:
        break
    if i in wanted:
        video[i + 1] = cv2.resize(img, (args.tile, args.tile))
    i += 1

top = np.hstack([video[f] for f in args.frames])
bottom = np.hstack([cv2.resize(cv2.imread(f'{args.renders}_{f:04d}.png'), (args.tile, args.tile)) for f in args.frames])
cv2.imwrite(args.out, np.vstack([top, bottom]))
print('saved', args.out)
