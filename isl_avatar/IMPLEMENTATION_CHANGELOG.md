# Implementation changelog

## 13 November 2026: cleaner student page

- New layout (`player/index.html`, `player/player.css` rewritten): title with a small **Draft** badge
  (details on hover), one row of chapter buttons, avatar beside the picture (word and ✋ Sign button
  above the picture), controls directly under them like a video player, then the captions and the
  word cards in one scrolling row. On a 1366×768 laptop the avatar, picture, controls and both
  captions fit on one screen; phones get one column with no sideways scrolling.
- Removed from the student view (still shown in review mode, `?review=1`): the language-rule note,
  the Kannada translation status, the long "ISL explanation is coming" message, sign status and
  reasons under the word, "picture card · ISL sign coming" tags, and "chapter x of 13 · step y" text
  (the step dots show it). The voice option moved into **More**.

## 13 November 2026: sign-first, no voice-driven lip-sync

School feedback: the lesson is for Deaf students. The mouth did not match the voice, and a lesson
built around voice and lips is not right for them. Everything should be in ISL signs, with captions,
and words that cannot be signed yet should be shown as word cards with meaning and picture.

- **Lip-sync removed** (`player/player.js`): the face always plays the ISLRTC signer's own face and
  mouth movements (ISL non-manual features). `tools/lipsync.py` is no longer used by the player.
- **Voice off by default**, relabelled "Voice (for hearing teachers)". Captions (English + Kannada) stay on.
- **Word cards on every step** (`renderWords`; glossary of 41 words in the lesson file; 30 new
  pictures in `player/icons.js`): picture, word in English and Kannada, meaning in both languages,
  and a ✋ Sign button for the 13 words with a checked ISLRTC sign. The other 28 are picture cards
  until an interpreter adds the sign.
- **▶ Play signs every step's main word**: the avatar signs it on its own with its card lit up, after the
  picture and caption appear. Signs are still never strung together into a fake sentence.
- **"Key words in ISL"** shows all 41 word cards.
- **Checks:** `tools/check_registry.py` requires every step word to be in the glossary with meanings and a
  picture, and every glossary sign to be registered; 3 new tests (105 in all).

## 12 November 2026 (later): school feedback, examples and finger neatness

From the school visit: (1) students cannot tell which thing is meant (leaf, plant, stem, tree, bush);
(2) signs must be neat, with fingers folding precisely; (3) detailed pictures for every small idea.

- **Example galleries** (`player/icons.js`, `showGallery` in `player/scenes.js`, styles in `scenes.css`):
  13 example steps added (67 steps in all), e.g. "all of these are plants" (tree, bush, grass, tulsi,
  creeper, cactus), "parts of a plant, one by one" (trunk = stem), "is it a leaf?" (✓ leaf, ✗ flower /
  stem / fruit), kinds of soil, water sources, where CO₂ comes from, who needs oxygen, food plants store.
  Cards appear one by one; each step has its own narration (regenerated: Kannada Sapna, English Lekha).
  The picture steps keep their numbering (`player.js` skips gallery steps when stepping the drawing).
- **Finger neatness, measured.** Close-ups (water, frames 29–31) showed the avatar's fingers half bent
  where the signer makes a tight fist. Cause found in `image_anchored_hand`: it put the whole fold into
  the middle joint (130–149°, beyond a real finger; cut to 115° by the joint limit) and left the knuckle
  almost straight. A new anatomical **finger fit** (`fitted_finger_hand`, 2 tests) gives a plausible fold
  (knuckle 30–51°, middle ~80°, tip ~48°). Tested on 14 signs with the visual loop check: **no overall
  gain** (22 hands: 10 better, 12 worse, median change +0.003; signs passing 4 → 4), so it is **off**
  (`hands.finger_fit: false`). In a fist the fingertips are hidden and the tracker guesses them; the
  ISLRTC videos (hands blurred in 59–98% of frames) do not contain the full fold.
- **New check:** which way the hand faces (palm or back towards the camera), from the picture.
  The avatar's hand faces the other way in 0–12% of frames in most signs; photosynthesis left 20%,
  carbon dioxide left 14% (a run of 8 frames, 26–33). Not fixed yet.

## 12 November 2026: lesson v3, one chapter per idea

Asked for by the team after the school visit: every idea shown and explained on its own, with clear pictures.

- **Lesson** (`player/lessons/photosynthesis.json`): 11 chapters × 4–5 steps (54 steps), each step with
  English and draft Kannada text. Old lesson kept in `player/lessons_archive/photosynthesis_v1.json`.
