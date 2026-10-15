"""Stateless MCP/JSON transport over the existing bounded REST operations.

No new execution path, credential issuance, session authentication or outbound
proxy. Every private operation passes the REST gate, including scope, owner,
expiry, budget, suspension and durable-deletion checks.
"""
import base64
import json
from pathlib import Path
import re
import time
from flask import jsonify, request
from werkzeug.test import EnvironBuilder
from .agent_access import EXAMPLES
from . import twin_mcp, club_mcp, mission_mcp, taxis

VERSIONS = ('2026-07-28', '2025-11-25', '2025-06-18', '2025-03-26')
INFO = dict(name='genius-decision',version='0.2.0')
ID_SCHEMA = dict(type='string',pattern='^[a-f0-9]{32}$')
CHOICE_SCHEMA = json.loads((Path(__file__).with_name('static')/'openapi.json').read_text())['components']['schemas']['ChoiceModel']


def tool(name, description, properties=None, required=(), scope=None, read=True, destructive=False):
    return dict(name=name,description=description,
        inputSchema=dict(type='object',properties=properties or {},required=list(required),additionalProperties=False),
        annotations=dict(readOnlyHint=read,destructiveHint=destructive,idempotentHint=read or destructive,openWorldHint=False),
        _meta={'app.geniusdecision/required-scope':scope})


TOOLS = [
    tool('get_contribution_inbox','Read the public contribution deposit contract. Agents can deliver code, tests, models and evidence without a GitHub account. Only publish material authorized by your operator.'),
    tool('submit_contribution','Publish one immutable contribution for authorized AI review. All fields and files become publicly readable. Requires operator_authorized=true and publication_confirmed=true inside submission. No private data or secrets. Does not execute, approve or merge the files. First read get_contribution_inbox for the exact contract.',
         {'submission':dict(type='object')},('submission',),read=False),
    tool('get_contribution','Read a public contribution and its immutable storage receipt. Receipt status is not review or integration status.',
         {'id':dict(type='string',pattern='^[a-f0-9]{64}$')},('id',)),
    tool('find_opportunities','Find voluntary Genius contribution opportunities for an explicit goal and capabilities. Read only: no execution, account, tracking, inference or forwarding. Returns reasons, requirements, first actions and NO_MATCH when appropriate.',
         {'goal':dict(type='string',enum=list(taxis.GOALS)),
          'capabilities':dict(type='array',items=dict(type='string',enum=list(taxis.CAPABILITIES)),maxItems=10,uniqueItems=True),
          'access':dict(type='string',enum=list(taxis.ACCESS)),
          'limit':dict(type='integer',minimum=1,maximum=10)}),
    tool('get_capabilities','Read Genius availability, limits, supported formal profiles and data policy.'),
    tool('read_demo_result','Read a SAVED real-engine synthetic result; does not execute a new job. Preserve unknown values and limits.',
         {'example':dict(type='string',enum=['hours-known','hours-unknown'])}),
    tool('run_demo','Execute one fixed SYNTHETIC example using the real engine; consumes shared quota. Temporary space is deleted before returning. No custom input or human data. Do not blindly retry failures.',
         {'example':dict(type='string',enum=list(EXAMPLES))},read=False),
    tool('list_cases','List only this agent credential’s own cases.',scope='cases:read'),
    tool('get_case','Read only this agent’s own case, revisions and job results.',{'case_id':ID_SCHEMA},('case_id',),scope='cases:read'),
    tool('prepare_decision','Review explicit alternatives, criteria, limits and preferences for a low-risk declared comparison. Narrative is NOT interpreted. Return questions and a model digest: confirm the represented model with its decision owner before creating a choice case. Only synthetic or non-personal data.',
         CHOICE_SCHEMA['properties'],
         ('context','criteria','alternatives','selection'),scope='cases:write'),
    tool('revise_case','Save a new version in this agent’s own space; preserves previous results. For choice inputs obtain a fresh prepare_decision digest and confirm changed data/preferences first.',
         {'case_id':ID_SCHEMA,'input':dict(type='object')},('case_id','input'),scope='cases:write',read=False),
    tool('create_case','Create a case in this agent’s own space. Only synthetic or non-personal data. Requires explicit input permission_confirmed and scope_acknowledged. Profiles: formal hours, supplied FDQ certificate or choice (confirmed low-risk declared comparison; first call prepare_decision). Never invent quantities, priorities or confirmation on behalf of a person.',
         {'title':dict(type='string',minLength=1,maxLength=120),'profile':dict(type='string',enum=['hours','fdq','choice']),
          'input':dict(type='object',description='Exact profile input from /static/api.html; acknowledgments must be explicit.')},
         ('profile','input'),scope='cases:write',read=False),
    tool('run_case','Queue an own case revision. Returns job status/id: use get_job to obtain its result. A completed job need not be a conclusive decision.',
         {'case_id':ID_SCHEMA,'revision':dict(type='integer',minimum=1),'retry':dict(type='boolean')},('case_id',),scope='jobs:run',read=False),
    tool('get_job','Read an own job and original result. Preserve RC01 transport, execution, evidence, decisions, PV_UNKNOWN, quality, obligations and closure.',
         {'job_id':ID_SCHEMA},('job_id',),scope='cases:read'),
    tool('cancel_job','Cancel an own queued/running job.',{'job_id':ID_SCHEMA},('job_id',),scope='jobs:run',read=False,destructive=True),
    tool('delete_case','Permanently delete an own case and its jobs. Requires confirm=true.',
         {'case_id':ID_SCHEMA,'confirm':dict(type='boolean',const=True)},('case_id','confirm'),scope='cases:delete',read=False,destructive=True),
    tool('delete_agent_space','Permanently delete this credential’s entire agent space and revoke access. Requires confirm=true.',
         {'confirm':dict(type='boolean',const=True)},('confirm',),scope='account:delete',read=False,destructive=True),
]
TOOLS += twin_mcp.definitions(tool)
TOOLS += club_mcp.definitions(tool)
TOOLS += mission_mcp.definitions(tool)
BY_NAME = {t['name']:t for t in TOOLS}


