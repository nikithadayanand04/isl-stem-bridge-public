"""Tests for tools/check_registry.py. Run: python -m unittest discover tests"""

import datetime
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
import check_registry as cr  # noqa: E402

TODAY = datetime.date(2026, 11, 3)


def row(**overrides):
    """A row that passes every rule unless a field is overridden."""
    base = {c: '' for c in cr.COLUMNS}
    base.update(sign_id='test_sign', english_term='Test', category='A', isl_source='Test source',
                source_reference='ref-1', attribution='Credit', license_status='granted',
                reference_video='ref.mp4', motion_file='motion.json', motion_qc='pass',
                retarget_check='pass', validation_report='report.json', published='no',
                interpreter='Reviewer', interpreter_review='approved', review_date='2026-11-01')
    base.update(overrides)
    return base


class CheckRegistryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        (self.base / 'ref.mp4').write_bytes(b'x')
        (self.base / 'motion.json').write_text('{}')
        (self.base / 'report.json').write_text('{"geometric_check": {"result": "pass"}}')
        (self.base / 'bad_report.json').write_text('{"geometric_check": {"result": "fail"}}')

    def tearDown(self):
        self.tmp.cleanup()

    def status(self, rows, sid='test_sign'):
        errors, results = cr.check(rows, self.base, TODAY)
        self.assertEqual(errors, [])
        return next(r for r in results if r['sign_id'] == sid)

    def test_complete_row_is_verified(self):
        self.assertEqual(self.status([row()])['status'], 'VERIFIED')

    def test_each_missing_requirement_blocks_verification(self):
        cases = {
            'license not granted': dict(license_status='requested'),
            'no source': dict(isl_source=''),
            'qc failed': dict(motion_qc='fail'),
            'not reviewed': dict(interpreter_review='not_reviewed'),
            'changes needed': dict(interpreter_review='changes_needed'),
            'no reviewer': dict(interpreter=''),
            'future review': dict(review_date='2026-12-01'),
            'bad date': dict(review_date='01/11/2026'),
            'missing video file': dict(reference_video='nope.mp4'),
            'missing motion file': dict(motion_file='nope.json'),
            'sign gap': dict(category='C'),
            'retarget not checked': dict(retarget_check='pending'),
            'no geometric report': dict(validation_report=''),
            'geometric check failed': dict(validation_report='bad_report.json'),
        }
        for name, overrides in cases.items():
            with self.subTest(name):
                result = self.status([row(**overrides)])
                self.assertEqual(result['status'], 'NOT VERIFIED')
                self.assertTrue(result['reasons'])

    def test_reference_video_hidden_unless_licensed(self):
        self.assertEqual(self.status([row(license_status='denied')])['reference_video'], '')
        self.assertEqual(self.status([row()])['reference_video'], 'ref.mp4')

    def test_composed_explanation_needs_verified_parts(self):
        rows = [row(sign_id='water'), row(sign_id='heat', interpreter_review='not_reviewed'),
                row(sign_id='evaporation', category='B', composed_of='water;heat')]
        result = self.status(rows, 'evaporation')
        self.assertEqual(result['status'], 'NOT VERIFIED')
        self.assertIn('part "heat" is not VERIFIED', result['reasons'])

        rows[1] = row(sign_id='heat')
        self.assertEqual(self.status(rows, 'evaporation')['status'], 'VERIFIED')

    def test_composed_without_parts_is_not_verified(self):
        result = self.status([row(category='B')])
        self.assertIn('category B but composed_of is empty', result['reasons'])

    def test_file_errors(self):
        errors, _ = cr.check([row(), row()], self.base, TODAY)
        self.assertTrue(any('duplicate' in e for e in errors))
        errors, _ = cr.check([row(license_status='yes')], self.base, TODAY)
        self.assertTrue(any('license_status' in e for e in errors))
        errors, _ = cr.check([row(category='B', composed_of='ghost')], self.base, TODAY)
        self.assertTrue(any('unknown sign "ghost"' in e for e in errors))
        errors, _ = cr.check([row(composed_of='x')], self.base, TODAY)
        self.assertTrue(any('only allowed for category B' in e for e in errors))

    def test_shipped_example_registry_has_no_verified_signs(self):
        rows = cr.read_rows(cr.ROOT / 'registry' / 'signs.csv')
        errors, results = cr.check(rows, cr.ROOT, TODAY)
        self.assertEqual(errors, [])
        self.assertTrue(all(r['status'] == 'NOT VERIFIED' for r in results))


if __name__ == '__main__':
    unittest.main()


class StagesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        (self.base / 'ref.mp4').write_bytes(b'x')
        (self.base / 'motion.json').write_text('{}')
        (self.base / 'report.json').write_text('{"geometric_check": {"result": "pass"}}')

    def tearDown(self):
        self.tmp.cleanup()

    def test_stages_are_reported_separately(self):
        errors, results = cr.check([row(interpreter_review='not_reviewed', interpreter='', review_date='')],
                                   self.base, TODAY)
        st = results[0]['stages']
        self.assertEqual(list(st), cr.STAGES)
        self.assertTrue(st['source_validated'] and st['motion_extraction_passed'])
        self.assertTrue(st['retargeting_passed'] and st['geometric_comparison_passed'])
        self.assertFalse(st['interpreter_reviewed'] or st['interpreter_approved'] or st['published'])
        self.assertEqual(results[0]['status'], 'NOT VERIFIED')

    def test_technical_passes_alone_never_verify(self):
        errors, results = cr.check([row(interpreter_review='changes_needed')], self.base, TODAY)
        self.assertTrue(results[0]['stages']['interpreter_reviewed'])
        self.assertFalse(results[0]['stages']['interpreter_approved'])
        self.assertEqual(results[0]['status'], 'NOT VERIFIED')

    def test_cannot_publish_unverified_sign(self):
        errors, _ = cr.check([row(published='yes', interpreter_review='not_reviewed')], self.base, TODAY)
        self.assertTrue(any('published is yes' in e for e in errors))
        errors, _ = cr.check([row(published='yes')], self.base, TODAY)
        self.assertEqual(errors, [])

    def test_qc_exception_must_be_documented(self):
        errors, _ = cr.check([row(motion_qc='pass_exception')], self.base, TODAY)
        self.assertTrue(any('QC EXCEPTION' in e for e in errors))
        errors, _ = cr.check([row(motion_qc='pass_exception', notes='QC EXCEPTION approved by X on 2026-11-01')],
                             self.base, TODAY)
        self.assertEqual(errors, [])


class LessonTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        for name in ('ref.mp4', 'motion.json'):
            (base / name).write_text('x')
        (base / 'report.json').write_text('{"geometric_check": {"result": "pass"}}')
        _, self.results = cr.check([row(sign_id='photosynthesis'), row(sign_id='leaf')], base, TODAY)

    def tearDown(self):
        self.tmp.cleanup()

    def lesson(self):
        steps = [{'id': t, 'kind': 'step', 'topic': t, 'caption': 'c', 'isl': {'status': 'awaiting_interpreter'},
                  'key_terms': ['leaf']} for t in cr.REQUIRED_TOPICS]
        explanation = {'status': 'available', 'sign': 'photosynthesis', 'type': 'recorded_explanation', 'author': 'A'}
        return {'sections': [{'id': 'introduction', 'kind': 'introduction', 'caption': 'c', 'isl': dict(explanation)},
                             {'id': 'concept', 'kind': 'concept', 'caption': 'c', 'isl': {'status': 'awaiting_interpreter'}},
                             *steps,
                             {'id': 'key_terms', 'kind': 'key_terms', 'caption': 'c',
                              'terms': [{'term': 'Leaf', 'sign': 'leaf'}, {'term': 'Roots', 'sign': None, 'why': 'none'}]},
                             {'id': 'recap', 'kind': 'recap', 'caption': 'c', 'isl': dict(explanation)}]}

    def test_valid_lesson(self):
        self.assertEqual(cr.check_lesson(self.lesson(), self.results), [])

    def test_concatenated_signs_are_rejected(self):
        lesson = self.lesson()
        lesson['sections'][2]['signs'] = ['leaf', 'photosynthesis']
        self.assertTrue(any('concatenated' in e for e in cr.check_lesson(lesson, self.results)))
        lesson = self.lesson()
        lesson['sections'][2]['isl'] = {'status': 'available', 'sign': ['leaf', 'photosynthesis'],
                                        'type': 'recorded_explanation', 'author': 'A'}
        self.assertTrue(any('exactly one recording' in e for e in cr.check_lesson(lesson, self.results)))

    def test_explanation_needs_author_and_known_sign(self):
        lesson = self.lesson()
        lesson['sections'][0]['isl'].update(author='', sign='unknown_sign')
        errors = cr.check_lesson(lesson, self.results)
        self.assertTrue(any('author' in e for e in errors))
        self.assertTrue(any('not in the registry' in e for e in errors))

    def test_science_coverage_and_sections_required(self):
        lesson = self.lesson()
        lesson['sections'] = [s for s in lesson['sections'] if s.get('topic') != 'growth' and s['kind'] != 'recap']
        errors = cr.check_lesson(lesson, self.results)
        self.assertIn('lesson steps do not cover "growth"', errors)
        self.assertIn('lesson has no "recap" section', errors)

    def test_missing_vocabulary_sign_needs_a_reason(self):
        lesson = self.lesson()
        lesson['sections'][-2]['terms'].append({'term': 'Air', 'sign': None})
        self.assertTrue(any('no sign and no reason' in e for e in cr.check_lesson(lesson, self.results)))

    def test_project_lesson_is_valid(self):
        import json
        lesson = json.loads((Path(__file__).resolve().parent.parent / 'player' / 'lessons' /
                             'photosynthesis.json').read_text(encoding='utf-8'))
        ids = {sid for s in lesson['sections'] for sid in
               [*(s.get('key_terms', [])), *(t['sign'] for t in s.get('terms', []) if t['sign']),
                *([s['isl']['sign']] if s.get('isl', {}).get('sign') else []),
                *([s['concept']['sign']] if (s.get('concept') or {}).get('sign') else [])]}
        tmp = Path(self.tmp.name)
        _, results = cr.check([row(sign_id=i) for i in ids], tmp, TODAY)
        self.assertEqual(cr.check_lesson(lesson, results), [])


