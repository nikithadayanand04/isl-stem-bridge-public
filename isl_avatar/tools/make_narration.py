"""Spoken narration for a lesson, plus the lip-sync curves for the avatar.

    .venv/bin/python tools/make_narration.py --lang kn --voice Soumya     # Kannada (voice must be installed)
    .venv/bin/python tools/make_narration.py --lang en --voice Lekha      # English, Indian female voice
    .venv/bin/python tools/make_narration.py --lang kn --engine edge --voice kn-IN-SapnaNeural
        # Kannada, Microsoft's online neural voice (the caption text is sent to Microsoft)

For every lesson section it speaks the caption (and the recap points); a chapter is spoken
step by step (one clip per step, "<section>.<step>"), with the Mac's offline
speech (`say`), and writes to player/audio/<lang>/:
  <section>.m4a       the audio
  <section>.lip.json  mouth shapes at 60 fps (tools/lipsync.py)
  index.json          what exists, durations, the voice used
Kannada text comes from each section's "kn" entry in the lesson file (a draft translation; see
lesson "narration.translation_status"). With the default engine (macOS `say`) nothing is sent over
the network. With --engine edge (Microsoft's online voices, via the edge-tts tool; chosen for
Kannada on 12 Nov 2026 because macOS offers no Kannada voice) the caption text is sent to Microsoft.
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import lipsync  # noqa: E402


# The avatar is a woman, so the narration voice must be female (project requirement, 11 Nov 2026).
# macOS does not report a voice's gender, so only voices listed here are accepted. Add a voice only
# after listening to it.
FEMALE_VOICES = {
    'Lekha': 'hi_IN', 'Vani': 'ta_IN', 'Veena': 'en_IN', 'Soumya': 'kn_IN',
    'Samantha': 'en_US', 'Karen': 'en_AU', 'Moira': 'en_IE', 'Tessa': 'en_ZA', 'Kathy': 'en_US',
}
MALE_VOICES = {'Rishi', 'Daniel', 'Fred', 'Ralph', 'Albert', 'Junior'}


def installed_voices():
    out = subprocess.run(['say', '-v', '?'], capture_output=True, text=True).stdout
    return {line.split()[0]: line.split()[1] for line in out.splitlines() if line.strip()}


def edge_voices():
    """{voice: gender} from Microsoft's own voice list."""
    out = subprocess.run([str(Path(sys.executable).parent / 'edge-tts'), '--list-voices'],
                         capture_output=True, text=True, check=True).stdout
    voices = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2 and '-' in parts[0] and parts[1] in ('Female', 'Male'):
            voices[parts[0]] = parts[1]
    return voices


def parts(section, lang):
    """(audio id, text) for each piece of narration in a section: one per step for a chapter
    (id "<section>.<step>"), else one for the whole section."""
    if section.get('beats'):
        key = 'text' if lang == 'en' else lang
        return [(f'{section["id"]}.{i}', b.get(key, '')) for i, b in enumerate(section['beats'], 1)]
    return [(section['id'], section_text(section, lang))]


def section_text(section, lang):
    if lang == 'en':
        return ' '.join([section['caption']] + section.get('points', []))
    tr = section.get(lang) or {}
    return ' '.join([tr.get('caption', '')] + tr.get('points', [])).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lesson', default=str(ROOT / 'player' / 'lessons' / 'photosynthesis.json'))
    ap.add_argument('--lang', required=True)
    ap.add_argument('--voice', required=True)
    ap.add_argument('--rate', type=int, default=150, help='words per minute (macOS voices; slow and clear)')
    ap.add_argument('--engine', choices=('say', 'edge'), default='say',
                    help='say = macOS offline voices; edge = Microsoft online neural voices (sends the text)')
    args = ap.parse_args()
    if args.engine == 'edge':
        gender = edge_voices().get(args.voice)
        if gender is None:
            raise SystemExit(f'Voice "{args.voice}" is not in Microsoft\'s voice list.')
        if gender != 'Female':
            raise SystemExit(f'Voice "{args.voice}" is {gender.lower()}. The avatar is a woman: use a female voice.')
        locale = '-'.join(args.voice.split('-')[:2])
    else:
        if args.voice not in FEMALE_VOICES:
            why = 'a male voice' if args.voice in MALE_VOICES else 'not on the list of checked female voices'
            raise SystemExit(f'Voice "{args.voice}" is {why}. The avatar is a woman: use a female voice '
                             f'({", ".join(sorted(FEMALE_VOICES))}), or add one to FEMALE_VOICES after listening to it.')
        voices = installed_voices()
        if args.voice not in voices:
            indian = {v: l for v, l in voices.items() if l.endswith('_IN')}
            raise SystemExit(f'Voice "{args.voice}" is not installed on this Mac. Installed Indian voices: {indian}. '
                             'Add one in System Settings > Accessibility > Spoken Content > System voice > Manage Voices.')
        locale = voices[args.voice]
    lesson = json.loads(Path(args.lesson).read_text(encoding='utf-8'))
    out_dir = ROOT / 'player' / 'audio' / args.lang
    out_dir.mkdir(parents=True, exist_ok=True)
    index = {'language': args.lang, 'voice': args.voice, 'voice_gender': 'female', 'engine': args.engine,
             'voice_locale': locale, 'sections': {}}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for sid, text in [p for s in lesson['sections'] for p in parts(s, args.lang)]:
            if not text:
                print(f'{sid}: no {args.lang} text, skipped')
                continue
            (tmp / 't.txt').write_text(text, encoding='utf-8')
            if args.engine == 'edge':
                subprocess.run([str(Path(sys.executable).parent / 'edge-tts'), '--voice', args.voice,
                                '--rate=-10%', '--file', str(tmp / 't.txt'), '--write-media', str(tmp / 'a.mp3')],
                               check=True, capture_output=True)
                subprocess.run(['afconvert', '-f', 'AIFF', '-d', 'BEI16@24000', str(tmp / 'a.mp3'), str(tmp / 'a.aiff')],
                               check=True)
            else:
                subprocess.run(['say', '-v', args.voice, '-r', str(args.rate), '-o', str(tmp / 'a.aiff'),
                                '-f', str(tmp / 't.txt')], check=True)
            subprocess.run(['afconvert', '-f', 'WAVE', '-d', 'LEI16@22050', '-c', '1', str(tmp / 'a.aiff'),
                            str(tmp / 'a.wav')], check=True)
            subprocess.run(['afconvert', '-f', 'm4af', '-d', 'aac', str(tmp / 'a.aiff'),
                            str(out_dir / f'{sid}.m4a')], check=True)
            lip = lipsync.from_wav(tmp / 'a.wav')
            (out_dir / f'{sid}.lip.json').write_text(json.dumps(lip), encoding='utf-8')
            index['sections'][sid] = {'audio': f'{sid}.m4a', 'lip': f'{sid}.lip.json', 'duration': lip['duration']}
            print(f'{sid:18} {lip["duration"]:5.1f} s')
    (out_dir / 'index.json').write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Wrote {out_dir}')


if __name__ == '__main__':
    main()
