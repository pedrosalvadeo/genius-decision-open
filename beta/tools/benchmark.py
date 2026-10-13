"""Declared synthetic operational loads; never empirical F6A evidence."""
import json
from pathlib import Path
import resource
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]


def child(profile):
    from genius_beta.adapter import execute_profile
    if profile == 'hours_100':
        payload = {'profile':'hours','assignments':[{'id':f't{i}','credit':'1.25'} for i in range(100)],
                   'target':'120','permission_confirmed':True,'scope_acknowledged':True}
    else:
        payload = json.loads((ROOT/'beta/examples/fdq-frontier.json').read_text())
        payload['permission_confirmed'] = payload['scope_acknowledged'] = True
    start = time.perf_counter()
    with tempfile.TemporaryDirectory() as directory:
        out = execute_profile(payload, Path(directory)/'case')
        size = sum(p.stat().st_size for p in Path(directory).rglob('*') if p.is_file())
        response = out['response']
        if profile == 'hours_100':
            answer = response['decisions'][0]['answers'][0]['value']
            assert answer['assigned']['value'] == '125/1' and answer['excess']['value'] == '5/1'
        else:
            assert response['decisions'][0]['answers'][0]['value']['value']['frontier'] == ['p','s']
        ru, ch = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
        print(json.dumps({'profile':profile,'wall_seconds':time.perf_counter()-start,
                          'cpu_seconds_parent_and_children':ru.ru_utime+ru.ru_stime+ch.ru_utime+ch.ru_stime,
                          'parent_maxrss_kib':ru.ru_maxrss,'largest_child_maxrss_kib':ch.ru_maxrss,
                          'store_bytes':size,'response_bytes':len(json.dumps(out).encode()),'correct':True}))


if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--child':
        child(sys.argv[2])
    else:
        rows=[]
        for profile in ('hours_100','fdq_received_frontier'):
            for _ in range(3):
                r=subprocess.run([sys.executable,'-B',__file__,'--child',profile],capture_output=True,text=True,timeout=40,check=True)
                rows.append(json.loads(r.stdout))
        print(json.dumps({'format':'genius-beta-operational-benchmark/1','synthetic':True,
                          'scope':'Sequential local adapter executions, 3 repeats per declared load; not HTTP, concurrency, cloud billing, SLA, human utility or worst-case FDQ.',
                          'memory_note':'Linux RSS high-water parent and largest child separately; not simultaneous container peak.',
                          'python':sys.version,'samples':rows},indent=2))
