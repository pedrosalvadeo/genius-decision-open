from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from genius_evolution import model, pipeline

ROOT = Path(__file__).resolve().parents[2]
BASE = 'a' * 40


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT/'evolution', self.root/'evolution', ignore=shutil.ignore_patterns('__pycache__', 'candidates', 'proposals', 'evidence'))
        for name in ['adaptive/genius_adaptive/contextual.py', '.github/workflows/code-evolution.yml',
                     'adaptive/evidence/2026-10-15-context-api/live-probe.json']:
            dest = self.root/name; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(ROOT/name, dest)
        self.spec_path = self.root/'evolution/requests/context-affine-001.json'
        self.spec = pipeline.strict(self.spec_path.read_bytes())
        self.manifest()

    def manifest(self):
        files = {str(p.relative_to(self.root)): pipeline.digest(p.read_bytes()) for p in self.root.rglob('*')
                 if p.is_file() and p.name != 'PUBLICATION_MANIFEST.json'}
        (self.root/'PUBLICATION_MANIFEST.json').write_bytes(pipeline.encoded(dict(format='genius-publication-files/1', files=files)))

    def data(self, split):
        return pipeline.strict((self.root/self.spec[split]['path']).read_bytes())

    def change_data(self, split, value):
        raw = pipeline.encoded(value); (self.root/self.spec[split]['path']).write_bytes(raw)
        self.spec[split]['sha256'] = pipeline.digest(raw); self.save_spec()

    def save_spec(self):
        self.spec_path.write_bytes(pipeline.encoded(self.spec))

    def report(self, bundle):
        return pipeline.strict(next(v for k, v in bundle['files'].items() if k.endswith('proposal.json')))


