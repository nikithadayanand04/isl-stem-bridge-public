"""Check the sign validation record and compute each sign's final status.

Usage:
    python tools/check_registry.py                      # checks registry/signs.csv
    python tools/check_registry.py --csv other.csv --out player/registry.json

Nobody types "VERIFIED" by hand. A sign is VERIFIED only when every rule in
REQUIRED_FOR_VERIFIED passes; otherwise it is NOT VERIFIED and the player
shows the fallback. Exits with code 1 if the file has errors.
"""

import argparse
import csv
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

COLUMNS = [
    'sign_id', 'english_term', 'category', 'composed_of', 'isl_source', 'source_reference',
    'attribution', 'license_status', 'reference_video', 'motion_file', 'motion_qc',
    'retarget_check', 'validation_report',
    'interpreter', 'interpreter_review', 'review_date', 'published', 'simple_english', 'illustration', 'notes',
]
ALLOWED = {
    'category': {'A', 'B', 'C'},
    'license_status': {'unknown', 'requested', 'granted', 'denied'},
    'motion_qc': {'pending', 'pass', 'pass_exception', 'fail'},   # pass_exception: team-approved, see notes
    'retarget_check': {'pending', 'pass', 'fail'},
    'interpreter_review': {'not_reviewed', 'approved', 'changes_needed', 'rejected'},
    'published': {'no', 'yes'},
}
# The stages a sign goes through, in order. Each is computed separately and shown separately;
# passing the technical stages never makes a sign correct ISL - only interpreter approval does.
STAGES = ['source_validated', 'motion_extraction_passed', 'retargeting_passed',
          'geometric_comparison_passed', 'interpreter_reviewed', 'interpreter_approved', 'published']
SIGN_ID = re.compile(r'^[a-z0-9_]+$')


def read_rows(csv_path):
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(f'{csv_path}: missing columns: {", ".join(missing)}')
        return [{k: (v or '').strip() for k, v in row.items()} for row in reader]


def file_exists(rel_path, base):
    return bool(rel_path) and (base / rel_path).is_file()


def geometric_result(row, base):
    """'pass', 'fail' or 'missing', read from the motion report (tools/motion_report.py)."""
    path = base / row['validation_report'] if row['validation_report'] else None
    if not path or not path.is_file():
        return 'missing'
    try:
        return json.loads(path.read_text(encoding='utf-8')).get('geometric_check', {}).get('result', 'missing')
    except (OSError, ValueError):
        return 'missing'


def stages(row, base, today):
    """Each pipeline stage as True/False, computed from the row and the files it names."""
    try:
        dated = datetime.date.fromisoformat(row['review_date']) <= today
    except ValueError:
        dated = False
    reviewed = row['interpreter_review'] != 'not_reviewed' and bool(row['interpreter']) and dated
    return {
        'source_validated': all(row[f] for f in ('isl_source', 'source_reference', 'attribution'))
        and row['license_status'] == 'granted' and file_exists(row['reference_video'], base),
        'motion_extraction_passed': file_exists(row['motion_file'], base)
        and row['motion_qc'] in ('pass', 'pass_exception'),
        'retargeting_passed': row['retarget_check'] == 'pass',
        'geometric_comparison_passed': geometric_result(row, base) == 'pass',
        'interpreter_reviewed': reviewed,
        'interpreter_approved': reviewed and row['interpreter_review'] == 'approved',
        'published': row['published'] == 'yes',
    }


def own_reasons(row, base, today):
    """Reasons this row cannot be VERIFIED on its own (ignores composed_of)."""
    reasons = []
    if row['category'] == 'C':
        reasons.append('category C (sign gap)')
    for field in ('isl_source', 'source_reference', 'attribution'):
        if not row[field]:
            reasons.append(f'{field} is empty')
    if row['license_status'] != 'granted':
        reasons.append(f'license_status is {row["license_status"]}, not granted')
    if not file_exists(row['reference_video'], base):
        reasons.append('reference_video file not found')
    if not file_exists(row['motion_file'], base):
        reasons.append('motion_file not found')
    if row['motion_qc'] not in ('pass', 'pass_exception'):
        reasons.append(f'motion_qc is {row["motion_qc"]}, not pass')
    if row['retarget_check'] != 'pass':
        reasons.append(f'retarget_check is {row["retarget_check"]}, not pass')
    geo = geometric_result(row, base)
    if geo != 'pass':
        reasons.append('geometric comparison report is missing' if geo == 'missing'
                       else 'geometric comparison failed (see validation_report)')
    if row['interpreter_review'] != 'approved':
        reasons.append(f'interpreter_review is {row["interpreter_review"]}, not approved')
    if not row['interpreter']:
        reasons.append('interpreter is empty')
    try:
        reviewed = datetime.date.fromisoformat(row['review_date'])
        if reviewed > today:
            reasons.append('review_date is in the future')
    except ValueError:
        reasons.append('review_date is missing or not YYYY-MM-DD')
    if row['category'] == 'B' and not row['composed_of']:
        reasons.append('category B but composed_of is empty')
    return reasons


