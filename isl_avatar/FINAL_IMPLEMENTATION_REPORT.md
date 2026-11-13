# Final implementation report

ISL STEM Bridge, 7 November 2026. What this improvement pass delivered, what was verified and how,
and what is left. The details are in the linked documents. Every number here comes from a file in
`reports/`.

## 1. Delivered

| Area | Delivered | Where |
| --- | --- | --- |
| Audit | Measured audit of the whole pipeline: 17 findings with severity, evidence and status | [AUDIT_REPORT.md](AUDIT_REPORT.md) |
| Motion capture | Second hand detector; metric 3D hands; face transform; per-frame quality; raw data never smoothed; gap severity; recording warnings; depth-flip detection | `tools/extract_landmarks.py`, `tools/motion_qc.py` |
| Retargeting | Full 3D finger frames; thumb swing chain (opposition kept, no roll flips); anatomical joint limits with logging; world-only hand shape; depth-flip interpolation; shoulder shrugs; neck share by SLERP; face neutral calibration; re-tuned smoothing; every value in a config file with its measurement | `tools/retarget_math.py`, `tools/retarget_blender.py`, `tools/retarget_config.json` |
| Validation system | Metrics, per-sign geometric reports with plots and separate pass limits (no overall %), avatar sampler, rig validator with positive controls, facial validator, generated summary table | `tools/motion_metrics.py`, `motion_report.py`, `animation_validator.py`, `rig_validator.py`, `facial_validator.py`, `validation_summary.py` |
| Status model | Seven separate stages per sign; publish blocked unless VERIFIED; QC exceptions must be documented | `tools/check_registry.py`, `registry/signs.csv` |
| Lesson | Introduction → big idea → 6 steps (light, water, CO₂ in, sugar, O₂ out, growth) → key words → recap. Interpreter-recording slots instead of chained dictionary signs. Lesson validator. | `player/lessons/photosynthesis.json` |
| Player | Section navigation, highlighted key words, ISL status per section, tap-to-play vocabulary, replay, speed, captions toggle, hands close-up (face kept), keyboard, growth animation, 0.1 s crossfade | `player/` |
| Avatar | v2 bake promoted to `avatar_source.blend` / `avatar.glb`; first pipeline archived | `avatar/` |
| Tests | 35 → 70 unit tests, all passing | `tests/` |
| Docs | README, AUDIT_REPORT, ARCHITECTURE, MOTION_VALIDATION, AVATAR_RIGGING, INTERPRETER_REVIEW_GUIDE, IMPLEMENTATION_CHANGELOG, this report, VALIDATION_SUMMARY | project root, `reports/` |

## 2. Verified, and how

| Claim | How it was checked | Result |
| --- | --- | --- |
| Unit tests pass | `python3 -m unittest discover tests` | 70 tests, OK |
| All 13 baked signs rebaked with the final pipeline | `sh tools/bake_all.sh` (log: `reports/v2/bake_all_log.txt`) | 13 baked, GLB exported |
| Geometric fidelity | `motion_report.py` per sign | **All 13 pass every limit.** Median finger-joint error 0.5–2.9°, palm 0.6–3.7°. |
| Better than the first pipeline | Same metrics on the archived bake (`reports/baseline/`) | Baseline fails all 5 signs measured (finger 13–22°, palm 14–32°) |
| Thumb overlap correction | Rig check on the bake before and after the correction (`reports/rig_before_thumb_fix/` vs `reports/rig/`), plus a before/after render (`previews/thumb/leaf_58_before_after.jpg`) | Passing-through frames 1,452 → 810; all 13 signs still pass the geometric check |
| Rig test poses clean | `rig_validator.py` | 14 test poses × 2 hands: no finger interpenetration, no joint over its limit |
| The interpenetration and limit checks actually detect problems | Two impossible control poses | Both caught on both hands (`detector_controls_passed: true`) |
| Face shapes complete and symmetric | `facial_validator.py` | 52/52 ARKit shapes; all left/right pairs within ratio 1.00–1.03; eyeballs move for gaze |
| Face and body on one timeline | `facial_validator.py` | 13 of 13 signs in sync |
| Face calibration fixes the half-closed eyes | Renders vs video frames (`previews/face/`) | Neutral frames now open-eyed; a real downward look still closes the eyes |
| Lesson follows the language rule | `check_registry.py` lesson validation, plus a unit test on the real lesson file | Valid: no concatenated sign lists, every section captioned, all science topics present |
| Player works with the final avatar | Browser: loaded `player/`, navigated sections, played the introduction and single vocabulary signs, toggled close-up, read the console | Works; no console errors |
| Registry consistency | `check_registry.py` | No errors; 0 of 18 VERIFIED (no interpreter approval yet) |

