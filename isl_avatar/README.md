# ISL STEM Bridge

**Making STEM learning accessible for Deaf and hard-of-hearing students through Indian Sign Language (ISL),
simple English and visual animation.**

Experiential Learning project, RV College of Engineering · status as of 7 November 2026

ISL STEM Bridge has two parts:

1. **Primary research** with students and teachers at a school for Deaf students: two survey forms and a
   school-visit plan.
2. **An ISL learning page** where a realistic 3D interpreter explains a science topic beside an animated
   diagram. The first lesson is **photosynthesis**.

> **The rule behind everything:** the avatar only ever performs real ISL, copied from recordings of ISLRTC
> signers. It never invents a sign, and it never strings dictionary signs together to fake an ISL sentence.
> Until a qualified ISL interpreter checks the avatar's signing, the page says so ("Draft").

## Documents

| Document | What it covers |
| --- | --- |
| [AUDIT_REPORT.md](AUDIT_REPORT.md) | What was measured to be wrong, what was fixed, what is still open |
| [ARCHITECTURE.md](ARCHITECTURE.md) | The pipeline, the seven validation stages, every component |
| [MOTION_VALIDATION.md](MOTION_VALIDATION.md) | How motion fidelity is measured, the pass limits, what the numbers cannot tell you |
| [AVATAR_RIGGING.md](AVATAR_RIGGING.md) | The avatar, how motion reaches each bone, rig and face validation |
| [INTERPRETER_REVIEW_GUIDE.md](INTERPRETER_REVIEW_GUIDE.md) | For the ISL interpreter: what to review, how, and the recordings still needed |
| [IMPLEMENTATION_CHANGELOG.md](IMPLEMENTATION_CHANGELOG.md) | Every change in the 7 Nov improvement pass, with reasons |
| [FINAL_IMPLEMENTATION_REPORT.md](FINAL_IMPLEMENTATION_REPORT.md) | What was delivered, verified results, limitations, next steps |
| [reports/VALIDATION_SUMMARY.md](reports/VALIDATION_SUMMARY.md) | Current results for every sign, generated from the report files |

---

## Where things stand

| Area | Status |
| --- | --- |
| Survey forms (2) | Live, with linked response spreadsheets |
| School-visit script | Written; PDF ready |
| 3D interpreter avatar | Realistic woman, full finger rig, 52 face expressions; rig and face validated |
| Signs on the avatar | 17 ISLRTC signs baked (soil, energy, grow (plants), breathe added 12 Nov 2026); 18th (Photosynthesis Process explanation) baked but fails the contact check, so not played |
| Photosynthesis lesson | v3 (12 Nov 2026): 11 chapters, one per idea (photosynthesis, plant, Sun, soil, water, leaf, chlorophyll, carbon dioxide, making food, oxygen, growing), 67 steps (54 animated pictures + 13 example galleries, e.g. tree / bush / grass / tulsi are all plants; is it a leaf?) with English + Kannada captions and narration, key words, recap |
| ISL explanations for the steps | Introduction: ISLRTC explanation. Other chapters: **waiting for an interpreter's recordings**; what to record is in [INTERPRETER_RECORDING_SHEET.md](INTERPRETER_RECORDING_SHEET.md) |
| ISLRTC permission for dictionary videos | Granted (recorded 6 Nov 2026) |
| Interpreter review of the avatar's signing | **Not done yet**: every sign is still "Draft" |
| Hosting online | Not yet; the page runs on the development Mac |

---

## Part 1 – Research materials

