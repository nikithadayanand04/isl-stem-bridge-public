# Interpreter review guide

For the qualified ISL interpreter, or Deaf ISL expert, who reviews the avatar. Your decision is the
only thing that can mark a sign as correct. The software's measurements cannot.

## What you are checking

The avatar copies the movement of ISLRTC dictionary signers, tracked from video. The team has
already checked that the copy follows the tracked movement closely: finger bends, palm direction,
hand position, contact and timing. What only you can judge:

1. **Is it the right sign, correctly formed?** Check five things:
   - handshape;
   - orientation;
   - location;
   - movement;
   - non-manual features (face, mouth, eyebrows, head).
2. **Is it clear and natural** enough for Deaf students to read?
3. **For the photosynthesis explanation:** is it an accurate, age-appropriate ISL explanation?
4. **Facial grammar:** does the avatar's face carry what the signer's face carries?

Single-camera tracking is weakest at palm direction, finger depth when fingers hide each other, and
small mouth shapes. Please look closely at those.

## How to open the review view

On the project computer:

```bash
cd isl_avatar
python3 tools/check_registry.py
python3 -m http.server 8811
```

Then open **http://localhost:8811/player/?review=1**.

- A red banner confirms review mode.
- When the avatar signs, the original ISLRTC video plays below for comparison.
- Use **Speed 0.5×**, **Hands close-up** and **↻ Replay sign** as often as you need.
- **Key words in ISL** lets you play each vocabulary sign on its own.

For a frame-by-frame look, each sign has a report with the original and avatar side by side:
`reports/v2/<sign>/report.md`.

## What to review

| Sign id | Word | Where it is used |
| --- | --- | --- |
| photosynthesis | ISLRTC explanation of photosynthesis (13 s) | Introduction and recap |
| leaf, sun, water, carbon_dioxide_sign_2, oxygen_sign_2, sugar, food, make | Vocabulary | Key words |
| magnet, magnet_sign_2, electricity, computer | Vocabulary for later lessons | Not on the page yet |

Two signs for magnet are baked. Please say which one the lesson should use, or whether both are fine.

## How to record your decision

For each sign, give the team:

- **Result:**
  - `approved`: correct and clear, can be shown to students as verified;
  - `changes_needed`: the sign is right but something on the avatar is off (say what and where:
    handshape, palm, position, movement, face, timing);
  - `rejected`: the wrong sign, or not usable.
- **Your name**, as you want it recorded (with your permission), and the **date**.
- **Notes:** anything the team should fix or re-record.

The team enters this in `registry/signs.csv` (`interpreter`, `interpreter_review`, `review_date`,
`notes`) and runs `python3 tools/check_registry.py`. A sign shows as verified only after your approval
**and** all the technical checks.

## The explanations still needed from you

Each step of the lesson has an empty ISL slot marked "waiting for a recording by an ISL interpreter".
The team will not build ISL sentences by stringing dictionary signs together. Correct ISL grammar,
spatial reference and classifiers need a signer.

We need a short recorded ISL explanation for each of these, in your own words:

| Step | What it must explain |
| --- | --- |
| The big idea | Plants make their own food. They need light, water and carbon dioxide, and give out oxygen. |
| 1 · Light | Leaves catch light from the Sun; light gives the energy to make food. |
| 2 · Water | Roots take in water from the soil; water travels up the stem to the leaves. |
| 3 · Carbon dioxide in | Tiny openings in the leaves take in carbon dioxide from the air. |
| 4 · Making sugar | In the leaf, light energy joins water and carbon dioxide to make sugar, the plant's food. |
| 5 · Oxygen out | The leaf gives out oxygen; people and animals breathe it. |
| 6 · Growing | The plant uses sugar for energy and to build new leaves, stems and roots. |

**Recording tips:**

- film chest-up so the hands and face fill the frame, with room for the signing space;
- 50–60 frames per second, 1280×720 or higher;
- bright, even light; a plain background; clothing that contrasts with the hands;
- one take per step, starting and ending with the hands at rest.

Each recording goes through the same pipeline: extraction, quality check, bake, comparison. It then
comes back to you for review on the avatar.

**Signs missing from the vocabulary.** Air (the ISLRTC recording failed the quality check), roots,
energy and grow have no recording yet. If you can sign them for a recording, the avatar can learn them.