class SynthesisTests(Fixture):
    def test_complete_cycle_generates_new_python_but_rejects_regressions(self):
        bundle = pipeline.prepare(self.root, BASE)
        report = self.report(bundle)
        self.assertEqual(report['model'], dict(lag=1, a=-1, b=110, denominator=1))
        self.assertIn('-1 * history[-1] + 110', next(v for k,v in bundle['files'].items() if k.endswith('.py')))
        self.assertLess(report['training'][0]['candidate']['weighted_loss'], report['training'][0]['incumbent']['weighted_loss'])
        self.assertEqual(report['decision'], 'REJECTED_BY_EVALUATION')
        self.assertFalse(report['promotion_eligible']); self.assertFalse(report['production_activated'])
        steady = next(r for r in report['evaluation'] if r['id'] == 'steady-midpoint')
        self.assertGreater(steady['candidate']['weighted_loss'], steady['incumbent']['weighted_loss'])
        self.assertEqual(bundle, pipeline.prepare(self.root, BASE))
        self.assertEqual(bundle, pipeline.verify_bundle(self.root, bundle))

    def test_synthesis_uses_training_only_even_when_evaluation_changes(self):
        first = self.report(pipeline.prepare(self.root, BASE))
        data = self.data('evaluation'); data['cases'] = data['cases'][:2]
        self.change_data('evaluation', data)
        second = self.report(pipeline.prepare(self.root, BASE))
        self.assertEqual(first['model'], second['model'])
        self.assertEqual(first['candidate_sha256'], second['candidate_sha256'])
        self.assertNotEqual(first['request_sha256'], second['request_sha256'])
        self.assertEqual(second['decision'], 'ELIGIBLE_FOR_REVIEW')
        self.assertTrue(second['promotion_eligible']); self.assertFalse(second['production_activated'])

    def test_changed_training_produces_different_code_without_handwritten_coefficients(self):
        spec, _, _ = pipeline.request(self.root)
        a, _ = model.discover([dict(values=[10,100]*8)], spec)
        b, _ = model.discover([dict(values=[20,90]*8)], spec)
        c, _ = model.discover([dict(values=[30,90]*8)], spec)
        self.assertEqual(a['model'], b['model'])
        self.assertNotEqual(model.render(a['model']), model.render(c['model']))
        self.assertEqual(c['model']['b'], 120)

    def test_weighted_loss_and_limits_have_explicit_units_and_integer_bounds(self):
        result = model.loss([10,100], [20,80], dict(under_cost=3, over_cost=2))
        self.assertEqual(result['weighted_loss'], 70)
        for field, value in [('under_cost',0), ('over_cost',True), ('baseline',1.5), ('warmup_count',2)]:
            spec = deepcopy(self.spec); spec[field] = value
            self.spec_path.write_bytes(pipeline.encoded(spec))
            with self.assertRaisesRegex(ValueError, 'OBJECTIVE_BOUNDS'): pipeline.prepare(self.root, BASE)

    def test_no_holdout_reuse_or_private_data_claims(self):
        self.spec['data_kind'] = 'real'; self.save_spec()
        with self.assertRaisesRegex(ValueError, 'PUBLIC_DATA_ONLY'): pipeline.prepare(self.root, BASE)
        self.spec['data_kind'] = 'synthetic'; self.save_spec()
        data = self.data('evaluation'); data['cases'][0]['values'] = self.data('training')['cases'][0]['values']
        self.change_data('evaluation',data)
        with self.assertRaisesRegex(ValueError, 'SPLIT_VALUES_REUSE'): pipeline.prepare(self.root,BASE)

    def test_corrupt_memory_and_changed_source_fail_closed(self):
        data = self.data('training'); data['cases'][0]['values'][4] += 1; self.change_data('training',data)
        with self.assertRaisesRegex(ValueError, 'PROBE_VALUES'): pipeline.prepare(self.root, BASE)
        self.setUp()  # independent fixture with original source/provenance
        source = self.root/'adaptive/genius_adaptive/contextual.py'; source.write_bytes(source.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError, 'PROBE_PLAN'): pipeline.prepare(self.root, BASE)

    def test_paths_hashes_duplicate_keys_and_ranges(self):
        for name in ('/etc/passwd','../secrets','evolution/data/../private','evolution//data/a'):
            with self.assertRaises(ValueError): pipeline.local(self.root,name,'evolution/data/')
        link=self.root/'evolution/data/link'; link.symlink_to(self.spec_path)
        with self.assertRaisesRegex(ValueError,'SYMLINK'): pipeline.local(self.root,'evolution/data/link')
        for text in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.assertRaises(ValueError): pipeline.strict(text)
        data=self.data('evaluation'); data['cases'][0]['values'][0]=True; self.change_data('evaluation',data)
        with self.assertRaisesRegex(ValueError,'VALUES'): pipeline.prepare(self.root,BASE)

    def test_approved_source_executes_in_clean_child_and_matches_exact_reference(self):
        fitted=dict(lag=1,a=-1,b=110,denominator=1); cases=[dict(values=[0,1,10,100,110,1000000])]
        with patch.dict(os.environ, {'GH_TOKEN':'should-not-pass', 'DATABASE_URL':'should-not-pass'}):
            actual=model.execute(model.render(fitted),fitted,cases,50)
            self.assertEqual(actual,[[50,110,109,100,10,0]])
            real_run=subprocess.run
            def check(*args,**kwargs):
                self.assertNotIn('GH_TOKEN',kwargs['env']); self.assertNotIn('DATABASE_URL',kwargs['env'])
                self.assertIn('-I',args[0]); self.assertIn('-S',args[0]); self.assertEqual(kwargs['timeout'],5)
                return real_run(*args,**kwargs)
            with patch.object(model.subprocess,'run',side_effect=check):
                model.execute(model.render(fitted),fitted,cases,50)
        with patch.object(model.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError,'UNAPPROVED_SOURCE'):
                model.execute(model.render(fitted)+'\nimport os\n',fitted,cases,50)
            run.assert_not_called()

    def test_timeout_does_not_produce_an_eligible_report(self):
        with patch.object(model.subprocess,'run',side_effect=subprocess.TimeoutExpired('fixed-worker',5)):
            with self.assertRaises(subprocess.TimeoutExpired): pipeline.prepare(self.root,BASE)

    def test_bundle_tampering_and_unlisted_write_are_rejected(self):
        bundle=pipeline.prepare(self.root,BASE)
        for modification in ('source','report','extra'):
            bad=deepcopy(bundle)
            if modification=='source':
                name=next(k for k in bad['files'] if k.endswith('.py')); bad['files'][name]+='\n'
            elif modification=='report':
                name=next(k for k in bad['files'] if k.endswith('proposal.json'))
                report=pipeline.strict(bad['files'][name]); report['promotion_eligible']=True
                bad['files'][name]=pipeline.encoded(report).decode()
            else:bad['files']['beta/genius_beta/app.py']='changed'
            bad['hashes']={k:pipeline.digest(v.encode()) for k,v in bad['files'].items()}
            with self.assertRaisesRegex(ValueError,'BUNDLE_RECOMPUTATION'): pipeline.verify_bundle(self.root,bad)

    def test_publication_manifest_matches_all_generated_bytes_and_old_files(self):
        bundle=pipeline.prepare(self.root,BASE); files=pipeline.tree_files(self.root,bundle)
        manifest=pipeline.strict(files['PUBLICATION_MANIFEST.json'])
        for name, text in bundle['files'].items():self.assertEqual(manifest['files'][name],pipeline.digest(text.encode()))
        self.spec_path.write_bytes(self.spec_path.read_bytes()+b' ')
        with self.assertRaises(ValueError):pipeline.tree_files(self.root,bundle)

    def test_generated_proposal_in_a_pr_is_checked_against_current_request(self):
        self.assertEqual(pipeline.audit_current(self.root)['status'],'NO_CURRENT_PROPOSAL_IN_CHECKOUT')
        bundle=pipeline.prepare(self.root,BASE)
        for name,text in bundle['files'].items():
            p=self.root/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text)
        self.assertEqual(pipeline.audit_current(self.root)['status'],'CURRENT_PROPOSAL_VERIFIED')
        name=next(p for p in bundle['files'] if p.endswith('.py'))
        (self.root/name).write_text('def predict(history, baseline): return 0\n')
        with self.assertRaisesRegex(ValueError,'PUBLISHED_PROPOSAL_CHANGED'):pipeline.audit_current(self.root)


if __name__=='__main__':unittest.main()
