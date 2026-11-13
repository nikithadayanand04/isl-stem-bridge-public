"""Write INTERPRETER_RECORDING_SHEET.md from the lesson: what an ISL interpreter records for each
chapter, and how each recording becomes the avatar's ISL explanation.

    python3 tools/recording_sheet.py

Why: an ISL explanation must be signed by a person (ISL has its own grammar; dictionary signs
strung together are not ISL). This sheet is what the school's interpreter works from.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSON = ROOT / 'player' / 'lessons' / 'photosynthesis.json'
OUT = ROOT / 'INTERPRETER_RECORDING_SHEET.md'


def main():
    lesson = json.loads(LESSON.read_text(encoding='utf-8'))
    out = [f'# ISL recording sheet: {lesson["title"]}', '',
           'Generated from `player/lessons/photosynthesis.json` by `tools/recording_sheet.py`. Do not edit by hand.', '',
           'One recording per chapter, by a qualified ISL interpreter or Deaf ISL expert, explaining the chapter',
           'in natural ISL (not word for word). The steps below are the content to cover, in order. The avatar',
           'copies the recording exactly; the student sees it beside the animated picture.', '',
           '## How to record', '',
           '- Plain, even background (grey or blue) and even light from the front; no shadows on the hands.',
           '- Camera fixed on a stand at chest height, landscape, 1920×1080, 25 fps or more.',
           '- Frame from just above the head to the hips, signer in the middle; elbows and hands always in the picture,',
           '  also when the arms are raised. (Hands leaving the picture make the recording fail the quality check.)',
           '- Dark plain top, no rings or bangles. Start and end with the hands resting at the sides for one second.',
           '- Steady, clear signing at teaching speed. Fast movement blurs the hands: the tracker loses them.',
           '- Save as `references/interp_<chapter id>.mp4` (chapter ids below).', '',
           '## How a recording reaches the avatar', '',
           '```',
           '.venv/bin/python tools/extract_landmarks.py references/interp_soil.mp4 --sign-id interp_soil \\',
           '    --out-dir motion/v2 --face-model models/face_landmarker.task      # prints motion_qc = pass/fail',
           '# add a row to registry/signs.csv (category B, isl_source = the interpreter, attribution, consent)',
           'sh tools/bake_all.sh interp_soil                                    # bake, validate, export',
           '.venv/bin/python tools/visual_loop_check.py interp_soil              # avatar vs recording',
           '```',
           'Then set the chapter\'s `isl` in the lesson to',
           '`{"status": "available", "sign": "interp_soil", "type": "interpreter_recording", "author": "<name>"}`',
           'and run `python3 tools/check_registry.py`. A recording that fails a check is re-recorded, never patched.', '',
           '## Chapters', '']
    for s in lesson['sections']:
        if s.get('kind') != 'chapter':
            continue
        isl = s.get('isl', {})
        have = isl.get('status') == 'available'
        c = s.get('concept') or {}
        out += [f'### {s["heading"]} · {s.get("kn_heading", "")}  (chapter id `{s["id"]}`)', '']
        out.append(f'- ISL sign for the idea: ' + (f'`{c["sign"]}` (ISLRTC)' if c.get('sign') else
                                                    f'**missing**: {c.get("why", "")} Please give the sign in the recording.'))
        out.append('- ISL explanation now: ' + (f'ISLRTC recording `{isl["sign"]}` ({isl.get("note", "")})' if have
                                                else 'none. **Please record.**' + (f' ({isl["note"]})' if isl.get('note') else '')))
        out.append('')
        out.append('| Step | Content (English) | ಕನ್ನಡ |')
        out.append('| --- | --- | --- |')
        for i, b in enumerate(s['beats'], 1):
            out.append(f'| {i} | {b["text"]} | {b["kn"]} |')
        out.append('')
    OUT.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(f'Wrote {OUT}')


if __name__ == '__main__':
    main()
