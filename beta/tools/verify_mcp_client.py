"""Official MCP SDK client against real local HTTP and the real isolated worker.

Install beta/tests/mcp-client.lock in a test environment. This never contacts
production, never prints credentials, and cleans its disposable database.
"""
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from importlib.metadata import version

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'beta'))
from genius_beta.app import create_app
from genius_beta.worker import Worker
from werkzeug.serving import WSGIRequestHandler,make_server
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
import httpx2


class QuietHandler(WSGIRequestHandler):
    def log_request(self,*args,**kwargs): pass


async def exercise(url):
    receipt={'sdk':'mcp','sdk_version':version('mcp'),'transport':'real-loopback-http','protocols':[]}
    for mode in ('auto','legacy'):
        async with httpx2.AsyncClient(trust_env=False) as public_http, Client(streamable_http_client(url+'/mcp',http_client=public_http),mode=mode) as client:
            tools=await client.list_tools()
            assert {t.name for t in tools.tools}=={'get_capabilities','read_demo_result','run_demo'}
            caps=await client.call_tool('get_capabilities',{})
            assert not caps.is_error and caps.structured_content['mcp_available']
            saved=await client.call_tool('read_demo_result',{'example':'hours-unknown'})
            assert not saved.is_error and saved.structured_content['saved_receipt']
            assert 'PV_UNKNOWN' in json.dumps(saved.structured_content)
            receipt['protocols'].append(client.protocol_version)
            if mode=='auto':
                demo=await client.call_tool('run_demo',{'example':'hours-unknown'})
                assert not demo.is_error
                assert demo.structured_content['temporary_space_deleted']
                assert demo.structured_content['result']['evidence_origin']=='synthetic'
                receipt['anonymous_live_demo_completed_and_deleted']=True
    async with httpx2.AsyncClient(trust_env=False) as http:
        bootstrap=await http.post(url+'/api/agents/register',json={'policy_version':'agent-access-2026-10-06-v1','data_policy_acknowledged':True})
        assert bootstrap.status_code==201
        token=bootstrap.json()['credential']['token']
        auth={'Authorization':'Bearer '+token}
        try:
            async with httpx2.AsyncClient(headers=auth,trust_env=False) as private_http:
                async with Client(streamable_http_client(url+'/mcp',http_client=private_http)) as client:
                    listing=await client.list_tools()
                    names={t.name for t in listing.tools}
                    assert {'create_case','get_job','delete_agent_space'}<=names and 'delete_case' not in names
                    payload=json.loads((ROOT/'beta/examples/hours-known.json').read_text())
                    profile=payload.pop('profile')
                    case=await client.call_tool('create_case',{'title':'Synthetic SDK interop','profile':profile,'input':payload})
                    assert not case.is_error
                    cid=case.structured_content['case']['id']
                    job=await client.call_tool('run_case',{'case_id':cid})
                    assert not job.is_error
                    jid=job.structured_content['job']['id']
                    for _ in range(20):
                        result=await client.call_tool('get_job',{'job_id':jid})
                        assert not result.is_error
                        if result.structured_content['job']['status']=='completed':break
                        await asyncio.sleep(.2)
                    assert result.structured_content['job']['status']=='completed'
                    assert result.structured_content['job']['result']['evidence_origin']=='synthetic'
                    denied=await client.call_tool('delete_case',{'case_id':cid,'confirm':True})
                    assert denied.is_error and denied.structured_content['error']['http_status']==403
                    deleted=await client.call_tool('delete_agent_space',{'confirm':True})
                    assert not deleted.is_error
                    receipt['private_scoped_flow_completed_and_deleted']=True
            assert (await http.get(url+'/api/agents/me',headers=auth)).status_code==401
            receipt['deleted_key_revoked']=True
        finally:
            # Idempotent cleanup attempt only on our disposable identity.
            await http.delete(url+'/api/agents/me',headers=auth)
            token=None;auth=None
    return receipt


def main():
    if os.environ.get('GENIUS_R2_BACKUP_ENABLED')=='true':raise RuntimeError('Offline verification only')
    with tempfile.TemporaryDirectory(prefix='genius-mcp-interop-') as temp:
        root=Path(temp)
        config=dict(DATA_DIR=root,DATABASE=root/'db.sqlite3',SUSPEND_FILE=root/'SUSPENDED',
            PUBLIC_URL='http://127.0.0.1',ENV='development',REGISTRATION_OPEN=True,TESTING=True)
        app=create_app(config)
        server=make_server('127.0.0.1',0,app,threaded=True,request_handler=QuietHandler)
        url='http://127.0.0.1:'+str(server.server_port)
        app.config['PUBLIC_URL']=url
        stop=threading.Event();errors=[]
        def work():
            worker=Worker(config)
            try:
                worker.acquire()
                while not stop.wait(.03):worker.run_once()
            except Exception as exc:errors.append(type(exc).__name__)
            finally:worker.close()
        web=threading.Thread(target=server.serve_forever);worker=threading.Thread(target=work)
        web.start();worker.start()
        try:
            receipt=asyncio.run(exercise(url))
        finally:
            stop.set();worker.join(5);server.shutdown();web.join(5);server.server_close()
        assert not errors and not worker.is_alive() and not web.is_alive()
        receipt['passed']=True
        print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
