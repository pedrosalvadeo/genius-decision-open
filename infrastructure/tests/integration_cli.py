#!/usr/bin/env python3
"""Reproduce end-to-end local synthetic CLI and recovery; keep exact command evidence."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
PROFILE='local-fp1-single-uid-lab-v1' if os.geteuid()==0 else 'local-fp1-v1'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    commands=[];checks=[]
    def check(name,condition,**details):
        checks.append({'name':name,'pass':bool(condition),**details})
        if not condition:raise AssertionError(name)
    def run(name,*arguments,expected=0,profile=True):
        cmd=[sys.executable,'-I',str(ROOT/'infrastructure/operate.py'),*map(str,arguments)]
        if profile:cmd+=['--profile',PROFILE]
        t=time.monotonic();before=resource.getrusage(resource.RUSAGE_CHILDREN)
        proc=subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=45)
        elapsed=time.monotonic()-t;after=resource.getrusage(resource.RUSAGE_CHILDREN)
        record={'name':name,'command':cmd,'cwd':str(ROOT),'exit_code':proc.returncode,
                'wall_seconds':elapsed,'children_cpu_seconds':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
                'stdout':proc.stdout.decode('utf-8'),'stderr':proc.stderr.decode('utf-8')}
        commands.append(record)
        (out/'COMMANDS.json').write_text(json.dumps(commands,indent=2)+'\n')
        check(name+'_exit',proc.returncode==expected,actual=proc.returncode,expected=expected)
        return json.loads(proc.stdout) if proc.stdout else None
    report={'status':'RUNNING','profile':PROFILE,'environment':{'python':sys.version,'linux':platform.platform(),'euid':os.geteuid()},
            'claims':'Synthetic one-owner local run, whole CLI observed timings; not production capacity or utility','checks':checks}
    try:
        store=out/'store'
        if os.geteuid()==0:
            run('default_root_refusal','init','--store',out/'refused','--profile','local-fp1-v1',expected=2,profile=False)
            check('default_refusal_no_store',not (out/'refused').exists())
        run('init','init','--store',store)
        raw=ROOT/'examples/water_habitat_f4/input.json'
        evaluation=run('evaluate','run','--store',store,'--method','evaluate','--input',raw)
        run_dir=store/'runs'/evaluation['run_id']
        check('exact_input_bytes',(run_dir/'input.json').read_bytes()==raw.read_bytes())
        value=json.loads((run_dir/'result.json').read_bytes())
        check('result_digest_bound',value['input_digest']==hashlib.sha256(raw.read_bytes()).hexdigest())
        verify=run('verify_result','run','--store',store,'--method','verify_result','--input',run_dir/'input.json','--candidate',run_dir/'result.json')
        vr=json.loads((store/'runs'/verify['run_id']/'report.json').read_bytes())
        check('verify_result_valid',vr['status']=='VALID' and vr['valid'] is True)
        cert=ROOT/'validation/CONSUMER_CONFORMANCE_04/artifacts/C10_valid'
        cv=run('verify_certificate','run','--store',store,'--method','verify_certificate','--input',cert/'input.json','--candidate',cert/'candidate.json')
        cr=json.loads((store/'runs'/cv['run_id']/'report.json').read_bytes())
        check('verify_certificate_valid',cr['status']=='VALID')
        limit=out/'limits.json';limit.write_text('{"max_operations":"0"}\n')
        limited=run('kernel_limited','run','--store',store,'--method','evaluate','--input',raw,'--kernel-limits',limit)
        lv=json.loads((store/'runs'/limited['run_id']/'result.json').read_bytes())
        check('real_kernel_limited_delivered',limited['status']=='DELIVERED' and lv['execution']['status']=='LIMITED')
        stopped=run('wall_limit','run','--store',store,'--method','evaluate','--input',raw,'--wall-seconds','0.000001',expected=1)
        stopdir=store/'runs'/stopped['run_id']
        check('wall_not_mathematical',stopped['status']=='FAILED' and not (stopdir/'result.json').exists())
        retry=run('retry','run','--store',store,'--method','evaluate','--input',raw,'--retry-of',stopped['run_id'])
        check('retry_new_execution',retry['run_id']!=stopped['run_id'])
        before=run('check','check','--store',store)
        run('backup','backup','--store',store,'--destination',out/'snapshot')
        run('restore','restore','--backup',out/'snapshot','--destination',out/'restored')
        after=run('check_restored','check','--store',out/'restored')
        check('restored_content_same',before==after)
        run('rollback','rollback','--backup',out/'snapshot','--destination',out/'rollback')
        rolled=run('check_rollback','check','--store',out/'rollback')
        check('rollback_content_same',before==rolled)
        check('rollback_exact_result',(out/'rollback/runs'/evaluation['run_id']/'result.json').read_bytes()==(run_dir/'result.json').read_bytes())
        run('restore_no_overwrite','restore','--backup',out/'snapshot','--destination',out/'restored',expected=1)
        for i in range(10):run('load_'+str(i),'run','--store',store,'--method','evaluate','--input',raw)
        load=[c for c in commands if c['name'].startswith('load_')]
        total=sum(c['wall_seconds'] for c in load)
        report['capacity_observed']={'runs':len(load),'parallelism':1,'queue':'none','input_bytes':raw.stat().st_size,
            'min_wall_seconds':min(c['wall_seconds'] for c in load),'median_wall_seconds':statistics.median(c['wall_seconds'] for c in load),
            'max_wall_seconds':max(c['wall_seconds'] for c in load),'total_wall_seconds':total,'observed_runs_per_second':len(load)/total,
            'children_cpu_seconds':sum(c['children_cpu_seconds'] for c in load),'no_remote_billed_service':True,
            'local_compute_monetary_cost':'not measured; existing environment subscription not allocated'}
        final=run('final_check','check','--store',store);report['store_summary']=final
        report['status']='PASS'
    except Exception as exc:
        report['status']='FAIL';report['error']=repr(exc)
    report['checks_count']=len(checks);report['passed_checks']=sum(c['pass'] for c in checks)
    (out/'REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'checks':len(checks),'out':str(out)}))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
