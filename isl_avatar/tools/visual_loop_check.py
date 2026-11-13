"""Closed-loop visual check: render each baked sign, track the render with the same tracker as the
source video, and compare the two in the picture (tools/visual_metrics.py).

    .venv/bin/python tools/visual_loop_check.py                    # every baked sign
    .venv/bin/python tools/visual_loop_check.py electricity magnet  # just these
    .venv/bin/python tools/visual_loop_check.py --reuse             # re-compare existing renders

Writes reports/visual_loop/<sign>/: render.mp4, landmarks of the render (<sign>.json),
report.json, report.md and side_by_side.mp4 (source | avatar render | landmark overlay), and
reports/visual_loop/SUMMARY.md.
"""

import argparse
import csv
import json
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import visual_metrics as vm  # noqa: E402

BLENDER = '/Applications/Blender.app/Contents/MacOS/Blender'
OUT = ROOT / 'reports' / 'visual_loop'


def baked_signs():
    rows = csv.DictReader(open(ROOT / 'registry' / 'signs.csv', encoding='utf-8'))
    return [r['sign_id'] for r in rows if r['retarget_check'] == 'pass']


def source_framing(motion):
    poses = [f['pose'] for f in motion['frames'] if f.get('pose')]
    med = lambda v: statistics.median(v)
    return {'width': motion['width'], 'height': motion['height'],
            'shoulder_u': med([(p[11][0] + p[12][0]) / 2 for p in poses]),
            'shoulder_v': med([(p[11][1] + p[12][1]) / 2 for p in poses]),
            'hip_v': med([(p[23][1] + p[24][1]) / 2 for p in poses])}


def render(sign, motion, blend, folder, width):
    frames_dir = Path(tempfile.mkdtemp(prefix=f'loop_{sign}_'))
    cmd = [BLENDER, '-b', str(blend), '--python', str(ROOT / 'tools' / 'render_sign_video.py'), '--',
           '--track', sign, '--out', str(frames_dir), '--frames', str(len(motion['frames'])),
           '--source-fps', str(motion['fps']), '--frame-json', json.dumps(source_framing(motion)),
           '--render-width', str(width)]
    log = subprocess.run(cmd, capture_output=True, text=True)
    if log.returncode != 0 or not any(frames_dir.iterdir()):
        raise SystemExit(f'Render of {sign} failed:\n{log.stdout[-2000:]}\n{log.stderr[-2000:]}')
    pngs = sorted(frames_dir.glob('frame_*.png'))
    first = cv2.imread(str(pngs[0]))
    video = folder / 'render.mp4'
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*'mp4v'), motion['fps'],
                             (first.shape[1], first.shape[0]))
    for p in pngs:
        writer.write(cv2.imread(str(p)))
    writer.release()
    shutil.rmtree(frames_dir)
    return video


def track(sign, video, folder, confidence):
    cmd = [sys.executable, str(ROOT / 'tools' / 'extract_landmarks.py'), str(video), '--sign-id', sign,
           '--out-dir', str(folder), '--confidence', str(confidence)]
    log = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    path = folder / f'{sign}.json'
    if not path.exists():
        raise SystemExit(f'Tracking the render of {sign} failed:\n{log.stdout[-2000:]}\n{log.stderr[-2000:]}')
    return json.loads(path.read_text(encoding='utf-8'))


EDGES = [(11, 12), (11, 13), (13, 15), (12, 14), (14, 16), (11, 23), (12, 24), (23, 24)]


def overlay(src_frame, av_frame, src, av, size):
    """Both skeletons on one canvas, each normalised to its own shoulders (blue source, red avatar)."""
    canvas = np.full((size, size, 3), 255, np.uint8)
    for frame, meta, colour in ((src_frame, src, (200, 90, 20)), (av_frame, av, (40, 40, 220))):
        pose = frame.get('pose')
        bf = vm.body_frame(pose, meta['width'], meta['height'])
        if bf is None:
            continue

        def px(lm):
            x, y = vm.normalised((lm[0] * meta['width'], lm[1] * meta['height']), bf)
            return int(size / 2 + x * size / 4), int(size * 0.35 + y * size / 4)
        for a, b in EDGES:
            cv2.line(canvas, px(pose[a]), px(pose[b]), colour, 2)
        cv2.circle(canvas, px(pose[0]), 5, colour, -1)
        for side in ('left', 'right'):
            hand = frame.get(f'{side}_hand')
            if hand:
                for lm in hand:
                    cv2.circle(canvas, px(lm), 2, colour, -1)
    cv2.putText(canvas, 'source', (8, 20), 0, 0.5, (200, 90, 20), 1)
    cv2.putText(canvas, 'avatar', (8, 40), 0, 0.5, (40, 40, 220), 1)
    return canvas