def check(rows, base, today):
    """Returns (errors, results). errors = problems in the file itself."""
    errors = []
    by_id = {}
    for line, row in enumerate(rows, start=2):  # line 1 is the header
        sid = row['sign_id']
        if not SIGN_ID.match(sid):
            errors.append(f'line {line}: sign_id "{sid}" must use only a-z, 0-9 and _')
        if sid in by_id:
            errors.append(f'line {line}: duplicate sign_id "{sid}"')
        for field, allowed in ALLOWED.items():
            if row[field] not in allowed:
                errors.append(f'line {line}: {field} "{row[field]}" is not one of {sorted(allowed)}')
        if row['composed_of'] and row['category'] != 'B':
            errors.append(f'line {line}: composed_of is only allowed for category B')
        by_id[sid] = row

    for row in rows:
        for part in filter(None, row['composed_of'].split(';')):
            if part.strip() not in by_id:
                errors.append(f'{row["sign_id"]}: composed_of names unknown sign "{part.strip()}"')

    reasons = {sid: own_reasons(row, base, today) for sid, row in by_id.items()}
    # A composed explanation is only as good as every sign inside it.
    changed = True
    while changed:
        changed = False
        for sid, row in by_id.items():
            for part in filter(None, (p.strip() for p in row['composed_of'].split(';'))):
                note = f'part "{part}" is not VERIFIED'
                if part in reasons and reasons[part] and note not in reasons[sid]:
                    reasons[sid].append(note)
                    changed = True

    results = []
    for sid, row in by_id.items():
        verified = not reasons[sid]
        if row['published'] == 'yes' and not verified:
            errors.append(f'{sid}: published is yes but the sign is not VERIFIED')
        if row['motion_qc'] == 'pass_exception' and 'QC EXCEPTION' not in row['notes'].upper():
            errors.append(f'{sid}: motion_qc is pass_exception but notes do not document the QC EXCEPTION')
        results.append({
            'sign_id': sid,
            'english_term': row['english_term'],
            'category': row['category'],
            'status': 'VERIFIED' if verified else 'NOT VERIFIED',
            'reasons': reasons[sid],
            'composed_of': [p.strip() for p in row['composed_of'].split(';') if p.strip()],
            'source': {'name': row['isl_source'], 'reference': row['source_reference'],
                       'attribution': row['attribution']},
            # Only a licensed reference video may ever be shown to students.
            'reference_video': row['reference_video'] if row['license_status'] == 'granted' else '',
            # For the team's interpreter-review mode only; never shown in the student view.
            'review_reference_video': row['reference_video'],
            'motion_qc': row['motion_qc'],
            'stages': stages(row, base, today),
            'validation_report': row['validation_report'],
            'simple_english': row['simple_english'],
            'illustration': row['illustration'],
            'review': {'interpreter': row['interpreter'], 'result': row['interpreter_review'],
                       'date': row['review_date']},
        })
    return errors, results


REQUIRED_SECTIONS = ['introduction', 'concept', 'step', 'key_terms', 'recap']
REQUIRED_TOPICS = ['light_energy', 'water_absorption', 'gas_exchange_co2', 'sugar_production',
                   'gas_exchange_o2', 'growth']
ISL_TYPES = {'recorded_explanation', 'interpreter_recording'}
# Chapter lessons (one chapter per idea, told in numbered steps; lesson v3, 12 Nov 2026). The
# school asked for each of these ideas to be shown and explained on its own.
REQUIRED_CHAPTERS = ['plant', 'sun', 'soil', 'water', 'leaf', 'chlorophyll', 'carbon_dioxide', 'oxygen']