## 3. Not verified

- **Linguistic correctness of any sign.** That needs an ISL interpreter.
- **The thumb overlap, by eye, in every sign.** One before/after render was checked (leaf, frame 58);
  the rest is measured, not looked at.
- **On other machines or browsers.** Tested only on the development Mac in the app's built-in
  browser.

## 4. Known issues and limits

1. **Thumb partly inside the index or middle finger** in pinch- and fist-type handshapes,
   now **reduced, not gone**. A correction step in the bake turns the thumb (base joint, then the
   middle joint, at most 25° each) until no more than 1 mm overlap is left, eased over 2 frames.
   Across all 13 signs, frames with any finger skin passing more than 2 mm into another fell from 1,452 to 810
   (−44%), and the mean overlap depth roughly halved in most signs. Finger-shape fidelity is
   unchanged: all 13 signs still pass every geometric limit. What is left is mostly the thumb tip
   pressed against the side of the index finger (key-grip contacts in make, food, computer and
   photosynthesis), with deepest overlaps of 5–8 mm. A larger turn limit (45°) clears most of the
   left hand in "make" but changes the handshape noticeably, so it was not used: that trade-off is
   for the interpreter to judge.
2. **Photosynthesis contact:** now within the limit (5 of 6 source contact frames reproduced).
3. **Photosynthesis QC exception moved.** Depth flips now count as lost frames, which places the
   clip's one 4-frame left-hand gap at frames 198–201. The team approved a 4-frame gap on 6 Nov at a
   different place. The team **reconfirmed** the exception for this location on 7 Nov; it is
   recorded as a documented QC EXCEPTION in the registry.
4. **Thumb twist** follows the hand, not the tracker (the tracker's thumb roll was unreliable).
5. **Brow movement is subtle** on this face (5–7 mm). The interpreter should judge whether it reads clearly.
6. **Air and gravity** fail QC (7 and 6 lost frames) and need new recordings.
7. **Facial validator notes:** brows and lashes move 1.0–3.0 mm where nearby skin moves 3.2–7.9 mm
   for blink and brow-down. Renders show no visible gap; it is most likely the nearest-skin match
   picking eyelid vertices.
8. **Geometric checks measure copying, not correctness**, and leave out the frames the avatar
   deliberately does not copy. Every report lists those frames with reasons.

## 5. Blocked on people, not code

| Needed | From | Unblocks |
| --- | --- | --- |
| Review of the 13 baked signs | Qualified ISL interpreter | Stages 5–6, VERIFIED status, removing "Draft" |
| Recorded ISL explanations for the big idea and the 6 steps | ISL interpreter / Deaf ISL expert | The empty ISL slots in the lesson |
| Recordings of air, roots, energy, grow | Signer | Missing key words |
| Choice between the two magnet signs | Interpreter | Future magnet lesson |

## 6. Suggested next steps

1. Interpreter review, using [INTERPRETER_REVIEW_GUIDE.md](INTERPRETER_REVIEW_GUIDE.md) and `?review=1`.
2. Ask the interpreter whether the remaining thumb contacts (make, food, computer) look wrong; if so, raise `thumb_collision.max_correction_deg` and rebake.
3. Record the step explanations. Each goes through extraction → QC → bake → report → review.
4. Host the page for the school.

## 7. How to reproduce everything

```bash
cd isl_avatar
python3 -m unittest discover tests
sh tools/bake_all.sh
blender -b avatar/avatar_source.blend --python tools/rig_validator.py -- \
    --bone-map tools/bone_maps/mixamo.json --out reports/rig --renders
blender -b avatar/avatar_source.blend --python tools/facial_validator.py -- --out reports/face --renders
python3 tools/validation_summary.py
python3 tools/check_registry.py
python3 -m http.server 8811          # then open http://localhost:8811/player/
```
