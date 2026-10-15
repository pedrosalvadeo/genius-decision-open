"""Operator-only synthetic forecast/check/learn probe against geniusdecision.app.

Arguments: NEW private credential-state path, public receipt path, calibration
fixture path. Always attempts account erasure; a failed cleanup leaves private
state for the operator. Never commit that state or run against a real account.
"""
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import time
from urllib.request import build_opener, Request, HTTPRedirectHandler
from urllib.error import HTTPError


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def main():
    state, receipt, fixture = map(Path, sys.argv[1:])
    if state.exists():
        raise SystemExit('A new private state path is required')
    origin = 'https://geniusdecision.app'
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs):
            return None
    opener, token = build_opener(NoRedirect()), None
    def request(method,path,payload=None,accepted=(200,201,202,204)):
        headers={'Accept':'application/json'}
        if token:headers['Authorization']='Bearer '+token
        raw=None if payload is None else json.dumps(payload).encode()
        if raw is not None:headers['Content-Type']='application/json'
        try:response=opener.open(Request(origin+path,data=raw,headers=headers,method=method),timeout=20)
        except HTTPError as exc:response=exc
        with response:
            raw=response.read(4*1024*1024);value=json.loads(raw) if raw else None
            if response.status not in accepted:raise RuntimeError('HTTP_'+str(response.status)+'_'+path)
            return value
    def check(condition,code):
        if not condition:raise RuntimeError(code)
    def execute(data):
        mid=request('POST','/api/missions',data)['mission']['id']
        request('POST','/api/missions/'+mid+'/run',{})
        deadline=time.monotonic()+75
        while True:
            mission=request('GET','/api/missions/'+mid)['mission']
            if mission['status']=='completed':break
            if mission['status'] in ('failed','needs_review','cancelled','interrupted') or time.monotonic()>deadline:
                raise RuntimeError('MISSION_'+mission['status'])
            time.sleep(1)
        artifact=request('GET','/api/missions/'+mid+'/artifact')
        raw=base64.b64decode(artifact['content_base64'],validate=True)
        check(hashlib.sha256(raw).hexdigest()==artifact['sha256'],'ARTIFACT_DIGEST')
        return mission,json.loads(raw)
    def observed(name,value):
        return dict(id=name,value=value,observed_at=datetime.now(timezone.utc).isoformat(),source='Synthetic operator probe generated after frozen prediction')
    manifest=request('GET','/agents/manifest.json')
    issued=request('POST','/api/agents/register',dict(policy_version=manifest['policy_version'],data_policy_acknowledged=True,
        scopes=['missions:read','missions:write','missions:run','missions:delete','account:delete']))
    token=issued['credential']['token'];os.umask(0o077)
    state.write_text(json.dumps(dict(origin=origin,token=token)));state.chmod(0o600)
    try:
        caps=request('GET','/api/missions/capabilities')
        check(caps.get('forecasts',{}).get('protocol')=='resource_forecast_v1','FORECASTS_NOT_DEPLOYED')
        data=json.loads(fixture.read_text());data['idempotency_key']='prospective-'+secrets.token_hex(16)
        parent,memory=execute(data);mid=parent['id'];path='/api/missions/'+mid
        check(memory['estimate']==100,'FIXTURE_ESTIMATE')
        frozen=request('POST',path+'/forecast',dict(artifact_sha256=parent['artifact_sha256'],expected_count=3))['forecast']
        check(digest(frozen['frozen'])==frozen['sha256'],'FORECAST_HASH')
        root=Path(__file__).resolve().parents[2]
        for key,file in (('scorer_sha256','beta/genius_beta/mission_forecasts.py'),('calibration_sha256','adaptive/genius_adaptive/calibration.py')):
            check(frozen['frozen']['scorer_identity'][key]==hashlib.sha256((root/file).read_bytes()).hexdigest(),'DEPLOYED_SCORER_IDENTITY')
        receipts=[]
        for index,value in enumerate((110,115,120),1):
            item=request('POST',path+'/observations',dict(forecast_sha256=frozen['sha256'],observation=observed('after-freeze-'+str(index),value)))
            check(item['forecast_status']==('complete' if index==3 else 'collecting'),'SAMPLE_COUNT')
            check(digest(item['observation']['receipt'])==item['observation']['sha256'],'RECEIPT_HASH')
            receipts.append(item['observation'])
        scored=request('GET',path+'/forecast')['forecast']
        check(scored['frozen']==frozen['frozen'],'FORECAST_CHANGED')
        check(digest(scored['report'])==scored['report_sha256'],'REPORT_HASH')
        check(scored['report']['comparison']['baseline']['absolute_error_sum']==195,'BASELINE_ERROR')
        check(scored['report']['comparison']['estimate']['absolute_error_sum']==45,'ESTIMATE_ERROR')
        check(scored['report']['outcome']=='NO_CONFIRMED_IMPROVEMENT','TOLERANCE_GUARD')
        validation=[observed('later-validation-1',115)]
        time.sleep(.01)
        validation.append(observed('later-validation-2',120))
        child,learned=execute(dict(kind='resource_calibration_v1',forecast_mission_id=mid,
            idempotency_key='after-scoring-'+secrets.token_hex(16),processing_permission=True,
            technical_scope_acknowledged=True,calibration=dict(validation=validation)))
        check(learned['baseline']==100 and learned['estimate']==115,'NEW_LEARNING_RESULT')
        check(learned['lineage']['report_sha256']==scored['report_sha256'],'SCORED_TRAINING_LINEAGE')
        check(request('GET',path+'/forecast')['forecast']==scored,'OLD_REPORT_CHANGED')
        result=dict(status='PASS',scope='LIVE_SYNTHETIC_POST_FREEZE_SUBMISSIONS',origin=origin,
            parent_mission_id=mid,child_mission_id=child['id'],forecast=scored,
            learned_estimate=learned['estimate'],child_artifact_sha256=child['artifact_sha256'],
            child_lineage=learned['lineage'],old_report_unchanged=True,
            receipt_times='SERVER_RECORDED',source_truth='NOT_INDEPENDENTLY_VERIFIED',
            wellbeing='UNMEASURED',life_sustainment='UNMEASURED')
    finally:
        request('DELETE','/api/agents/me',{})
        request('GET','/api/missions',accepted=(401,))
        state.write_text(json.dumps(dict(status='probe_account_erased',credential_revoked=True,secret_removed=True)))
    result.update(probe_account_erased=True,credential_revoked=True,verified_at=int(time.time()))
    receipt.parent.mkdir(parents=True,exist_ok=True);receipt.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':
    main()
