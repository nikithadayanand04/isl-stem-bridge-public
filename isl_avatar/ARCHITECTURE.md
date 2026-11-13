# Architecture

How a recorded ISL sign becomes avatar motion on the lesson page, and where each check sits.
Status: 7 November 2026.

## The pipeline

```
 ISLRTC video ─► extract_landmarks.py ─► motion_qc.py ─► retarget_blender.py ─► animation_validator.py
 (licensed)       raw landmarks, kept      pass / fail     bake one NLA clip       sample the avatar
                  unchanged (motion/v2)    (≤ 3 lost       per sign on the rig     frame by frame
                                            frames)              │                        │
                                                                  ▼                        ▼
                                                     export avatar/avatar.glb     motion_report.py
                                                                  │               geometric check
                                                                  ▼               (reports/v2/<sign>)
 registry/signs.csv ─► check_registry.py ─► player/registry.json ─► player (three.js)
 (one row per sign)    stages + VERIFIED     + lesson validation      lesson page
                                                      ▲
                       rig_validator.py, facial_validator.py ── whole-avatar checks (reports/rig, reports/face)
```

Nothing is ever patched by hand along the way. A sign that fails a stage is re-recorded or left out.

## Stages and who decides them

| Stage | Decided by | Stored in |
| --- | --- | --- |
| 1. Source validated | Computed: source, attribution, licence `granted`, video file present | `check_registry.py` |
| 2. Motion extraction passed | `motion_qc.py` (no signing hand lost for more than 3 frames in a row) | `signs.csv: motion_qc` |
| 3. Retargeting passed | The bake ran without error and the clip exists | `signs.csv: retarget_check` |
| 4. Geometric comparison passed | `motion_report.py` limits, each checked separately | `reports/v2/<sign>/report.json` |
| 5. Interpreter reviewed | A named interpreter has watched it, with a date | `signs.csv: interpreter, review_date` |
| 6. Interpreter approved | That interpreter approved it | `signs.csv: interpreter_review` |
| 7. Published | The team publishes a VERIFIED sign | `signs.csv: published` (refused unless VERIFIED) |

A sign is **VERIFIED** only when stages 1 to 6 all pass. Stages 1 to 4 are technical. Passing them
means the avatar faithfully copies the tracked recording. They can never make a sign VERIFIED by
themselves. The player shows **Draft** for anything not VERIFIED.

## Components

### Extraction: `tools/extract_landmarks.py`

MediaPipe 0.10.14, one pass per video. Stored per frame:

- `pose`, `pose_world`: body, in image and metric 3D form;
- `left/right_hand_holistic`, plus a second detector (`mp.solutions.hands`) as `{side}_hand_model` and
  `{side}_hand_world` (metric 3D hand, which keeps finger depth);
- `{side}_hand`: the merged hand (Holistic first, the hand model when Holistic misses). `{side}_hand_source`
  says which one was used;
- `face` (478 points), `blendshapes` (52 ARKit scores) and `head_matrix` (FaceLandmarker);
- `quality`: frame brightness and the sharpness of each hand crop.

Untracked frames stay `null`. The raw file is never smoothed or edited. Smoothing happens only on a
working copy inside the baker.

### Quality check: `tools/motion_qc.py`

- Pose coverage of 95% or more.
- Face coverage.
- The longest run of lost frames for each signing hand, at most 3. A hand resting at the side is not counted as lost.
- Every gap is classified as `critical` (during a movement or hold) or `transition`.
- Recording warnings: frame rate, resolution, brightness, and low hand sharpness. Warnings never fail a clip.

### Retargeting: `tools/retarget_math.py` (pure Python) and `tools/retarget_blender.py` (Blender)