- **Pictures** (`player/scenes.js`, `player/scenes.css`, new): an animated drawing per chapter; each step
  reveals and animates its own part (Sun → light travelling to Earth → leaf catching energy; soil layers →
  magnified grains, water and air spaces → roots taking in minerals; leaf → veins → stomata → cells;
  chloroplast → solar panel → colours of light; CO₂ molecule; guard cells day/night; water split → glucose;
  oxygen cycle; starch stores). Labels in English and Kannada.
- **Player** (`player/player.js`): chapter flow (sign → ISL explanation → steps), step dots, word card with
  the ISL sign button, ◀ ▶ through steps; avatar always loaded fresh (a cached copy hid new signs).
- **New ISLRTC signs on the avatar:** soil, energy, grow (plants), breathe. All pass tracking QC and the 3D check.
- **Downloaded but not used** (fail the 3-frame tracking limit or the contact check; limits unchanged):
  chlorophyll (6), chlorophyll academic (7), stomata (5), energy explanation (39), gases explanation (8),
  plant nutrition (7), photosynthesis process (contact 0.40 > 0.25). A lower tracker confidence made
  chlorophyll worse (8), so it was not used.
- **Narration:** one clip per step (`<chapter>.<step>`); Kannada (Microsoft Sapna, female) and English (Lekha).
- **Checks:** `tools/check_registry.py` understands chapters (8 required ideas, Kannada per step, reasons
  for missing signs); 4 new tests.
- **Interpreter sheet:** `tools/recording_sheet.py` writes `INTERPRETER_RECORDING_SHEET.md`: per chapter
  the content to sign, recording rules and the commands that put a recording on the avatar.


Changes made in the 7 November 2026 improvement pass, grouped by area. Each entry gives the reason,
which was measured where possible. The detailed numbers are in [AUDIT_REPORT.md](AUDIT_REPORT.md).

## Motion capture: `tools/extract_landmarks.py`, `tools/motion_qc.py`

- **Second hand detector.** `mp.solutions.hands` runs next to Holistic. Its detections are matched to
  the signer's left/right hand by the nearest wrist. When Holistic misses a hand, the hand model's
  detection is used, and the frame records which source it came from (`{side}_hand_source`).
  - Why: Holistic lost hands for 4–6 frames in a row in sun, computer and the full-HD magnet video.
    With the second detector, all three now pass QC.
- **Metric 3D hand points** (`{side}_hand_world`) are stored and used for the hand shape.
  - Why: image landmarks flatten finger depth. Measured finger flexion was 1.5–3× larger in world points.
- **Face transform** (`head_matrix`) and per-frame **quality** values (brightness, sharpness of each hand
  crop) are stored.
- **Raw data stays raw.** Nothing is smoothed in the motion file.
- **QC additions:**
  - gaps classified as `critical` / `transition`;
  - recording warnings (frame rate, resolution, brightness, low sharpness);
  - **depth-flip detection**: a hand mirrored front-to-back by the tracker counts as a lost frame.
    The 3-frame limit is unchanged.
- **Bug fixed:** the face reader returned a single `None` on early exit and crashed the gravity extraction.
- **New:** `--confidence` option.

## Retargeting: `tools/retarget_math.py`, `tools/retarget_blender.py`, `tools/retarget_config.json`

- **Smoothing re-tuned** and moved to a config file (One Euro: 8 Hz / β 30 for hands, 6 Hz / β 5 for
  the body).
  - Why: the old 1.5 Hz / β 0.3 removed up to half of real finger movement (magnet_sign_2: a 140°
    bend came out as 74°).
- **Full 3D finger frames.** Each of the 30 finger bones now gets a complete orientation, not just a
  direction, so finger twist and **thumb opposition** are reproduced. The frames are relative to the
  avatar's own rest hand, so the method does not depend on how the rig's bone axes are set up.
- **Thumb roll reference** blends the index-knuckle direction and the palm normal.
  - Why: the old reference could line up with the thumb (cos up to 0.99) and flip the roll by up to 176°.
- **World-only hand shape.** When a hand has metric points in at least 80% of its frames, the few
  image-only frames are interpolated, not mixed in.
  - Why: switching between the two coordinate systems made fingers jump.
- **Depth-flipped frames** are interpolated, never copied.
- **Anatomical finger joint limits.** Each finger bone's rotation relative to its parent is limited
  (thumb 70/70/90°, fingers 105/115/90°). Every limited frame is counted in the bake log.
  - Why: the tracker sometimes reports impossible shapes; the avatar copied bends up to 178°.
- **Shoulder shrugs.** Collarbone rotation follows the signer's shoulder lift, limited to −10°…+25°.
  The arm IK starts from the raised shoulder.
