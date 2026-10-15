"""No-future-data, strategy switching, scoring, and interrupted I/O boundaries."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from observers import context_study, http_latency as source, strategies


def plan(**overrides):
    return dict(format='genius-context-study/1', rule=strategies.RULE, baseline=50,
                baseline_reference='Synthetic fixture, not field evidence', max_underprediction=50,
                warmup_count=3, scored_count=12, context='PREVIOUS_VALUE_GT_FROZEN_BASELINE',
                strategies=list(strategies.ORDER),
                selection='PAST_SCORED_SAME_CONTEXT_MIN3_GUARDED_LOWEST_ERROR_FIXED_TIES',
                stopping='FIXED_COUNT_OR_FIRST_FAILED_OR_UNKNOWN_MEASUREMENT', **overrides)


def simulate(values, config):
    history = []
    for value in values:
        history.append(dict(**strategies.predict(history, config), value=value))
    return history


class PredictionTests(unittest.TestCase):
    def test_selection_learns_context_from_past_then_scores_the_executed_policy(self):
        config = plan()
        history = simulate([10, 100] * 7 + [10], config)
        self.assertEqual({row['selected'] for row in history}, {'baseline', 'context_median'})
        for row in history:
            if row['selection_count'] < 3:
                self.assertEqual(row['selected'], 'baseline')
        result = strategies.report(history, config)
        self.assertEqual(result['outcome'], 'OBSERVED_GUARDED_IMPROVEMENT')
        self.assertLess(result['comparison']['adaptive']['absolute_error_sum'],
                        result['comparison']['baseline']['absolute_error_sum'])
        self.assertTrue(result['native']['verification']['valid'])
        # Warmup does not count as evidence; each scored target is used once.
        self.assertEqual(result['comparison']['adaptive']['count'], 12)
        self.assertEqual(result['comparison']['adaptive']['absolute_error_sum'],
                         sum(abs(row['predictions']['adaptive'] - row['value']) for row in history[3:]))

    def test_unseen_future_cannot_change_any_prior_prediction(self):
        config = plan()
        a = simulate([10, 100] * 5 + [20, 20, 20, 20, 20], config)
        b = simulate([10, 100] * 5 + [999999] * 5, config)
        self.assertEqual(a[:10], b[:10])
        for key in a[10]:
            if key != 'value':
                self.assertEqual(a[10][key], b[10][key])
        self.assertNotEqual(a[11]['context'], b[11]['context'])

    def test_context_is_previous_target_not_current_value_and_window_is_bounded(self):
        config = plan()
        history = simulate([50, 100, 1, 80, 2], config)
        self.assertEqual(history[0]['context'], 'unknown')
        self.assertEqual(history[1]['context'], 'previous_at_or_below_baseline')
        self.assertEqual(history[2]['context'], 'previous_above_baseline')
        prediction = strategies.predict(history, config)
        self.assertEqual(prediction['predictions']['rolling_median'], 2)
        self.assertEqual(prediction['predictions']['last_value'], 2)
        self.assertEqual(prediction['predictions']['context_median'], 80)  # preceding targets 100,80

    def test_ties_keep_base_and_limit_blocks_adoption_even_with_lower_error(self):
        config = plan()
        history = simulate([50] * 15, config)
        self.assertTrue(all(row['selected'] == 'baseline' for row in history))
        self.assertEqual(strategies.report(history, config)['outcome'], 'NO_CONFIRMED_IMPROVEMENT')
        base = dict(absolute_error_sum=100, max_underprediction=70)
        proposed = dict(absolute_error_sum=30, max_underprediction=20)
        self.assertFalse(all(strategies.guards(proposed, base, 10).values()))
        proposed['max_underprediction'] = 80
        self.assertFalse(strategies.guards(proposed, base, 100)['no_worse_underprediction'])

    def test_warmup_cannot_select_a_winner_and_future_reversal_can_lose(self):
        config = plan()
        history = simulate([10] * 10 + [1000] * 5, config)
        self.assertTrue(all(row['selected'] == 'baseline' for row in history[:6]))
        self.assertNotEqual(strategies.report(history, config)['outcome'], 'OBSERVED_GUARDED_IMPROVEMENT')


class Clock:
    def __init__(self):
        self.when = datetime(2026, 10, 15, tzinfo=timezone.utc)

    def __call__(self):
        self.when += timedelta(seconds=1)
        return self.when.isoformat()


class Response(io.BytesIO):
    status = 200


class StudyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name) / 'study'
        self.clock, self.config = Clock(), plan()
        self.calls = 0

    def sample(self, sample_id):
        self.calls += 1
        # Inspect on-disk prediction before collecting this target.
        latest = sorted((self.directory / 'events').glob('*.json'))[-1]
        self.assertEqual(json.loads(latest.read_text())['event']['kind'], 'PREDICT')
        opener = Mock()
        opener.open.return_value = Response(b'{"status":"ok","backup":"ok","suspended":false}')
        clock = iter((0, (10 if self.calls % 2 else 100) * 1000000))
        return source.sample(sample_id, opener=opener, wall=self.clock, monotonic=lambda: next(clock))

    def study(self, sampler=None):
        return context_study.Study(self.directory, self.config, sampler=sampler or self.sample, wall=self.clock)

    def test_full_native_cycle_resumes_without_network_or_rewriting_evidence(self):
        result = self.study().run()
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(self.calls, 15)
        before = (self.directory / 'evidence.json').read_bytes()
        self.assertEqual(result, self.study().run())
        self.assertEqual(self.calls, 15)
        self.assertEqual(before, (self.directory / 'evidence.json').read_bytes())

    def test_unknown_network_result_is_not_retried(self):
        sampler = Mock(side_effect=TimeoutError())
        with self.assertRaises(TimeoutError): self.study(sampler).run()
        with self.assertRaisesRegex(ValueError, 'MEASUREMENT_OUTCOME_UNKNOWN'): self.study(sampler).run()
        self.assertEqual(sampler.call_count, 1)

    def test_committed_observation_recovers_without_repeating_the_target(self):
        study = self.study()
        original = study.append
        def append(kind, body):
            result = original(kind, body)
            if kind == 'OBSERVE': raise RuntimeError('simulated process exit')
            return result
        with patch.object(study, 'append', append):
            with self.assertRaises(RuntimeError): study.run()
        result = self.study().run()
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(self.calls, 15)

    def test_failed_sample_is_retained_and_blocks_a_new_attempt(self):
        def failed(sample_id):
            item = self.sample(sample_id)
            item['measurement'].update(outcome='REJECTED', failure='TRANSPORT_FAILURE')
            item['observation'] = None
            item['sha256'] = source.digest(item['measurement'])
            return item
        for _ in range(2):
            with self.assertRaisesRegex(ValueError, 'SOURCE_SAMPLE_REJECTED'): self.study(failed).run()
        self.assertEqual(self.calls, 1)
        self.assertEqual(len(list((self.directory / 'events').glob('*.json'))), 3)

    def test_code_or_plan_change_refuses_resume(self):
        self.study().run()
        with patch.object(context_study, 'identity', return_value={}):
            with self.assertRaisesRegex(ValueError, 'PLAN_OR_CODE_CHANGED'): self.study().run()
        self.config['max_underprediction'] = 49
        with self.assertRaisesRegex(ValueError, 'PLAN_OR_CODE_CHANGED'): self.study().run()

    def test_chronology_mapping_and_forged_predictions_are_rejected(self):
        study = self.study(); study.run()
        observation = deepcopy(study.entries[2]['event']['body'])
        intent = study.entries[1]['event']
        saved_at = study.entries[2]['event']['at']
        observation['observation']['value'] += 1
        with self.assertRaisesRegex(ValueError, 'SOURCE_MAPPING'):
            study.validate_sample(observation, intent, saved_at)
        observation = deepcopy(study.entries[2]['event']['body'])
        observation['measurement']['started_at'] = intent['at']
        observation['sha256'] = source.digest(observation['measurement'])
        observation['observation'] = source.observation(observation['measurement'])
        with self.assertRaisesRegex(ValueError, 'SOURCE_CHRONOLOGY'):
            study.validate_sample(observation, intent, saved_at)
        study.entries[1]['event']['body']['predictions']['adaptive'] += 1
        with self.assertRaisesRegex(ValueError, 'PREDICTION_NOT_PAST_ONLY'): study.replay()

    def test_tamper_missing_event_concurrency_and_symlinks_are_rejected(self):
        self.study().run()
        event_path = self.directory / 'events' / '0002.json'
        original = event_path.read_text()
        event = json.loads(original); event['event']['body']['observation']['value'] = 999
        event_path.write_text(json.dumps(event))
        with self.assertRaisesRegex(ValueError, 'EVENT_INTEGRITY'): self.study().run()
        event_path.write_text(original)
        with context_study.exclusive(self.directory):
            with self.assertRaisesRegex(ValueError, 'MISSION_BUSY'): self.study().run()
        event_path.unlink()
        with self.assertRaisesRegex(ValueError, 'EVENT_SEQUENCE'): self.study().run()
        event_path.symlink_to(self.directory / 'events' / '0001.json')
        with self.assertRaisesRegex(ValueError, 'STATE_SYMLINK'): self.study().run()


if __name__ == '__main__':
    unittest.main()
