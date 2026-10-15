"""Offline source failure, chronology and checkpoint recovery boundaries."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
from observers import http_latency as source
from observers.study import Study, API, exclusive


class Response(io.BytesIO):
    status = 200


class SourceTests(unittest.TestCase):
    def sample(self, body=b'{"status":"ok","backup":"ok","suspended":false}', **kwargs):
        opener = Mock()
        opener.open.return_value = Response(body)
        wall = iter(('2026-10-15T04:00:00.000000+00:00','2026-10-15T04:00:00.100000+00:00'))
        clock = iter((100, 1000101))
        entry = source.sample('sample-1', opener=opener, wall=lambda:next(wall), monotonic=lambda:next(clock), **kwargs)
        return entry, opener

    def test_duration_rounding_exact_bytes_and_unauthenticated_request(self):
        entry, opener = self.sample()
        self.assertEqual(entry['observation']['value'], 2)
        self.assertEqual(entry['measurement']['elapsed_ns'], 1000001)
        self.assertEqual(source.digest(entry['measurement']), entry['sha256'])
        self.assertIn(entry['sha256'], entry['observation']['source'])
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, source.TARGET)
        self.assertNotIn('Authorization', dict(request.header_items()))
        self.assertEqual(entry['observation']['observed_at'], entry['measurement']['completed_at'])

    def test_unhealthy_invalid_and_oversized_responses_are_retained_but_not_training(self):
        for body, failure in ((b'not json','INVALID_JSON'),(b'{}','HEALTH_NOT_OK'),
                              (b'x'*(source.BODY_LIMIT+1),'BODY_LIMIT')):
            with self.subTest(failure=failure):
                entry, _ = self.sample(body)
                self.assertEqual(entry['measurement']['failure'], failure)
                self.assertIsNone(entry['observation'])
                self.assertEqual(source.digest(entry['measurement']), entry['sha256'])

    def test_redirect_timeout_and_backwards_clock_cannot_become_valid_observations(self):
        for error in (HTTPError(source.TARGET,302,'redirect',{},None),URLError('timeout')):
            opener = Mock();opener.open.side_effect = error
            wall=iter(('2026-10-15T04:00:00+00:00','2026-10-15T04:00:01+00:00'))
            clock=iter((0,1000000))
            result=source.sample('failed',opener=opener,wall=lambda:next(wall),monotonic=lambda:next(clock))
            self.assertIsNone(result['observation'])
            self.assertEqual(opener.open.call_count,1)
        opener = Mock();opener.open.return_value = Response(b'{}')
        result=source.sample('backwards',opener=opener,wall=lambda:'2026-10-15T04:00:00+00:00',monotonic=lambda:0)
        self.assertEqual(result['measurement']['failure'],'CLOCK_NOT_ADVANCING')


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'private.json'

    def test_recorded_sample_is_reused_and_unknown_attempt_is_not_retried(self):
        entry,_=SourceTests().sample()
        sampler=Mock(return_value=entry)
        study=Study(self.path,sampler=sampler)
        first=study.collect('baseline')
        resumed=Study(self.path,sampler=sampler)
        self.assertEqual(first,resumed.collect('baseline'))
        self.assertEqual(sampler.call_count,1)
        resumed.state['samples']['unknown']={'status':'MEASUREMENT_INTENT'};resumed.save()
        with self.assertRaisesRegex(ValueError,'MEASUREMENT_OUTCOME_UNKNOWN'):
            Study(self.path,sampler=sampler).collect('unknown')
        self.assertEqual(sampler.call_count,1)

    def test_failed_sample_does_not_resample_and_changed_contract_refuses_resume(self):
        entry,_=SourceTests().sample(b'{}')
        sampler=Mock(return_value=entry)
        study=Study(self.path,sampler=sampler)
        for attempt in range(2):
            with self.assertRaisesRegex(ValueError,'SOURCE_SAMPLE_REJECTED'):
                study.collect('failed')
        self.assertEqual(sampler.call_count,1)
        with self.assertRaisesRegex(ValueError,'OBSERVER_CONFIG_CHANGED'):
            Study(self.path,count=6)
        study.state['samples']['failed']['measurement']['response_bytes']=999;study.save()
        with self.assertRaisesRegex(ValueError,'SOURCE_HASH'):
            Study(self.path).collect('failed')

    def test_credential_excluded_from_public_receipt_and_removed_after_cleanup(self):
        api=Mock();study=Study(self.path,api=api)
        study.state['token']='PRIVATE-BEARER';study.api.token='PRIVATE-BEARER';study.save()
        self.assertNotIn('PRIVATE-BEARER',json.dumps(study.public()))
        study.cleanup()
        self.assertTrue(study.state['account_erased']);self.assertTrue(study.state['credential_revoked'])
        self.assertNotIn('token',json.loads(self.path.read_text()))
        self.assertEqual(self.path.stat().st_mode & 0o077,0)
        self.assertEqual(api.request.call_count,2)
        study.cleanup();self.assertEqual(api.request.call_count,2)

    def test_normalized_record_cannot_diverge_from_the_measurement_receipt(self):
        entry,_=SourceTests().sample()
        study=Study(self.path,sampler=Mock(return_value=entry))
        study.collect('baseline')
        study.state['samples']['baseline']['observation']['value']=999
        study.save()
        with self.assertRaisesRegex(ValueError,'SOURCE_MAPPING_CHANGED'):
            Study(self.path).collect('baseline')

    def test_unknown_registration_and_cleanup_do_not_claim_success(self):
        api=Mock();study=Study(self.path,api=api)
        study.state['registration_attempted']=True;study.save()
        with self.assertRaisesRegex(ValueError,'REGISTRATION_OUTCOME_UNKNOWN'):
            study.account()
        self.assertFalse(api.request.called)
        study.api.token='PRIVATE';study.state['token']='PRIVATE'
        api.request.side_effect=RuntimeError('API_HTTP_401')
        with self.assertRaises(RuntimeError):study.cleanup()
        self.assertFalse(study.state.get('account_erased',False))
        self.assertIn('token',study.state)

    def test_exclusive_writer_and_private_permissions(self):
        with exclusive(self.path):
            with self.assertRaises(BlockingIOError):
                with exclusive(self.path):pass
        Study(self.path);self.path.chmod(0o644)
        with self.assertRaisesRegex(ValueError,'PRIVATE_FILE_PERMISSIONS'):Study(self.path)


if __name__=='__main__':unittest.main()
