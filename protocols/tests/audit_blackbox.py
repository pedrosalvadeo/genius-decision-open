#!/usr/bin/env python3
"""Independent F4 black-box checks. Never imports Kernel or adapter modules."""
from __future__ import annotations
import argparse
import base64
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

from audit_fixture import instance, certificate, expected_projection, semantic_projection

PROTOCOL = 'genius-protocols/1.0'
ERRORS = {-32700:'Parse error', -32600:'Invalid Request', -32601:'Method not found',
          -32602:'Invalid params', -32603:'Internal error', -32001:'Incompatible protocol',
          -32002:'Invalid session state', -32003:'Transport limit exceeded'}


def encoded(value, *, pretty=False):
    return json.dumps(value, ensure_ascii=False, separators=None if pretty else (',', ':'),
                      indent=2 if pretty else None).encode('utf-8')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def envelope(raw):
    return {'encoding':'base64', 'data':base64.b64encode(raw).decode('ascii'), 'sha256':digest(raw)}


def unpack(value):
    assert set(value) == {'encoding','data','sha256'} and value['encoding'] == 'base64'
    raw = base64.b64decode(value['data'], validate=True)
    assert base64.b64encode(raw).decode('ascii') == value['data']
    assert digest(raw) == value['sha256']
    return raw


def req(method, params=None, id='case'):
    return {'jsonrpc':'2.0', 'id':id, 'method':'genius.'+method, 'params':{} if params is None else params}


def init(id='initialize', versions=None, caps=None):
    return req('initialize', {'protocol_versions':[PROTOCOL] if versions is None else versions,
                             'required_capabilities':[] if caps is None else caps}, id)


def rpcerr(code, id='case'):
    return {'jsonrpc':'2.0','id':id,'error':{'code':code,'message':ERRORS[code]}}


def strict_output(raw):
    def pairs(items):
        out={}
        for key,value in items:
            if key in out: raise ValueError('duplicate response key')
            out[key]=value
        return out
    def constant(value): raise ValueError(value)
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)


