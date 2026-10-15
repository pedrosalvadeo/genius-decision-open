"""Causal adapter, persistence, unchanged controls, and frozen evidence replay."""
import copy
import importlib.util
from pathlib import Path
import sqlite3
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from genius_beta.db import transaction

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('regulation_history_study',ROOT/'beta/tools/regulation_history_study.py')
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


class HistoryAdapter(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:',isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript((ROOT/'beta/migrations/011_mission_regulation.sql').read_text())
        self.addCleanup(self.db.close)
        self.now = 1_000_000_000
        self.decisions = []
        self.rt = self.load_adapter()
        self.config = dict(ADAPTIVE_ENABLED=True,MISSION_REGULATION_ENABLED=True,
                           MAX_DATABASE_BYTES=100*1024**2,MIN_FREE_BYTES=10*1024**2)

    def load_adapter(self):
        rt = study.controller(15,self.decisions)
        rt.time = SimpleNamespace(time=lambda:self.now)
        rt.observe = lambda *_:dict(storage_bytes=1000,free_bytes=1024**3,pending=0)
        return rt

    def attempt(self,outcome='failed',reason='MISSION_PROCESS_FAILED'):
        rt = self.rt
        state = rt.load(self.db)
        self.now = max(self.now,state['cooldown_until'])
        with transaction(self.db):
            state = rt.refresh(self.db,self.config,force=True)
            token = rt.begin(self.db,self.config,state)
            self.now += 5
            rt.finish(self.db,self.config,token,outcome,reason)
        return rt.load(self.db)

    def test_wait_uses_observed_count_and_is_bounded(self):
        self.assertEqual([study.wait_after_failures(n,15) for n in range(1,7)],[60,60,60,75,90,105])
        self.assertEqual(study.wait_after_failures(1000,60),180)
        for args in ((True,15),(-1,15),(4,True),(4,1)):
            with self.assertRaises(ValueError): study.wait_after_failures(*args)

    def test_first_pause_then_failed_probe_increases_wait(self):
        for _ in range(3): state = self.attempt()
        self.assertEqual(state['cooldown_until']-self.now,60)
        state = self.attempt()
        self.assertEqual(state['cooldown_until']-self.now,75)
        self.assertEqual([d['wait_seconds'] for d in self.decisions],[60,75])
        self.assertEqual(self.rt.POLICY['cooldown_seconds'],60)

    def test_success_resets_and_neutral_result_does_not_erase_history(self):
        for _ in range(4): self.attempt()
        state = self.attempt('needs_review','DOMAIN_REJECTED')
        self.assertEqual(state['failures'],4)
        self.assertEqual(len(self.decisions),2)
        state = self.attempt()
        self.assertEqual(state['cooldown_until']-self.now,90)
        state = self.attempt('completed',None)
        self.assertEqual(state['failures'],0)
        for _ in range(3): state = self.attempt()
        self.assertEqual(state['cooldown_until']-self.now,60)

    def test_history_survives_loading_a_new_adapter(self):
        for _ in range(4): self.attempt()
        identity = self.rt.POLICY_SHA
        self.rt = self.load_adapter()
        self.assertEqual(self.rt.POLICY_SHA,identity)
        state = self.attempt()
        self.assertEqual(state['failures'],5)
        self.assertEqual(state['cooldown_until']-self.now,90)

    def test_wrong_token_rolls_back_and_restores_private_policy(self):
        for _ in range(3): self.attempt()
        before = self.rt.load(self.db)
        decisions = list(self.decisions)
        with self.assertRaisesRegex(RuntimeError,'IDENTITY_CHANGED'),transaction(self.db):
            self.rt.finish(self.db,self.config,'wrong-token','failed','MISSION_PROCESS_FAILED')
        self.assertEqual(self.rt.load(self.db),before)
        self.assertEqual(self.decisions,decisions)
        self.assertEqual(self.rt.POLICY['cooldown_seconds'],60)

    def test_only_classified_operational_failures_escalate(self):
        for _ in range(5): self.attempt('failed','MISSION_EXECUTION_FAILED')
        self.assertEqual(self.rt.load(self.db)['failures'],0)
        self.assertEqual(self.decisions,[])


class HistoryStudy(unittest.TestCase):
    def setUp(self):
        self.plan = study.read(study.EXPERIMENT/'plan.json')

    def test_step_zero_matches_frozen_simulator_on_all_new_trajectories(self):
        old_plan = study.read(study.legacy.EXPERIMENT/'plan.json')
        for name in ('training.json','evaluation.json'):
            for case in study.scenarios(name):
                with self.subTest(case=case['id']):
                    old = study.legacy.simulate(case,60,old_plan)
                    new = study.simulate(case,0,self.plan)
                    for key in ('metrics','mode_seconds','trace_sha256','policy_sha256'):
                        self.assertEqual(new[key],old[key])

    def test_unobserved_future_changes_cannot_change_earlier_decisions(self):
        common = dict(id='causality',horizon=600,duration=5,arrivals=list(range(0,500,10)),
                      failures=[[0,180]],storage=[],sensors=[])
        future = {**common,'failures':[[0,180],[300,450]]}
        a,b = [study.simulate(c,30,self.plan) for c in (common,future)]
        prefix = lambda r:[d for d in r['policy_decisions'] if d['observed_at']<=180]
        self.assertTrue(prefix(a))
        self.assertEqual(prefix(a),prefix(b))

    def test_training_does_not_parse_evaluation(self):
        names, original = [],study.scenarios
        def training_only(name):
            names.append(name)
            if name!='training.json': raise AssertionError('held-out leak')
            return original(name)
        with patch.object(study,'scenarios',side_effect=training_only):
            candidate = study.train(study.lock_inputs())
        self.assertEqual(names,['training.json'])
        self.assertIn(candidate['selected_step_seconds'],[15,30,60])

    def test_fresh_scenarios_are_not_renamed_old_or_training_cases(self):
        identity = lambda c:study.digest({k:v for k,v in c.items() if k!='id'})
        old = {identity(c) for name in ('training.json','evaluation.json') for c in study.legacy.scenarios(name)}
        training = {identity(c) for c in study.scenarios('training.json')}
        evaluation = {identity(c) for c in study.scenarios('evaluation.json')}
        self.assertFalse(old & (training|evaluation))
        self.assertFalse(training & evaluation)

    def test_frozen_candidate_cannot_be_replaced_after_training(self):
        lock = study.lock_inputs()
        candidate = study.train(lock)
        candidate['selected_step_seconds'] = 0
        with self.assertRaisesRegex(ValueError,'CANDIDATE_NOT_FROZEN'):
            study.evaluate(lock,candidate)

    def test_source_changes_invalidate_lock(self):
        lock = study.lock_inputs()
        lock['files']['beta/tools/regulation_history_study.py'] = '0'*64
        with self.assertRaisesRegex(ValueError,'HISTORY_STUDY_INPUT_CHANGED'):
            study.train(lock)

    def test_report_replay_and_limits(self):
        evidence = ROOT/'adaptive/evidence/2026-10-15-regulation-history'
        report = study.evaluate(study.read(evidence/'lock.json'),study.read(evidence/'candidate.json'))
        self.assertEqual(report,study.read(evidence/'evaluation.json'))
        self.assertFalse(report['production_promotion'])
        for pair in report['cases']:
            for side in ('baseline','candidate'):
                self.assertEqual(pair[side]['metrics']['safety_violations'],0)
                self.assertLessEqual(pair[side]['metrics']['max_pending'],4)
                for decision in pair[side]['policy_decisions']:
                    self.assertGreaterEqual(decision['wait_seconds'],60)
                    self.assertLessEqual(decision['wait_seconds'],180)


if __name__=='__main__':
    unittest.main()
