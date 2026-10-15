"""Independent small-system oracles, leakage checks and frozen-report replay."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from genius_beta import regulation

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('regulation_study', ROOT/'beta/tools/regulation_study.py')
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class RegulationStudy(unittest.TestCase):
    def setUp(self):
        self.plan = study.read(study.EXPERIMENT/'plan.json')

    def case(self, **updates):
        return dict(dict(id='oracle',horizon=120,duration=5,arrivals=[0],failures=[],storage=[],sensors=[]),**updates)

    def run_case(self, cooldown=60, **updates):
        return study.simulate(self.case(**updates),cooldown,self.plan)

    def test_fifo_exposure_counts_every_request_including_wait(self):
        result = self.run_case(duration=10,arrivals=[0,0])['metrics']
        self.assertEqual(result['completed'],2)
        self.assertEqual(result['exposure_seconds'],30)
        self.assertEqual(result['max_success_latency_seconds'],20)
        self.assertEqual(result['loss'],30)

    def test_real_controller_waits_after_three_failures_then_one_probe(self):
        result = self.run_case(arrivals=[0,0,0,0],failures=[[0,60]])
        self.assertEqual(result['metrics']['operational_failures'],3)
        self.assertEqual(result['metrics']['completed'],1)
        self.assertEqual(result['metrics']['max_success_latency_seconds'],80)
        self.assertEqual(result['metrics']['exposure_seconds'],110)
        self.assertEqual(result['mode_seconds']['COOLDOWN'],60)
        self.assertEqual(result['mode_seconds']['PROBING'],5)
        self.assertEqual(result['metrics']['safety_violations'],0)

    def test_longer_policy_does_not_hide_unfinished_work_at_horizon(self):
        result = self.run_case(cooldown=120,arrivals=[0,0,0,0],failures=[[0,60]])['metrics']
        self.assertEqual(result['operational_failures'],3)
        self.assertEqual(result['completed'],0)
        self.assertEqual(result['unfinished'],1)
        self.assertEqual(result['exposure_seconds'],150)
        self.assertEqual(result['loss'],550)

    def test_storage_and_unavailable_sensor_both_pause_admission_and_start(self):
        for field in ('storage','sensors'):
            with self.subTest(field=field):
                result = self.run_case(arrivals=[0,0],**{field:[[0,20]]})['metrics']
                self.assertEqual(result['completed'],2)
                self.assertEqual(result['exposure_seconds'],55)
                self.assertEqual(result['max_success_latency_seconds'],30)
                self.assertEqual(result['safety_violations'],0)

    def test_pressure_does_not_kill_already_running_work(self):
        result = self.run_case(duration=20,storage=[[5,40]])['metrics']
        self.assertEqual(result['completed'],1)
        self.assertEqual(result['exposure_seconds'],20)
        self.assertEqual(result['operational_failures'],0)

    def test_failure_window_overlap_and_endpoint_are_unambiguous(self):
        self.assertEqual(self.run_case(duration=10,failures=[[5,10]])['metrics']['operational_failures'],1)
        self.assertEqual(self.run_case(duration=5,failures=[[5,10]])['metrics']['completed'],1)

    def test_censor_running_and_not_yet_admitted_requests(self):
        result = self.run_case(horizon=60,duration=60,arrivals=[0]*10)['metrics']
        self.assertEqual(result['completed'],1)
        self.assertEqual(result['unfinished'],9)
        self.assertEqual(result['max_pending'],4)
        self.assertEqual(result['exposure_seconds'],600)

    def test_simulations_are_repeatable_and_do_not_mutate_imported_runtime(self):
        policy, sha = copy.deepcopy(regulation.POLICY),regulation.POLICY_SHA
        a = self.run_case(cooldown=90,arrivals=[0,0,0,0],failures=[[0,60]])
        b = self.run_case(cooldown=90,arrivals=[0,0,0,0],failures=[[0,60]])
        self.assertEqual(a,b)
        self.assertEqual(regulation.POLICY,policy)
        self.assertEqual(regulation.POLICY_SHA,sha)
        self.assertNotEqual(a['policy_sha256'],sha)

    def test_train_never_parses_or_scores_evaluation(self):
        lock = study.lock_inputs()
        original = study.scenarios
        names = []
        def training_only(name):
            names.append(name)
            if name != 'training.json': raise AssertionError('evaluation leak')
            return original(name)
        with patch.object(study,'scenarios',side_effect=training_only):
            study.train(lock)
        self.assertEqual(names,['training.json'])

    def test_candidate_substitution_is_rejected_before_evaluation(self):
        lock = study.lock_inputs()
        candidate = study.train(lock)
        candidate['selected_cooldown_seconds'] = 999
        with self.assertRaisesRegex(ValueError,'CANDIDATE_NOT_FROZEN'):
            study.evaluate(lock,candidate)

    def test_modified_lock_is_rejected(self):
        lock = study.lock_inputs()
        lock['files']['beta/genius_beta/regulation.py'] = '0'*64
        with self.assertRaisesRegex(ValueError,'STUDY_INPUT_CHANGED'):
            study.train(lock)

    def test_invalid_time_inputs_and_undeclared_policies_rejected(self):
        for change in (dict(duration=True),dict(arrivals=[10,0]),dict(sensors=[[20,10]]),dict(horizon=999999)):
            with self.subTest(change=change),self.assertRaises(ValueError):
                self.run_case(**change)
        with self.assertRaisesRegex(ValueError,'UNDECLARED_POLICY'):
            self.run_case(cooldown=30)

    def test_regressions_are_rejected_even_when_aggregate_loss_improves(self):
        before = self.run_case()
        after = copy.deepcopy(before)
        after['metrics'].update(loss=0,completed=0,unfinished=1,max_success_latency_seconds=100)
        gates = study.compare_case(before,after,self.plan)
        self.assertTrue(gates['loss_not_worse'])
        self.assertFalse(gates['completed_not_fewer'])
        self.assertFalse(gates['unfinished_not_more'])
        self.assertFalse(gates['latency_within_margin'])

    def test_saved_evaluation_recomputes_exactly(self):
        evidence = ROOT/'adaptive/evidence/2026-10-15-regulation-study'
        result = study.evaluate(study.read(evidence/'lock.json'),study.read(evidence/'candidate.json'))
        self.assertEqual(result,study.read(evidence/'evaluation.json'))
        self.assertFalse(result['production_promotion'])

    def test_existing_evidence_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'receipt.json'
            study.write_new(path,{'result':'first'})
            with self.assertRaises(FileExistsError): study.write_new(path,{'result':'changed'})
            self.assertEqual(study.read(path),{'result':'first'})


if __name__=='__main__':
    unittest.main()