class Audit:
    def __init__(self, root, out):
        self.root=root;self.out=out;out.mkdir(parents=True,exist_ok=False)
        self.env=os.environ.copy();self.env['PYTHONPATH']=str(root/'kernel')+os.pathsep+str(root/'protocols')
        self.command=[sys.executable,'-m','genius_protocols'];self.cases=[];self.checks=[]
        self.source_before=self.sources()

    def sources(self):
        names=[self.root/'protocols/CONTRACT.md', self.root/'protocols/AUDIT_DESIGN_F4.md',
               *sorted((self.root/'protocols/genius_protocols').glob('*.py')),
               *sorted((self.root/'protocols/tests').glob('audit_*.py')),
               *sorted((self.root/'kernel/genius_kernel').glob('*.py'))]
        return {str(p.relative_to(self.root)):digest(p.read_bytes()) for p in names}

    def check(self, label, actual, expected):
        self.checks.append({'label':label,'actual':actual,'expected':expected,'pass':actual==expected})

    def process(self, frames, *, initialized=True, chunks=None):
        if initialized:frames=[init()]+frames
        raw=b''.join(f if isinstance(f,bytes) else encoded(f)+b'\n' for f in frames)
        if chunks is None:
            proc=subprocess.run(self.command,input=raw,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                cwd=self.root,env=self.env,timeout=30)
            output,err,code=proc.stdout,proc.stderr,proc.returncode
        else:
            proc=subprocess.Popen(self.command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,cwd=self.root,env=self.env)
            cursor=0
            for size in chunks:
                proc.stdin.write(raw[cursor:cursor+size]);proc.stdin.flush();cursor+=size
            proc.stdin.write(raw[cursor:]);proc.stdin.close();proc.stdin=None
            output,err=proc.communicate(timeout=30);code=proc.returncode
        number=len(list(self.case_dir.glob('request_*.bin')))+1
        (self.case_dir/f'request_{number:02}.bin').write_bytes(raw)
        (self.case_dir/f'stdout_{number:02}.bin').write_bytes(output)
        (self.case_dir/f'stderr_{number:02}.bin').write_bytes(err)
        self.check('stdout LF complete',not output or output.endswith(b'\n'),True)
        self.check('stderr empty',err,b'')
        responses=[strict_output(line) for line in output.splitlines()]
        if initialized:
            self.check('initialize response id',responses[0]['id'],'initialize')
            self.check('initialize product',responses[0].get('result',{}).get('protocols_version'),'GENIUS-PROTOCOLS-1.0.0')
            responses=responses[1:]
        return responses,code

    def case(self,name,fn):
        self.checks=[];self.case_dir=self.out/name;self.case_dir.mkdir()
        try:
            fn(); error=None
        except Exception as exc:
            error=type(exc).__name__+': '+str(exc)
        status='ERROR' if error else 'FAIL' if any(not c['pass'] for c in self.checks) else 'PASS'
        record={'id':name,'status':status,'checks':self.checks,'error':error}
        (self.case_dir/'CASE.json').write_text(json.dumps(record,indent=2,ensure_ascii=False,default=str)+'\n')
        self.cases.append(record)
        print(name,status, error or '',flush=True)

    def errors(self, frames, expected, *, initialized=True, exitcode=0):
        response,code=self.process(frames,initialized=initialized)
        self.check('process exit',code,exitcode);self.check('exact RPC responses',response,expected)

    def result(self, raw, *, limits=None):
        params={'input':envelope(raw)}
        if limits is not None:params['limits']=limits
        response,code=self.process([req('evaluate',params)])
        self.check('evaluate exit',code,0);self.check('single evaluate response',len(response),1)
        self.check('evaluate response shape',sorted(response[0]),['id','jsonrpc','result'])
        unit=response[0]['result'];self.check('unit fields',sorted(unit),['input','result'])
        self.check('exact input bytes',unpack(unit['input']),raw)
        result_raw=unpack(unit['result']);result=strict_output(result_raw)
        self.check('Result input digest',result['input_digest'],digest(raw))
        return result,result_raw

    def verify(self, raw, candidate, *, method='verify_result', limits=None):
        params={'input':envelope(raw),'candidate':envelope(candidate)}
        if limits is not None:params['limits']=limits
        response,code=self.process([req(method,params)])
        self.check('verify exit',code,0);self.check('single verify response',len(response),1)
        value=response[0]['result'];self.check('verify result fields',sorted(value),['artifact_digest','input_digest','report'])
        self.check('verify input digest',value['input_digest'],digest(raw))
        self.check('verify artifact digest',value['artifact_digest'],digest(candidate))
        return value['report']

    def finish(self):
        after=self.sources();summary={'status':'PASS' if all(c['status']=='PASS' for c in self.cases) and after==self.source_before else 'FAIL',
          'cases':len(self.cases),'checks':sum(len(c['checks']) for c in self.cases),
          'passed':sum(c['status']=='PASS' for c in self.cases),'failed':sum(c['status']=='FAIL' for c in self.cases),
          'errors':sum(c['status']=='ERROR' for c in self.cases),'source_before':self.source_before,'source_after':after,
          'sources_unchanged':after==self.source_before,'python':sys.version,'platform':platform.platform(),
          'command':[sys.executable,'protocols/tests/audit_blackbox.py','--out',str(self.out.relative_to(self.root) if self.out.is_relative_to(self.root) else self.out)],
          'independence':'New fixture and normative oracles; black-box subprocess only; no subject imports.',
          'case_results':[{'id':c['id'],'status':c['status']} for c in self.cases]}
        (self.out/'REPORT.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ['source_before','source_after','case_results']}));return summary['status']=='PASS'


def run(a):
    obj=instance();raw=encoded(obj);cache={}
    def base():
        result,data=a.result(raw);cache.update(result=result,result_raw=data)
        a.check('independent full projection',semantic_projection(result),expected_projection())
    a.case('AUD4-SEM-001',base)
    def bytes_equivalent():
        alt=encoded(obj,pretty=True)+b'\n';r,_=a.result(alt)
        a.check('different bytes have different digest',r['input_digest']!=digest(raw),True)
        a.check('same mathematical projection',semantic_projection(r),expected_projection())
        a.check('cross-byte certificate rejected',a.verify(alt,encoded(certificate(digest(raw))),method='verify_certificate')['status'],'INVALID')
    a.case('AUD4-ID-001',bytes_equivalent)
    def versions():
        frames=[req('evaluate',{'input':envelope(raw)}),init('bad',['genius-protocols/9.0']),
                init('cap',[PROTOCOL],['MCP']),init('ok',['genius-protocols/9.0',PROTOCOL],['evaluate']),init('again')]
        res,code=a.process(frames,initialized=False);a.check('exit',code,0)
        a.check('pre-init',res[0],rpcerr(-32002));a.check('version incompatibility',res[1],rpcerr(-32001,'bad'))
        a.check('capability incompatibility',res[2],rpcerr(-32001,'cap'))
        cap=res[3]['result'];a.check('selected exact protocol',cap['protocol_version'],PROTOCOL)
        a.check('Kernel version',cap['kernel_version'],'GENIUS-KERNEL-1.0.1')
        a.check('capabilities',sorted(cap['capabilities']),['evaluate','verify_certificate','verify_result'])
        a.check('exact limits',cap['transport_limits'],{'max_frame_bytes':'16777216','max_input_bytes':'2097152','max_candidate_bytes':'8388608','max_response_bytes':'33554432','max_batch_items':'16','max_limit_digits':'12'})
        a.check('repeat init',res[4],rpcerr(-32002,'again'))
    a.case('AUD4-NEG-001',versions)
    def notifications():
        note=init();note.pop('id');r= req('evaluate',{'input':envelope(raw)})
        a.errors([note,r],[rpcerr(-32002)],initialized=False)
        a.errors([[note],r],[rpcerr(-32002)],initialized=False)
        a.errors([[init('batch')],r],[[rpcerr(-32002,'batch')],rpcerr(-32002)],initialized=False)
        for method in ['initialize','evaluate','verify_result','unknown']:
            n=req(method);n.pop('id')
            a.errors([n,req('unknown',id='sentinel')],[rpcerr(-32601,'sentinel')])
        a.errors([[{'jsonrpc':'2.0','method':'genius.evaluate'},{'jsonrpc':'2.0','method':'unknown','params':[]}]],[])
        a.errors([{'jsonrpc':'2.0','method':3}],[rpcerr(-32600,None)])
    a.case('AUD4-NOT-001',notifications)
    def batch():
        a.errors([[]],[rpcerr(-32600,None)])
        a.errors([[req('unknown',id=str(i)) for i in range(16)]],[[rpcerr(-32601,str(i)) for i in range(16)]])
        a.errors([[req('unknown')]*17],[rpcerr(-32003,None)])
        n=req('unknown');n.pop('id')
        a.errors([[req('unknown',id=0),n,False,req('unknown',id=None)]],[[rpcerr(-32601,0),rpcerr(-32600,None),rpcerr(-32601,None)]])
    a.case('AUD4-BAT-001',batch)
    for i,token in enumerate(['true','1.0','1e0','9007199254740992','-9007199254740992','""','"á"','[]','{}']):
        frame=('{"jsonrpc":"2.0","id":'+token+',"method":"genius.unknown"}\n').encode()
        a.case(f'AUD4-RPC-{i+1:03}',lambda frame=frame:a.errors([frame],[rpcerr(-32600,None)]))
    def ids():
        a.errors([req('unknown',id=x) for x in [None,0,-9007199254740991,9007199254740991,'0']],
                 [rpcerr(-32601,x) for x in [None,0,-9007199254740991,9007199254740991,'0']])
    a.case('AUD4-RPC-010',ids)
    badframes=[b'\n',b'\xff\n',b'\xef\xbb\xbf{}\n',b'{"x":1,"x":2}\n',b'{"a":1,"\\u0061":2}\n',
               b'{"x":NaN}\n',b'{"x":Infinity}\n',b'{"x":"\\ud800"}\n',b'{"x":1,}\n']
    for i,frame in enumerate(badframes):
        a.case(f'AUD4-PAR-{i+1:03}',lambda frame=frame:a.errors([frame,req('unknown')],[rpcerr(-32700,None),rpcerr(-32601)]))
    for i,frame in enumerate([{'jsonrpc':'2.0','id':'case','method':'genius.evaluate','params':1},
                              {'jsonrpc':'2.0','id':'case','method':'genius.unknown','extra':0},42]):
        a.case(f'AUD4-REQ-{i+1:03}',lambda frame=frame:a.errors([frame],[rpcerr(-32600,None)]))
    def framing():
        a.errors([encoded(req('unknown'))+b'\r\n'],[rpcerr(-32601)])
        a.errors([encoded(init())],[],initialized=False,exitcode=2)
        a.errors([b'{'],[],initialized=False,exitcode=2)
        r,code=a.process([req('unknown')],chunks=[1,2,3,5,7,11]);a.check('fragmented exit',code,0);a.check('fragmented exact response',r,[rpcerr(-32601)])
        a.errors([b' '*(16777216-2)+b'{}\n'],[rpcerr(-32600,None)],initialized=False)
        a.errors([b' '*16777217+b'\n'],[rpcerr(-32003,None)],initialized=False,exitcode=2)
    a.case('AUD4-FRM-001',framing)
    for i,blob in enumerate([{'encoding':'base64','data':'e31=','sha256':digest(b'{}')},
                             {'encoding':'base64','data':'e30','sha256':digest(b'{}')},
                             {'encoding':'base64','data':'e30=\n','sha256':digest(b'{}')},
                             {'encoding':'base64','data':'e30=','sha256':'0'*64},
                             {'encoding':'base64','data':'e30=','sha256':digest(b'{}').upper()},
                             {'encoding':'base64','data':'e30=','sha256':digest(b'{}'),'path':'/etc/passwd'}]):
        a.case(f'AUD4-BLOB-{i+1:03}',lambda blob=blob:a.errors([req('evaluate',{'input':blob})],[rpcerr(-32602)]))
    for i,value in enumerate([0,True,None,'01','-1','1.0','1000000000000']):
        a.case(f'AUD4-LIM-{i+1:03}',lambda value=value:a.errors([req('evaluate',{'input':envelope(raw),'limits':{'max_nodes':value}})],[rpcerr(-32602)]))
    def limits():
        for name,value in [('max_nodes','2'),('max_operations','0'),('max_input_bytes',str(len(raw)-1)),('max_integer_digits','0'),('max_seconds','0')]:
            r,data=a.result(raw,limits={name:value});a.check(name+' status',r['execution']['status'],'LIMITED')
            a.check(name+' no integration',r['integration']['state'],'BLOCKED');a.check(name+' no decision',r['decision']['state'],'BLOCKED')
            a.check(name+' verifier incomplete',a.verify(raw,data)['status'],'INCOMPLETE')
        r,_=a.result(raw,limits={'max_nodes':'3','max_input_bytes':str(len(raw))});a.check('exact operational boundary',semantic_projection(r),expected_projection())
        a.check('verifier limit',a.verify(raw,cache['result_raw'],limits={'max_operations':'0'})['status'],'INCOMPLETE')
    a.case('AUD4-LIM-008',limits)
    def blobs_limits():
        accepted=b'{}'+b' '*(2097152-2);r,_=a.result(accepted);a.check('exact input cap reaches Kernel',r['presentation'],'INVALID')
        a.errors([req('evaluate',{'input':envelope(accepted+b' ')})],[rpcerr(-32003)])
        c=b'{}'+b' '*(8388608-2);a.check('exact candidate cap reaches verifier',a.verify(raw,c)['status'],'INVALID')
        a.errors([req('verify_result',{'input':envelope(raw),'candidate':envelope(c+b' ')})],[rpcerr(-32003)])
    a.case('AUD4-LIM-009',blobs_limits)
    for i,bad in enumerate([b'',b'\xff',b'{"format":1,"format":2}',b'{"x":"\\ud800"}',encoded(obj).replace(b'"horizon":"1"',b'"horizon":1'),encoded(obj).replace(b'genius-fp1/1.0',b'genius-fp1/9.0')]):
        def invalid(raw=bad):
            r,_=a.result(raw);a.check('invalid presentation via successful RPC',r['presentation'],'INVALID');a.check('no policies',r['policies'],[])
        a.case(f'AUD4-INP-{i+1:03}',invalid)
    def semantics():
        partial=deepcopy(obj);partial['welfare']['values'].pop();r,_=a.result(encoded(partial));p=r['policies'][0]
        a.check('partial input valid',r['presentation'],'VALID');a.check('partial computation complete',r['execution']['status'],'COMPLETE')
        a.check('relative frontier',r['decision']['value']['coverage'],'RELATIVE');a.check('no relative selection',r['decision']['value']['selection']['state'],'OUTSIDE_DOMAIN')
        a.check('partial null branch preserved',len(p['causal']['leaves']),2);a.check('independent PVS',p['probability']['pvs']['value'],'1/1')
        a.check('welfare missing not zero',p['welfare']['profile']['state'],'OUTSIDE_DOMAIN')
        hard=deepcopy(obj);hard['constraints'].append({'id':'universal','kind':'task_all','scope':'LEAVES','basis':['assumption']})
        r,_=a.result(encoded(hard));p=r['policies'][0];a.check('null leaf refutes universal',p['hard'][1]['value']['value'],'0')
        a.check('hard no causal pruning',len(p['causal']['leaves']),2);a.check('PVS one no universal guarantee',p['probability']['pvs']['value'],'1/1')
        a.check('no feasible frontier',r['decision']['value']['frontier'],[])
        law=deepcopy(obj);law['law']['rows'][0]['weights'][0]['mass']='1/2';r,_=a.result(encoded(law))
        a.check('bad law structurally valid',r['presentation'],'VALID');a.check('bad law BLOCKED',r['policies'][0]['probability']['pvs']['state'],'BLOCKED')
        missing=deepcopy(obj);missing['model']['updates']=[];r,_=a.result(encoded(missing))
        a.check('unresolved query presentation',r['presentation'],'UNRESOLVED');a.check('no invented leaves',r['policies'][0]['causal']['leaves'],[])
    a.case('AUD4-SEM-002',semantics)
    def certificates():
        for negative,superset in [(False,False),(False,True),(True,False)]:
            candidate=encoded(certificate(digest(raw),negative=negative,superset=superset))
            a.check('handmade positive '+str((negative,superset)),a.verify(raw,candidate,method='verify_certificate'),{'valid':True,'status':'VALID','errors':[]})
        mutations=[]
        c=certificate(digest(raw));c['certificate']['A']=[];mutations.append(c)
        c=certificate(digest(raw));c['certificate']['value']='0';mutations.append(c)
        c=certificate(digest(raw));c['certificate']['task_rows'][1]['value']='0';mutations.append(c)
        c=certificate(digest(raw));c['certificate']['read']['leaves']=[];mutations.append(c)
        c=certificate('0'*64);mutations.append(c)
        c=certificate(digest(raw));c['certificate']['A'].append('no');c['certificate']['task_rows'].append({'state':'no','value':'1'});mutations.append(c)
        for i,c in enumerate(mutations):a.check('certificate mutation '+str(i),a.verify(raw,encoded(c),method='verify_certificate')['status'],'INVALID')
    a.case('AUD4-CER-001',certificates)
    def candidate_syntax():
        for value in [b'{"a":1,"a":2}',b'{"a":1,}',b'{"a":1,"s":"\\ud800"}',b'\xff',b'{"x":NaN}']:
            a.check('candidate malformed syntax',a.verify(raw,value),{'valid':False,'status':'INVALID','errors':['CANDIDATE_SYNTAX']})
        for value in [b'1',b'{"a":1.2}',b'{"a":'+b'9'*100001+b'}']:
            a.check('candidate numeric type',a.verify(raw,value),{'valid':False,'status':'INVALID','errors':['CANDIDATE_TYPE']})
    a.case('AUD4-CER-002',candidate_syntax)
    def results():
        a.check('valid complete Result',a.verify(raw,cache['result_raw']),{'valid':True,'status':'VALID','errors':[]})
        mutations=[]
        r=deepcopy(cache['result']);r['input_digest']='0'*64;mutations.append(r)
        r=deepcopy(cache['result']);r['format']='genius-fp1-result/9.0';mutations.append(r)
        r=deepcopy(cache['result']);r['policies'][0]['causal']['leaves'].pop();mutations.append(r)
        r=deepcopy(cache['result']);r['policies'][0]['probability']['pvs']['value']='0/1';mutations.append(r)
        r=deepcopy(cache['result']);r['policies'][0]['welfare']['cells'][-1]['value']['value']='0/1';mutations.append(r)
        r=deepcopy(cache['result']);r['decision']['value']['coverage']='RELATIVE';mutations.append(r)
        r=deepcopy(cache['result']);r['integration']['value']['assumptions']=[];mutations.append(r)
        for i,r in enumerate(mutations):a.check('Result mutation '+str(i),a.verify(raw,encoded(r))['status'],'INVALID')
    a.case('AUD4-RES-001',results)


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    root=args.root.resolve();out=args.out if args.out.is_absolute() else root/args.out
    audit=Audit(root,out);run(audit);return 0 if audit.finish() else 1

if __name__=='__main__':raise SystemExit(main())
