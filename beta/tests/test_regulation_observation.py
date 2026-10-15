"""A real SQLite/WAL journal, measured outcomes, bounded reads and private output."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from genius_beta import regulation as reg
from genius_beta.db import initialize, transaction

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('regulation_observation', ROOT/'beta/tools/regulation_observation.py')
observation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observation)


class Observation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'private.sqlite3'
        initialize(self.path)
        self.db = sqlite3.connect(self.path, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)
        self.config = dict(ADAPTIVE_ENABLED=True, MISSION_REGULATION_ENABLED=True,
                           MAX_DATABASE_BYTES=100*1024**2, MIN_FREE_BYTES=10*1024**2)
        self.now = 1_000_000_000
        self.signals = dict(storage_bytes=1000, free_bytes=1024**3, pending=0)
        sensor = patch.object(reg, 'observe', side_effect=lambda *_: dict(self.signals))
        sensor.start()
        self.addCleanup(sensor.stop)
        clock = patch.object(reg.time, 'time', side_effect=lambda: self.now)
        clock.start()
        self.addCleanup(clock.stop)

    def start(self):
        with transaction(self.db):
            state = reg.refresh(self.db, self.config, force=True, now=self.now)
            return reg.begin(self.db, self.config, state)

    def attempt(self, outcome='completed', reason=None, elapsed=5):
        token = self.start()
        self.now += elapsed
        with transaction(self.db):
            reg.finish(self.db, self.config, token, outcome, reason)
        return token

    def read(self, since=999_999_999, until=None, now=None):
        return observation.report(self.path, since=since, until=until or self.now+1,
                                  now=now or self.now+1, source='synthetic')

    def insert_mission(self, status):
        self.db.execute('INSERT INTO adaptive_missions '
            '(id,user_id,idempotency_key,request_sha256,input_json,status,result_json,artifact,created_at,updated_at) '
            'VALUES(?,?,?,?,?,?,?,?,?,?)', ('private-id-'+status, 'private-user', 'private-key-'+status,
                'private-hash', '{"secret":"private-input"}', status,
                '{"secret":"private-result"}', b'private-artifact', self.now-100, self.now))

    def test_real_outcomes_are_separate_from_unknown_and_snapshot(self):
        self.attempt(elapsed=2)
        self.attempt('failed', 'MISSION_TIMEOUT', elapsed=9)
        self.attempt('cancelled', 'CANCELLED', elapsed=1)
        self.start()
        self.now += 7
        reg.recover(self.db, self.config)
        self.insert_mission('queued')
        self.insert_mission('running')
        self.insert_mission('completed')
        value = self.read()
        events = value['retained_window_events']
        self.assertEqual(events['started'], 4)
        self.assertEqual(events['finished'], dict(completed=1, operational_failure=1, neutral=1))
        self.assertEqual(events['interrupted_unknown'], 1)
        self.assertEqual(value['recorded_elapsed_seconds']['all_finished'],
                         dict(count=3, min=1, p50=2, p95=9, max=9))
        self.assertEqual(value['current_snapshot']['pending_missions'], 2)
        self.assertFalse(value['current_snapshot']['regulator']['active_attempt'])
        self.assertIsNone(value['current_snapshot']['regulator']['enabled_in_runtime'])
        self.assertFalse(value['coverage']['complete_window_proven'])
        self.assertFalse(value['eligible_for_policy_promotion'])

    def test_half_open_window_counts_finishes_even_if_start_precedes_it(self):
        beginning = self.now
        self.attempt(elapsed=10)
        self.attempt(elapsed=1)
        value = self.read(since=beginning+5, until=beginning+11)
        self.assertEqual(value['retained_window_events']['started'], 1)
        self.assertEqual(value['retained_window_events']['finished']['completed'], 1)
        self.assertEqual(value['recorded_elapsed_seconds']['all_finished']['max'], 10)

    def test_empty_journal_does_not_invent_health_or_zero_latency(self):
        value = self.read()
        self.assertEqual(value['recorded_elapsed_seconds']['all_finished']['count'], 0)
        self.assertIsNone(value['recorded_elapsed_seconds']['all_finished']['p95'])
        self.assertFalse(value['current_snapshot']['regulator']['record_present'])
        self.assertIsNone(value['current_snapshot']['regulator']['active_attempt'])
        self.assertIn('queue_wait_seconds', value['unavailable_metrics'])
        self.assertIn('pending_time_integral', value['unavailable_metrics'])

    def test_current_active_marker_and_private_payloads_are_not_exported(self):
        self.insert_mission('running')
        token = self.start()
        self.now += 20
        value = self.read()
        state = value['current_snapshot']['regulator']
        self.assertTrue(state['active_attempt'])
        self.assertEqual(state['active_age_seconds'], 21)
        self.assertEqual(state['freshness'], 'stale')
        serialized = json.dumps(value)
        for secret in (token, 'private-', str(self.path), 'input_json', 'result_json', 'artifact'):
            self.assertNotIn(secret, serialized)
        self.assertEqual(value['retained_window_events']['finished']['completed'], 0)

    def test_reads_committed_wal_without_changing_or_observing_uncommitted_data(self):
        self.db.execute('PRAGMA wal_autocheckpoint=0')
        self.attempt()
        before = '\n'.join(self.db.iterdump())
        db_bytes = self.path.read_bytes()
        wal = Path(str(self.path)+'-wal')
        wal_bytes = wal.read_bytes()
        self.db.execute('BEGIN IMMEDIATE')
        self.db.execute('DELETE FROM mission_regulation_events')
        value = self.read()
        self.db.rollback()
        self.assertEqual(value['retained_window_events']['finished']['completed'], 1)
        self.assertEqual('\n'.join(self.db.iterdump()), before)
        self.assertEqual(self.path.read_bytes(), db_bytes)
        self.assertEqual(wal.read_bytes(), wal_bytes)

    def test_missing_database_is_not_created_and_schema_mismatch_is_explicit(self):
        missing = self.path.with_name('missing.sqlite3')
        with self.assertRaisesRegex(observation.ObservationError, 'DATABASE_NOT_FOUND'):
            observation.report(missing, since=1, until=2)
        self.assertFalse(missing.exists())
        self.db.execute('DROP TABLE mission_regulation_events')
        with self.assertRaisesRegex(observation.ObservationError, 'SCHEMA_UNAVAILABLE'):
            self.read()

    def test_retention_and_gaps_are_visible_without_claiming_complete_history(self):
        self.attempt()
        self.attempt()
        self.db.execute('DELETE FROM mission_regulation_events WHERE sequence IN (1,3)')
        value = self.read(since=0)
        coverage = value['coverage']
        self.assertTrue(coverage['deleted_prefix_detected'])
        self.assertEqual(coverage['internal_missing_sequences'], 1)
        self.assertTrue(coverage['requested_start_older_than_retention'])
        self.assertFalse(coverage['complete_window_proven'])

    def test_record_limit_and_overflow_are_distinguished(self):
        state = reg.refresh(self.db, self.config, force=True, now=self.now)
        with transaction(self.db):
            for _ in range(520):
                reg.event(self.db, 'transition', state, self.now)
        value = self.read()
        self.assertTrue(value['coverage']['record_limit_reached'])
        self.assertTrue(value['coverage']['deleted_prefix_detected'])
        self.db.execute('INSERT INTO mission_regulation_events(created_at,kind,receipt_json) '
                        'SELECT created_at,kind,receipt_json FROM mission_regulation_events LIMIT 1')
        with self.assertRaisesRegex(observation.ObservationError, 'JOURNAL_BOUND_EXCEEDED'):
            self.read()

    def test_unknown_identity_kind_outcome_and_malformed_records_fail_closed(self):
        self.attempt()
        row = self.db.execute("SELECT sequence,receipt_json FROM mission_regulation_events WHERE kind='execution_finished'").fetchone()
        original = json.loads(row['receipt_json'])
        for change, error in ((dict(policy_sha256='unknown'), 'UNSUPPORTED_RECORD_IDENTITY'),
                (dict(format='future'), 'UNSUPPORTED_RECORD_IDENTITY'),
                (dict(outcome='assumed_success'), 'UNSUPPORTED_EXECUTION_OUTCOME'),
                (dict(elapsed_seconds=True), 'INVALID_RECORDED_DURATION'),
                (dict(mode=[]), 'UNSUPPORTED_RECORDED_MODE')):
            with self.subTest(change=change):
                self.db.execute('UPDATE mission_regulation_events SET receipt_json=? WHERE sequence=?',
                                (json.dumps({**original, **change}), row['sequence']))
                with self.assertRaisesRegex(observation.ObservationError, error):
                    self.read()
        for raw, error in (('{', 'INVALID_RECORD_JSON'), ('x'*16385, 'OVERSIZED_RECORD')):
            self.db.execute('UPDATE mission_regulation_events SET receipt_json=? WHERE sequence=?', (raw, row['sequence']))
            with self.assertRaisesRegex(observation.ObservationError, error):
                self.read()
        self.db.execute('UPDATE mission_regulation_events SET receipt_json=?,kind=? WHERE sequence=?',
                        (row['receipt_json'], 'future_kind', row['sequence']))
        with self.assertRaisesRegex(observation.ObservationError, 'UNSUPPORTED_EVENT_KIND'):
            self.read()

    def test_incoherent_clock_and_unrecognized_persisted_policy_fail_closed(self):
        self.attempt()
        original = reg.load(self.db)
        for change, error in ((dict(observed_at=self.now+100), 'INCOHERENT_CLOCK'),
                (dict(reason='CLOCK_MOVED_BACKWARD'), 'INCOHERENT_CLOCK'),
                (dict(policy_sha256='future'), 'UNSUPPORTED_RECORD_IDENTITY')):
            with self.subTest(change=change):
                with transaction(self.db):
                    reg.save(self.db, {**original, **change})
                with self.assertRaisesRegex(observation.ObservationError, error):
                    self.read()
        with transaction(self.db):
            reg.save(self.db, original)
        self.db.execute('UPDATE mission_regulation_events SET created_at=created_at+100')
        with self.assertRaisesRegex(observation.ObservationError, 'INCOHERENT_CLOCK'):
            self.read()

    def test_future_window_invalid_interval_and_source_are_rejected(self):
        for args, error in ((dict(since=10, until=10), 'INVALID_WINDOW'),
                (dict(since=1, until=self.now+100, now=self.now), 'WINDOW_AFTER_SNAPSHOT'),
                (dict(since=1, until=2, source='verified_live'), 'INVALID_SOURCE_DECLARATION')):
            with self.subTest(args=args), self.assertRaisesRegex(observation.ObservationError, error):
                observation.report(self.path, **args)

    def test_cli_writes_0600_without_printing_payload_and_refuses_overwrite_or_symlink(self):
        self.attempt()
        output = self.path.with_name('report.json')
        args = ['--database', str(self.path), '--since', str(self.now-100),
                '--until', str(self.now), '--output', str(output), '--source', 'synthetic']
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.assertEqual(observation.main(args), 0)
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        self.assertNotIn(str(output), stdout.getvalue())
        self.assertNotIn('retained_window_events', stdout.getvalue())
        before = output.read_bytes()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(observation.main(args), 1)
        self.assertEqual(output.read_bytes(), before)
        link = self.path.with_name('link.json')
        link.symlink_to(output)
        with self.assertRaises(FileExistsError):
            observation.write_private(link, {})
        self.assertEqual(output.read_bytes(), before)


    def test_published_example_is_reproduced_from_synthetic_transitions(self):
        spec = importlib.util.spec_from_file_location('observation_example',
            ROOT/'beta/experiments/regulation-observation/example.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        expected = json.loads((ROOT/'adaptive/evidence/2026-10-15-regulation-observation/synthetic.json').read_text())
        self.assertEqual(module.example(), expected)


if __name__ == '__main__':
    unittest.main()
