"""Extract body, hand and face landmarks from an authorised ISL reference video.

The video is the linguistic reference and is never changed. This script only
records what MediaPipe sees in each frame. Frames where a part is not detected
are stored as null - they are NOT filled in. motion_qc.py decides whether the
clip is usable.

Usage:
    python tools/extract_landmarks.py references/magnet.mp4 --sign-id magnet
    -> writes motion/magnet.json and prints the quality report

Needs: pip install -r requirements.txt
"""

import argparse
import json
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

from motion_qc import qc_report

ROOT = Path(__file__).resolve().parent.parent


def points(landmark_list, with_visibility=False):
    if landmark_list is None:
        return None
    if with_visibility:
        return [[round(p.x, 5), round(p.y, 5), round(p.z, 5), round(p.visibility, 3)]
                for p in landmark_list.landmark]
    return [[round(p.x, 5), round(p.y, 5), round(p.z, 5)] for p in landmark_list.landmark]


def hand_crop_quality(gray, hand, width, height):
    """Sharpness (variance of the Laplacian) of the image around one hand. Low = motion blur."""
    if hand is None:
        return None
    xs = [p[0] * width for p in hand]
    ys = [p[1] * height for p in hand]
    pad = 0.25 * max(max(xs) - min(xs), max(ys) - min(ys), 20)
    x0, y0 = max(int(min(xs) - pad), 0), max(int(min(ys) - pad), 0)
    x1, y1 = min(int(max(xs) + pad), width), min(int(max(ys) + pad), height)
    crop = gray[y0:y1, x0:x1]
    if crop.size == 0:
        return None
    return round(float(cv2.Laplacian(crop, cv2.CV_64F).var()), 1)


def match_hands_model(result, frame, width, height):
    """Assign the hand model's detections to the signer's left/right hand.

    The hand model labels hands by appearance, which is unreliable on unmirrored video, so
    each detection is matched to the nearest hand Holistic found, or else to the nearest
    body-tracker wrist. Returns {'left': (image_pts, world_pts, score), 'right': ...}.
    """
    out = {}
    if not result.multi_hand_landmarks:
        return out
    pose = frame['pose']
    shoulder_px = (abs(pose[11][0] - pose[12][0]) * width) if pose else width * 0.2
    anchors = {}
    for side in ('left', 'right'):
        hol = frame[f'{side}_hand_holistic']
        if hol is not None:
            anchors[side] = (hol[0][0] * width, hol[0][1] * height)
        elif pose is not None:
            w = pose[15 if side == 'left' else 16]
            anchors[side] = (w[0] * width, w[1] * height)
    candidates = []
    for k, lms in enumerate(result.multi_hand_landmarks):
        wx, wy = lms.landmark[0].x * width, lms.landmark[0].y * height
        for side, (ax, ay) in anchors.items():
            d = ((wx - ax) ** 2 + (wy - ay) ** 2) ** 0.5
            if d < 0.6 * shoulder_px:
                candidates.append((d, k, side))
    used_k, used_side = set(), set()
    for d, k, side in sorted(candidates):
        if k in used_k or side in used_side:
            continue
        used_k.add(k)
        used_side.add(side)
        score = round(result.multi_handedness[k].classification[0].score, 3)
        out[side] = (points(result.multi_hand_landmarks[k]), points(result.multi_hand_world_landmarks[k]), score)
    return out


def face_blendshape_reader(model_path):
    """52 ARKit-named face scores per frame (eyebrows, blinks, mouth) plus the head-pose matrix."""
    if not model_path:
        return None
    from mediapipe.tasks import python as mp_tasks
    from mediapipe.tasks.python import vision

    options = vision.FaceLandmarkerOptions(
        base_options=mp_tasks.BaseOptions(model_asset_path=str(model_path)),
        running_mode=vision.RunningMode.VIDEO,
        output_face_blendshapes=True,
        output_facial_transformation_matrixes=True,
        num_faces=1,
    )
    landmarker = vision.FaceLandmarker.create_from_options(options)

    def read(rgb, timestamp_ms, face_landmarks):
        # The face model is built for close-up faces, so give it a crop around the face
        # that Holistic already found. Cropping changes only what the model sees, not the motion.
        if face_landmarks is None:
            return None, None
        h, w = rgb.shape[:2]
        xs = [p.x for p in face_landmarks.landmark]
        ys = [p.y for p in face_landmarks.landmark]
        cx, cy = (min(xs) + max(xs)) / 2 * w, (min(ys) + max(ys)) / 2 * h
        half = max((max(xs) - min(xs)) * w, (max(ys) - min(ys)) * h)  # face size x 2 crop
        x0, y0 = max(int(cx - half), 0), max(int(cy - half), 0)
        x1, y1 = min(int(cx + half), w), min(int(cy + half), h)
        crop = np.ascontiguousarray(rgb[y0:y1, x0:x1])
        if crop.size == 0:
            return None, None
        result = landmarker.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=crop), timestamp_ms)
        if not result.face_blendshapes:
            return None, None
        scores = {c.category_name: round(c.score, 4) for c in result.face_blendshapes[0]}
        matrix = None
        if result.facial_transformation_matrixes:
            matrix = [[round(float(v), 5) for v in row] for row in result.facial_transformation_matrixes[0]]
        return scores, matrix

    return read