def check_lesson(lesson, results):
    """Errors in a lesson file. results: the registry check results.

    Enforces the language rule: a section's ISL is one interpreter-authored recording or
    nothing ("awaiting_interpreter"); a list of dictionary signs is never accepted as an
    explanation. Vocabulary signs may be offered one at a time (key_terms)."""
    by_id = {r['sign_id']: r for r in results}
    errors = []
    sections = lesson.get('sections', [])
    kinds = [s.get('kind') for s in sections]
    if 'chapter' in kinds:
        for kind in ('key_terms', 'recap'):
            if kind not in kinds:
                errors.append(f'lesson has no "{kind}" section')
        ids = {s.get('id') for s in sections if s.get('kind') == 'chapter'}
        for cid in REQUIRED_CHAPTERS:
            if cid not in ids:
                errors.append(f'lesson has no chapter "{cid}"')
    else:
        for kind in REQUIRED_SECTIONS:
            if kind not in kinds:
                errors.append(f'lesson has no "{kind}" section')
        topics = {s.get('topic') for s in sections if s.get('kind') == 'step'}
        for topic in REQUIRED_TOPICS:
            if topic not in topics:
                errors.append(f'lesson steps do not cover "{topic}"')

    def known(sid, where):
        if sid not in by_id:
            errors.append(f'{where}: sign "{sid}" is not in the registry')
            return False
        return True

    # Word cards (13 Nov 2026): every word a step shows must be in the glossary, with a meaning in
    # English and Kannada and a picture; a sign, if given, must be a registered sign.
    glossary = lesson.get('glossary', {})
    for wid, g in glossary.items():
        for field in ('en', 'kn', 'meaning', 'meaning_kn', 'icon'):
            if not g.get(field):
                errors.append(f'glossary "{wid}": {field} is empty')
        if g.get('sign'):
            known(g['sign'], f'glossary "{wid}"')

    for s in sections:
        where = f'section "{s.get("id")}"'
        for i, b in enumerate(s.get('beats') or [], 1):
            for w in b.get('words', []):
                if w not in glossary:
                    errors.append(f'{where} step {i}: word "{w}" is not in the glossary')
        if 'signs' in s or 'signs' in s.get('isl', {}):
            errors.append(f'{where}: a list of signs is not an ISL explanation (concatenated dictionary signs)')
        if s.get('kind') == 'chapter':
            beats = s.get('beats') or []
            if not beats:
                errors.append(f'{where}: a chapter needs at least one step')
            for i, b in enumerate(beats, 1):
                if not b.get('text'):
                    errors.append(f'{where} step {i}: text is empty')
                if not b.get('kn'):
                    errors.append(f'{where} step {i}: Kannada text is empty')
            c = s.get('concept') or {}
            if c.get('sign'):
                if known(c['sign'], f'{where} concept'):
                    st = by_id[c['sign']]['stages']
                    if not (st['motion_extraction_passed'] and st['retargeting_passed']) and not c.get('why'):
                        errors.append(f'{where}: concept sign "{c["sign"]}" cannot be played and no reason is given')
            elif not c.get('why'):
                errors.append(f'{where}: concept has no sign and no reason given')
        elif not s.get('caption'):
            errors.append(f'{where}: caption is empty')
        isl = s.get('isl')
        if isl is not None:
            status = isl.get('status')
            if status not in ('available', 'awaiting_interpreter'):
                errors.append(f'{where}: isl.status "{status}" is not available or awaiting_interpreter')
            if status == 'available':
                if not isinstance(isl.get('sign'), str):
                    errors.append(f'{where}: an available ISL explanation must name exactly one recording')
                elif known(isl['sign'], where):
                    st = by_id[isl['sign']]['stages']
                    if not (st['motion_extraction_passed'] and st['retargeting_passed']):
                        errors.append(f'{where}: "{isl["sign"]}" has not passed motion extraction and retargeting')
                if isl.get('type') not in ISL_TYPES:
                    errors.append(f'{where}: isl.type must be one of {sorted(ISL_TYPES)}')
                if not isl.get('author'):
                    errors.append(f'{where}: isl.author (who signed the explanation) is empty')
        for sid in s.get('key_terms', []):
            known(sid, where)
        for term in s.get('terms', []):
            if term.get('sign'):
                known(term['sign'], f'{where} term "{term.get("term")}"')
            elif not term.get('why'):
                errors.append(f'{where} term "{term.get("term")}": no sign and no reason given')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--csv', default=str(ROOT / 'registry' / 'signs.csv'))
    parser.add_argument('--out', default=str(ROOT / 'player' / 'registry.json'))
    args = parser.parse_args()

    rows = read_rows(args.csv)
    errors, results = check(rows, ROOT, datetime.date.today())
    if errors:
        print('Registry has errors - nothing written:')
        for e in errors:
            print('  ✗', e)
        sys.exit(1)

    lesson_errors = []
    for lesson_path in sorted((ROOT / 'player' / 'lessons').glob('*.json')):
        lesson = json.loads(lesson_path.read_text(encoding='utf-8'))
        lesson_errors += [f'{lesson_path.name}: {e}' for e in check_lesson(lesson, results)]
    if lesson_errors:
        print('Lesson has errors - nothing written:')
        for e in lesson_errors:
            print('  ✗', e)
        sys.exit(1)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'generated': datetime.date.today().isoformat(), 'signs': results},
                              indent=2, ensure_ascii=False), encoding='utf-8')

    for r in results:
        mark = '✓' if r['status'] == 'VERIFIED' else '•'
        print(f'{mark} {r["sign_id"]:<20} {r["category"]}  {r["status"]}')
        for reason in r['reasons']:
            print(f'      - {reason}')
    verified = sum(r['status'] == 'VERIFIED' for r in results)
    print(f'\n{verified} of {len(results)} signs VERIFIED. Wrote {out}')


if __name__ == '__main__':
    main()
