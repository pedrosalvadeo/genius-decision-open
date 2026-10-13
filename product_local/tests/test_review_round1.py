"""Public regressions for non-author C1 findings; expectations are contractual.

No implementation imports. GENIUS_REVIEW_PRODUCT permits replaying applicable
tests against the preserved C1 tree without modifying that candidate.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile


SOURCE = Path(__file__).resolve().parents[1]
PRODUCT = Path(os.environ.get('GENIUS_REVIEW_PRODUCT', SOURCE))
R1 = Path(os.environ.get('GENIUS_R1_BASELINE', SOURCE.parent / 'baseline/R1'))
R0 = Path(os.environ.get('GENIUS_R0_BASELINE', SOURCE.parent / 'baseline/received_baseline/R0'))


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class ReviewRound1Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.input = self.root / 'input'
        shutil.copytree(SOURCE / 'examples/hours', self.input)
        self.request = json.loads((self.input / 'request.json').read_bytes())
        self.case = self.root / 'case'

    def cli(self, command='run', expected=0, r1=None, r0=None):
        args = [sys.executable, '-I', '-B', '-c',
                "import sys;sys.path.insert(0,sys.argv.pop(1));from genius_local.__main__ import main;raise SystemExit(main())",
                str(PRODUCT), command, '--case', str(self.case)]
        if command in ('run', 'continue'):
            (self.input / 'request.json').write_bytes(encode(self.request))
            args += ['--request', str(self.input / 'request.json'), '--r1', str(r1 or R1), '--baseline', str(r0 or R0)]
        proc = subprocess.run(args, capture_output=True, timeout=70)
        self.assertEqual(proc.returncode, expected, proc.stderr.decode())
        return json.loads(proc.stdout if expected == 0 else proc.stderr)

    def write_source(self, name, value):
        raw = encode(value)
        (self.input / (name + '.json')).write_bytes(raw)
        for artifact in self.request['artifacts']:
            if artifact['path'] == name + '.json':
                artifact['sha256'] = sha(raw)
                for operation in self.request['operations']:
                    assessment = operation['parameters'].get('assessment')
                    if assessment and assessment['source_ref'] == artifact['id']:
                        assessment['source_digest'] = sha(raw)

    def next_revision(self, reason, refs):
        state = self.cli('inspect')
        self.request['revision'] = state['latest']['request']['revision'] + 1
        self.request['supersedes'] = {'revision': state['revisions'][-1]['revision'], 'sha256': state['head']}
        self.request['novelty'] = {'reason': reason, 'changed_refs': refs}

    def assert_not_closed(self, response):
        self.assertNotIn(response['decisions'][0]['state'], ('PR_JUSTIFIED_RESULT', 'PR_SET_OR_INCOMPARABLE', 'PR_PROVEN_INFEASIBLE'))
        obligation = response['obligations_ref']['record']['obligations'][0]
        self.assertFalse(obligation['closure']['verified'])
        self.assertFalse(obligation['status'].startswith('CLOSED_'))

    def reuse(self, value, pointer=''):
        self.write_source('hours', value)
        self.request['queries'][0]['scope'] = {'operator': 'REUSE/1', 'artifact_ref': 'hours', 'pointer': pointer}
        self.request['obligations'][0]['primary_cause'] = 'YA_DISPONIBLE'
        operation = self.request['operations'][0]
        operation['kind'] = 'REUSE'
        operation['parameters'].pop('rule_id')
        operation['parameters']['pointer'] = pointer

    def test_contractual_hours_control_and_physical_target_rejected(self):
        response = self.cli()
        self.assertEqual(response['decisions'][0]['answers'][0]['value']['assigned']['value'], '14/1')
        self.case = self.root / 'physical-case'
        self.request['queries'][0]['target_spec']['unit'] = 'h_physical'
        self.request['obligations'][0]['input_spec']['unit'] = 'h_physical'
        assessment = self.request['operations'][0]['parameters']['assessment']
        assessment['target_spec']['unit'] = 'h_physical'
        assessment['axes']['unit']['source_value'] = 'h_physical'
        assessment['axes']['unit']['target_value'] = 'h_physical'
        metadata = json.loads((self.input / 'metadata.json').read_bytes())
        metadata['unit'] = 'h_physical'
        self.write_source('metadata', metadata)
        self.assert_not_closed(self.cli())

    def test_nested_unknown_is_outside_profile_and_direct_unknown_preserved(self):
        unknown = {'state': 'PV_UNKNOWN', 'reasons': ['not received'], 'obligation_refs': ['O']}
        self.reuse({'known': {'state': 'PV_KNOWN', 'value': '14/1', 'unit': 'h_contractual', 'basis': ['stipulation']}, 'missing': unknown})
        response = self.cli()
        self.assert_not_closed(response)
        self.assertEqual(response['decisions'][0]['state'], 'PR_OUTSIDE_PROFILE')
        self.case = self.root / 'direct-case'
        self.request['queries'][0]['scope']['pointer'] = '/missing'
        self.request['operations'][0]['parameters']['pointer'] = '/missing'
        direct = self.cli()
        self.assert_not_closed(direct)
        self.assertIn('PV_UNKNOWN', json.dumps(direct))

    def test_known_wrapper_cannot_hide_nested_product_state(self):
        value = {'state': 'PV_KNOWN', 'value': {'missing': {'state': 'PV_UNKNOWN', 'reasons': ['unknown'], 'obligation_refs': ['O']}}, 'unit': 'h_contractual', 'basis': ['synthetic']}
        self.reuse(value)
        self.assert_not_closed(self.cli())

    def test_literal_reuse_positive_control(self):
        self.reuse({'left': '14/1', 'right': '0/1'})
        response = self.cli()
        self.assertEqual(response['decisions'][0]['state'], 'PR_JUSTIFIED_RESULT')
        self.assertEqual(response['decisions'][0]['answers'][0]['value']['value'], {'left': '14/1', 'right': '0/1'})

    def test_renamed_aliases_are_not_novel_but_changed_credit_is(self):
        self.cli()
        aliases = {'Q': 'Q-new', 'O': 'O-new', 'OP1': 'OP-new', 'A1': 'A-new', 'hours': 'hours-new', 'metadata': 'metadata-new'}
        def rename(value):
            if type(value) is str:
                return aliases.get(value, value)
            if type(value) is dict:
                return {key: rename(child) for key, child in value.items()}
            if type(value) is list:
                return [rename(child) for child in value]
            return value
        self.request = rename(self.request)
        self.next_revision('Only references renamed', ['Q-new', 'O-new', 'OP-new', 'hours-new'])
        rejected = self.cli('continue', expected=2)
        self.assertEqual(rejected['reason'], 'NO_PERTINENT_NOVELTY')
        hours = json.loads((self.input / 'hours.json').read_bytes())
        hours['assignments'][1]['credit_hours']['value'] = '17/2'
        self.write_source('hours', hours)
        self.request['novelty'] = {'reason': 'Changed exact credit', 'changed_refs': ['hours-new']}
        response = self.cli('continue')
        self.assertEqual(response['decisions'][0]['answers'][0]['value']['assigned']['value'], '15/1')

    def test_literal_equal_to_artifact_alias_stays_literal(self):
        # A domain identity may happen to spell the same as an artifact alias.
        # Renaming the reference must not rewrite that literal descriptor.
        self.request['queries'][0]['target_spec']['identity'] = 'hours'
        assessment = self.request['operations'][0]['parameters']['assessment']
        assessment['target_spec']['identity'] = 'hours'
        assessment['axes']['identity'].update(source_value='hours', target_value='hours')
        metadata = json.loads((self.input / 'metadata.json').read_bytes())
        metadata['identity'] = 'hours'
        self.write_source('metadata', metadata)
        self.cli()
        for artifact in self.request['artifacts']:
            if artifact['id'] == 'hours': artifact['id'] = 'another-alias'
        query = self.request['queries'][0]
        query['artifact_refs'] = ['another-alias' if ref == 'hours' else ref for ref in query['artifact_refs']]
        params = self.request['operations'][0]['parameters']
        params['artifact_ref'] = params['assessment']['source_ref'] = 'another-alias'
        self.next_revision('Artifact alias only, literal identity unchanged', ['another-alias'])
        self.assertEqual(self.cli('continue', expected=2)['reason'], 'NO_PERTINENT_NOVELTY')

    def test_unknown_cell_reference_alias_is_not_new_source_evidence(self):
        original = json.loads((self.input / 'hours.json').read_bytes())
        unknown = copy.deepcopy(original)
        unknown['assignments'][0]['credit_hours'] = {
            'state': 'PV_UNKNOWN', 'reasons': ['credit not received'], 'obligation_refs': ['O']}
        self.write_source('hours', unknown)
        self.assert_not_closed(self.cli())
        self.request['obligations'][0]['id'] = 'O-new'
        self.request['queries'][0]['obligation_refs'] = ['O-new']
        self.request['operations'][0]['obligation_refs'] = ['O-new']
        unknown['assignments'][0]['credit_hours']['obligation_refs'] = ['O-new']
        self.write_source('hours', unknown)
        self.next_revision('Only typed unknown reference renamed', ['O-new', 'hours'])
        self.assertEqual(self.cli('continue', expected=2)['reason'], 'NO_PERTINENT_NOVELTY')
        self.write_source('hours', original)
        self.request['novelty'] = {'reason': 'Received missing exact credit', 'changed_refs': ['hours']}
        self.assertEqual(self.cli('continue')['decisions'][0]['state'], 'PR_JUSTIFIED_RESULT')

    def test_duplicate_semantic_query_is_not_novel_but_distinct_target_is(self):
        self.cli()
        aliases = {'Q': 'Q-copy', 'O': 'O-copy', 'OP1': 'OP-copy', 'A1': 'A-copy'}
        def rename(value):
            if type(value) is str: return aliases.get(value, value)
            if type(value) is dict: return {key: rename(child) for key, child in value.items()}
            if type(value) is list: return [rename(child) for child in value]
            return value
        for field in ('queries', 'obligations', 'operations'):
            self.request[field].append(rename(self.request[field][0]))
        self.next_revision('Only duplicated aliases', ['Q-copy', 'O-copy', 'OP-copy'])
        self.assertEqual(self.cli('continue', expected=2)['reason'], 'NO_PERTINENT_NOVELTY')
        # A distinct stated target is a meaningful new question. Its source
        # correspondence is independently supplied; no ID rewrite creates it.
        target = 'synthetic-register-second'
        self.request['queries'][1]['target_spec']['identity'] = target
        assessment = self.request['operations'][1]['parameters']['assessment']
        assessment['target_spec']['identity'] = target
        assessment['axes']['identity'].update(source_value=target, target_value=target)
        meta = json.loads((self.input / 'metadata.json').read_bytes())
        meta['identity'] = target
        descriptor = copy.deepcopy(self.request['artifacts'][1])
        descriptor.update(id='metadata-second', path='metadata-second.json')
        self.request['artifacts'].append(descriptor)
        self.request['queries'][1]['artifact_refs'].append('metadata-second')
        for axis in assessment['axes'].values():
            axis['basis']['artifact_ref'] = 'metadata-second'
        self.write_source('metadata-second', meta)
        self.request['novelty'] = {'reason': 'Distinct target with supplied correspondence', 'changed_refs': ['Q-copy', 'metadata-second']}
        response = self.cli('continue')
        self.assertEqual(len(response['decisions']), 2)
        self.assertTrue(all(row['state'] == 'PR_JUSTIFIED_RESULT' for row in response['decisions']))

    def test_typed_derivation_rule_references_are_not_alias_novelty(self):
        original = copy.deepcopy(self.request)
        for variant in ('RULE', 'PENDING_RULE'):
            with self.subTest(variant=variant):
                self.case = self.root / variant
                self.request = copy.deepcopy(original)
                if variant == 'RULE':
                    self.request['obligations'][0]['derivation_rule'] = {
                        'kind': 'RULE', 'id': 'CONTRACT_HOURS/1', 'version': '1',
                        'procedure': 'Exact credit sum', 'domain': 'Synthetic contractual credits',
                        'basis': {'artifact_ref': 'metadata', 'pointer': '/method'}}
                else:
                    model = copy.deepcopy(self.request['obligations'][0])
                    model.update(id='MODEL', primary_cause='DEFINICION_MODELO')
                    self.request['obligations'].append(model)
                    self.request['queries'][0]['obligation_refs'].append('MODEL')
                    self.request['obligations'][0]['derivation_rule'] = {
                        'kind': 'PENDING_RULE', 'reason': 'Rule admission pending', 'obligation_ref': 'MODEL'}
                    self.request['obligations'][0]['dependencies'] = [{'ref': 'MODEL', 'revision': 1, 'role': 'rule'}]
                self.cli()
                aliases = {'Q': 'Q-2', 'O': 'O-2', 'MODEL': 'MODEL-2', 'OP1': 'OP-2', 'A1': 'A-2', 'metadata': 'meta-2'}
                def rename(value):
                    if type(value) is str: return aliases.get(value, value)
                    if type(value) is dict: return {key: rename(child) for key, child in value.items()}
                    if type(value) is list: return [rename(child) for child in value]
                    return value
                self.request = rename(self.request)
                self.next_revision('Typed references renamed only', ['Q-2', 'O-2', 'OP-2', 'meta-2'])
                self.assertEqual(self.cli('continue', expected=2)['reason'], 'NO_PERTINENT_NOVELTY')

    def test_worker_does_not_import_unpinned_siblings(self):
        shutil.rmtree(self.input)
        shutil.copytree(SOURCE / 'examples/fdq_selector', self.input)
        self.request = json.loads((self.input / 'request.json').read_bytes())
        marker = self.root / 'UNPINNED_EXECUTED'
        shadow = self.root / 'r1-shadow'
        (shadow / 'research').mkdir(parents=True)
        for name in ('verify_fdq.py', 'fdq_oracle.py'):
            shutil.copyfile(R1 / 'research' / name, shadow / 'research' / name)
        (shadow / 'research/fractions.py').write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("executed")\nraise RuntimeError("UNPINNED_SIBLING")\n')
        response = self.cli(r1=shadow)
        self.assertFalse(marker.exists(), 'Unpinned sibling was executed')
        self.assertEqual(response['decisions'][0]['state'], 'PR_JUSTIFIED_RESULT')

    def test_old_producer_receipt_is_reverified_explicitly_not_reused(self):
        shutil.rmtree(self.input)
        fixture = SOURCE / 'examples/legacy_c1_hours_case.zip'
        self.assertEqual(sha(fixture.read_bytes()), 'd27189f5e230d5cd5a10c302f18f1244c1f4068ab6b02310212e1541805820cf')
        with zipfile.ZipFile(fixture) as archive:
            archive.extractall(self.root)
        self.request = json.loads((self.input / 'request.json').read_bytes())
        old_objects = {path.name: path.read_bytes() for path in (self.case / 'objects').iterdir()}
        old = self.cli('inspect')
        self.assertNotIn('producer', old['latest'])
        self.assertEqual(old['latest']['response']['decisions'][0]['state'], 'PR_JUSTIFIED_RESULT')
        self.next_revision('Ordinary repetition', ['OP1'])
        self.assertEqual(self.cli('continue', expected=2)['reason'], 'IMPLEMENTATION_CHANGED_REQUIRES_EXPLICIT_REVERIFICATION')
        self.next_revision('REVERIFY_IMPLEMENTATION_CHANGED', ['OP1'])
        response = self.cli('continue')
        self.assert_not_closed(response)
        latest = self.cli('inspect')['latest']
        self.assertIn('producer', latest)
        self.assertFalse(any(event.get('type') == 'LOCAL_RECEIPT_REUSE' for outcome in latest['outcomes'] for event in outcome['evidence']))
        self.assertTrue(all((self.case / 'objects' / name).read_bytes() == raw for name, raw in old_objects.items()))
        self.next_revision('REVERIFY_IMPLEMENTATION_CHANGED', ['OP1'])
        self.assertEqual(self.cli('continue', expected=2)['reason'], 'NO_PERTINENT_NOVELTY')

    def test_interrupted_old_producer_requires_explicit_new_verification(self):
        shutil.rmtree(self.input)
        with zipfile.ZipFile(SOURCE / 'examples/legacy_c1_hours_case.zip') as archive:
            archive.extractall(self.root)
        self.request = json.loads((self.input / 'request.json').read_bytes())
        # Replay the preserved outcome checkpoint as a process interruption;
        # leave the later complete revision present as an unadopted orphan.
        checkpoint = '9f4031a1022927d9bce33d288a4b78d1731251f89d7f9049f8c845380f380086'
        (self.case / 'HEAD').write_bytes(encode({'format': 'genius-local-head/0.1.0', 'sha256': checkpoint}))
        before = {str(path.relative_to(self.case)): path.read_bytes()
                  for group in ('objects', 'revisions') for path in (self.case / group).iterdir()}
        current = self.cli('inspect')
        self.assertEqual(current['latest']['phase'], 'RUNNING')
        self.assertEqual(current['latest']['outcomes'][0]['status'], 'CONDITIONAL')
        rejected = self.cli('recover', expected=2)
        self.assertEqual(rejected['reason'], 'IMPLEMENTATION_CHANGED_REQUIRES_EXPLICIT_REVERIFICATION')
        self.assertEqual(self.cli('inspect')['head'], checkpoint)
        self.next_revision('REVERIFY_IMPLEMENTATION_CHANGED', ['OP1'])
        self.assert_not_closed(self.cli('continue'))
        self.assertTrue(all((self.case / name).read_bytes() == raw for name, raw in before.items()))
        self.assertTrue(self.cli('inspect')['uncommitted_revisions'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