| Part | Method |
| --- | --- |
| Arms | Two-bone IK to body-relative wrist targets: sideways scaled by shoulder width, downwards by torso length, up and forwards by arm length. The shoulder rides on the shrugged collarbone. |
| Shoulders | Collarbone rotation from shoulder lift relative to the signer's own median, limited to −10°…+25°. |
| Hand | Palm frame from wrist, index, middle and pinky knuckles, as a full rotation. |
| Fingers and thumb | One full 3D frame per finger bone: Y along the bone, X from the knuckle line (for the thumb, from the thumb base towards the index), so twist and thumb opposition are kept. Absolute rotations relative to the avatar's own rest hand, so they are rig-independent. |
| Joint limits | Each finger bone's rotation relative to its parent is limited to the anatomical range (`retarget_config.json: finger_joint_limits`). Limited frames are counted and printed. |
| Chest, neck, head | Chest from shoulders and hips. Head from the face transform. The neck takes 40% of the head turn (SLERP), the head the rest. |
| Contact | Where the raw data shows fingertips touching (distance below threshold), the wrist targets are corrected until the avatar's fingertips touch too, eased over 3 frames. Contact is never added where the source has none. |
| Face | 52 ARKit shape keys keyed per frame from the scores, with an optional gain per shape. Frames without a face get no key, never a guess. |
| Smoothing | One Euro filter per stream (config), applied to the working copy only. |
| Interpolation | Linear (no overshoot). Rotations are quaternions. |

All tunable values are in `tools/retarget_config.json`, each with the measurement that set it.

### Validation

- `tools/animation_validator.py` (Blender) samples the baked clip: shoulders, elbows, wrists, the 21
  hand points of each hand, the head rotation and every face shape value.
- `tools/motion_metrics.py` (pure Python) computes joint flexion (15 joints per hand), finger spread,
  palm orientation relative to the chest, body-relative positions, contact, speed, and DTW.
- `tools/motion_report.py` compares the samples with the source frame by frame, applies the
  geometric limits and writes `report.json`, `report.md` and plots.
- `tools/rig_validator.py` (Blender) poses the hand through test poses, measures skin interpenetration
  and joint limits, checks every baked sign, and renders close-ups.
- `tools/facial_validator.py` (Blender) audits all 52 face shapes, left/right symmetry, eye gaze,
  how the secondary meshes follow, and face/body timeline sync, and renders each shape.

See [MOTION_VALIDATION.md](MOTION_VALIDATION.md).

### Registry and lesson: `tools/check_registry.py`

- Reads `registry/signs.csv` and computes every stage and the final status for each sign.
- Refuses inconsistent records: a published sign that is not VERIFIED, or a `pass_exception` without
  a documented QC EXCEPTION.
- Validates every lesson in `player/lessons/`:
  - the required sections are present;
  - the science topics are covered;
  - each explanation is one authored recording;
  - lists of concatenated signs are rejected;
  - every sign named is in the registry.
- Writes `player/registry.json`.

### Player: `player/`

three.js 0.160 loads `avatar/avatar.glb` (one animation clip per sign, plus `idle`). The lesson JSON
has these sections:

1. introduction
2. big idea
3. six steps
4. key words
5. recap

Each section has a diagram scene (SVG with CSS animation), a caption with highlighted key words, and
an ISL slot. An ISL slot plays one authored recording, or says it is waiting for an interpreter.
Vocabulary signs play one at a time, only when tapped.

Player controls:

- speed (0.5×, 0.75×, 1×);
- captions on/off;
- hands close-up (face kept in view);
- replay;
- keyboard (← → space).

Crossfade between clips is 0.1 s. `?review=1` adds the original video for the interpreter.

## File layout

```
isl_avatar/
├── avatar/            avatar_source.blend (working file), avatar.glb (page), archive_v1/
├── motion/v2/         raw extracted motion per sign (current); motion/*.json = first pipeline
├── registry/          signs.csv (the record), archive_signs_v1.csv
├── reports/
│   ├── v2/<sign>/     geometric report, plots, avatar samples (current bake)
│   ├── baseline/      the first pipeline's bake measured the same way (for comparison)
│   ├── rig/           rig_report.json, pose renders
│   └── face/          face_report.json, shape renders
├── player/            index.html, player.js, player.css, lessons/, registry.json (generated)
├── tools/             pipeline (see above), bake_all.sh, retarget_config.json, bone_maps/
└── tests/             unit tests (pure Python; Blender scripts are checked by running them)
```
