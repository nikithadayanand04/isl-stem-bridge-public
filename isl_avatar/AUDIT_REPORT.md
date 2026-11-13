# Audit report: avatar motion fidelity

Date: 7 November 2026. Scope: the whole pipeline (extraction → QC → retargeting → avatar → player),
the 13 baked ISLRTC signs and the photosynthesis lesson.

Method: every finding below was measured with the project's own tools. The numbers come from:

- `reports/baseline/`: the first pipeline, re-measured with the new metrics;
- `reports/v2/`: the current bake;
- `reports/rig/` and `reports/face/`.

The full current table is [reports/VALIDATION_SUMMARY.md](reports/VALIDATION_SUMMARY.md).

> All numbers compare the avatar with landmarks tracked from the source videos. They show how
> faithfully the avatar copies the tracking, not whether the signing is correct ISL. No sign is
> interpreter-approved yet.

## Summary

The first pipeline produced recognisable movement, but its handshapes were measurably wrong:

- median finger-joint error 13–22°;
- median palm-orientation error 14–32°;
- it fails the geometric check on all 5 signs measured.

The main causes were heavy smoothing, flattened image landmarks and direction-only fingers. All
three are fixed. **All 13 signs now pass every geometric limit**, with median finger-joint error
of 0.5–2.9° and median palm error of 0.6–3.7°.

The audit also found problems in the source data that the first pipeline copied blindly:

- depth-flipped hands;
- anatomically impossible finger bends;
- relaxed faces read as squinting.

These are now detected, limited or calibrated, and every case is counted.

## Findings

Severity: **High** = visibly wrong handshape or orientation; **Medium** = wrong in some frames or
for some signs; **Low** = cosmetic or diagnostic.

| # | Severity | Finding | Evidence | Fix | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | High | Smoothing removed real finger movement | Old filter (1.5 Hz, β 0.3) reduced a 140° bend to 74° in magnet_sign_2. Fast handshape changes were rounded off. | One Euro per stream, 8 Hz / β 30 for hands (keeps 87–97% of the flexion range, still removes about 35% of jitter). Raw file never smoothed. | Fixed |
| 2 | High | Fingers had no twist; the thumb could not oppose | Fingers were driven by bone direction only. Median finger-joint error 13–22° (baseline). | A full 3D frame per finger bone. The thumb uses a swing chain. | Fixed: medians 0.5–2.9° |
| 3 | High | Palm orientation off | Baseline median palm error 14–32°. | Full palm frame; metric hand points; body-relative comparison. | Fixed: medians 0.6–3.7° |
| 4 | High | Hands lost for 4–6 frames in a row (sun, computer, full-HD magnet) | QC failures on the first extraction. | Second hand detector (`mp.solutions.hands`), matched to sides by wrist. | Fixed: all three pass QC |
| 5 | High | Depth flips: the tracker mirrors the hand front-to-back for 1–5 frames | Palm normal jumps about 160° between frames 40 ms apart, in 11 of 16 clips. The avatar copied them. | Detected (`depth_flip_frames`), counted as lost in QC, interpolated in the bake, left out of the comparison (counted). | Fixed |
| 6 | Medium | Impossible finger bends copied | Tracked bends up to 178° (water, leaf, photosynthesis). | Anatomical joint limits in retargeting (thumb 70/70/90°, fingers 105/115/90° from rest). Each limited frame is logged. | Fixed: 0–92 limited bone-frames per sign, listed in the bake log |
| 7 | Medium | Thumb roll flipped up to 179° between frames | The roll reference (towards the index knuckle) lined up with the thumb (cos up to 0.99). A first fix that blended in the palm normal made it worse: 131 limited frames in magnet_sign_2. | Swing chain: no roll reference. | Fixed: thumb limiting fell to 0–5 per sign |
| 8 | Medium | Two coordinate systems mixed inside one sign | 0–7 image-only hand frames per sign between metric frames. Image and world points disagree strongly (PIP 6° vs 30° in sugar; 127° vs 71° in make). | World-only hand shape when world points cover ≥ 80% of frames; the rest interpolated. | Fixed |
| 9 | Medium | Avatar's eyes looked half closed at rest | On a relaxed ISLRTC signer MediaPipe reads squint 0.24, brow-down 0.36, smile 0.31. The renders showed narrowed eyes. | Per-clip neutral calibration from rest frames. | Fixed (renders checked against video) |
| 10 | Medium | The lesson strung dictionary signs together as if they were ISL sentences | Steps played "sun · leaf", "air · carbon dioxide" in sequence. | Steps now carry an interpreter-recording slot. Vocabulary plays one sign at a time on request. The validator rejects concatenated lists. | Fixed (explanations awaiting an interpreter) |
| 11 | Medium | No shoulder shrug, rigid neck | Not retargeted. | Collarbone shrug (−10°…+25°); the neck takes 40% of the head turn. | Fixed |
| 12 | Medium | Status was one word (VERIFIED / NOT) | The technical and linguistic stages were not separated. | Seven stages computed per sign. Publish blocked unless VERIFIED. Exceptions must be documented. | Fixed |
| 13a | Medium | Thumb skin inside index/middle finger in pinch/fist shapes | 5–9 mm deepest per sign (rig check, per-segment convex hulls) | Thumb overlap correction in the bake (`tools/hand_collision.py`) | **Reduced**: passing-through frames 1,452 → 810; key-grip contacts remain |
| 13 | Low | Validation measured nothing objective | Checks were visual only. | Metrics, per-sign reports with plots, rig and face validators, positive controls. | Fixed |
| 14 | Low | The stored QC result could go stale | The baker trusted the result saved at extraction time. | The baker re-runs QC. | Fixed |
| 15 | Low | Crossfade 0.25 s blurred sign onsets | Player setting. | 0.1 s. | Fixed |
| 16 | Low | Report wrist error mixed the axes | The body-offset scaling used the wrong axis order. | Corrected; tests added. | Fixed |