- **Neck.** It takes 40% of the head rotation (SLERP); the head takes the rest.
- **Quaternion helpers:** `slerp`, `quat_to_mat`, `partial_rotation`, `rotation_angle`.
- **Face gains** can be set per shape key (config). They are all 1.0 by default.
- **Thumb overlap correction** (`tools/hand_collision.py`, config `thumb_collision`). After
  baking, every frame is checked for thumb skin inside a finger (per-segment convex hulls). The
  thumb is turned at its base, then its middle joint (at most 25° each), with all overlaps pushing
  at once in proportion to their depth, until at most 1 mm is left. Corrections ease over 2 frames.
  Other signs' tracks are muted while measuring.
  - Why: the thumb sat 5–9 mm inside the index/middle finger in most signing frames. One push at a
    time made a sandwiched thumb bounce between two fingers. Result: passing-through frames
    1,452 → 810 (−44%), and all signs still pass the geometric check.
- **The baker re-runs QC** with the current rules instead of trusting the stored result.
- **Face neutral calibration.** Each clip's resting face (median scores while both hands rest) is
  subtracted and the remaining range rescaled.
  - Why: a relaxed ISLRTC signer read as squint 0.24, brow-down 0.36, smile 0.31, so the avatar's
    eyes looked half closed. Checked against the video.
- **Bone map** gained `neck`, `left_clavicle` and `right_clavicle`.
- **New:** `tools/bake_all.sh` re-bakes every passing sign, validates each and exports the GLB in one step.

## Validation (new)

- `tools/motion_metrics.py`: joint flexion (15 joints per hand), spread, palm orientation relative to the
  chest, body-relative offsets, contact, speed correlation, and DTW (diagnostic only).
- `tools/animation_validator.py`: samples a baked clip in Blender.
- `tools/motion_report.py`:
  - frame-by-frame comparison, plots and a markdown report per sign;
  - a **geometric check with separate limits** (no overall percentage);
  - side-by-side images when renders are given;
  - registry status read from `signs.csv`;
  - frames the avatar deliberately does not copy (depth flips, image-only frames, impossible
    bends) are left out of the hand-shape comparison and counted.
- `tools/validation_summary.py`: one table of every stage and measure, generated from the report files.
- `tools/rig_validator.py`: test poses (fist, spread, opposition, single-finger curls, wrist range),
  finger interpenetration depth on the deformed skin (per-segment convex hulls), anatomical limits,
  every baked sign frame by frame, close-up renders, and **positive controls** that prove the
  detector works.
- `tools/facial_validator.py`: all 52 ARKit shapes (size, region, left/right symmetry), eye gaze,
  secondary meshes following the face, face/body timeline sync, and a render per shape.
- `tools/render_preview.py`: `--focus BONE` close-up.

## Registry and lesson

- `registry/signs.csv`:
  - new columns `retarget_check`, `validation_report` and `published`;
  - motion paths now point to `motion/v2/`;
  - QC values recomputed.
- `tools/check_registry.py`:
  - computes **seven separate stages** per sign;
  - VERIFIED needs the geometric check and interpreter approval;
  - refuses `published = yes` on an unverified sign, and `pass_exception` without a documented QC EXCEPTION;
  - **validates lessons**: required sections, science coverage, one authored recording per
    explanation, concatenated sign lists rejected, every sign known.
- `player/lessons/photosynthesis.json` restructured:
  1. introduction (ISLRTC explanation);
  2. the big idea;
  3. six steps (light energy, water uptake, CO₂ in, sugar, O₂ out, **growth**), each with emphasis
     words and an ISL slot waiting for an interpreter recording;
  4. key words (single vocabulary signs, with reasons for the missing ones);
  5. recap.

  The avatar no longer strings dictionary signs together during the steps.

## Player

- Section navigation, captions with highlighted key words, an ISL status panel per section, tap-to-play
  vocabulary, replay, speed 0.5/0.75/1×, captions toggle, **hands close-up** that keeps the face in
  view, keyboard control, and a growth animation in the diagram.
- Crossfade between clips shortened from 0.25 s to 0.1 s, so sign onsets stay crisp.

## Avatar files

- The v2 bake is now `avatar/avatar_source.blend` and `avatar/avatar.glb`.
- The first pipeline's files are kept in `avatar/archive_v1/`.
- The old registry is kept as `registry/archive_signs_v1.csv`.

## Tests

- 35 → 70 unit tests. New areas:
  - finger frames, thumb roll, joint limits;
  - shrugs, neck share, SLERP, arm IK with shrug;
  - metrics and DTW;
  - registry stages, publish rule, QC exception rule, lesson validation;
  - depth-flip detection;
  - face neutral calibration;
  - thumb swing chain;
  - easing of per-frame corrections.
