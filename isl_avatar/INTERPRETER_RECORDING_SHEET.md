# ISL recording sheet: Photosynthesis: how plants make their own food

Generated from `player/lessons/photosynthesis.json` by `tools/recording_sheet.py`. Do not edit by hand.

One recording per chapter, by a qualified ISL interpreter or Deaf ISL expert, explaining the chapter
in natural ISL (not word for word). The steps below are the content to cover, in order. The avatar
copies the recording exactly; the student sees it beside the animated picture.

## How to record

- Plain, even background (grey or blue) and even light from the front; no shadows on the hands.
- Camera fixed on a stand at chest height, landscape, 1920×1080, 25 fps or more.
- Frame from just above the head to the hips, signer in the middle; elbows and hands always in the picture,
  also when the arms are raised. (Hands leaving the picture make the recording fail the quality check.)
- Dark plain top, no rings or bangles. Start and end with the hands resting at the sides for one second.
- Steady, clear signing at teaching speed. Fast movement blurs the hands: the tracker loses them.
- Save as `references/interp_<chapter id>.mp4` (chapter ids below).

## How a recording reaches the avatar

```
.venv/bin/python tools/extract_landmarks.py references/interp_soil.mp4 --sign-id interp_soil \
    --out-dir motion/v2 --face-model models/face_landmarker.task      # prints motion_qc = pass/fail
# add a row to registry/signs.csv (category B, isl_source = the interpreter, attribution, consent)
sh tools/bake_all.sh interp_soil                                    # bake, validate, export
.venv/bin/python tools/visual_loop_check.py interp_soil              # avatar vs recording
```
Then set the chapter's `isl` in the lesson to
`{"status": "available", "sign": "interp_soil", "type": "interpreter_recording", "author": "<name>"}`
and run `python3 tools/check_registry.py`. A recording that fails a check is re-recorded, never patched.

## Chapters

### What is photosynthesis? · ದ್ಯುತಿಸಂಶ್ಲೇಷಣೆ ಎಂದರೇನು?  (chapter id `introduction`)

