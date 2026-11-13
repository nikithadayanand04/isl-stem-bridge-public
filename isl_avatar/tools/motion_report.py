"""Per-sign motion fidelity report: source ISL signer vs reconstructed avatar.

    python tools/motion_report.py --motion motion/food.json --avatar reports/food/avatar_samples.json \
        --video references/dict_Food.mp4 --renders previews/food --out reports/food

Writes report.json, report.md and plots/images into --out. Frames are compared at the
ORIGINAL timing (source frame i = avatar frame i + 1); a DTW alignment is reported
separately as a diagnostic only.

There is deliberately no overall "accuracy %": each measure is reported on its own, and
geometric similarity is never presented as linguistic correctness.
"""

import argparse
import json
import os
import math
from pathlib import Path

import motion_metrics as mm
import retarget_math as rm

# Hand-shape error bands used only to label results in the report (degrees, median per joint).
SHAPE_BANDS = [(10, 'close'), (20, 'noticeable'), (float('inf'), 'large')]


def source_points(frame):
    """Body points of the source frame in armature axes (from MediaPipe world pose)."""
    w = frame.get('pose_world')
    if w is None:
        return None
    return {k: rm.mp_to_blender(w[i][:3]) for k, i in rm.POSE.items()}


def source_hand(frame, side, width, height, segments=None):
    pts, kind = rm.hand_points(frame, side, width, height, segments=segments)
    return pts, kind


def normalised_offset(point, l_sh, r_sh, dims):
    """Offset from the shoulder middle in the body frame, scaled per direction like the
    retargeting does: sideways by shoulder width, downwards by torso length, upwards and
    forwards by arm length. Returns [sideways, up, forward] in fractions of those measures."""
    chest = mm.chest_frame(l_sh, r_sh)
    rel = rm.sub(point, rm.mid(l_sh, r_sh))
    # Body frame columns: X = towards the person's left, Y = up, Z = forward (towards the viewer).
    side, up, forward = (sum(chest[r][i] * rel[r] for r in range(3)) for i in range(3))
    return [side / dims['shoulder_width'], up / (dims['arm'] if up >= 0 else dims['torso']), forward / dims['arm']]


def avatar_dims(sample):
    sw = rm.length(rm.sub(sample['l_shoulder'], sample['r_shoulder']))
    arm = (rm.length(rm.sub(sample['l_elbow'], sample['l_shoulder'])) +
           rm.length(rm.sub(sample['l_wrist'], sample['l_elbow'])))
    torso = None
    if 'l_hip' in sample:
        torso = rm.mid(sample['l_shoulder'], sample['r_shoulder'])[2] - rm.mid(sample['l_hip'], sample['r_hip'])[2]
    return {'shoulder_width': sw, 'arm': arm, 'torso': torso or arm}


def video_dims(frames):
    arms = rm.video_arm_lengths(frames)
    sizes = rm.video_body_sizes(frames)
    return {'shoulder_width': sizes['shoulder_width'], 'torso': sizes['torso'],
            'arm': (arms['left'] + arms['right']) / 2}


def processed_input(motion, config):
    """The source as the bake receives it: detector switches crossfaded and every stream
    filtered as configured (retarget_config.json). The raw file is not changed."""
    import copy
    import smoothing
    frames = copy.deepcopy(motion['frames'])
    for side in ('left', 'right'):
        smoothing.blend_detector_switches(frames, side, config.get('detector_blend_frames', 4))
    for key, params in config.get('smoothing', {}).items():
        if key.startswith('_'):
            continue
        if 'cutoff_hz' in params:
            smoothing.zero_phase_track(frames, key, motion['fps'], params['cutoff_hz'])
        else:
            rm.smooth_track(frames, key, motion['fps'], **params)
    return frames


