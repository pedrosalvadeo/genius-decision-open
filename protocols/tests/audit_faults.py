#!/usr/bin/env python3
"""Independent injected adapter-boundary checks; NOT black-box Kernel evidence."""
import argparse,base64,hashlib,json,sys
from pathlib import Path
from unittest.mock import patch


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    root=Path(__file__).resolve().parents[2];out=args.out if args.out.is_absolute() else root/args.out
    out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(root/'protocols'));sys.path.insert(0,str(root/'kernel'))
    import genius_kernel
    from genius_protocols import server,wire
    paths=[*sorted((root/'protocols/genius_protocols').glob('*.py')),Path(__file__).resolve(),root/'protocols/AUDIT_DESIGN_F4.md',root/'protocols/CONTRACT.md']
    hashes=lambda:{str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    before=hashes();checks=[]
    def check(label,actual,expected):checks.append({'label':label,'actual':actual,'expected':expected,'pass':actual==expected})
    def request(method,params,id='audit'):return {'jsonrpc':'2.0','id':id,'method':'genius.'+method,'params':params}
    def error(code,id='audit'):return {'jsonrpc':'2.0','id':id,'error':{'code':code,'message':{-32603:'Internal error',-32003:'Transport limit exceeded',-32601:'Method not found'}[code]}}
    inp={'encoding':'base64','data':'e30=','sha256':hashlib.sha256(b'{}').hexdigest()}
    session=server.Session();session.handle_request(request('initialize',{'protocol_versions':['genius-protocols/1.0'],'required_capabilities':[]}))
    compute=request('evaluate',{'input':inp})
    with patch.object(genius_kernel,'evaluate',side_effect=RuntimeError('controlled auditor fault')):
        check('AUD4-FAULT-001 adapter exception exact RPC error',session.handle_request(compute),error(-32603))
    # This artificial Kernel reply exercises only adapter preservation, and does
    # not claim that the mocked document is a certified formal instance.
    fake={'execution':{'status':'ERROR'},'audit_injected':True}
    with patch.object(genius_kernel,'evaluate',return_value=fake):
        reply=session.handle_request(compute);decoded=json.loads(base64.b64decode(reply['result']['result']['data']))
        check('AUD4-FAULT-002 Kernel ERROR stays successful RPC',decoded,fake)
    cap=wire.MAX_RESPONSE_BYTES
    check('actual configured response cap',cap,33554432)
    # Choose an ASCII ID length and payload length so encoded RPC response is
    # exactly 32 MiB. The sole mocked field is a controlled serialization load.
    binding=None
    for id_len in range(1,5):
        ident='i'*id_len
        def size(n):
            raw=json.dumps({'audit_load':'x'*n},separators=(',',':')).encode()+b'\n'
            reply={'jsonrpc':'2.0','id':ident,'result':{'input':inp,'result':{'encoding':'base64','data':base64.b64encode(raw).decode(),'sha256':hashlib.sha256(raw).hexdigest()}}}
            return len(json.dumps(reply,separators=(',',':')).encode())
        # Serialization grows by four bytes for each full three raw bytes.
        small=size(0)
        guess=(cap-small)*3//4
        for n in range(max(0,guess-6),guess+7):
            # Avoid materializing the large object while selecting the length.
            c=len(json.dumps({'audit_load':''},separators=(',',':')).encode())+1
            predicted=small-4*((c+2)//3)+4*((n+c+2)//3)
            if predicted==cap:binding=(ident,n);break
        if binding:break
    assert binding is not None
    ident,n=binding;calls=[]
    with patch.object(genius_kernel,'evaluate',side_effect=lambda *a,**kw:(calls.append(1) or {'audit_load':'x'*n})):
        reply=session.handle_request(request('evaluate',{'input':inp},ident))
        check('AUD4-FAULT-003 exact 32MiB delivered',len(wire.json_bytes(reply)),cap)
        check('exact cap is successful RPC','result' in reply,True)
    del reply
    with patch.object(genius_kernel,'evaluate',return_value={'audit_load':'x'*(n+3)}):
        check('AUD4-FAULT-004 above cap error',session.handle_request(request('evaluate',{'input':inp},ident)),error(-32003,ident))
    batch=[request('evaluate',{'input':inp},str(i)) for i in range(14)]
    batch+=[{'jsonrpc':'2.0','method':'genius.evaluate','params':{'input':inp}},False]
    calls=[]
    with patch.object(genius_kernel,'evaluate',side_effect=lambda *a,**kw:(calls.append(1) or {'audit_load':'x'*1800000})):
        reply=session.handle_payload(wire.json_bytes(batch))
        check('AUD4-FAULT-005 batch cap errors preserve each id',reply,[error(-32003,str(i)) for i in range(14)]+[error(-32003,None)])
        check('notifications not computed',len(calls),14)
    check('post-cap session remains READY',session.handle_request(request('unknown',{},'after')),error(-32601,'after'))
    after=hashes();report={'status':'PASS' if all(c['pass'] for c in checks) and before==after else 'FAIL','cases':5,'checks':checks,'source_before':before,'source_after':after,'sources_unchanged':before==after,'boundary':{'max_response_bytes':cap,'mock_payload_characters_at_exact_cap':n,'rpc_id':ident},'scope':'Independent auditor fault injection into Kernel API at adapter boundary; no Kernel failure or large-instance computation claimed.'}
    (out/'REPORT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'status':report['status'],'cases':5,'checks':len(checks),'sources_unchanged':before==after}));return report['status']!='PASS'
if __name__=='__main__':raise SystemExit(main())
