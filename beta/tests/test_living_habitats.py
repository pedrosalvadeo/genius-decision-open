from copy import deepcopy
from datetime import datetime,timedelta,timezone
from decimal import Decimal
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_public_network as network_tests
from federation.core import Node,digest
from federation.habitat import Habitat,SourceError,observations
from federation.internet import InternetNode,RemoteError
from federation.organism import Organism


class HabitatTests(unittest.TestCase):
    setUp=network_tests.PublicNetworkTests.setUp
    transport=network_tests.PublicNetworkTests.transport

    def prepare(self,station='SAME'):
        self.serial+=1;self.stamp=datetime.now(timezone.utc).replace(microsecond=0)
        self.base=self.stamp;self.source_calls=0
        self.value=20;self.rows=[self.row(station,self.stamp-timedelta(hours=i,minutes=10),20-i) for i in range(9)]
        def source(code):self.source_calls+=1;self.assertEqual(code,station);return deepcopy(self.rows)
        habitat=Habitat(self.root/station,station,'https://hub.example',self.transport,source,lambda:self.stamp.isoformat())
        habitat.authorize(True);return habitat

    def row(self,station,when,value):
        return dict(icaoId=station,obsTime=int(when.timestamp()),temp=value,rawOb='METAR '+station+' TEST '+str(value))

    def advance(self,habitat,hours=1):
        self.stamp+=timedelta(hours=hours);self.value+=0.5
        self.rows.append(self.row(habitat.station,self.stamp-timedelta(minutes=10),self.value))
        self.rows=self.rows[-18:]
        return habitat.step()

    def organism(self,habitat):
        return Organism(Node(habitat.state/'memory',habitat.client.load()['node_id'],lambda:self.stamp.isoformat()))

    def test_permission_required_and_no_network_before_authorization(self):
        h=Habitat(self.root/'none','SAME','https://hub.example',self.transport)
        with self.assertRaisesRegex(ValueError,'AUTHORIZATION'):h.authorize()
        self.assertFalse(h.path.exists());self.assertEqual(self.client.get('/network/manifest.json').json['nodes'],0)

    def test_adapter_preserves_source_time_units_missing_and_conflicts(self):
        stamp=datetime.now(timezone.utc);r=self.row('SAME',stamp-timedelta(minutes=10),Decimal('-2.5'))
        rows=observations([r,r,{**r,'temp':None}],'SAME',stamp.isoformat())
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]['value'],27065)
        self.assertEqual(rows[0]['context']['data_kind'],'reported');self.assertIn('METAR',rows[0]['source']['excerpt'])
        self.assertEqual(len(observations([r,{**r,'temp':1}],'SAME',stamp.isoformat())),2)
        for bad in ({**r,'icaoId':'SAMM'},{**r,'temp':True},{**r,'temp':float('nan')},
                    {**r,'obsTime':int(stamp.timestamp())+100},{**r,'rawOb':'unrelated'}):
            with self.assertRaises((ValueError,SourceError)):observations([bad],'SAME',stamp.isoformat())

    def test_first_forecast_is_prospective_and_restart_keeps_identity(self):
        h=self.prepare();first=h.step();cfg=h.client.load()
        self.assertEqual(first['status'],'WAITING_FOR_OUTCOME');self.assertEqual(first['organism']['scored_outcomes'],0)
        prediction=deepcopy(first['last_prediction'])
        h.step();self.assertEqual(self.source_calls,1)
        h=Habitat(h.state,'SAME',h.hub,self.transport,h.source,h.clock)
        self.assertEqual(h.step()['last_prediction'],prediction)
        second=self.advance(h)
        self.assertEqual(second['node_id'],cfg['node_id']);self.assertEqual(second['organism']['scored_outcomes'],1)
        self.assertEqual(second['last_scored']['forecast_sha256'],prediction['forecast_sha256'])
        self.assertGreater(second['last_scored']['observed_at'],prediction['frozen_at'])
        self.assertEqual(self.client.get('/network/manifest.json').json['nodes'],1)

    def test_prediction_uses_the_actual_post_fetch_clock(self):
        from federation.core import now
        h=self.prepare();h.clock=now
        report=h.step()
        self.assertEqual(report['status'],'WAITING_FOR_OUTCOME')
        self.assertEqual(report['last_prediction']['target_window'][0],report['last_prediction']['frozen_at'])
        self.assertGreaterEqual(report['last_prediction']['frozen_at'],self.base.isoformat())

    def test_evolution_adopts_only_after_future_confirmation_and_keeps_running(self):
        h=self.prepare();h.step()
        for i in range(4):report=self.advance(h)
        self.assertEqual(report['organism']['locally_confirmed_changes'],0)
        for i in range(4):report=self.advance(h)
        self.assertEqual(report['organism']['locally_confirmed_changes'],1)
        self.assertEqual(report['last_archive']['status'],'ADOPTED')
        self.assertEqual(report['organism']['context_traits'][0]['genes']['estimator'],'last_value')
        self.assertIsNone(report['life_sustainment_probability'])
        self.assertEqual(report['organism']['scored_outcomes'],8)
        self.assertEqual(report['last_prediction']['trial_id'],'metar-2')
        archive=next((h.state/'memory/evolution-history').glob('*.json'))
        content=json.loads(archive.read_text())
        self.assertEqual(content['trial']['status'],'ADOPTED');self.assertEqual(len(content['forecasts']),8)
        self.assertTrue(content['trial']['confirmation_native']['verification']['valid'])
        self.assertEqual(digest(content),report['last_archive']['sha256'])

    def test_continuous_memory_releases_finished_slots_without_resetting_genome(self):
        h=self.prepare();h.step()
        for i in range(45):report=self.advance(h)
        self.assertEqual(report['organism']['scored_outcomes'],45)
        self.assertGreater(report['organism']['archived_trials'],4)
        self.assertEqual(report['organism']['locally_confirmed_changes'],1)
        organism=self.organism(h)
        with organism.node.db() as db:
            self.assertLessEqual(db.execute('SELECT count(*) FROM records').fetchone()[0],66)
            self.assertLessEqual(db.execute('SELECT count(*) FROM forecasts').fetchone()[0],8)
        self.assertEqual(len(organism.load()['trials']),1)
        with self.assertRaisesRegex(ValueError,'ACTIVE'):organism.archive_finished(next(iter(organism.load()['trials'])))

    def test_missing_outcome_is_not_zero_and_stale_data_does_not_predict(self):
        h=self.prepare();h.step();first=h.load()['last_prediction']
        self.stamp+=timedelta(hours=3);report=h.step()
        self.assertEqual(report['status'],'STALE_OBSERVATIONS')
        self.assertEqual(report['organism']['scored_outcomes'],0)
        self.assertEqual(report['last_archive']['status'],'MISSED_TARGET')
        self.assertEqual(report['last_prediction'],first)
        self.assertIsNone(report['last_scored'])

    def test_conflicting_outcome_is_not_scored(self):
        h=self.prepare();h.step();self.stamp+=timedelta(hours=1)
        row=self.row('SAME',self.stamp-timedelta(minutes=10),21)
        self.rows+=[row,{**row,'temp':22}]
        report=h.step();self.assertEqual(report['status'],'SOURCE_CONFLICT_REVIEW')
        self.assertEqual(report['organism']['scored_outcomes'],0)
        self.rows=self.rows[:-1];self.stamp+=timedelta(hours=1)
        self.assertEqual(h.step()['status'],'SOURCE_CONFLICT_REVIEW')

    def test_missing_measurement_never_becomes_zero_or_synthetic(self):
        h=self.prepare();self.rows=[{**r,'temp':None} for r in self.rows]
        report=h.step();self.assertEqual(report['status'],'NO_OBSERVATIONS')
        self.assertIsNone(report['last_prediction']);self.assertEqual(report['organism']['scored_outcomes'],0)

    def test_source_failure_is_bounded_and_forbidden_access_stays_blocked(self):
        h=self.prepare()
        with patch.object(h,'source',side_effect=SourceError('SOURCE_HTTP_403')) as source:
            report=h.step();self.assertEqual(report['status'],'SOURCE_UNAVAILABLE')
            h.step();self.assertEqual(source.call_count,1)
            self.stamp+=timedelta(hours=1);report=h.step()
            self.assertEqual(report['status'],'SOURCE_ACCESS_REVIEW');self.assertEqual(source.call_count,1)

    def test_pause_resume_and_revocation_do_not_create_replacement_identity(self):
        h=self.prepare();before=h.step();cfg=h.client.load()
        self.assertEqual(h.control('pause')['status'],'OPERATOR_PAUSE')
        self.stamp+=timedelta(hours=1);self.assertEqual(h.step()['status'],'OPERATOR_PAUSE')
        self.assertEqual(self.source_calls,1)
        h.control('resume');after=self.advance(h)
        self.assertEqual(after['node_id'],before['node_id'])
        self.assertEqual(h.control('revoke')['status'],'REVOKED')
        with self.assertRaisesRegex(ValueError,'REVOKED'):h.control('resume')
        self.assertEqual(self.client.get('/network/manifest.json').json['nodes'],0)
        self.assertTrue((h.state/'memory/memory.sqlite3').exists())

    def test_global_pause_stops_source_reads_and_expired_account_is_not_replaced(self):
        h=self.prepare();h.step();self.config['SUSPEND_FILE'].write_text('pause')
        self.stamp+=timedelta(hours=1);self.assertEqual(h.step()['status'],'PAUSED_OR_REVIEW_REQUIRED')
        self.assertEqual(self.source_calls,1)
        self.config['SUSPEND_FILE'].unlink();h.client.leave()
        self.stamp+=timedelta(hours=1);h.step()
        self.assertEqual(self.source_calls,1);self.assertEqual(self.client.get('/network/manifest.json').json['nodes'],0)

    def test_public_report_is_current_projection_and_never_contains_credentials(self):
        h=self.prepare();h.step();destination=self.config['DATA_DIR']/'living-habitats/SAME'
        destination.mkdir(parents=True);(destination/'public-report.json').write_bytes(h.report.read_bytes())
        row=json.loads((destination/'public-report.json').read_text());row['credential']='DO-NOT-PUBLISH'
        (destination/'public-report.json').write_text(json.dumps(row))
        response=self.client.get('/network/organisms.json');body=response.get_data(as_text=True)
        self.assertEqual(response.status_code,200);self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.assertNotIn('DO-NOT-PUBLISH',body);self.assertNotIn(h.client.load()['credential']['token'],body)
        self.assertEqual(response.json['organisms'][0]['source_kind'],'REAL_REPORTED_OBSERVATIONS')
        with self.client.get('/organisms') as page:self.assertEqual(page.status_code,200)
        with patch('time.time',return_value=self.stamp.timestamp()+4*3600):
            self.assertTrue(self.client.get('/network/organisms.json').json['organisms'][0]['report_stale'])

    def test_controller_lock_prevents_concurrent_forecasts(self):
        h=self.prepare()
        with h.lock():
            with self.assertRaises(BlockingIOError):h.step()
        self.assertEqual(self.source_calls,0)

    def test_archival_failure_retains_active_memory_and_is_retryable(self):
        h=self.prepare();h.step()
        for i in range(7):self.advance(h)
        with patch.object(Organism,'archive_finished',side_effect=OSError('disk unavailable')):
            report=self.advance(h)
        self.assertEqual(report['status'],'PAUSED_OR_REVIEW_REQUIRED')
        self.assertEqual(self.organism(h).status()['scored_outcomes'],8)
        report=self.advance(h)
        self.assertEqual(report['organism']['locally_confirmed_changes'],1)
        self.assertEqual(report['organism']['archived_trials'],1)


if __name__=='__main__':unittest.main()