## Before and after (median, from the reports)

| Sign | Hand | Finger-joint error before → now | Palm error before → now | Geometric check before → now |
| --- | --- | --- | --- | --- |
| food | right | 15.3° → 0.5° | 25.6° → 1.0° | fail → pass |
| magnet_sign_2 | left / right | 15.4° / 13.6° → 1.2° / 1.5° | 28.4° / 24.4° → 1.6° / 1.7° | fail → pass |
| make | left / right | 22.2° / 15.0° → 1.4° / 0.9° | 23.6° / 19.8° → 1.8° / 0.6° | fail → pass |
| photosynthesis | left / right | 16.9° / 13.4° → 1.8° / 1.3° | 31.7° / 29.6° → 2.8° / 2.4° | fail → pass |
| water | right | 22.1° → 1.5° | 14.5° → 2.7° | fail → pass |

"Now" excludes the frames the avatar deliberately does not copy (depth flips, image-only frames,
impossible bends). They are counted in each report: for example photosynthesis left, 28 impossible
bends, 7 image-only and 5 depth-flipped frames out of 176.

The "now" values are in [reports/VALIDATION_SUMMARY.md](reports/VALIDATION_SUMMARY.md), which is
regenerated from the report files after every bake, so the two documents cannot drift apart.

## What is still open

1. **Interpreter review.** No sign is approved. This blocks VERIFIED status for everything.
2. **Interpreter-authored explanations** for the big idea and the six steps. Each slot shows
   "waiting for a recording by an ISL interpreter".
3. **Photosynthesis contact (resolved).** After the thumb correction, 5 of the 6 source contact
   frames are reproduced (limit: at most 25% missing). The one missed frame lies in the stretch
   where the tracker mirrored the left hand (frames 199–203).
4. **Photosynthesis QC exception (resolved).** Depth flips now count as lost frames. That gives
   one 4-frame left-hand gap (frames 198–201): the same size the team approved on 6 Nov, but at a
   different place. The team reconfirmed the exception for this location on 7 Nov; it is recorded
   as a QC EXCEPTION in the registry.
5. **Air, gravity** still fail QC (7 and 6 lost frames). They need new recordings.
6. **Thumb twist** now follows the hand rather than the tracker; the tracker's thumb roll proved
   unreliable. If the interpreter sees a thumb orientation problem in a specific sign, that is the
   place to look.
7. **Brow movement is subtle** on this face (5–7 mm at full strength). The interpreter should judge
   whether raised and lowered brows read clearly enough for question and negation grammar.
   Per-shape gains are available.