class ChapterLessonTest(unittest.TestCase):
    """Chapter lessons (v3): one chapter per idea, told in steps with English and Kannada text."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        for name in ('ref.mp4', 'motion.json'):
            (base / name).write_text('x')
        (base / 'report.json').write_text('{"geometric_check": {"result": "pass"}}')
        _, self.results = cr.check([row(sign_id='leaf'), row(sign_id='chlorophyll', motion_qc='fail')], base, TODAY)

    def tearDown(self):
        self.tmp.cleanup()

    def lesson(self):
        chapters = [{'id': c, 'kind': 'chapter', 'beats': [{'text': 't', 'kn': 'k'}],
                     'concept': {'term': c, 'sign': 'leaf'}, 'isl': {'status': 'awaiting_interpreter'}}
                    for c in cr.REQUIRED_CHAPTERS]
        return {'sections': [*chapters,
                             {'id': 'key_terms', 'kind': 'key_terms', 'caption': 'c', 'terms': []},
                             {'id': 'recap', 'kind': 'recap', 'caption': 'c'}]}

    def test_valid(self):
        self.assertEqual(cr.check_lesson(self.lesson(), self.results), [])

    def test_every_idea_needs_its_own_chapter(self):
        lesson = self.lesson()
        lesson['sections'] = [s for s in lesson['sections'] if s['id'] != 'soil']
        self.assertIn('lesson has no chapter "soil"', cr.check_lesson(lesson, self.results))

    def test_steps_need_english_and_kannada(self):
        lesson = self.lesson()
        lesson['sections'][0]['beats'].append({'text': 'only English'})
        self.assertTrue(any('Kannada text is empty' in e for e in cr.check_lesson(lesson, self.results)))

    def test_unplayable_concept_sign_needs_a_reason(self):
        lesson = self.lesson()
        lesson['sections'][0]['concept'] = {'term': 'Chlorophyll', 'sign': 'chlorophyll'}
        self.assertTrue(any('no reason' in e for e in cr.check_lesson(lesson, self.results)))
        lesson['sections'][0]['concept']['why'] = 'fails QC'
        self.assertEqual(cr.check_lesson(lesson, self.results), [])
        lesson['sections'][0]['concept'] = {'term': 'Plant', 'sign': None}
        self.assertTrue(any('no sign and no reason' in e for e in cr.check_lesson(lesson, self.results)))


class GlossaryTest(unittest.TestCase):
    """Word cards: every word a step shows needs a glossary entry with meanings and a picture."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        for name in ('ref.mp4', 'motion.json'):
            (base / name).write_text('x')
        (base / 'report.json').write_text('{"geometric_check": {"result": "pass"}}')
        _, self.results = cr.check([row(sign_id='leaf')], base, TODAY)

    def tearDown(self):
        self.tmp.cleanup()

    def lesson(self):
        g = {'en': 'Leaf', 'kn': 'ಎಲೆ', 'meaning': 'm', 'meaning_kn': 'ಮ', 'icon': 'mango_leaf', 'sign': 'leaf'}
        chapters = [{'id': c, 'kind': 'chapter', 'beats': [{'text': 't', 'kn': 'k', 'words': ['leaf']}],
                     'concept': {'term': c, 'sign': 'leaf'}} for c in cr.REQUIRED_CHAPTERS]
        return {'glossary': {'leaf': g}, 'sections': [*chapters, {'id': 'key_terms', 'kind': 'key_terms', 'caption': 'c'},
                                                       {'id': 'recap', 'kind': 'recap', 'caption': 'c'}]}

    def test_valid(self):
        self.assertEqual(cr.check_lesson(self.lesson(), self.results), [])

    def test_unknown_word_and_missing_meaning(self):
        lesson = self.lesson()
        lesson['sections'][0]['beats'][0]['words'].append('stomata')
        lesson['glossary']['leaf']['meaning_kn'] = ''
        errors = cr.check_lesson(lesson, self.results)
        self.assertTrue(any('"stomata" is not in the glossary' in e for e in errors))
        self.assertTrue(any('meaning_kn is empty' in e for e in errors))

    def test_glossary_sign_must_be_registered(self):
        lesson = self.lesson()
        lesson['glossary']['leaf']['sign'] = 'made_up_sign'
        self.assertTrue(any('not in the registry' in e for e in cr.check_lesson(lesson, self.results)))
