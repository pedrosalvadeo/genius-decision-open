"""Resumable synthetic service-integration probe; never a real-world improvement trial.

Use a NEW private --state path. It contains a short-lived credential until cleanup.
--cleanup-only performs no forecasts and can be used after a failed/interrupted run.
"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import time

from observers.study import API, atomic, exclusive, require
from genius_beta import context_forecasts as cf
from genius_adaptive import contextual


class Probe:
    def __init__(self, path, *, api=None, cleanup_only=False):
        self.path, self.api = Path(path), api or API()
        require(not self.path.is_symlink(),'STATE_SYMLINK')
        config=dict(format='genius-context-service-probe/1',baseline=50,max_underprediction=50,
                    values=([10,100]*8)[:15],warmup_count=3,scored_count=12,
                    expected_scorer=cf.scorer_identity(),driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        if self.path.exists():
            require(self.path.stat().st_mode & 0o077 == 0,'PRIVATE_FILE_PERMISSIONS')
            self.state=json.loads(self.path.read_text())
            if not cleanup_only:require(self.state['config']==config,'PROBE_CONFIG_CHANGED')
        else:
            require(not cleanup_only,'NO_PRIVATE_STATE')
            self.state=dict(config=config,run_id=secrets.token_hex(12),steps={},started_at=self.now())
            self.save()
        self.api.token=self.state.get('token')

    def now(self):
        return datetime.now(timezone.utc).isoformat(timespec='microseconds')

    def save(self):
        atomic(self.path,self.state)

    def step(self, name, action):
        if name not in self.state['steps']:
            self.state['steps'][name]=action();self.save()
        return self.state['steps'][name]

    def account(self):
        if self.api.token:return
        require(not self.state.get('registration_attempted'),'REGISTRATION_OUTCOME_UNKNOWN')
        manifest=self.api.request('GET','/agents/manifest.json')
        require(manifest.get('missions',{}).get('contextual_forecast_protocol')==cf.FORMAT and
                manifest['missions']['enabled'] is True,'CONTEXT_API_NOT_DEPLOYED')
        self.state['registration_attempted']=True;self.save()
        issued=self.api.request('POST','/api/agents/register',dict(policy_version=manifest['policy_version'],
            data_policy_acknowledged=True,scopes=['missions:read','missions:write','missions:run','account:delete']))
        self.state['token']=self.api.token=issued['credential']['token'];self.save()

    def cleanup(self):
        if self.state.get('account_erased'):return
        if not self.api.token:
            require(not self.state.get('registration_attempted'),'REGISTRATION_OUTCOME_UNKNOWN')
            return
        self.api.request('DELETE','/api/agents/me',{})
        self.api.request('GET','/api/missions',accepted=(401,))
        self.state.update(account_erased=True,credential_revoked=True)
        self.state.pop('token',None);self.api.token=None;self.save()

    def run(self):
        if self.state.get('status')=='PASS':
            self.cleanup();return
        self.account()
        def record(index):
            return dict(id='seed-'+str(index),value=50,observed_at=f'2026-10-01T00:00:0{index}Z',source='Synthetic context integration seed')
        payload=dict(kind='resource_calibration_v1',idempotency_key=self.state['run_id']+'-parent',
            processing_permission=True,technical_scope_acknowledged=True,
            calibration=dict(context='Synthetic alternating targets for contextual API integration',resource='synthetic_test_resource',
                unit='test_unit',baseline=50,max_underprediction=50,data_kind='synthetic',
                training=[record(i) for i in (1,2,3)],validation=[record(i) for i in (4,5)]))
        created=self.step('created',lambda:self.api.request('POST','/api/missions',payload))
        mid=created['mission']['id'];base='/api/missions/'+mid;path=base+'/context-forecast'
        def execute():
            self.api.request('POST',base+'/run',{})
            deadline=time.monotonic()+90
            while True:
                mission=self.api.request('GET',base)['mission']
                if mission['status']=='completed':return mission
                require(mission['status'] not in ('failed','needs_review','interrupted','cancelled'),'PARENT_EXECUTION_FAILED')
                require(time.monotonic()<deadline,'PARENT_EXECUTION_TIMEOUT');time.sleep(.2)
        parent=self.step('parent',execute)
        artifact=self.step('artifact',lambda:self.api.request('GET',base+'/artifact'))
        raw=base64.b64decode(artifact['content_base64'],validate=True)
        require(hashlib.sha256(raw).hexdigest()==artifact['sha256']==parent['artifact_sha256'],'PARENT_ARTIFACT_HASH')
        require(json.loads(raw)['estimate']==50,'PARENT_BASELINE')
        frozen=self.step('frozen',lambda:self.api.request('POST',path,dict(artifact_sha256=artifact['sha256'],warmup_count=3,scored_count=12))['forecast'])
        require(frozen['frozen']['scorer_identity']==self.state['config']['expected_scorer'],'DEPLOYED_SCORER_CHANGED')
        require(cf.fingerprint(frozen['frozen'])==frozen['sha256'],'PLAN_HASH')
        history=[];pairs=[];previous=frozen['sha256'];last=frozen['frozen']['frozen_at_us']
        for index,value in enumerate(self.state['config']['values'],1):
            name='target-'+str(index)
            prediction=self.step(name+'-prediction',lambda:self.api.request('POST',path+'/predictions',
                dict(forecast_sha256=frozen['sha256'],prediction_id=name))['prediction'])
            receipt=prediction['receipt']
            require(cf.fingerprint(receipt)==prediction['sha256'] and receipt['previous_sha256']==previous,'PREDICTION_HASH_CHAIN')
            require(receipt['issued_at_us']>last and receipt['prediction']==contextual.predict(history,frozen['frozen']),'PREDICTION_PREFIX')
            # Synthetic target is materialized and checkpointed only after the response.
            target=self.step(name+'-target',lambda:dict(id=name,value=value,observed_at=self.now(),source='Synthetic target generated after server prediction; not field evidence'))
            require(target['id']==name and target['value']==value,'SYNTHETIC_TARGET_CHANGED')
            observed=self.step(name+'-observation',lambda:self.api.request('POST',path+'/observations',
                dict(forecast_sha256=frozen['sha256'],prediction_sha256=prediction['sha256'],observation=target))['observation'])
            entry=observed['receipt']
            require(entry['observation']==target and cf.fingerprint(entry)==observed['sha256'] and entry['previous_sha256']==prediction['sha256'],'OBSERVATION_CHAIN')
            require(receipt['issued_at_us']<cf.event_us(target['observed_at'])<=entry['received_at_us'],'EVENT_TIME')
            pairs.append(dict(prediction=prediction,observation=observed))
            history.append(dict(**receipt['prediction'],value=value));previous,last=observed['sha256'],entry['received_at_us']
        closed=self.step('closed',lambda:self.api.request('POST',path+'/close',dict(forecast_sha256=frozen['sha256']))['forecast'])
        require(closed['status']=='complete' and cf.fingerprint(closed['report'])==closed['report_sha256'],'REPORT_HASH')
        require(closed['pairs']==pairs and closed['frozen']==frozen['frozen'],'CLOSED_RECEIPTS_CHANGED')
        report=closed['report'];expected=contextual.report(history,frozen['frozen'])
        for key in ('comparison','checks','outcome','selected_counts','context_counts'):
            require(report[key]==expected[key],'REPORT_ARITHMETIC')
        require(report['native']['verification']['valid'] is True,'NATIVE_VERIFICATION')
        require(report['previous_sha256']==previous and report['closed_at_us']>last,'REPORT_CHAIN')
        require(report['receipt_sha256s']==[[p['prediction']['sha256'],p['observation']['sha256']] for p in pairs],'REPORT_RECEIPTS')
        require(report['outcome']=='OBSERVED_GUARDED_IMPROVEMENT' and report['selected_counts']['context_median']>0,'SYNTHETIC_SELECTOR_EXPECTATION')
        replay=self.step('replayed_close',lambda:self.api.request('POST',path+'/close',dict(forecast_sha256=frozen['sha256']))['forecast'])
        require(replay==closed,'REPORT_REPLAY_CHANGED')
        exported=self.step('exported',lambda:self.api.request('GET',base+'/export')['mission']['context_forecast'])
        require(exported==closed,'EXPORT_CHANGED')
        self.state.update(status='PASS',completed_at=self.now(),scope='LIVE_SYNTHETIC_SERVICE_INTEGRATION',
            closed_report_replayed=True,export_verified=True,wellbeing='UNMEASURED',life_sustainment='UNMEASURED');self.save()
        self.cleanup()

    def public(self):
        result={key:value for key,value in self.state.items() if key not in ('token','steps')}
        result['steps']={key:value for key,value in self.state['steps'].items() if key not in ('replayed_close','exported')}
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--cleanup-only',action='store_true');args=parser.parse_args()
    require(args.state.resolve()!=args.out.resolve(),'DISTINCT_PATHS_REQUIRED')
    with exclusive(args.state):
        probe=Probe(args.state,cleanup_only=args.cleanup_only)
        try:
            probe.cleanup() if args.cleanup_only else probe.run()
        except Exception as exc:
            code=str(exc) if str(exc).isupper() else type(exc).__name__
            probe.state['last_error']=code;probe.save();atomic(args.out,probe.public())
            print(json.dumps(dict(status='STOPPED',error=code,cleanup_required=bool(probe.api.token))))
            raise SystemExit(2) from None
        atomic(args.out,probe.public())
        print(json.dumps({key:probe.state.get(key) for key in ('status','scope','account_erased','credential_revoked')}))


if __name__=='__main__':main()