8. **Thumb partly inside the index or middle finger** in pinch- and fist-type handshapes,
   now **reduced, not gone**. A correction step in the bake turns the thumb (base joint, then the
   middle joint, at most 25° each) until no more than 1 mm overlap is left, eased over 2 frames.
   Across all 13 signs, frames with any finger skin passing more than 2 mm into another fell from 1,452 to 810
   (−44%), and the mean overlap depth roughly halved in most signs. Finger-shape fidelity is
   unchanged: all 13 signs still pass every geometric limit. What is left is mostly the thumb tip
   pressed against the side of the index finger (key-grip contacts in make, food, computer and
   photosynthesis), with deepest overlaps of 5–8 mm. A larger turn limit (45°) clears most of the
   left hand in "make" but changes the handshape noticeably, so it was not used: that trade-off is
   for the interpreter to judge.

## Constraints kept

- No sign was invented or edited by hand. Every movement comes from an ISLRTC recording.
- The 3-frame QC limit is unchanged. The one exception is documented in the registry and above.
- Every sign stays **Draft** until interpreter approval. Students see no recorded video.

## 12 November 2026: new signs for the chapter lesson

Four new ISLRTC signs were baked for the chapter-per-idea lesson. Nothing was loosened.

| Sign | Tracking QC | 3D check | Visual check (render, re-track, compare) |
| --- | --- | --- | --- |
| soil | pass | pass | **fail**: left wrist 0.154 (≤ 0.15), left handshape 0.907, right handshape 0.361 (≤ 0.30) |
| energy | pass | pass | **fail**: left wrist 0.152 / p90 0.342, left handshape 0.318 |
| grow_plants | pass | pass | **fail**: left handshape 0.549 |
| breathe | pass | pass | pass |
| photosynthesis_process (ISLRTC explanation) | pass | **fail**: contact missing 0.40 (≤ 0.25) | not run; not played |

Side by side: `previews/compare_new_signs.jpg`. Arm paths and timing follow the signers. The failures are
handshape, as for the earlier signs: the avatar's fingers are more open or curled than the signer's in
part of the movement (most visible in grow (plants)). The signs are playable (they pass QC and the 3D
check) and marked Draft; the interpreter must judge them.

Not usable (tracking loses a hand for longer than 3 frames): chlorophyll 6, chlorophyll academic 7 (and body
71%), stomata 5, energy explanation 39, gases explanation 8, plant nutrition 7. No ISLRTC sign was found
for "plant" on its own or "root". Visual check now: 6 of 17 signs pass (`reports/visual_loop/SUMMARY.md`).

## 12 November 2026 (later): finger neatness, measured

Asked by the school: fingers must fold neatly and precisely.

| Finding | Evidence |
| --- | --- |
| Picture reading puts the whole fold in one joint | water right, frames 29–31: knuckle 10–34°, middle joint 130–149° (limit 115°) |
| Anatomical finger fit gives a plausible fold | same frames: knuckle 30–51°, middle ~80°, tip ~48° |
| …but no better in the visual check | 14 signs, 22 hands: 10 better, 12 worse, median +0.003; within limit 10 → 12; signs passing 4 → 4 |
| A tight fist is not in the data | the fingertips are hidden; the tracker's 3D hand bends 33–49° / 78–101°, the picture shows a full fist |
| Hand turned the wrong way in some frames | 0–12% of frames in most signs; photosynthesis left 20%, carbon dioxide left 14% (frames 26–33) |

Decision: the finger fit stays off (`hands.finger_fit: false`); no limit was changed. Neat handshapes need
either sharper recordings (the ISLRTC hands are motion-blurred in 59–98% of frames) or an interpreter's
recording made to the rules in INTERPRETER_RECORDING_SHEET.md.

## 13 November 2026: lip-sync removed

The voice-driven mouth (loudness and pitch → jaw and lip shapes) did not match the spoken words, and
it replaced the ISLRTC signer's own mouth movements, which are part of ISL. For Deaf students that is
wrong on both counts. It is removed; the face always follows the signer. The voice is off by default.
Words: 41 in the glossary, 13 with a checked ISLRTC sign, 28 shown as picture cards (no checked sign yet).