def side_by_side(motion, src_video, render_video, src, av, out, height=360):
    a, b = cv2.VideoCapture(str(src_video)), cv2.VideoCapture(str(render_video))
    writer = None
    for i in range(min(len(src['frames']), len(av['frames']))):
        ok1, f1 = a.read()
        ok2, f2 = b.read()
        if not (ok1 and ok2):
            break
        f1 = cv2.resize(f1, (int(f1.shape[1] * height / f1.shape[0]), height))
        f2 = cv2.resize(f2, (int(f2.shape[1] * height / f2.shape[0]), height))
        row = np.hstack([f1, f2, overlay(src['frames'][i], av['frames'][i], src, av, height)])
        cv2.putText(row, f'frame {i}', (8, height - 10), 0, 0.6, (0, 0, 255), 2)
        if writer is None:
            writer = cv2.VideoWriter(str(out), cv2.VideoWriter_fourcc(*'mp4v'), motion['fps'], (row.shape[1], row.shape[0]))
        writer.write(row)
    if writer:
        writer.release()


def write_markdown(sign, result, folder):
    v = result['visual_check']
    lines = [f'# Visual loop check: {sign}', '',
             'The avatar was rendered framed like the source video and tracked with the same tracker. Each frame is',
             'centred on the shoulder midpoint and measured in shoulder widths (y down: + means lower in the picture).',
             'Nothing here uses the retargeting\'s own scaling.', '',
             f'## Result: {v["result"].upper()}', '', '| Check | Value | Limit | Result |', '| --- | --- | --- | --- |']
    lines += [f'| {c["check"]} | {c["value"]} | ≤ {c["limit"]} | {"pass" if c["passed"] else "FAIL"} |' for c in v['checks']]
    for side in ('left', 'right'):
        r = result.get(side)
        if not r:
            continue
        lines += ['', f'## {side.capitalize()} hand (signer\'s {side})', '', '| Measure | Median | p90 |', '| --- | --- | --- |']
        for key in ('wrist_error', 'wrist_height_error_signed', 'wrist_sideways_error_signed',
                    'wrist_height_vs_nose_error_signed', 'elbow_height_error', 'handshape_error'):
            s = r[key]
            if s.get('n'):
                lines.append(f'| {key.replace("_", " ")} | {s["median"]} | {s["p90"]} |')
        pk = r['peak_height']
        lines.append(f'\nHighest wrist point (y, shoulder widths): source {pk["source"]}, avatar {pk["avatar"]}, '
                     f'difference {pk["error"]}.')
    lines += ['', 'Video: `side_by_side.mp4` (source | avatar render | both skeletons, blue = source, red = avatar).']
    (folder / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('signs', nargs='*')
    ap.add_argument('--blend', default=str(ROOT / 'avatar' / 'avatar_source.blend'))
    ap.add_argument('--out', default=str(OUT))
    ap.add_argument('--reuse', action='store_true', help='reuse existing renders and their landmarks')
    ap.add_argument('--render-width', type=int, default=960)
    args = ap.parse_args()
    out_root = Path(args.out)
    rows = []
    for sign in args.signs or baked_signs():
        motion = json.loads((ROOT / 'motion' / 'v2' / f'{sign}.json').read_text(encoding='utf-8'))
        folder = out_root / sign
        folder.mkdir(parents=True, exist_ok=True)
        if args.reuse and (folder / f'{sign}.json').exists():
            av = json.loads((folder / f'{sign}.json').read_text(encoding='utf-8'))
        else:
            video = render(sign, motion, args.blend, folder, args.render_width)
            conf = (motion.get('extractor') or {}).get('confidence', 0.5)
            av = track(sign, video, folder, conf)
        result = vm.compare(motion, av)
        (folder / 'report.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        write_markdown(sign, result, folder)
        side_by_side(motion, ROOT / motion['source_video'], folder / 'render.mp4', motion, av, folder / 'side_by_side.mp4')
        failed = [c['check'] for c in result['visual_check']['checks'] if not c['passed']]
        print(f'{sign:24} {result["visual_check"]["result"]:5} {"; ".join(failed)}')
        rows.append((sign, result))
    lines = ['# Visual loop check: summary', '', 'Limits: ' + ', '.join(f'{k} ≤ {v}' for k, v in vm.VISUAL_LIMITS.items()),
             '', '| Sign | Result | Failed checks |', '| --- | --- | --- |']
    for s, r in rows:
        failed = '; '.join(f"{c['check']} {c['value']}" for c in r['visual_check']['checks'] if not c['passed'])
        lines.append(f"| {s} | {r['visual_check']['result']} | {failed or '–'} |")
    if not args.signs:
        (out_root / 'SUMMARY.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