def valid_arguments(value, schema):
    if not isinstance(value,dict) or set(value)-set(schema['properties']) or set(schema['required'])-set(value):
        return False
    types = {'string':str,'integer':int,'boolean':bool,'object':dict,'array':list}
    for key, item in value.items():
        spec = schema['properties'][key]
        if type(item) is not types[spec['type']]: return False
        if 'enum' in spec and item not in spec['enum']: return False
        if 'const' in spec and item != spec['const']: return False
        if 'pattern' in spec and not re.fullmatch(spec['pattern'],item): return False
        if 'minLength' in spec and len(item)<spec['minLength']: return False
        if 'maxLength' in spec and len(item)>spec['maxLength']: return False
        if 'minimum' in spec and item<spec['minimum']: return False
    return True


def install(app, body, error, fail_quota, digest):
    def rest(method, path, payload=None, authorization=''):
        # Fixed local routes only. Never forward cookies, host, forwarded IP or URLs.
        remote = request.remote_addr
        headers = {'Authorization':authorization} if authorization else {}
        builder = EnvironBuilder(path=path,method=method,base_url=app.config['PUBLIC_URL'],
            json=payload,headers=headers,environ_base={'REMOTE_ADDR':remote})
        try:
            # Separate g/database lifetimes; nested request cannot replace outer auth.
            with app.app_context(), app.request_context(builder.get_environ()):
                response = app.full_dispatch_request()
                try:
                    value = response.get_json(silent=True) if response.status_code != 204 else {'deleted':True}
                    if response.status_code >= 400:
                        e = (value or {}).get('error',{})
                        raise error(e.get('code','operation_failed'),e.get('message','Operation failed.'),response.status_code)
                    return value
                finally:
                    response.close()
        finally:
            builder.close()

    def demo(example):
        issued = rest('POST','/api/agents/demo',{'example':example})
        authorization = 'Bearer '+issued['credential']['token']
        job_id = issued['job']['id']
        del issued
        outcome = None
        cleanup = False
        try:
            deadline = time.monotonic()+app.config['MCP_DEMO_WAIT_SECONDS']
            while True:
                job = rest('GET','/api/jobs/'+job_id,authorization=authorization)['job']
                if job['status'] not in ('queued','running'): break
                if time.monotonic() >= deadline:
                    raise error('demo_wait_expired','Demo did not finish in the bounded wait; it is being cancelled and deleted. Read the saved demo instead.',503)
                time.sleep(.5)
            if job['status'] != 'completed':
                raise error('demo_failed','The synthetic execution did not complete; do not infer a decision.',503)
            outcome = dict(example=example,live_execution=True,evidence_origin='synthetic',
                status=job['status'],result=job['result'],result_json=job['result_json'],
                artifact_sha256=job['artifacts']['sha256'] if job['artifacts'] else None)
        finally:
            try:
                rest('DELETE','/api/agents/me',authorization=authorization)
                cleanup = True
            finally:
                authorization = None
            # Durable deletion failure propagates instead of claiming successful cleanup.
        outcome['temporary_space_deleted'] = cleanup
        return outcome

    def execute(name, args, authorization):
        if name in mission_mcp.ROUTES:
            return mission_mcp.execute(name,args,authorization,rest)
        if name in club_mcp.ROUTES:
            return club_mcp.execute(name, args, authorization, rest)
        if name == 'get_contribution_inbox': return rest('GET','/contributions')
        if name == 'submit_contribution': return rest('POST','/contributions',args['submission'])
        if name == 'get_contribution': return rest('GET','/contributions/'+args['id'])
        if name == 'find_opportunities':
            try: return taxis.orient(**args)
            except ValueError as exc: raise error('invalid_orientation',str(exc),400)
        if name in twin_mcp.ROUTES:
            if not app.config['TWIN_ENABLED']:
                raise error('twin_unavailable', 'Twin access is disabled.', 503)
            return twin_mcp.execute(name, args, authorization, rest)
        if name == 'prepare_decision': return rest('POST','/api/choice/review',args,authorization)
        if name == 'revise_case': return rest('PATCH','/api/cases/'+args['case_id'],{'input':args['input']},authorization)
        if name == 'get_capabilities': return rest('GET','/agents/manifest.json')
        if name == 'read_demo_result':
            saved = json.loads((Path(app.static_folder)/'demo-result.json').read_text())
            selected = next(r for r in saved['records'] if r['example']==args.get('example','hours-unknown'))
            return dict(saved_receipt=True,live_execution=False,generated_at_utc=saved['generated_at_utc'],record=selected)
        if name == 'run_demo': return demo(args.get('example','hours-unknown'))
        if name == 'list_cases': return rest('GET','/api/cases',authorization=authorization)
        if name == 'create_case': return rest('POST','/api/cases',args,authorization)
        if name == 'get_case': return rest('GET','/api/cases/'+args['case_id'],authorization=authorization)
        if name == 'run_case':
            return rest('POST','/api/cases/'+args['case_id']+'/run',{k:v for k,v in args.items() if k!='case_id'},authorization)
        if name == 'get_job': return rest('GET','/api/jobs/'+args['job_id'],authorization=authorization)
        if name == 'cancel_job': return rest('POST','/api/jobs/'+args['job_id']+'/cancel',{},authorization)
        if name == 'delete_case': return rest('DELETE','/api/cases/'+args['case_id'],authorization=authorization)
        if name == 'delete_agent_space': return rest('DELETE','/api/agents/me',authorization=authorization)
        raise error('unknown_tool','Unknown tool.')

    def rpc_error(ident, code, message, status=400, data=None):
        value = dict(code=code,message=message)
        if data is not None: value['data']=data
        return jsonify(jsonrpc='2.0',id=ident,error=value),status

    @app.route('/mcp',methods=['GET','POST','DELETE'])
    def mcp():
        origin = request.headers.get('Origin')
        if (origin and origin != app.config['PUBLIC_URL']) or request.headers.get('Sec-Fetch-Site') == 'cross-site':
            return rpc_error(None,-32000,'Origin denied',403)
        if request.method != 'POST':
            return '',405,{'Allow':'POST'}
        if request.args:
            return rpc_error(None,-32600,'Query parameters are not supported')
        if not app.config['MCP_ENABLED']:
            return rpc_error(None,-32000,'MCP temporarily disabled',503)
        if not request.is_json:
            return rpc_error(None,-32600,'application/json required',415)
        accepts = request.accept_mimetypes
        if accepts['application/json'] == 0 or accepts['text/event-stream'] == 0:
            return rpc_error(None,-32600,'Accept application/json and text/event-stream',406)
        # Day reservation first bounds IP-counter cardinality under floods.
        fail_quota('mcp-global-day',app.config['MAX_MCP_REQUESTS_DAILY'])
        fail_quota('mcp-global-minute',app.config['MAX_MCP_REQUESTS_MINUTE'],60)
        fail_quota('mcp-ip:'+digest(request.remote_addr or ''),60,60)
        try:
            message = body()
        except error:
            return rpc_error(None,-32700,'Invalid JSON-RPC object')
        ident = message.get('id')
        method = message.get('method')
        params = message.get('params',{})
        if (message.get('jsonrpc') != '2.0' or not isinstance(method,str) or
                not isinstance(params,dict) or set(message)-{'jsonrpc','id','method','params'} or
                ('id' in message and (type(ident) not in (str,int) or (isinstance(ident,str) and len(ident)>128)))):
            return rpc_error(None,-32600,'Invalid request')
        version = request.headers.get('MCP-Protocol-Version','2025-03-26')
        if version not in VERSIONS:
            return rpc_error(ident,-32022,'Unsupported protocol version',400,{'supported':list(VERSIONS),'requested':version})
        modern = version == '2026-07-28'
        if modern:
            meta = params.get('_meta',{})
            name_header = request.headers.get('Mcp-Name','')
            try:
                if name_header.startswith('=?base64?') and name_header.endswith('?='):
                    name_header = base64.b64decode(name_header[9:-2],validate=True).decode('utf-8')
            except (ValueError,UnicodeDecodeError):
                return rpc_error(ident,-32020,'Header mismatch')
            if (not isinstance(meta,dict) or meta.get('io.modelcontextprotocol/protocolVersion') != version or
                    request.headers.get('Mcp-Method') != method or
                    (method=='tools/call' and name_header != params.get('name'))):
                return rpc_error(ident,-32020,'Header mismatch')
            if not isinstance(meta.get('io.modelcontextprotocol/clientCapabilities'),dict):
                return rpc_error(ident,-32602,'Client capabilities required')
        if 'id' not in message:
            if not modern and method in ('notifications/initialized','notifications/cancelled'):
                return '',202
            return rpc_error(None,-32600,'Unsupported notification')
        authorization = request.headers.get('Authorization','')
        scopes = []
        if authorization:
            if not re.fullmatch(r'Bearer ga_[A-Za-z0-9_-]{43}',authorization):
                return rpc_error(ident,-32000,'A machine credential is required; human cookies/keys are not accepted',401)
            try:
                scopes = rest('GET','/api/agents/me',authorization=authorization)['credential']['scopes']
            except error as exc:
                return rpc_error(ident,-32000,exc.message,exc.status)
        def success(value):
            if modern: value = dict(value,resultType='complete')
            return jsonify(jsonrpc='2.0',id=ident,result=value)
        if method == 'initialize' and not modern:
            wanted = params.get('protocolVersion')
            if not isinstance(wanted,str) or not isinstance(params.get('capabilities'),dict) or not isinstance(params.get('clientInfo'),dict):
                return rpc_error(ident,-32602,'Invalid initialization')
            negotiated = wanted if wanted in VERSIONS[1:] else '2025-11-25'
            return success(dict(protocolVersion=negotiated,capabilities={'tools':{'listChanged':False}},serverInfo=INFO,
                instructions='Formal bounded profiles only. Public discovery is read-only; demo tools use synthetic examples. Private tools require a scoped machine credential in the HTTP Authorization header. Preserve PV_UNKNOWN and all evidence limits.'))
        if method == 'server/discover' and modern:
            return success(dict(supportedVersions=list(VERSIONS),capabilities={'tools':{'listChanged':False}},
                _meta={'io.modelcontextprotocol/serverInfo':INFO},ttlMs=0,cacheScope='private'))
        if method == 'ping': return success({})
        if method == 'tools/list':
            if params.get('cursor') is not None: return rpc_error(ident,-32602,'No pagination cursor supported')
            listing = {'tools':[t for t in TOOLS if t['_meta']['app.geniusdecision/required-scope'] in [None,*scopes]
                and (app.config['TWIN_ENABLED'] or t['name'] not in twin_mcp.ROUTES)
                and (app.config['ADAPTIVE_ENABLED'] or t['name'] not in ('mission_create','mission_run','mission_freeze','mission_observe'))]}
            if modern: listing.update(ttlMs=0,cacheScope='private')
            return success(listing)
        if method != 'tools/call':
            return rpc_error(ident,-32601,'Method not found',404 if modern else 200)
        name, args = params.get('name'),params.get('arguments',{})
        if not isinstance(name,str) or name not in BY_NAME:
            return rpc_error(ident,-32602,'Unknown tool',200)
        selected = BY_NAME[name]
        if not valid_arguments(args,selected['inputSchema']):
            return rpc_error(ident,-32602,'Invalid tool arguments',200)
        try:
            scope = selected['_meta']['app.geniusdecision/required-scope']
            if scope and not authorization:
                raise error('agent_credential_required','Configure a scoped agent credential in the connector Authorization header; never in tool arguments.',401)
            if scope and scope not in scopes:
                raise error('insufficient_scope','The credential does not permit this operation.',403)
            value = execute(name,args,authorization)
            return success(dict(content=[dict(type='text',text=json.dumps(value,ensure_ascii=False,allow_nan=False))],structuredContent=value,isError=False))
        except error as exc:
            value = dict(error=dict(code=exc.code,message=exc.message,http_status=exc.status))
            return success(dict(content=[dict(type='text',text=json.dumps(value,ensure_ascii=False))],structuredContent=value,isError=True))
