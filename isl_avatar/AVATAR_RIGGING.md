# Avatar and rig

## The avatar

| Part | What it is |
| --- | --- |
| Body | MPFB 2.0.18 (MakeHuman for Blender) with CC0 MakeHuman assets. A young woman with fair skin, brown eyes, and dark hair tied back (never over the face or hands). Near-black T-shirt and trousers, for contrast with the hands. Built by `tools/create_avatar.py`. |
| Skeleton | Mixamo layout, 52 bones: hips, 3 spine bones, neck, head, collarbones, arms, legs, and **3 bones for each finger and thumb** (30 hand bones). |
| Face | 52 ARKit shape keys on the face mesh (`Interpreter`). Secondary meshes carry the shapes that move them: eyebrows (25), eyelashes (25), eyes (8 gaze shapes), teeth (4), tongue (5), ponytail (24). |
| Eyes | No eye bones. Gaze comes from the eight `eyeLook*` shapes, which move the eyeballs (2.9–5.8 mm at full strength) and the lids. |
| Files | `avatar/avatar_source.blend` is the working file, with one NLA track per sign plus `idle`. `avatar/avatar.glb` (about 18 MB) is what the page loads. Older versions are in `avatar/archive_v1/`. |

## How motion reaches the bones

All of this lives in `tools/retarget_math.py`, which is pure Python and unit-tested. Blender only
applies the result (`tools/retarget_blender.py`). The bone map `tools/bone_maps/mixamo.json` names
the 43 bones used.

| Bones | Driven by | Notes |
| --- | --- | --- |
| Hips | Not animated | The avatar stands; the dictionary signers stand still. |
| Spine2 (chest) | Shoulder and hip line | Upright frame from both. |
| Collarbones | Shoulder lift vs the signer's own median | −10°…+25°, about the chest's forward axis. |
| Upper arm, forearm | Two-bone IK to a body-relative wrist target | Elbow bends towards the signer's elbow side. The shoulder rides on the collarbone. |
| Hand | Palm frame (wrist, index, middle, pinky knuckles) | Full rotation, relative to the avatar's rest palm. |
| Fingers (index–pinky), 3 bones each | Full frame per bone: along the bone, rolled by the knuckle line | Keeps twist. Limited to 105/115/90° per joint relative to the parent. |
| Thumb, 3 bones | Swing chain: each bone takes its parent's rotation plus the smallest turn onto the tracked thumb direction | No roll reference can flip it, and opposition is kept. Limited to 70/70/90°. Then the overlap correction (below). |
| Neck, head | Face transform | The neck takes 40% of the turn (SLERP), the head the rest. |
| Face shapes | 52 scores per frame, neutral-calibrated | See [Face](#face). |

Rotations are computed relative to the avatar's own rest pose, from geometry. They therefore do
not depend on how the bone axes of a particular rig were set up. Another rig needs only a new bone
map.

## Thumb overlap correction (`tools/hand_collision.py`)

When the signer's thumb touches a finger, copying the directions onto a hand with different
proportions can leave the avatar's thumb partly inside that finger. After each sign is baked:

1. Each frame is posed with only that sign's clip active.
2. Overlap is measured with per-segment convex hulls (as in the rig check).
3. The thumb's base joint is turned, then if needed its middle joint, by the smallest angle that
   moves the overlapping points out. All overlaps push at once, weighted by depth, so a thumb
   pressed between two fingers does not bounce between them. Each joint turns at most 25°.
4. The best pose found is kept; corrections are eased over 2 frames before and after.

Settings: `thumb_collision` in `retarget_config.json`. The bake log prints, per hand, how many
frames were corrected, the deepest overlap before and after, and how many frames stay above 2 mm.
Result on the 13 signs: frames passing through 1,452 → 810. Key-grip contacts (thumb against the
side of the index finger) are only partly resolved within the 25° limit.

## Rig validation (`tools/rig_validator.py`)

Run:

```bash
blender -b avatar/avatar_source.blend --python tools/rig_validator.py -- \
    --bone-map tools/bone_maps/mixamo.json --out reports/rig --renders
```

What it does:

1. **Hierarchy.** Every mapped bone exists; each finger chain is parented 1 → 2 → 3 → hand.
2. **Which side is the palm** is measured, not assumed. In the baked signs, fingertips approach the
   wrist when real signers flex, and flexion goes towards the palm. This is needed because the two
   hands are mirror images.
3. **Test poses** for each hand, built from the rig's own geometry:
   - rest, fist, spread, thumb opposition, index point;
   - each finger curled alone;
   - wrist flexion/extension (±60°) and radial/ulnar deviation (+20/−30°).
4. **Interpenetration on the deformed skin.**
   - Skin vertices are grouped by the finger segment (bone) that moves them most.
   - Each segment is replaced by its convex hull (a finger segment is close to convex).
   - For every pair of segments on different fingers, the deepest vertex of one inside the
     other's hull gives the depth (exact for convex shapes).
   - Up to 2 mm counts as *skin contact* (real fingers squash together). Deeper is *passing through*.
   - An earlier nearest-surface test on open patches of skin gave values that piled up at its
     search radius, so it was replaced.
5. **Anatomical limits** on the 15 joint angles of each hand.
6. **Every baked sign, every frame**: frames over the joint limits, frames with skin contact,
   frames passing through, and the deepest overlap.
7. **Controls**: two impossible poses (index finger pushed through the middle finger; fingers
   curled past their range). If either is missed, the run reports `detector_controls_passed: false`
   and its "clean" results cannot be trusted.

Renders: `reports/rig/pose_<side>_<pose>.png`. Numbers: `reports/rig/rig_report.json`, summarised
in [reports/VALIDATION_SUMMARY.md](reports/VALIDATION_SUMMARY.md).

### Known limits of the rig check

- A convex hull slightly overfills a segment where the skin is concave (the crease at a joint),
  so very shallow depths (below about 1 mm) can come from the hull rather than real overlap. The
  2 mm skin-contact allowance covers this.
- The palm is not compared: its hollow is not convex. A fingertip pressing into the palm is not measured.
- The over-curl control mainly proves the joint-limit check; its fingers barely overlap each other.
- The joint-angle measure is unsigned: bending back too far reads like bending forward too far.
  Both are caught by the limit, but the report cannot tell which happened.
- Segments of the same finger are not compared (they share skin at the joint).

## Face

- **Calibration.** MediaPipe reads some relaxed faces as partly squinting or frowning. On the
  ISLRTC "magnet" signer at rest: squint 0.24, brow-down 0.36, smile 0.31. The avatar then looked
  half asleep. Each clip's **neutral** is now the median score of every shape over the frames where
  both hands rest. It is subtracted and the rest rescaled to 0–1, so a real raised brow still
  reaches full strength. Set `face.calibration` to `"none"` in `retarget_config.json` to key raw
  scores.
- **Gains.** Per-shape gains are available in the config. All are 1.0; change one only after
  checking the renders.
- **Validation** (`tools/facial_validator.py`): presence, size, region and left/right symmetry of
  every shape, gaze, secondary meshes following the skin under them, and face/body timeline sync.
  Renders are in `reports/face/shape_<name>.png`.

## Rebuilding the avatar

Edit `LOOK` at the top of `tools/create_avatar.py`, then:

```bash
blender --background --python tools/create_avatar.py
sh tools/bake_all.sh
```

The builder handles four known traps:

- the rig must exist before clothes and hair are added;
- hidden MPFB helper geometry must be deleted (the web export would show it);
- skin and clothes are made opaque;
- hair, lashes and cornea keep their transparency.