def compare(motion, avatar):
    # What this measures: how faithfully the bake reproduces its own input (the processed
    # source: smoothed, arms and fingers anchored to the picture). Errors here are retargeting
    # errors (IK, rig, limits). Whether that input matches the video is measured independently
    # by tools/visual_loop_check.py, against the raw video.
    config = json.loads((Path(__file__).resolve().parent / 'retarget_config.json').read_text(encoding='utf-8'))
    fit = os.environ.get('ISL_FINGER_FIT')
    rm.FINGER_FIT = bool(int(fit)) if fit is not None else bool(config.get('hands', {}).get('finger_fit', False))
    raw_frames = motion['frames']
    src_frames = processed_input(motion, config)
    av_frames = avatar['frames']
    n = min(len(src_frames), len(av_frames))
    W, H = motion['width'], motion['height']
    vdims = video_dims(src_frames)
    adims = avatar_dims(av_frames[0])

    # The baker subtracts each clip's neutral face (retarget_config.json: face.calibration); the
    # avatar is compared with the same calibrated values, so this measures the bake itself.
    import motion_qc
    config = json.loads((Path(__file__).resolve().parent / 'retarget_config.json').read_text(encoding='utf-8'))
    neutral = {}
    if config.get('face', {}).get('calibration', 'neutral') == 'neutral':
        resting = [all(f.get(f'{sd}_hand') is None or motion_qc.hand_resting(f, f'{sd}_hand') for sd in ('left', 'right'))
                   for f in src_frames]
        neutral, _ = rm.face_neutral(src_frames, resting)

    # Source frames the pipeline deliberately does not copy are left out of the hand-shape
    # comparison (and counted): comparing the avatar with impossible data says nothing.
    #   depth_flip       the tracker mirrored the hand front-to-back (see motion_qc)
    #   image_only       this hand is baked from metric world points; a frame with only image points
    #                    is interpolated, so it is not compared against the flatter image shape
    #   impossible_bend  the tracked hand bends a joint beyond the anatomical range (joint limits)
    #   rest_pose        the hand rests at the side, so the avatar's arm and hand go to the fixed rest
    #                    pose (tools/rest_pose.py), including the blend in and out of it
    world_only = rm.world_only_sides(src_frames)
    flips = {sd: rm.depth_flip_frames(src_frames, sd) for sd in ('left', 'right')}
    rest_cfg = config.get('rest_pose', {})
    rest_w = {sd: (rm.rest_weights([motion_qc.hand_resting(f, f'{sd}_hand') for f in src_frames], rest_cfg.get('ease_frames', 6))
                   if rest_cfg.get('enabled', False) else [0.0] * len(src_frames)) for sd in ('left', 'right')}
    # Arms: the retargeting places them from the picture (image_anchored_arms), with the 3D pose
    # only for depth, because the 3D pose puts the wrists too low (measured). This check compares
    # the avatar with that same corrected input; tools/visual_loop_check.py is the independent check.
    anchor = config.get('arms', {}).get('image_anchor', False)
    segments = rm.video_segment_lengths(src_frames)
    sizes = rm.video_body_sizes(src_frames)
    # Fingers: the same picture-anchored hand the retargeting uses (config hands.image_anchor).
    hand_segs = ({sd: rm.hand_segment_lengths(src_frames, sd) for sd in ('left', 'right')}
                 if config.get('hands', {}).get('image_anchor', False) else {})

    per_frame = []
    for i in range(n):
        s, a = src_frames[i], av_frames[i]
        row = {'frame': i}
        sp = source_points(s)
        if sp is not None and anchor:
            sp = rm.image_anchored_arms(s, W, H, sp, sizes.get('shoulder_width'), segments)
        for side, k in (('left', 'l'), ('right', 'r')):
            pts, kind = source_hand(s, side, W, H, hand_segs.get(side))
            apts = a[f'{side}_hand_points']
            reason = None
            if pts is not None:
                if rest_w[side][i] > 0:
                    reason = 'rest_pose'
                elif i in flips[side]:
                    reason = 'depth_flip'
                elif side in world_only and kind != 'world':
                    reason = 'image_only'
                elif mm.over_limit(mm.flexion_angles(pts)):
                    reason = 'impossible_bend'
            if reason:
                row[f'{side}_excluded'] = reason
            if pts is not None and not reason:
                fs, fa = mm.flexion_angles(pts), mm.flexion_angles(apts)
                row[f'{side}_flex_src'] = fs
                row[f'{side}_flex_av'] = fa
                row[f'{side}_flex_err'] = {j: (None if fs[j] is None or fa[j] is None else abs(fs[j] - fa[j])) for j in fs}
                ss, sa = mm.spread_angles(pts), mm.spread_angles(apts)
                row[f'{side}_spread_err'] = {j: (None if ss[j] is None or sa[j] is None else abs(ss[j] - sa[j])) for j in ss}
                row[f'{side}_hand_kind'] = kind
                if sp is not None:
                    rs = mm.palm_relative_to_chest(pts, mm.chest_frame(sp['l_shoulder'], sp['r_shoulder']))
                    ra = mm.palm_relative_to_chest(apts, mm.chest_frame(a['l_shoulder'], a['r_shoulder']))
                    row[f'{side}_palm_err'] = mm.orientation_error(rs, ra)
            if sp is not None and rest_w[side][i] == 0:          # resting arms go to the rest pose
                for joint in ('wrist', 'elbow'):
                    vs = normalised_offset(sp[f'{k}_{joint}'], sp['l_shoulder'], sp['r_shoulder'], vdims)
                    va = normalised_offset(a[f'{k}_{joint}'], a['l_shoulder'], a['r_shoulder'], adims)
                    row[f'{side}_{joint}_src'] = vs
                    row[f'{side}_{joint}_av'] = va
                    row[f'{side}_{joint}_err'] = rm.length(rm.sub(vs, va))
        # Contact: source from the image (as the bake decides it), avatar in 3D.
        row['contact_src'] = rm.fingertip_contact(raw_frames[i], W, H)
        row['contact_av'] = mm.contact(a['left_hand_points'], a['right_hand_points'], adims['shoulder_width']) < mm.CONTACT_THRESHOLD
        if s.get('blendshapes') and a.get('face'):
            diffs = [abs((rm.calibrate_score(v, neutral.get(k, 0.0)) if neutral else v) - a['face'][k])
                     for k, v in s['blendshapes'].items() if k in a['face']]
            row['face_err'] = sum(diffs) / len(diffs) if diffs else None
        per_frame.append(row)
    return per_frame, vdims, adims


