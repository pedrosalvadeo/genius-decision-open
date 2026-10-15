import base64,hashlib,json,os,secrets,sys,time
from pathlib import Path
from urllib.request import build_opener,Request,HTTPRedirectHandler
from urllib.error import HTTPError

origin='https://geniusdecision.app'
state=Path(sys.argv[1]);receipt=Path(sys.argv[2]);fixture=Path(sys.argv[3])
if state.exists():raise SystemExit('Use a new private state path')
class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):return None
opener=build_opener(NoRedirect())
token=None

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

manifest=request('GET','/agents/manifest.json')
issued=request('POST','/api/agents/register',dict(policy_version=manifest['policy_version'],data_policy_acknowledged=True,
 scopes=['missions:read','missions:write','missions:run','missions:delete','account:delete']))
token=issued['credential']['token']
os.umask(0o077)
state.write_text(json.dumps(dict(origin=origin,token=token)));state.chmod(0o600)
results=[]
try:
 caps=request('GET','/api/missions/capabilities')
 if 'resource_calibration_v1' not in caps['kinds']:raise RuntimeError('CALIBRATION_NOT_DEPLOYED')
 for cycle in range(2):
  data=json.loads(fixture.read_text());data['idempotency_key']='live-learning-'+secrets.token_hex(16)
  if cycle:
   data['parent_mission_id']=results[0]['mission_id'];del data['calibration']['baseline']
   for i,(row,value) in enumerate(zip(data['calibration']['training']+data['calibration']['validation'],(110,115,120,115,120)),6):
    row['value']=value;row['observed_at']=f'2026-10-{i:02d}T12:00:00Z'
  mid=request('POST','/api/missions',data)['mission']['id']
  request('POST','/api/missions/'+mid+'/run',{})
  deadline=time.monotonic()+75
  while True:
   mission=request('GET','/api/missions/'+mid)['mission']
   if mission['status']=='completed':break
   if mission['status'] in ('failed','needs_review','cancelled','interrupted') or time.monotonic()>deadline:raise RuntimeError('MISSION_'+mission['status'])
   time.sleep(1)
  export=request('GET','/api/missions/'+mid+'/export')['mission']
  artifact=request('GET','/api/missions/'+mid+'/artifact')
  raw=base64.b64decode(artifact['content_base64'],validate=True);memory=json.loads(raw)
  expected=100 if cycle==0 else 115
  if hashlib.sha256(raw).hexdigest()!=artifact['sha256']:raise RuntimeError('ARTIFACT_HASH')
  if memory['estimate']!=expected or memory['decision']!='ADOPT_PROPOSAL':raise RuntimeError('ADOPTION_MISMATCH')
  if not export['evidence']['evaluate']['native']['verification']['valid']:raise RuntimeError('NATIVE_VERIFICATION')
  if cycle and (export['input']['calibration']['baseline']!=100 or memory['lineage']['artifact_sha256']!=results[0]['artifact_sha256']):raise RuntimeError('MEMORY_CONTINUITY')
  if request('POST','/api/missions/'+mid+'/run',{})['mission']!=mission:raise RuntimeError('COMPLETED_REEXECUTION')
  results.append(dict(cycle=cycle+1,mission_id=mid,baseline=memory['baseline'],estimate=memory['estimate'],comparison=memory['comparison'],decision=memory['decision'],native_verified=True,artifact_sha256=artifact['sha256'],last_stage=mission['last_stage'],attempts=mission['attempts'],explicit_run_reused=True,lineage=memory['lineage']))
finally:
 request('DELETE','/api/agents/me',{})
 request('GET','/api/missions',accepted=(401,))
 state.write_text(json.dumps(dict(status='probe_account_erased',credential_revoked=True,secret_removed=True)))
record=dict(status='PASS',origin=origin,scope='LIVE_SERVICE_SYNTHETIC_TWO_CYCLE_PROBE',cycles=results,
 probe_account_erased=True,credential_revoked=True,verified_at=int(time.time()),
 prospective_validation='PENDING',water_savings='UNMEASURED',wellbeing='UNMEASURED',life_sustainment='UNMEASURED')
receipt.parent.mkdir(parents=True,exist_ok=True);receipt.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
