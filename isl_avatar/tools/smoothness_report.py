"""Smoothness of every baked sign against its source: angular velocity, jerk and velocity spikes
per moving segment (upper arm, forearm and the 15 finger bones of each hand).

    python3 tools/smoothness_report.py [--avatar-dir reports/v2] [--out reports/smoothness]

The source is the raw tracking (world points, as recorded). The avatar is reports/v2/<sign>/
avatar_samples.json, sampled at the source frame times. A spike frame is one where a segment
turns faster than 3x its own median speed in the clip (and faster than 60 deg/s). The target
is a spike count close to the source's: real fast movements spike in both; jitter, pops and
detector switches spike only in one.
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import retarget_math as rm  # noqa: E402
import smoothing as sm  # noqa: E402

FINGER_SEGMENTS = [(a, b) for a, b in rm.FINGER_BONES.values()]


def segments_source(frame, side):
    out = {}
    w = frame.get('pose_world')
    s = 'l' if side == 'left' else 'r'
    if w:
        p = {k: rm.mp_to_blender(w[i][:3]) for k, i in rm.POSE.items()}
        out['upper_arm'] = rm.sub(p[f'{s}_elbow'], p[f'{s}_shoulder'])
        out['forearm'] = rm.sub(p[f'{s}_wrist'], p[f'{s}_elbow'])
    h = frame.get(f'{side}_hand_world')
    if h:
        pts = [rm.mp_to_blender(q) for q in h]
        for n, (a, b) in enumerate(FINGER_SEGMENTS):
            out[f'finger{n}'] = rm.sub(pts[b], pts[a])
    return out


def segments_avatar(sample, side):
    s = 'l' if side == 'left' else 'r'
    out = {'upper_arm': rm.sub(sample[f'{s}_elbow'], sample[f'{s}_shoulder']),
           'forearm': rm.sub(sample[f'{s}_wrist'], sample[f'{s}_elbow'])}
    pts = sample[f'{side}_hand_points']
    for n, (a, b) in enumerate(FINGER_SEGMENTS):
        out[f'finger{n}'] = rm.sub(pts[b], pts[a])
    return out


def measure(series_by_segment, fps):
    per = {k: sm.smoothness(v, fps) for k, v in series_by_segment.items()}
    per = {k: v for k, v in per.items() if v.get('n', 0) >= 4}
    if not per:
        return None
    jerks = [v['mean_jerk_deg_s3'] for v in per.values() if v.get('mean_jerk_deg_s3') is not None]
    return {'spike_frames': sum(v['spike_frames'] for v in per.values()),
            'arm_spike_frames': sum(per[k]['spike_frames'] for k in ('upper_arm', 'forearm') if k in per),
            'finger_spike_frames': sum(v['spike_frames'] for k, v in per.items() if k.startswith('finger')),
            'median_speed_deg_s': round(statistics.median(v['median_deg_s'] for v in per.values()), 1),
            'median_jerk_deg_s3': round(statistics.median(jerks), 0) if jerks else None}


def sign_report(sign, avatar_dir):
    motion = json.loads((ROOT / 'motion' / 'v2' / f'{sign}.json').read_text(encoding='utf-8'))
    samples = json.loads((avatar_dir / sign / 'avatar_samples.json').read_text(encoding='utf-8'))['frames']
    n = min(len(motion['frames']), len(samples))
    out = {}
    for side in ('left', 'right'):
        src, av = {}, {}
        tracked = [bool(motion['frames'][i].get(f'{side}_hand_world')) for i in range(n)]
        if sum(tracked) < 10:
            continue
        for i in range(n):
            s = segments_source(motion['frames'][i], side)
            a = segments_avatar(samples[i], side)
            for k in a:
                src.setdefault(k, []).append(s.get(k))
                # Compare like with like: the avatar only where the source tracked this hand.
                av.setdefault(k, []).append(a[k] if s.get(k) is not None else None)
        out[side] = {'source': measure(src, motion['fps']), 'avatar': measure(av, motion['fps'])}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--avatar-dir', default=str(ROOT / 'reports' / 'v2'))
    ap.add_argument('--out', default=str(ROOT / 'reports' / 'smoothness'))
    args = ap.parse_args()
    avatar_dir, out = Path(args.avatar_dir), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    results = {}
    for d in sorted(avatar_dir.iterdir()):
        if (d / 'avatar_samples.json').exists() and (ROOT / 'motion' / 'v2' / f'{d.name}.json').exists():
            results[d.name] = sign_report(d.name, avatar_dir)
    (out / 'smoothness.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    lines = ['# Smoothness', '', 'Spike frames: a segment turning faster than 3x its own median speed in the clip '
             '(and > 60 deg/s), summed over upper arm, forearm and 15 finger bones. Source = raw tracking.', '',
             '| Sign | Hand | Spikes source | Spikes avatar | Arm spikes src / avatar | Finger spikes src / avatar | '
             'Median jerk src / avatar (deg/s³) |', '| --- | --- | --- | --- | --- | --- | --- |']
    for sign, sides in results.items():
        for side, r in sides.items():
            s, a = r['source'], r['avatar']
            if not s or not a:
                continue
            lines.append(f'| {sign} | {side} | {s["spike_frames"]} | {a["spike_frames"]} | {s["arm_spike_frames"]} / '
                         f'{a["arm_spike_frames"]} | {s["finger_spike_frames"]} / {a["finger_spike_frames"]} | '
                         f'{s["median_jerk_deg_s3"]:.0f} / {a["median_jerk_deg_s3"]:.0f} |')
    (out / 'SUMMARY.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