def summarise(per_frame, fps):
    out = {}
    for side in ('left', 'right'):
        joints = {}
        for name, *_ in mm.FLEXION_JOINTS:
            joints[name] = mm.summarise([r.get(f'{side}_flex_err', {}).get(name) for r in per_frame])
        if not any(v.get('n') for v in joints.values()):
            continue
        all_err = [e for r in per_frame for e in (r.get(f'{side}_flex_err') or {}).values()]
        excluded = {}
        for r in per_frame:
            if r.get(f'{side}_excluded'):
                excluded[r[f'{side}_excluded']] = excluded.get(r[f'{side}_excluded'], 0) + 1
        out[side] = {
            'excluded_frames': excluded,
            'frames_with_hand': sum(1 for r in per_frame if f'{side}_flex_err' in r),
            'hand_data': sorted({r[f'{side}_hand_kind'] for r in per_frame if f'{side}_hand_kind' in r}),
            'finger_flexion_error_deg': mm.summarise(all_err),
            'finger_flexion_error_by_joint_deg': joints,
            'finger_spread_error_deg': mm.summarise([e for r in per_frame for e in (r.get(f'{side}_spread_err') or {}).values()]),
            'palm_orientation_error_deg': mm.summarise([r.get(f'{side}_palm_err') for r in per_frame]),
            'wrist_position_error': mm.summarise([r.get(f'{side}_wrist_err') for r in per_frame]),
            'elbow_position_error': mm.summarise([r.get(f'{side}_elbow_err') for r in per_frame]),
        }
        src = [r.get(f'{side}_wrist_src') for r in per_frame]
        av = [r.get(f'{side}_wrist_av') for r in per_frame]
        out[side]['wrist_speed_correlation'] = (
            None if mm.correlation(mm.speeds(src, fps), mm.speeds(av, fps)) is None
            else round(mm.correlation(mm.speeds(src, fps), mm.speeds(av, fps)), 3))
        pairs = [(x, y) for x, y in zip(src, av) if x is not None and y is not None]
        if len(pairs) > 3:
            aligned, path = mm.dtw([p[0] for p in pairs], [p[1] for p in pairs], lambda u, v: rm.length(rm.sub(u, v)))
            shift = sorted(j - i for i, j in path)
            out[side]['dtw_diagnostic'] = {
                'aligned_mean_wrist_error': round(aligned, 3),
                'original_time_mean_wrist_error': round(sum(rm.length(rm.sub(x, y)) for x, y in pairs) / len(pairs), 3),
                'median_frame_shift': shift[len(shift) // 2]}
    src_c = [r['contact_src'] for r in per_frame]
    av_c = [r['contact_av'] for r in per_frame]
    both = sum(1 for s, a in zip(src_c, av_c) if s and a)
    out['contact'] = {'source_frames': sum(src_c), 'avatar_frames': sum(av_c), 'matching_frames': both,
                      'avatar_contact_not_in_source': sum(1 for s, a in zip(src_c, av_c) if a and not s),
                      'source_contact_missing_on_avatar': sum(1 for s, a in zip(src_c, av_c) if s and not a)}
    out['face_value_error'] = mm.summarise([r.get('face_err') for r in per_frame])
    return out


def band(median):
    return next(label for limit, label in SHAPE_BANDS if median <= limit)


def plots(per_frame, summary, out_dir):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    made = []
    for side in ('left', 'right'):
        if side not in summary:
            continue
        frames = [r['frame'] for r in per_frame]
        fig, axes = plt.subplots(2, 2, figsize=(10, 6), sharex=True)
        for ax, joint in zip(axes.flat, ('thumb_mcp', 'index_pip', 'middle_pip', 'ring_pip')):
            ax.plot(frames, [(r.get(f'{side}_flex_src') or {}).get(joint) for r in per_frame], label='source signer', color='#1f77b4')
            ax.plot(frames, [(r.get(f'{side}_flex_av') or {}).get(joint) for r in per_frame], label='avatar', color='#d62728', linestyle='--')
            ax.set_title(f'{side} {joint.replace("_", " ")} flexion (deg)', fontsize=10)
        axes[0][0].legend(fontsize=8)
        fig.tight_layout()
        path = out_dir / f'{side}_finger_angles.png'
        fig.savefig(path, dpi=110)
        plt.close(fig)
        made.append(path.name)

        joints = [name for name, *_ in mm.FLEXION_JOINTS]
        grid = [[(r.get(f'{side}_flex_err') or {}).get(j) or 0.0 for r in per_frame] for j in joints]
        fig, ax = plt.subplots(figsize=(10, 4))
        im = ax.imshow(grid, aspect='auto', cmap='magma', vmin=0, vmax=45)
        ax.set_yticks(range(len(joints)))
        ax.set_yticklabels(joints, fontsize=7)
        ax.set_xlabel('frame')
        ax.set_title(f'{side} hand: finger flexion error per joint (deg, 0-45)')
        fig.colorbar(im, ax=ax)
        fig.tight_layout()
        path = out_dir / f'{side}_error_heatmap.png'
        fig.savefig(path, dpi=110)
        plt.close(fig)
        made.append(path.name)

        fig, ax = plt.subplots(figsize=(5, 5))
        src = [r.get(f'{side}_wrist_src') for r in per_frame]
        av = [r.get(f'{side}_wrist_av') for r in per_frame]
        ax.plot([p[0] for p in src if p], [p[1] for p in src if p], label='source signer', color='#1f77b4')
        ax.plot([p[0] for p in av if p], [p[1] for p in av if p], label='avatar', color='#d62728', linestyle='--')
        ax.set_xlabel('sideways (shoulder widths)')
        ax.set_ylabel('up / down (arm or torso lengths)')
        ax.set_title(f'{side} wrist path, front view')
        ax.legend(fontsize=8)
        ax.set_aspect('equal', adjustable='datalim')
        fig.tight_layout()
        path = out_dir / f'{side}_wrist_trajectory.png'
        fig.savefig(path, dpi=110)
        plt.close(fig)
        made.append(path.name)

    fig, ax = plt.subplots(figsize=(10, 1.8))
    ax.step(range(len(per_frame)), [1.1 if r['contact_src'] else None for r in per_frame], where='mid', label='source', lw=6)
    ax.step(range(len(per_frame)), [0.9 if r['contact_av'] else None for r in per_frame], where='mid', label='avatar', lw=6)
    ax.set_ylim(0.6, 1.4)
    ax.set_yticks([])
    ax.set_xlabel('frame')
    ax.set_title('fingertip contact between the hands')
    ax.legend(fontsize=8, loc='upper right')
    fig.tight_layout()
    path = out_dir / 'contact_timeline.png'
    fig.savefig(path, dpi=110)
    plt.close(fig)
    made.append(path.name)
    return made


def side_by_side(video, motion, renders, frames, out_dir):
    """Source frames with the extracted landmarks drawn, above avatar renders."""
    import cv2
    import numpy as np
    wanted = set(frames)
    cap = cv2.VideoCapture(str(video))
    shots, i = {}, 0
    while True:
        ok, img = cap.read()
        if not ok:
            break
        if i + 1 in wanted:
            f = motion['frames'][i]
            for side, colour in (('left', (255, 140, 0)), ('right', (0, 200, 255))):
                pts = f.get(f'{side}_hand')
                if pts:
                    xy = [(int(p[0] * motion['width']), int(p[1] * motion['height'])) for p in pts]
                    for a, b in [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9), (9, 10),
                                 (10, 11), (11, 12), (9, 13), (13, 14), (14, 15), (15, 16), (13, 17), (0, 17),
                                 (17, 18), (18, 19), (19, 20)]:
                        cv2.line(img, xy[a], xy[b], colour, 3)
            h, w = img.shape[:2]
            side_len = min(h, w)
            crop = img[(h - side_len) // 2:(h + side_len) // 2, (w - side_len) // 2:(w + side_len) // 2]
            shots[i + 1] = cv2.resize(crop, (260, 260))
        i += 1
    top = np.hstack([shots[f] for f in frames if f in shots])
    bottom = np.hstack([cv2.resize(cv2.imread(f'{renders}_{f:04d}.png'), (260, 260)) for f in frames if f in shots])
    path = out_dir / 'side_by_side.jpg'
    cv2.imwrite(str(path), np.vstack([top, bottom]))
    return path.name


def write_markdown(sign, summary, images, out_dir, motion, registry_row):
    lines = [f'# Motion fidelity report: {sign}', '',
             f'Source video: `{motion["source_video"]}` · {motion["frame_count"]} frames at {motion["fps"]:.2f} fps',
             '',
             '> **Geometric similarity only.** These numbers compare the avatar with the landmarks extracted from',
             '> the source video. They cannot show whether the signing is correct ISL. Only a qualified ISL',
             '> interpreter can approve a sign.', '']
    if registry_row:
        lines += ['## Status', '', '| Check | Result |', '| --- | --- |']
        for key in ('license_status', 'motion_qc', 'interpreter_review'):
            lines.append(f'| {key} | {registry_row.get(key, "")} |')
        lines.append('')
    g = summary.get('geometric_check')
    if g:
        lines += [f'## Geometric check: {g["result"].upper()}', '',
                  'Each limit is checked on its own; there is no overall percentage.', '',
                  '| Check | Value | Limit | Result |', '| --- | --- | --- | --- |']
        for c in g['checks']:
            lines.append(f'| {c["check"]} | {c["value"]} | ≤ {c["limit"]} | {"pass" if c["passed"] else "FAIL"} |')
        lines.append('')
    lines += ['## Hands', '']
    for side in ('left', 'right'):
        s = summary.get(side)
        if not s:
            continue
        f = s['finger_flexion_error_deg']
        ex = s.get('excluded_frames') or {}
        ex_txt = (' Left out of the hand-shape comparison: ' + ', '.join(f'{n} {k.replace("_", " ")}' for k, n in ex.items())
                  + ' (frames the avatar deliberately does not copy; see MOTION_VALIDATION.md).') if ex else ''
        lines += [f'### {side.capitalize()} hand ({s["frames_with_hand"]} frames compared, data: {", ".join(s["hand_data"])})', '',
                  *([ex_txt.strip(), ''] if ex_txt else []),
                  '| Measure | Median | 90th percentile | Max |', '| --- | --- | --- | --- |']
        for label, key, unit in (('Finger joint flexion error', 'finger_flexion_error_deg', '°'),
                                 ('Finger spread error', 'finger_spread_error_deg', '°'),
                                 ('Palm orientation error (vs chest)', 'palm_orientation_error_deg', '°'),
                                 ('Wrist position error (body-relative)', 'wrist_position_error', ''),
                                 ('Elbow position error (body-relative)', 'elbow_position_error', '')):
            v = s[key]
            if v.get('n'):
                lines.append(f'| {label} | {v["median"]}{unit} | {v["p90"]}{unit} | {v["max"]}{unit} |')
        lines += ['', f'Hand shape overall: **{band(f["median"])}** (median joint error {f["median"]}°).', '',
                  '| Joint | Median error | 90th percentile |', '| --- | --- | --- |']
        for joint, v in s['finger_flexion_error_by_joint_deg'].items():
            if v.get('n'):
                lines.append(f'| {joint} | {v["median"]}° | {v["p90"]}° |')
        lines += ['', f'Wrist speed correlation (original timing): {s["wrist_speed_correlation"]}']
        if 'dtw_diagnostic' in s:
            d = s['dtw_diagnostic']
            lines.append(f'DTW diagnostic: original-time mean wrist error {d["original_time_mean_wrist_error"]}, '
                         f'time-aligned {d["aligned_mean_wrist_error"]}, median shift {d["median_frame_shift"]} frames '
                         '(the original timing is kept; DTW is for diagnosis only).')
        lines.append('')
    c = summary['contact']
    lines += ['## Contact between the hands', '',
              f'Source frames with fingertip contact: {c["source_frames"]}; avatar: {c["avatar_frames"]}; '
              f'matching: {c["matching_frames"]}; avatar contact not in the source: {c["avatar_contact_not_in_source"]}; '
              f'source contact missing on the avatar: {c["source_contact_missing_on_avatar"]}.', '']
    fe = summary['face_value_error']
    if fe.get('n'):
        lines += ['## Face', '', f'Shape-key values vs source expression scores: median difference {fe["median"]} '
                  '(this checks the baking path; whether each expression LOOKS right needs the face renders from '
                  '`tools/facial_validator.py` and the interpreter).', '']
    lines += ['## Images', ''] + [f'![{img}]({img})' for img in images] + ['']
    (out_dir / 'report.md').write_text('\n'.join(lines), encoding='utf-8')


# Limits for the geometric comparison (avatar against the extracted source landmarks).
# Chosen from the measured error of the extraction itself (MediaPipe joint angles move by
# a few degrees frame to frame on a still hand) plus room for rig differences. Passing them
# means the avatar reproduces the tracked motion; it does not mean the sign is correct ISL.
GEOMETRIC_LIMITS = {
    'finger_flexion_median_deg': 5.0,
    'finger_flexion_p90_deg': 15.0,
    'palm_orientation_median_deg': 10.0,
    'palm_orientation_p90_deg': 25.0,
    'wrist_position_median': 0.10,     # fraction of the body measure (see body_offset)
    'contact_missing_fraction': 0.25,  # share of source contact frames without avatar contact
}


def geometric_verdict(summary, limits=GEOMETRIC_LIMITS):
    """Pass/fail per check, never one blended percentage."""
    checks = []

    def check(name, value, limit):
        if value is None:
            return
        checks.append({'check': name, 'value': value, 'limit': limit, 'passed': value <= limit})

    for side in ('left', 'right'):
        s = summary.get(side)
        if not s:
            continue
        check(f'{side} finger flexion median (deg)', s['finger_flexion_error_deg'].get('median'),
              limits['finger_flexion_median_deg'])
        check(f'{side} finger flexion p90 (deg)', s['finger_flexion_error_deg'].get('p90'),
              limits['finger_flexion_p90_deg'])
        check(f'{side} palm orientation median (deg)', s['palm_orientation_error_deg'].get('median'),
              limits['palm_orientation_median_deg'])
        check(f'{side} palm orientation p90 (deg)', s['palm_orientation_error_deg'].get('p90'),
              limits['palm_orientation_p90_deg'])
        check(f'{side} wrist position median', s['wrist_position_error'].get('median'),
              limits['wrist_position_median'])
    c = summary.get('contact', {})
    if c.get('source_frames'):
        check('contact frames missing on avatar (fraction)',
              round(c['source_contact_missing_on_avatar'] / c['source_frames'], 3), limits['contact_missing_fraction'])
    if not checks:
        return {'result': 'fail', 'checks': [], 'note': 'no hand frames to compare'}
    return {'result': 'pass' if all(x['passed'] for x in checks) else 'fail', 'checks': checks}


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--motion', required=True)
    p.add_argument('--avatar', required=True)
    p.add_argument('--video')
    p.add_argument('--renders', help='prefix of render_preview.py images for the side-by-side')
    p.add_argument('--frames', type=int, nargs='*', default=[])
    p.add_argument('--out', required=True)
    args = p.parse_args()

    motion = json.loads(Path(args.motion).read_text(encoding='utf-8'))
    avatar = json.loads(Path(args.avatar).read_text(encoding='utf-8'))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    per_frame, vdims, adims = compare(motion, avatar)
    summary = summarise(per_frame, motion['fps'])
    summary['body_dims'] = {'source': vdims, 'avatar': adims}
    summary['geometric_check'] = geometric_verdict(summary)
    images = plots(per_frame, summary, out_dir)
    if args.video and args.renders and args.frames:
        images.insert(0, side_by_side(args.video, motion, args.renders, args.frames, out_dir))

    registry_row = None
    reg = Path(__file__).resolve().parent.parent / 'registry' / 'signs.csv'
    if reg.exists():
        import csv
        with reg.open(encoding='utf-8') as fh:
            row = next((r for r in csv.DictReader(fh) if r['sign_id'] == motion['sign_id']), None)
        if row:
            registry_row = {'license_status': row.get('license_status', ''), 'motion_qc': row.get('motion_qc', ''),
                            'interpreter_review': row.get('interpreter_review', '') or 'not reviewed'}
    (out_dir / 'report.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    write_markdown(motion['sign_id'], summary, images, out_dir, motion, registry_row)
    for side in ('left', 'right'):
        if side in summary:
            s = summary[side]
            print(f'{side}: flexion median {s["finger_flexion_error_deg"]["median"]} deg, '
                  f'palm {s["palm_orientation_error_deg"].get("median")} deg, wrist {s["wrist_position_error"].get("median")}')
    print(f'contact: {summary["contact"]}')
    print(f'geometric_check: {summary["geometric_check"]["result"]}')
    print(f'Report: {out_dir / "report.md"}')


if __name__ == '__main__':
    main()