def extract(video_path, sign_id, face_model=None, confidence=0.5):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise SystemExit(f'Could not open video: {video_path}')
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    read_blendshapes = face_blendshape_reader(face_model)

    frames = []
    holistic = mp.solutions.holistic.Holistic(
        static_image_mode=False,
        model_complexity=2,           # most accurate model; slower, fine for offline work
        refine_face_landmarks=True,   # adds iris points, useful for eye gaze
        smooth_landmarks=False,       # keep raw data; any smoothing happens later, visibly
        min_detection_confidence=confidence,   # lower = finds blurred hands more often; never invents them
        min_tracking_confidence=confidence,
    )
    # A second, hand-only detector. Its "world" landmarks are metric 3D hand shapes: curled
    # fingers keep their depth, which the image-based landmarks flatten.
    hands = mp.solutions.hands.Hands(static_image_mode=False, max_num_hands=2, model_complexity=1,
                                     min_detection_confidence=confidence, min_tracking_confidence=confidence)
    index = 0
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        result = holistic.process(rgb)
        frame = {
            't': round(index / fps, 5),
            # pose: image coordinates (0-1) + visibility; pose_world: metres, hip-centred
            'pose': points(result.pose_landmarks, with_visibility=True),
            'pose_world': points(result.pose_world_landmarks, with_visibility=True),
            # Raw Holistic hands (the signer's own left/right).
            'left_hand_holistic': points(result.left_hand_landmarks),
            'right_hand_holistic': points(result.right_hand_landmarks),
            'face': points(result.face_landmarks),
            'blendshapes': None,
            'head_matrix': None,
        }
        if read_blendshapes:
            frame['blendshapes'], frame['head_matrix'] = read_blendshapes(
                rgb, round(index * 1000 / fps), result.face_landmarks)

        found = match_hands_model(hands.process(rgb), frame, width, height)
        for side in ('left', 'right'):
            image_pts, world_pts, score = found.get(side, (None, None, None))
            frame[f'{side}_hand_model'] = image_pts            # raw hand-model image landmarks
            frame[f'{side}_hand_world'] = world_pts            # metric 3D hand shape (metres)
            frame[f'{side}_hand_score'] = score
            # Merged image landmarks: Holistic first, the hand model where Holistic missed.
            # Both are real detections in this frame; nothing is interpolated.
            holistic_pts = frame[f'{side}_hand_holistic']
            frame[f'{side}_hand'] = holistic_pts if holistic_pts is not None else image_pts
            frame[f'{side}_hand_source'] = ('holistic' if holistic_pts is not None
                                            else 'hand_model' if image_pts is not None else None)
        frame['quality'] = {
            'brightness': round(float(gray.mean()), 1),
            'left_sharpness': hand_crop_quality(gray, frame['left_hand'], width, height),
            'right_sharpness': hand_crop_quality(gray, frame['right_hand'], width, height),
        }
        frames.append(frame)
        index += 1
    cap.release()
    holistic.close()
    hands.close()

    return {
        'sign_id': sign_id,
        'source_video': str(video_path),
        'fps': fps,
        'width': width,
        'height': height,
        'frame_count': len(frames),
        'extractor': {'name': 'mediapipe-holistic + mediapipe-hands', 'version': mp.__version__,
                      'smoothing': 'none', 'gap_filling': 'none', 'confidence': confidence,
                      'hand_merge': 'holistic, else hand model (matched to the nearest wrist)'},
        'frames': frames,
    }


def main():
    parser = argparse.ArgumentParser(description='Extract ISL motion landmarks from a reference video.')
    parser.add_argument('video', help='authorised reference video, e.g. references/magnet.mp4')
    parser.add_argument('--sign-id', required=True, help='sign_id from registry/signs.csv')
    parser.add_argument('--out-dir', default=str(ROOT / 'motion'))
    parser.add_argument('--face-model', help='face_landmarker.task, to record facial expression scores')
    parser.add_argument('--confidence', type=float, default=0.5,
                        help='MediaPipe detection/tracking confidence (default 0.5); try 0.3 for blurred fast movement')
    args = parser.parse_args()

    motion = extract(Path(args.video), args.sign_id, args.face_model, args.confidence)
    report = qc_report(motion)
    motion['qc'] = report

    out = Path(args.out_dir) / f'{args.sign_id}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(motion, separators=(',', ':')), encoding='utf-8')

    print(f'Wrote {out} ({motion["frame_count"]} frames at {motion["fps"]:.1f} fps)')
    print(json.dumps(report, indent=2))
    print(f'\nmotion_qc = {report["result"]}  (copy this into registry/signs.csv)')


if __name__ == '__main__':
    main()