- ISL sign for the idea: `photosynthesis` (ISLRTC)
- ISL explanation now: ISLRTC recording `photosynthesis` (ISLRTC's own short explanation of photosynthesis. It is not a word-for-word translation of these captions.)

| Step | Content (English) | ಕನ್ನಡ |
| --- | --- | --- |
| 1 | All living things need food to live and grow. | ಎಲ್ಲಾ ಜೀವಿಗಳಿಗೂ ಬದುಕಲು ಮತ್ತು ಬೆಳೆಯಲು ಆಹಾರ ಬೇಕು. |
| 2 | People, animals, birds, fish and plants are all living things. They all need food. | ಮನುಷ್ಯರು, ಪ್ರಾಣಿಗಳು, ಪಕ್ಷಿಗಳು, ಮೀನುಗಳು ಮತ್ತು ಸಸ್ಯಗಳು ಎಲ್ಲವೂ ಜೀವಿಗಳು. ಎಲ್ಲಕ್ಕೂ ಆಹಾರ ಬೇಕು. |
| 3 | People and animals find food and eat it. A plant cannot walk to find food. | ಮನುಷ್ಯರು ಮತ್ತು ಪ್ರಾಣಿಗಳು ಆಹಾರವನ್ನು ಹುಡುಕಿ ತಿನ್ನುತ್ತವೆ. ಸಸ್ಯವು ಆಹಾರ ಹುಡುಕಿಕೊಂಡು ನಡೆಯಲಾರದು. |
| 4 | So a plant makes its own food, in its leaves. | ಆದ್ದರಿಂದ ಸಸ್ಯವು ತನ್ನ ಆಹಾರವನ್ನು ತಾನೇ, ತನ್ನ ಎಲೆಗಳಲ್ಲಿ ತಯಾರಿಸುತ್ತದೆ. |
| 5 | This is called photosynthesis. Photo means light. Synthesis means putting things together. | ಇದನ್ನು ದ್ಯುತಿಸಂಶ್ಲೇಷಣೆ ಎನ್ನುತ್ತಾರೆ. ದ್ಯುತಿ ಎಂದರೆ ಬೆಳಕು. ಸಂಶ್ಲೇಷಣೆ ಎಂದರೆ ವಸ್ತುಗಳನ್ನು ಒಟ್ಟುಗೂಡಿಸುವುದು. |
| 6 | The plant puts together sunlight, water and carbon dioxide to make food. Let us meet each one. | ಸಸ್ಯವು ಸೂರ್ಯನ ಬೆಳಕು, ನೀರು ಮತ್ತು ಇಂಗಾಲದ ಡೈಆಕ್ಸೈಡ್ ಅನ್ನು ಒಟ್ಟುಗೂಡಿಸಿ ಆಹಾರ ತಯಾರಿಸುತ್ತದೆ. ಬನ್ನಿ, ಒಂದೊಂದನ್ನೂ ಪರಿಚಯ ಮಾಡಿಕೊಳ್ಳೋಣ. |

### The plant · ಸಸ್ಯ  (chapter id `plant`)

- ISL sign for the idea: **missing**: The ISLRTC dictionary folders have no sign for 'plant' on its own (only 'Tree', 'Grow (Plants)' and longer phrases). An interpreter must give the sign; it is not guessed. Please give the sign in the recording.
- ISL explanation now: none. **Please record.**

| Step | Content (English) | ಕನ್ನಡ |
| --- | --- | --- |
| 1 | This is a plant. It has four main parts. | ಇದು ಒಂದು ಸಸ್ಯ. ಇದಕ್ಕೆ ನಾಲ್ಕು ಮುಖ್ಯ ಭಾಗಗಳಿವೆ. |
| 2 | Plants come in many kinds. A tree, a bush, grass, a tulsi plant, a creeper and a cactus are all plants. | ಸಸ್ಯಗಳಲ್ಲಿ ಹಲವು ಬಗೆಗಳಿವೆ. ಮರ, ಪೊದೆ, ಹುಲ್ಲು, ತುಳಸಿ ಗಿಡ, ಬಳ್ಳಿ ಮತ್ತು ಕಳ್ಳಿ ಎಲ್ಲವೂ ಸಸ್ಯಗಳೇ. |
| 3 | The roots grow under the soil. They hold the plant firmly and take in water. | ಬೇರುಗಳು ಮಣ್ಣಿನೊಳಗೆ ಬೆಳೆಯುತ್ತವೆ. ಅವು ಸಸ್ಯವನ್ನು ಗಟ್ಟಿಯಾಗಿ ಹಿಡಿದುಕೊಳ್ಳುತ್ತವೆ ಮತ್ತು ನೀರನ್ನು ಹೀರಿಕೊಳ್ಳುತ್ತವೆ. |
| 4 | The stem holds the plant up. Like a pipe, it carries water up to the leaves. | ಕಾಂಡವು ಸಸ್ಯವನ್ನು ನೇರವಾಗಿ ನಿಲ್ಲಿಸುತ್ತದೆ. ಕೊಳವೆಯಂತೆ ಅದು ನೀರನ್ನು ಎಲೆಗಳವರೆಗೆ ಮೇಲಕ್ಕೆ ಸಾಗಿಸುತ್ತದೆ. |
| 5 | The leaves are flat and green. They are the plant's kitchen: food is made here. | ಎಲೆಗಳು ಚಪ್ಪಟೆಯಾಗಿ ಹಸಿರಾಗಿವೆ. ಅವು ಸಸ್ಯದ ಅಡುಗೆಮನೆ: ಆಹಾರ ಇಲ್ಲಿಯೇ ತಯಾರಾಗುತ್ತದೆ. |
| 6 | The flower makes seeds, and new plants grow from the seeds. | ಹೂವು ಬೀಜಗಳನ್ನು ಉತ್ಪಾದಿಸುತ್ತದೆ. ಬೀಜಗಳಿಂದ ಹೊಸ ಸಸ್ಯಗಳು ಬೆಳೆಯುತ್ತವೆ. |
| 7 | A tree has the same parts. Its trunk is a big, hard stem. Its roots are under the ground. | ಮರಕ್ಕೂ ಇದೇ ಭಾಗಗಳಿವೆ. ಅದರ ಬುಡ ಅಥವಾ ಕಾಂಡ ದೊಡ್ಡ, ಗಟ್ಟಿಯಾದ ಕಾಂಡ. ಅದರ ಬೇರುಗಳು ನೆಲದ ಕೆಳಗಿವೆ. |

### The Sun · ಸೂರ್ಯ  (chapter id `sun`)

- ISL sign for the idea: `sun` (ISLRTC)
- ISL explanation now: none. **Please record.**

| Step | Content (English) | ಕನ್ನಡ |
| --- | --- | --- |
| 1 | This is the Sun. It is a star: a huge ball of very hot gas. | ಇದು ಸೂರ್ಯ. ಸೂರ್ಯ ಒಂದು ನಕ್ಷತ್ರ: ತುಂಬಾ ಬಿಸಿಯಾದ ಅನಿಲದ ದೊಡ್ಡ ಚೆಂಡು. |
| 2 | The Sun gives out light and heat. | ಸೂರ್ಯನು ಬೆಳಕು ಮತ್ತು ಶಾಖವನ್ನು ಕೊಡುತ್ತಾನೆ. |
| 3 | We feel the Sun every day: it dries our clothes and lights up the day. | ನಾವು ದಿನವೂ ಸೂರ್ಯನನ್ನು ಅನುಭವಿಸುತ್ತೇವೆ: ಅದು ನಮ್ಮ ಬಟ್ಟೆ ಒಣಗಿಸುತ್ತದೆ, ಹಗಲನ್ನು ಬೆಳಗಿಸುತ್ತದೆ. |
| 4 | Sunlight travels about 15 crore kilometres to reach the Earth. It takes about 8 minutes. | ಸೂರ್ಯನ ಬೆಳಕು ಸುಮಾರು 15 ಕೋಟಿ ಕಿಲೋಮೀಟರ್ ಪ್ರಯಾಣಿಸಿ ಭೂಮಿಯನ್ನು ತಲುಪುತ್ತದೆ. ಅದಕ್ಕೆ ಸುಮಾರು 8 ನಿಮಿಷ ಬೇಕು. |
| 5 | When sunlight falls on a leaf, the leaf catches its energy. | ಸೂರ್ಯನ ಬೆಳಕು ಎಲೆಯ ಮೇಲೆ ಬಿದ್ದಾಗ, ಎಲೆ ಅದರ ಶಕ್ತಿಯನ್ನು ಹಿಡಿದುಕೊಳ್ಳುತ್ತದೆ. |
| 6 | Without light, a plant cannot make food. That is why plants grow towards light. | ಬೆಳಕಿಲ್ಲದೆ ಸಸ್ಯವು ಆಹಾರ ತಯಾರಿಸಲಾರದು. ಅದಕ್ಕೇ ಸಸ್ಯಗಳು ಬೆಳಕಿನ ಕಡೆಗೆ ಬೆಳೆಯುತ್ತವೆ. |
| 7 | A plant kept in the dark turns pale and weak. A plant in sunlight stays green and strong. | ಕತ್ತಲಲ್ಲಿ ಇಟ್ಟ ಸಸ್ಯ ಬಿಳಿಚಿಕೊಂಡು ದುರ್ಬಲವಾಗುತ್ತದೆ. ಬಿಸಿಲಿನಲ್ಲಿರುವ ಸಸ್ಯ ಹಸಿರಾಗಿ ಗಟ್ಟಿಯಾಗಿರುತ್ತದೆ. |

### Soil · ಮಣ್ಣು  (chapter id `soil`)

- ISL sign for the idea: `soil` (ISLRTC)
- ISL explanation now: none. **Please record.**

| Step | Content (English) | ಕನ್ನಡ |
| --- | --- | --- |
| 1 | This is soil, the top layer of the ground. | ಇದು ಮಣ್ಣು, ನೆಲದ ಮೇಲಿನ ಪದರ. |
| 2 | Soil is made of tiny bits of rock, sand and clay, mixed with rotting leaves called humus. | ಮಣ್ಣು ಕಲ್ಲು, ಮರಳು ಮತ್ತು ಜೇಡಿಮಣ್ಣಿನ ಸಣ್ಣ ಕಣಗಳಿಂದ ಆಗಿದೆ. ಅದರಲ್ಲಿ ಕೊಳೆತ ಎಲೆಗಳು, ಅಂದರೆ ಹ್ಯೂಮಸ್, ಬೆರೆತಿರುತ್ತದೆ. |
| 3 | Soils have different colours. In Karnataka we see red soil and black soil. There is also sandy soil and clay soil. | ಮಣ್ಣಿನಲ್ಲಿ ಬೇರೆ ಬೇರೆ ಬಣ್ಣಗಳಿವೆ. ಕರ್ನಾಟಕದಲ್ಲಿ ಕೆಂಪು ಮಣ್ಣು ಮತ್ತು ಕಪ್ಪು ಮಣ್ಣು ಕಾಣುತ್ತೇವೆ. ಮರಳು ಮಣ್ಣು ಮತ್ತು ಜೇಡಿಮಣ್ಣು ಕೂಡ ಇವೆ. |
| 4 | Earthworms and other tiny living things live in the soil and keep it loose. | ಎರೆಹುಳುಗಳು ಮತ್ತು ಇತರ ಸಣ್ಣ ಜೀವಿಗಳು ಮಣ್ಣಿನಲ್ಲಿ ವಾಸಿಸಿ ಅದನ್ನು ಸಡಿಲವಾಗಿಡುತ್ತವೆ. |
| 5 | Between the bits there are small spaces. They hold water and air. | ಕಣಗಳ ನಡುವೆ ಸಣ್ಣ ಖಾಲಿ ಜಾಗಗಳಿವೆ. ಅವುಗಳಲ್ಲಿ ನೀರು ಮತ್ತು ಗಾಳಿ ಇರುತ್ತದೆ. |
| 6 | Soil has minerals too. The roots take in water and minerals from the soil. | ಮಣ್ಣಿನಲ್ಲಿ ಖನಿಜಗಳೂ ಇವೆ. ಬೇರುಗಳು ಮಣ್ಣಿನಿಂದ ನೀರು ಮತ್ತು ಖನಿಜಗಳನ್ನು ಹೀರಿಕೊಳ್ಳುತ್ತವೆ. |

### Water · ನೀರು  (chapter id `water`)

- ISL sign for the idea: `water` (ISLRTC)
- ISL explanation now: none. **Please record.**

| Step | Content (English) | ಕನ್ನಡ |
| --- | --- | --- |
| 1 | Rain falls and soaks into the soil. | ಮಳೆ ಬಿದ್ದು ಮಣ್ಣಿನೊಳಗೆ ಇಂಗುತ್ತದೆ. |
| 2 | Plants get water from rain, from rivers and wells, and when we water them. | ಸಸ್ಯಗಳಿಗೆ ಮಳೆಯಿಂದ, ನದಿ ಮತ್ತು ಬಾವಿಗಳಿಂದ, ಮತ್ತು ನಾವು ನೀರು ಹಾಕಿದಾಗ ನೀರು ಸಿಗುತ್ತದೆ. |
| 3 | Tiny root hairs on the roots take in the water. | ಬೇರುಗಳ ಮೇಲಿನ ಸಣ್ಣ ಬೇರುಕೂದಲುಗಳು ನೀರನ್ನು ಹೀರಿಕೊಳ್ಳುತ್ತವೆ. |
| 4 | The water moves up the stem through thin tubes, like a drink going up a straw. | ನೀರು ಕಾಂಡದೊಳಗಿನ ತೆಳುವಾದ ಕೊಳವೆಗಳ ಮೂಲಕ, ಸ್ಟ್ರಾದಲ್ಲಿ ಪಾನೀಯ ಮೇಲೇರುವಂತೆ, ಮೇಲಕ್ಕೆ ಸಾಗುತ್ತದೆ. |
| 5 | The tubes spread into each leaf as veins, and the water reaches the leaf. | ಈ ಕೊಳವೆಗಳು ಪ್ರತಿ ಎಲೆಯೊಳಗೆ ನರಗಳಾಗಿ ಹರಡುತ್ತವೆ, ಹೀಗೆ ನೀರು ಎಲೆಯನ್ನು ತಲುಪುತ್ತದೆ. |
| 6 | The leaf uses some water to make food. Extra water goes into the air as water vapour. | ಎಲೆ ಸ್ವಲ್ಪ ನೀರನ್ನು ಆಹಾರ ತಯಾರಿಸಲು ಬಳಸುತ್ತದೆ. ಹೆಚ್ಚಿನ ನೀರು ನೀರಾವಿಯಾಗಿ ಗಾಳಿಗೆ ಹೋಗುತ್ತದೆ. |

### The leaf · ಎಲೆ  (chapter id `leaf`)

- ISL sign for the idea: `leaf` (ISLRTC)
- ISL explanation now: none. **Please record.**

| Step | Content (English) | ಕನ್ನಡ |
| --- | --- | --- |
| 1 | This is a leaf. It is thin, flat and wide, so it can catch a lot of sunlight. | ಇದು ಒಂದು ಎಲೆ. ಅದು ತೆಳುವಾಗಿ, ಚಪ್ಪಟೆಯಾಗಿ, ಅಗಲವಾಗಿದೆ. ಹಾಗಾಗಿ ಅದು ಹೆಚ್ಚು ಸೂರ್ಯನ ಬೆಳಕನ್ನು ಹಿಡಿಯಬಲ್ಲದು. |
| 2 | Leaves have many shapes and sizes, but they are all leaves. | ಎಲೆಗಳಲ್ಲಿ ಹಲವು ಆಕಾರ ಮತ್ತು ಗಾತ್ರಗಳಿವೆ, ಆದರೆ ಅವೆಲ್ಲವೂ ಎಲೆಗಳೇ. |
| 3 | The lines on the leaf are veins. They bring water in and take food out. | ಎಲೆಯ ಮೇಲಿನ ಗೆರೆಗಳು ನರಗಳು. ಅವು ನೀರನ್ನು ಒಳಗೆ ತರುತ್ತವೆ ಮತ್ತು ಆಹಾರವನ್ನು ಹೊರಗೆ ಒಯ್ಯುತ್ತವೆ. |
| 4 | Is it a leaf? A leaf is flat and green and grows from the stem. A flower, a stem and a fruit are not leaves. | ಇದು ಎಲೆಯೇ? ಎಲೆ ಚಪ್ಪಟೆಯಾಗಿ ಹಸಿರಾಗಿರುತ್ತದೆ, ಕಾಂಡದಿಂದ ಬೆಳೆಯುತ್ತದೆ. ಹೂವು, ಕಾಂಡ ಮತ್ತು ಹಣ್ಣು ಎಲೆಗಳಲ್ಲ. |
| 5 | Under the leaf there are tiny holes called stomata. Air goes in and out through them. | ಎಲೆಯ ಕೆಳಭಾಗದಲ್ಲಿ ಪತ್ರರಂಧ್ರಗಳು ಎಂಬ ಸಣ್ಣ ರಂಧ್ರಗಳಿವೆ. ಅವುಗಳ ಮೂಲಕ ಗಾಳಿ ಒಳಗೆ ಹೋಗುತ್ತದೆ ಮತ್ತು ಹೊರಗೆ ಬರುತ್ತದೆ. |
| 6 | A leaf is made of tiny cells. They are so small that we need a microscope to see them. | ಎಲೆ ಸಣ್ಣ ಸಣ್ಣ ಜೀವಕೋಶಗಳಿಂದ ಮಾಡಲ್ಪಟ್ಟಿದೆ. ಅವು ಎಷ್ಟು ಚಿಕ್ಕವೆಂದರೆ ಅವುಗಳನ್ನು ನೋಡಲು ಸೂಕ್ಷ್ಮದರ್ಶಕ ಬೇಕು. |
| 7 | The cells are full of green chlorophyll. This is where food is made. | ಈ ಜೀವಕೋಶಗಳಲ್ಲಿ ಹಸಿರು ಪತ್ರಹರಿತ್ತು ತುಂಬಿದೆ. ಆಹಾರ ತಯಾರಾಗುವುದು ಇಲ್ಲಿಯೇ. |

### Chlorophyll · ಪತ್ರಹರಿತ್ತು  (chapter id `chlorophyll`)

- ISL sign for the idea: `chlorophyll` (ISLRTC)
- ISL explanation now: none. **Please record.**

| Step | Content (English) | ಕನ್ನಡ |
| --- | --- | --- |
| 1 | Let us look inside one leaf cell with a microscope. | ಸೂಕ್ಷ್ಮದರ್ಶಕದಿಂದ ಒಂದು ಎಲೆಯ ಜೀವಕೋಶದ ಒಳಗೆ ನೋಡೋಣ. |
| 2 | The small green parts are called chloroplasts. | ಈ ಸಣ್ಣ ಹಸಿರು ಭಾಗಗಳನ್ನು ಹರಿತ್ತಿಲುಗಳು ಅಥವಾ ಕ್ಲೋರೋಪ್ಲಾಸ್ಟ್‌ಗಳು ಎನ್ನುತ್ತಾರೆ. |
| 3 | Chloroplasts contain chlorophyll, a green colouring. | ಹರಿತ್ತಿಲುಗಳಲ್ಲಿ ಪತ್ರಹರಿತ್ತು ಎಂಬ ಹಸಿರು ಬಣ್ಣದ ವಸ್ತು ಇದೆ. |
| 4 | Chlorophyll catches the energy of sunlight, like a solar panel. | ಸೌರ ಫಲಕದಂತೆ, ಪತ್ರಹರಿತ್ತು ಸೂರ್ಯನ ಬೆಳಕಿನ ಶಕ್ತಿಯನ್ನು ಹಿಡಿಯುತ್ತದೆ. |
| 5 | Sunlight has many colours. Chlorophyll takes in red and blue light and gives back green light. That is why leaves look green. | ಸೂರ್ಯನ ಬೆಳಕಿನಲ್ಲಿ ಹಲವು ಬಣ್ಣಗಳಿವೆ. ಪತ್ರಹರಿತ್ತು ಕೆಂಪು ಮತ್ತು ನೀಲಿ ಬೆಳಕನ್ನು ಹೀರಿಕೊಂಡು ಹಸಿರು ಬೆಳಕನ್ನು ಹಿಂದಕ್ಕೆ ಕಳುಹಿಸುತ್ತದೆ. ಅದಕ್ಕೇ ಎಲೆಗಳು ಹಸಿರಾಗಿ ಕಾಣುತ್ತವೆ. |
| 6 | Green parts of a plant have chlorophyll: leaves, green stems and raw green fruit. Roots and most flowers do not. | ಸಸ್ಯದ ಹಸಿರು ಭಾಗಗಳಲ್ಲಿ ಪತ್ರಹರಿತ್ತು ಇದೆ: ಎಲೆಗಳು, ಹಸಿರು ಕಾಂಡಗಳು ಮತ್ತು ಹಸಿ ಕಾಯಿಗಳು. ಬೇರುಗಳಲ್ಲಿ ಮತ್ತು ಹೆಚ್ಚಿನ ಹೂವುಗಳಲ್ಲಿ ಇಲ್ಲ. |

### Carbon dioxide · ಇಂಗಾಲದ ಡೈಆಕ್ಸೈಡ್  (chapter id `carbon_dioxide`)

- ISL sign for the idea: `carbon_dioxide_sign_2` (ISLRTC)
- ISL explanation now: none. **Please record.**

| Step | Content (English) | ಕನ್ನಡ |
| --- | --- | --- |
| 1 | Air is a mix of gases. We cannot see them. | ಗಾಳಿ ಅನೇಕ ಅನಿಲಗಳ ಮಿಶ್ರಣ. ಅವುಗಳನ್ನು ನಾವು ನೋಡಲಾರೆವು. |
| 2 | One of these gases is carbon dioxide. People and animals breathe it out. | ಅವುಗಳಲ್ಲಿ ಒಂದು ಇಂಗಾಲದ ಡೈಆಕ್ಸೈಡ್. ಮನುಷ್ಯರು ಮತ್ತು ಪ್ರಾಣಿಗಳು ಅದನ್ನು ಉಸಿರಿನೊಂದಿಗೆ ಹೊರಗೆ ಬಿಡುತ್ತಾರೆ. |
| 3 | Carbon dioxide comes from our breath, from animals' breath, from burning wood and from vehicle smoke. | ಇಂಗಾಲದ ಡೈಆಕ್ಸೈಡ್ ನಮ್ಮ ಉಸಿರಿನಿಂದ, ಪ್ರಾಣಿಗಳ ಉಸಿರಿನಿಂದ, ಕಟ್ಟಿಗೆ ಉರಿಸುವುದರಿಂದ ಮತ್ತು ವಾಹನಗಳ ಹೊಗೆಯಿಂದ ಬರುತ್ತದೆ. |
| 4 | Each tiny bit of carbon dioxide is one carbon joined to two oxygens. We write it C O 2. | ಇಂಗಾಲದ ಡೈಆಕ್ಸೈಡ್‌ನ ಪ್ರತಿಯೊಂದು ಸಣ್ಣ ಕಣದಲ್ಲಿ ಒಂದು ಇಂಗಾಲ ಎರಡು ಆಮ್ಲಜನಕಗಳೊಂದಿಗೆ ಸೇರಿರುತ್ತದೆ. ಅದನ್ನು ಸಿ ಓ ಟು ಎಂದು ಬರೆಯುತ್ತೇವೆ. |
| 5 | Carbon dioxide goes into the leaf through the stomata, the tiny holes under the leaf. | ಇಂಗಾಲದ ಡೈಆಕ್ಸೈಡ್ ಎಲೆಯ ಕೆಳಗಿನ ಸಣ್ಣ ರಂಧ್ರಗಳಾದ ಪತ್ರರಂಧ್ರಗಳ ಮೂಲಕ ಎಲೆಯೊಳಗೆ ಹೋಗುತ್ತದೆ. |
| 6 | Two guard cells open each stoma in the day, and close it at night or when it is very dry. | ಎರಡು ಕಾವಲು ಜೀವಕೋಶಗಳು ಹಗಲಿನಲ್ಲಿ ಪತ್ರರಂಧ್ರವನ್ನು ತೆರೆಯುತ್ತವೆ, ರಾತ್ರಿ ಅಥವಾ ತುಂಬಾ ಒಣ ಹವೆಯಲ್ಲಿ ಮುಚ್ಚುತ್ತವೆ. |

### Making food · ಆಹಾರ ತಯಾರಿಕೆ  (chapter id `making_food`)

- ISL sign for the idea: `sugar` (ISLRTC)
- ISL explanation now: none. **Please record.** (ISLRTC's 'Photosynthesis Process' explanation passes tracking QC but fails the avatar contact check (2 of 5 fingertip contacts missing; limit 25%). It is not played until that is fixed.)

| Step | Content (English) | ಕನ್ನಡ |
| --- | --- | --- |
| 1 | Now the leaf has everything it needs: light energy, water and carbon dioxide. | ಈಗ ಎಲೆಗೆ ಬೇಕಾದ ಎಲ್ಲವೂ ಇದೆ: ಬೆಳಕಿನ ಶಕ್ತಿ, ನೀರು ಮತ್ತು ಇಂಗಾಲದ ಡೈಆಕ್ಸೈಡ್. |
| 2 | In the chloroplasts, the light's energy splits water into hydrogen and oxygen. | ಹರಿತ್ತಿಲುಗಳಲ್ಲಿ ಬೆಳಕಿನ ಶಕ್ತಿ ನೀರನ್ನು ಜಲಜನಕ ಮತ್ತು ಆಮ್ಲಜನಕವಾಗಿ ಒಡೆಯುತ್ತದೆ. |
| 3 | The hydrogen joins with carbon dioxide to make a sugar called glucose. | ಜಲಜನಕವು ಇಂಗಾಲದ ಡೈಆಕ್ಸೈಡ್‌ನೊಂದಿಗೆ ಸೇರಿ ಗ್ಲೂಕೋಸ್ ಎಂಬ ಸಕ್ಕರೆ ಆಗುತ್ತದೆ. |
| 4 | Sugar is the plant's food. The veins carry it to every part of the plant. | ಸಕ್ಕರೆಯೇ ಸಸ್ಯದ ಆಹಾರ. ನರಗಳು ಅದನ್ನು ಸಸ್ಯದ ಪ್ರತಿಯೊಂದು ಭಾಗಕ್ಕೂ ಒಯ್ಯುತ್ತವೆ. |
| 5 | In short: light, water and carbon dioxide make sugar and oxygen. | ಸಂಕ್ಷಿಪ್ತವಾಗಿ: ಬೆಳಕು, ನೀರು ಮತ್ತು ಇಂಗಾಲದ ಡೈಆಕ್ಸೈಡ್‌ನಿಂದ ಸಕ್ಕರೆ ಮತ್ತು ಆಮ್ಲಜನಕ ತಯಾರಾಗುತ್ತವೆ. |

### Oxygen · ಆಮ್ಲಜನಕ  (chapter id `oxygen`)

- ISL sign for the idea: `oxygen_sign_2` (ISLRTC)
- ISL explanation now: none. **Please record.**

| Step | Content (English) | ಕನ್ನಡ |
| --- | --- | --- |
| 1 | When water is split, oxygen is left over. | ನೀರು ಒಡೆದಾಗ ಆಮ್ಲಜನಕ ಉಳಿಯುತ್ತದೆ. |
| 2 | The leaf lets the oxygen out through its stomata. | ಎಲೆ ತನ್ನ ಪತ್ರರಂಧ್ರಗಳ ಮೂಲಕ ಆಮ್ಲಜನಕವನ್ನು ಹೊರಗೆ ಬಿಡುತ್ತದೆ. |
| 3 | The oxygen goes into the air. People and animals breathe it in to live. | ಆಮ್ಲಜನಕ ಗಾಳಿಗೆ ಸೇರುತ್ತದೆ. ಮನುಷ್ಯರು ಮತ್ತು ಪ್ರಾಣಿಗಳು ಬದುಕಲು ಅದನ್ನು ಉಸಿರಾಡುತ್ತಾರೆ. |
| 4 | All living things need oxygen: people, animals, birds, fish in the water, and plants too. | ಎಲ್ಲಾ ಜೀವಿಗಳಿಗೂ ಆಮ್ಲಜನಕ ಬೇಕು: ಮನುಷ್ಯರು, ಪ್ರಾಣಿಗಳು, ಪಕ್ಷಿಗಳು, ನೀರಿನಲ್ಲಿರುವ ಮೀನುಗಳು, ಮತ್ತು ಸಸ್ಯಗಳಿಗೂ ಕೂಡ. |
| 5 | We breathe out carbon dioxide, and plants take it in. Plants and animals help each other. | ನಾವು ಇಂಗಾಲದ ಡೈಆಕ್ಸೈಡ್ ಅನ್ನು ಹೊರಗೆ ಬಿಡುತ್ತೇವೆ, ಸಸ್ಯಗಳು ಅದನ್ನು ಒಳಗೆ ತೆಗೆದುಕೊಳ್ಳುತ್ತವೆ. ಸಸ್ಯಗಳು ಮತ್ತು ಪ್ರಾಣಿಗಳು ಒಂದಕ್ಕೊಂದು ಸಹಾಯ ಮಾಡುತ್ತವೆ. |
| 6 | The oxygen we breathe is made by plants on land and by tiny plants in the sea. | ನಾವು ಉಸಿರಾಡುವ ಆಮ್ಲಜನಕವನ್ನು ನೆಲದ ಮೇಲಿನ ಸಸ್ಯಗಳು ಮತ್ತು ಸಮುದ್ರದ ಸೂಕ್ಷ್ಮ ಸಸ್ಯಗಳು ತಯಾರಿಸುತ್ತವೆ. |

### Growing · ಬೆಳವಣಿಗೆ  (chapter id `growing`)

- ISL sign for the idea: `grow_plants` (ISLRTC)
- ISL explanation now: none. **Please record.**

| Step | Content (English) | ಕನ್ನಡ |
| --- | --- | --- |
| 1 | The plant uses some of its sugar for energy, to stay alive. | ಸಸ್ಯವು ತನ್ನ ಸ್ವಲ್ಪ ಸಕ್ಕರೆಯನ್ನು ಬದುಕಿರಲು ಬೇಕಾದ ಶಕ್ತಿಗಾಗಿ ಬಳಸುತ್ತದೆ. |
| 2 | It uses some sugar to build new leaves, stems and roots. The plant grows. | ಸ್ವಲ್ಪ ಸಕ್ಕರೆಯಿಂದ ಹೊಸ ಎಲೆ, ಕಾಂಡ ಮತ್ತು ಬೇರುಗಳನ್ನು ಕಟ್ಟುತ್ತದೆ. ಹೀಗೆ ಸಸ್ಯ ಬೆಳೆಯುತ್ತದೆ. |
| 3 | Extra sugar is stored as starch, in potatoes, rice grains and bananas. | ಹೆಚ್ಚಾದ ಸಕ್ಕರೆ ಪಿಷ್ಟವಾಗಿ ಆಲೂಗಡ್ಡೆ, ಅಕ್ಕಿ ಕಾಳು ಮತ್ತು ಬಾಳೆಹಣ್ಣಿನಲ್ಲಿ ಸಂಗ್ರಹವಾಗುತ್ತದೆ. |
| 4 | We eat food that plants have stored: potato, carrot, rice, sugarcane, mango and peanut. | ಸಸ್ಯಗಳು ಸಂಗ್ರಹಿಸಿದ ಆಹಾರವನ್ನು ನಾವು ತಿನ್ನುತ್ತೇವೆ: ಆಲೂಗಡ್ಡೆ, ಕ್ಯಾರೆಟ್, ಅಕ್ಕಿ, ಕಬ್ಬು, ಮಾವಿನಹಣ್ಣು ಮತ್ತು ಕಡಲೆಕಾಯಿ. |
| 5 | When we eat plants, we get this stored food and energy. | ನಾವು ಸಸ್ಯಗಳನ್ನು ತಿಂದಾಗ ಈ ಸಂಗ್ರಹಿತ ಆಹಾರ ಮತ್ತು ಶಕ್ತಿ ನಮಗೆ ಸಿಗುತ್ತದೆ. |

