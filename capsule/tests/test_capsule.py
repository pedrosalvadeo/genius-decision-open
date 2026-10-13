import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('capsule', ROOT/'capsule/genius.py')
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)


class CapsuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.folder = Path(cls.temp.name)
        cls.run_dir = cls.folder/'run'
        cls.result = c.evaluate(ROOT/'twin/examples/stockflow_time.json', ROOT/'capsule/examples/synthetic-evidence.json', cls.run_dir)

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_native_execution_and_recomputation(self):
        self.assertEqual(self.result['status'], 'COMPLETE')
        self.assertEqual(c.verify(self.run_dir)['native_runs'], 2)
        self.assertFalse(self.result['empirical_validation'])

    def test_receipt_cannot_overwrite_previous_run(self):
        with self.assertRaisesRegex(ValueError, 'new'):
            c.evaluate(ROOT/'twin/examples/stockflow_time.json', ROOT/'capsule/examples/synthetic-evidence.json', self.run_dir)

    def test_changed_artifact_rejected(self):
        import shutil
        target = self.folder/'changed'; shutil.copytree(self.run_dir, target)
        with (target/'model.json').open('ab') as f: f.write(b' ')
        with self.assertRaisesRegex(ValueError, 'integrity'):
            c.verify(target)

    def test_forged_empirical_claim_rejected(self):
        import shutil
        target = self.folder/'claim'; shutil.copytree(self.run_dir, target)
        receipt = json.loads((target/'receipt.json').read_text())
        receipt['empirical_validation_by_this_execution'] = True
        (target/'receipt.json').write_bytes(c.encoded(receipt))
        with self.assertRaisesRegex(ValueError, 'inconsistent'): c.verify(target)

    def test_forged_summary_rejected_even_with_updated_hash(self):
        import shutil
        target = self.folder/'summary'; shutil.copytree(self.run_dir, target)
        result = json.loads((target/'evaluation.json').read_text())
        result['canonical_results']['decision']['selected'] = 'fabricated'
        (target/'evaluation.json').write_bytes(c.encoded(result))
        receipt = json.loads((target/'receipt.json').read_text())
        receipt['files']['evaluation.json'] = c.digest((target/'evaluation.json').read_bytes())
        (target/'receipt.json').write_bytes(c.encoded(receipt))
        with self.assertRaisesRegex(ValueError, 'recomputation'): c.verify(target)

    def test_real_requires_observation_and_source(self):
        e = json.loads((ROOT/'capsule/examples/synthetic-evidence.json').read_text()); e['origin'] = 'real'
        with self.assertRaisesRegex(ValueError, 'observations and sources'): c.evidence_record(e)
        e['sources'] = [{'id':'measurement', 'reference':'local laboratory record', 'accessed_at':'2026-10-13'}]
        e['observations'] = [{'statement':'A measured value', 'source_id':'unknown'}]
        with self.assertRaisesRegex(ValueError, 'identified source'): c.evidence_record(e)
        e['observations'][0]['source_id'] = 'measurement'
        self.assertEqual(c.evidence_record(e)['origin'], 'real')

    def test_strict_json_rejects_duplicate_and_nonfinite(self):
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            with self.assertRaises(ValueError): c.strict_json(raw)

    def test_contribution_handoff_and_tampering(self):
        p = self.folder/'contrib'; p.mkdir()
        (p/'finding.txt').write_text('Reproducible counterexample proposal')
        manifest = {'format':'genius-contribution/1','id':'C1','author':'test agent','summary':'Counterexample',
                    'base_revision':'test','kind':'mathematics','claim':'Claim to review','reproduction':'Read the proof; no command is executed',
                    'artifacts':[{'path':'finding.txt','sha256':c.digest((p/'finding.txt').read_bytes())}], 'review_status':'PROPOSED'}
        (p/'contribution.json').write_bytes(c.encoded(manifest))
        self.assertFalse(c.contribution(p/'contribution.json')['accepted_by_this_check'])
        (p/'handoff.json').write_bytes(c.encoded({'format':'genius-handoff/1','mission':'Build Genius', 'host':'test',
            'base_revision':'test','next_work':'Review claim','contributions':['contribution.json']}))
        self.assertFalse(c.handoff(p/'handoff.json')['authority_transfer'])
        (p/'finding.txt').write_text('Changed')
        with self.assertRaisesRegex(ValueError, 'changed'): c.contribution(p/'contribution.json')

    def test_external_file_reference_rejected(self):
        with self.assertRaises(ValueError): c.local_file(self.folder, '../outside')
        with self.assertRaises(ValueError): c.local_file(self.folder, '/etc/passwd')
        (self.folder/'escape').symlink_to('/etc/passwd')
        with self.assertRaises(ValueError): c.local_file(self.folder, 'escape')


if __name__ == '__main__': unittest.main()