| What | Link / file | Notes |
| --- | --- | --- |
| Survey: *Help Us Make Learning Easier!* | [student link](https://forms.gle/hmMi6feNsLS4ub5b9) | 8 questions, anonymous, no sign-in |
| Survey: *🌈 Let's Learn Together!* | [student link](https://forms.gle/9EfYhCFCC1Kbv15q7) | 6 questions, child-friendly theme, custom header |
| Apps Script that built each form | `../ISL_STEM_Bridge_Survey.gs`, `../Lets_Learn_Together_Survey.gs` | Safe to re-run: never makes a duplicate form |
| School-visit script | [doc](https://claude.ai/artifact/QNVzT8W6xp2ZKjPbvMPKJa), `../School_Visit_Script.pdf` | 70-minute session, activities, teacher questions, observation sheet |
| Form header image | `../header/lets_learn_header.png` | 1600 × 400, original illustration |

Both forms collect no names, emails or IDs, and every question is optional. Each spreadsheet has a
**Summary** tab with counts and percentages that update automatically.

---

## Part 2 – The ISL learning page

### Quick start

You need Python 3.10+. Blender 4.5 is needed only to build the avatar or add signs.

```bash
cd isl_avatar
python3 tools/check_registry.py      # refresh player/registry.json and check the lesson
python3 -m http.server 8811          # serve the page
```

Open **<http://localhost:8811/player/>** and press **▶ Play**.

The interpreter's comparison view is **<http://localhost:8811/player/?review=1>**. It adds the original
ISLRTC video under the avatar. It is for the project team only; never send students this link.

### What the student sees

![Avatar compared with ISLRTC signers](docs_avatar_compare.jpg)

*Top of each pair: the ISLRTC dictionary video. Below: the avatar performing the same sign.*

One page, one topic: **Photosynthesis – how plants make their own food.** The lesson has ten sections,
reachable from a row of buttons:

| Section | Diagram | ISL |
| --- | --- | --- |
| Introduction | The whole process | The avatar performs the ISLRTC signer's 13-second ISL explanation |
| The big idea | Plant glows | Waiting for an interpreter's recording |
| 1 · Light | Rays stream to the leaves | Waiting for an interpreter's recording |
| 2 · Water | Drops rise from the roots | Waiting for an interpreter's recording |
| 3 · Carbon dioxide in | CO₂ drifts into the leaf | Waiting for an interpreter's recording |
| 4 · Making sugar | Sugar appears in the leaf | Waiting for an interpreter's recording |
| 5 · Oxygen out | O₂ floats away | Waiting for an interpreter's recording |
| 6 · Growing | The plant grows new leaves and roots | Waiting for an interpreter's recording |
| Key words in ISL | – | Tap a word to see its single ISLRTC sign |
| Recap | The whole process | ISLRTC explanation again, plus five summary points |

Each section shows a large simple-English caption with its key words highlighted. Sections that are
waiting for an interpreter say so plainly; the avatar does not fill the gap by chaining dictionary signs.
Key words under each step can be tapped to see one sign at a time.

- **Controls:**
  - ▶ Play / ■ Stop, and ◀ ▶ (or the arrow keys) to move between sections;
  - **Speed** 0.5× / 0.75× / 1×;
  - **Captions** on/off;
  - **Hands close-up**, which keeps the face in view for facial grammar;
  - **↻ Replay sign**;
  - drag on the avatar to turn the view.
- **Accessibility:**
  - large captions, at least 5 seconds per section;
  - high-contrast dark clothing so the hands stand out;
  - no animation for users who have "reduce motion" switched on.
- **No recorded videos for students.** The ISLRTC videos appear only in review mode.

### How a sign gets onto the avatar

```
Authorised ISL video ─► Extract ─► Quality check ─► Retarget & bake ─► Geometric check ─► Interpreter ─► VERIFIED
 (ISLRTC dictionary)     (raw data   (≤ 3 lost or    (Blender: IK, full   (avatar vs          review
                          kept)       flipped frames)  finger frames,       tracked signer,
                                          │            joint limits, face)  separate limits)
                                          └── fail ─► find a clearer recording (never patched)
```

Seven stages are tracked separately for every sign:

1. source validated;
2. motion extraction passed;
3. retargeting passed;
4. geometric comparison passed;
5. interpreter reviewed;
6. interpreter approved;
7. published.

The technical stages (1–4) can never make a sign VERIFIED on their own. See
[ARCHITECTURE.md](ARCHITECTURE.md) and [MOTION_VALIDATION.md](MOTION_VALIDATION.md).

### Signs so far

All from the ISLRTC dictionary. **None is interpreter-verified yet.** Current numbers are in
[reports/VALIDATION_SUMMARY.md](reports/VALIDATION_SUMMARY.md).

| Sign | Quality check | Geometric check | Used in |
| --- | --- | --- | --- |
| photosynthesis (ISLRTC explanation) | pass by documented exception (one 4-frame gap) | pass | Introduction, recap |
| leaf, sun, water, sugar, food, make | pass | pass | Key words |
| carbon dioxide (sign 2), oxygen (sign 2) | pass | pass | Key words |
| magnet, magnet (sign 2), electricity, computer | pass | pass | Not on the page (later lessons) |
| air | fail (7 frames) | – | Key words, marked "not available yet" |
| gravity | fail (6 frames) | – | – |
| carbon dioxide, oxygen (first entries) | fail: long explanation videos | – | Replaced by the "sign 2" versions |
| evaporation | pending (37-second explanation) | – | – |

The full record is `registry/signs.csv`: source, licence, every stage, review status, notes.

### Quality and accuracy rules

| Rule | Why |
| --- | --- |
| **Max 3 lost frames in a row** for a signing hand | Movement is never invented. Decided by the team on 6 Nov 2026. |
| **Depth-flipped frames count as lost** | From one camera, the tracker sometimes mirrors the hand front-to-back. Every joint is wrong in such a frame. |
| **Exceptions are documented** (`pass_exception` plus a QC EXCEPTION note) | The checker refuses an undocumented one. |
| **Thumb overlap correction** | After baking, the thumb is turned (at most 25° per joint) until it rests on a finger instead of sinking in. |
| **Anatomical joint limits** | Impossible tracked bends (up to 178°) are limited, and every case is logged. |
| **Body-relative placement** | A sign at the chest stays at the chest on a differently shaped body. |
| **Hand contact is copied, never added** | Fingertips that touch in the video are made to touch on the avatar. |
| **Face neutral calibration** | Each signer's relaxed face is subtracted, so the avatar does not look half asleep. |
| **No concatenated sign sentences** | ISL explanations come only from a signer's recording. The lesson checker rejects lists of signs. |
| **Draft until verified** | An unchecked sign is never presented as approved. |

### Adding a sign or a lesson

**A new sign**

```bash
cd isl_avatar
python3 tools/fetch_dictionary.py find "magnetic field"
python3 tools/fetch_dictionary.py get "Magnetic_Field.mp4"
.venv/bin/python tools/extract_landmarks.py "references/dict_Magnetic_Field.mp4" \
    --sign-id magnetic_field --face-model models/face_landmarker.task --out-dir motion/v2
# prints the quality check; add a row to registry/signs.csv (motion_file motion/v2/magnetic_field.json)
sh tools/bake_all.sh magnetic_field       # bake, sample, geometric report, export GLB
python3 tools/validation_summary.py
```

Then mark `retarget_check = pass` and set `validation_report` in the registry, and send the sign for
interpreter review.

**First-time setup**

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Download `face_landmarker.task` from Google's MediaPipe Face Landmarker page into `models/`.

**A new lesson:** copy `player/lessons/photosynthesis.json`. Every section needs a `caption`; an `isl`
slot is either `{"status": "available", "sign": <one recording>, "type": "recorded_explanation" |
"interpreter_recording", "author": ...}` or `{"status": "awaiting_interpreter"}`. `check_registry.py`
validates it.

**Recording advice** for new or clearer signs and for interpreter explanations:

- film chest-up, at 50–60 fps and 1280×720 or higher;
- use bright, even light and a plain background;
- start and end with the hands at rest.

### Project layout

```
isl_avatar/
├── player/                    the learning page (index.html, player.js, player.css, lessons/, registry.json)
├── registry/signs.csv         the sign record (generated registry.json comes from it)
├── tools/
│   ├── extract_landmarks.py   MediaPipe body / two hand detectors / face extraction
│   ├── motion_qc.py           quality check (gaps, depth flips, recording warnings)
│   ├── retarget_math.py       pose maths, pure Python and unit-tested
│   ├── retarget_blender.py    bake signs, export the GLB (Blender)
│   ├── retarget_config.json   every tuned value, with the measurement behind it
│   ├── bake_all.sh            re-bake + validate every passing sign
│   ├── animation_validator.py sample a baked clip (Blender)
│   ├── motion_metrics.py      joint angles, palm orientation, contact, DTW
│   ├── motion_report.py       per-sign geometric report and plots
│   ├── rig_validator.py       rig test poses, interpenetration, joint limits (Blender)
│   ├── facial_validator.py    52-shape face audit (Blender)
│   ├── validation_summary.py  reports/VALIDATION_SUMMARY.md
│   ├── check_registry.py      stages, VERIFIED, lesson validation
│   ├── create_avatar.py, render_preview.py, compare_frames.py, fetch_dictionary.py, fetch_include.py
│   └── bone_maps/mixamo.json
├── avatar/                    avatar_source.blend, avatar.glb, archive_v1/
├── motion/v2/                 extracted motion (current); motion/ = first pipeline
├── reports/                   v2/<sign>/, baseline/, rig/, face/, VALIDATION_SUMMARY.md
├── references/                original videos (not for redistribution; git-ignored)
└── tests/                     unit tests
```

### Tests

```bash
python3 -m unittest discover tests
```

All 70 tests pass. They cover:

- registry stages and rules;
- lesson validation;
- QC, including depth flips;
- hand, thumb and finger retargeting, and joint limits;
- shoulders, neck and SLERP;
- metrics and DTW;
- face calibration.

The Blender tools are checked by running them. Their results are in `reports/`.

---

## Sources, permissions and credits

| Source | Used for | Licence / permission |
| --- | --- | --- |
| **ISLRTC** Indian Sign Language dictionary videos (team's shared folders) | All signs on the avatar | Permission obtained by the project team (recorded 6 Nov 2026). Keep a copy with the project records. |
| CISLR, IIT Kanpur (Hugging Face) | Early tests; a second copy of `magnet` | AFL-3.0; clips originate from the ISLRTC dictionary |
| INCLUDE, AI4Bharat (Zenodo) | Early pipeline tests | CC BY 4.0 |
| MakeHuman / MPFB assets | Avatar body, skin, hair, clothes, face shapes | CC0 assets; MPFB tool is GPL |
| Google MediaPipe | Landmark and face-expression extraction | Apache 2.0 |
| three.js | 3D rendering on the page | MIT |

---

## Known limits

- **Not yet verified by an interpreter.** Every sign is "Draft".
- **Step explanations are missing** until an interpreter records them. The page says so, not guesses.
- **Geometric checks measure copying, not correctness.** The tracking itself can be wrong; the
  interpreter is the judge.
- **Thumb twist follows the hand.** The tracker's thumb roll proved unreliable. The thumb's
  direction at every joint follows the signer.
- **Thumb contacts:** where the thumb presses the side of the index finger (make, food, computer),
  the avatar's thumb still sits partly inside the finger in some frames, after an automatic
  correction that halved the overlap.
- **Air and gravity** need new recordings.
- **No ISLRTC sign found** for plant (on its own) or root; the ISLRTC chlorophyll, stomata, energy, gases and
  plant-nutrition explanations fail the 3-frame tracking limit (hands lost 4–39 frames). Not shown rather than guessed.
- **Kannada captions and narration are a draft translation** and need a fluent Kannada speaker's check.
- **Brow movement is subtle** on this face. The interpreter should judge whether it reads clearly.
- **The page runs locally only.**

## Next steps

1. **Interpreter review** in `?review=1`, following [INTERPRETER_REVIEW_GUIDE.md](INTERPRETER_REVIEW_GUIDE.md).
2. **Interpreter recordings**, one per chapter, from [INTERPRETER_RECORDING_SHEET.md](INTERPRETER_RECORDING_SHEET.md), plus the signs for plant, root, chlorophyll, stomata and air.
3. **Hosting** for the school.
4. **More lessons** from the survey results.

## Lesson v3: one chapter per idea (12 Nov 2026)

After the school visit the team asked for every idea (Sun, water, soil, leaf, plant, oxygen, carbon
dioxide, chlorophyll) to be shown and explained on its own, like a teaching video. Each chapter now:

1. shows the idea's word in English and Kannada with its ISLRTC sign, played once as a single word;
2. plays the ISL explanation, when a real signed recording exists (never assembled from dictionary signs);
3. tells the idea in 4–5 numbered steps; each step changes the animated picture (`player/scenes.js`),
   shows the English and Kannada caption and plays that step's narration with lip-sync.

**Examples (12 Nov 2026, from the school visit):** students could not tell which thing we meant
(leaf, plant, stem, tree, bush …). Each chapter now has example steps: a gallery of drawn examples with
English and Kannada names, and ✓/✗ cards for "is it a …?" (`player/icons.js`, `showGallery` in `player/scenes.js`).

**Sign-first (13 Nov 2026, school feedback):** no voice-driven lip-sync (the avatar keeps the ISLRTC
signer's own face); the voice is off by default and offered only for hearing teachers. Every step shows
**word cards**: picture, word and meaning in English and Kannada, and a ✋ ISL sign for the 13 words with
a checked ISLRTC sign (28 more words are picture cards until an interpreter adds their signs). ▶ Play
signs each step's main word on its own.

**Student view vs team view:** the page shows students only the lesson (avatar, picture, captions,
word cards, controls). Team details (sign status, reasons a sign is missing, translation status,
the original ISLRTC video) appear with `?review=1`.

**▶ Play** runs the whole lesson; ◀ ▶ (or the arrow keys) step through it; the step dots jump within a chapter.
Pictures: `player/scenes.js` + `player/scenes.css`. Narration: `tools/make_narration.py` (one clip per step).
The lesson checker (`tools/check_registry.py`) requires a chapter for each of the eight ideas, English and
Kannada text for every step, and a reason wherever a sign is missing. The previous lesson is in
`player/lessons_archive/`.

## Decisions log

| Date | Decision |
| --- | --- |
| 3 Nov 2026 | The avatar only performs real recorded ISL; no AI-generated signs. |
| 4 Nov 2026 | Avatar built with MPFB and CC0 assets. |
| 6 Nov 2026 | Avatar changed to a woman with fair skin. |
| 6 Nov 2026 | The quality limit stays at 3 untracked frames in a row. |
| 6 Nov 2026 | ISLRTC permission recorded for the dictionary videos. |
| 6 Nov 2026 | Students no longer see recorded videos; the avatar and the animation explain the topic. |
| 6 Nov 2026 | Quality-check exception for the ISLRTC photosynthesis explanation (one 4-frame gap). |
| 6 Nov 2026 | The avatar signs on the main page under a "Draft" note until verified. |
| 7 Nov 2026 | Steps no longer chain dictionary signs; each waits for an interpreter-authored explanation. |
| 7 Nov 2026 | Depth-flipped frames count as lost; anatomical joint limits; face neutral calibration. |
| 7 Nov 2026 | Photosynthesis QC exception reconfirmed by the team for its new 4-frame gap (frames 198–201). |
