"""Independent arithmetic, holdout separation and durable estimate delivery."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from genius_adaptive.calibration import Calibration, prepare, validate_input
from genius_adaptive.runtime import run
from genius_adaptive.journal import Conflict


def example(training=(90,100,110), validation=(100,105), baseline=50, limit=10):
    rows=[dict(id=f'obs-{i}',value=v,observed_at=f'2026-01-{i:02d}T12:00:00Z',source='synthetic fixture')
          for i,v in enumerate((*training,*validation),1)]
    return dict(context='Constant operation A',resource='water',unit='millilitre',
        baseline=baseline,max_underprediction=limit,data_kind='synthetic',
        training=rows[:len(training)],validation=rows[len(training):])


class Learning(unittest.TestCase):
    def execute(self, data, hook=None):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        directory=Path(temp.name)/'mission'
        prepare(data,directory,'test-calibration')
        result=run(directory,Calibration(),after_stage=hook)
        return directory,result['memory']

    def test_holdout_oracle_and_internal_adoption(self):
        directory,memory=self.execute(example())
        self.assertEqual(memory['proposal'],100)
        self.assertEqual(memory['decision'],'ADOPT_PROPOSAL')
        self.assertEqual(memory['comparison']['baseline']['absolute_error_sum'],105)
        self.assertEqual(memory['comparison']['proposal']['absolute_error_sum'],5)
        self.assertEqual(memory['estimate'],100)
        self.assertEqual(memory['prospective_validation'],'PENDING')
        self.assertEqual(memory['life_sustainment_effect'],'UNMEASURED')
        native=json.loads((directory/'evidence/evaluate.json').read_text())['native']
        self.assertTrue(native['verification']['valid'])
        self.assertEqual(native['canonical_results']['decision']['selected'],'proposal')
        self.assertTrue(run(directory,Calibration())['reused'])

    def test_validation_cannot_fit_proposal_and_shift_is_rejected(self):
        _,first=self.execute(example(validation=(0,0)))
        _,second=self.execute(example(validation=(100,105)))
        self.assertEqual(first['proposal'],second['proposal'])
        self.assertEqual(first['decision'],'KEEP_BASELINE')
        self.assertEqual(second['decision'],'ADOPT_PROPOSAL')

    def test_lower_error_is_insufficient_if_underprediction_worsens(self):
        _,memory=self.execute(example(baseline=150))
        self.assertTrue(memory['checks']['lower_holdout_error'])
        self.assertFalse(memory['checks']['no_worse_underprediction'])
        self.assertEqual(memory['estimate'],150)

    def test_declared_limit_and_ties_preserve_baseline(self):
        for data in (example(limit=0),example(training=(0,0,0),validation=(0,0),baseline=0),
                     example(training=(40,50,60),validation=(40,60),baseline=50)):
            with self.subTest(data=data):
                _,memory=self.execute(data)
                self.assertEqual(memory['decision'],'KEEP_BASELINE')
                self.assertEqual(memory['estimate'],data['baseline'])

    def test_even_training_uses_lower_median_without_fractional_units(self):
        _,memory=self.execute(example(training=(2,4,6,8),validation=(4,5),baseline=0))
        self.assertEqual(memory['proposal'],4)

    def test_invalid_units_samples_provenance_and_chronology(self):
        mutations=[lambda x:x.update(baseline=True), lambda x:x.update(baseline=1.1),
            lambda x:x.update(unit=''),lambda x:x.update(data_kind='sensor_verified'),
            lambda x:x['validation'][0].update(id=x['training'][0]['id']),
            lambda x:x['validation'][0].update(observed_at='2025-12-01T00:00:00Z'),
            lambda x:x['training'][0].update(observed_at='2026-01-01T00:00:00'),
            lambda x:x['training'][0].update(source=''),
            lambda x:x['training'][0].update(value=-1),lambda x:x.update(training=x['training'][:2])]
        for change in mutations:
            data=deepcopy(example());change(data)
            with self.assertRaises(ValueError):validate_input(data)

    def test_restart_after_effect_preserves_artifact(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        directory=Path(temp.name)/'mission';prepare(example(),directory,'restart')
        def interrupt(stage):
            if stage=='act':raise RuntimeError('simulated interruption after durable effect')
        with self.assertRaises(RuntimeError):run(directory,Calibration(),after_stage=interrupt)
        raw=(directory/'delivery/resource-estimate.json').read_bytes()
        result=run(directory,Calibration())
        self.assertEqual(result['status'],'completed')
        self.assertEqual((directory/'delivery/resource-estimate.json').read_bytes(),raw)
        (directory/'delivery/resource-estimate.json').write_text('changed')
        with self.assertRaises(Conflict):run(directory,Calibration())

    def test_input_mutation_is_not_new_evidence(self):
        directory,_=self.execute(example())
        (directory/'input/observations.json').write_text('{}')
        with self.assertRaises(Conflict):run(directory,Calibration())
