"""Fixed routes; credentials are headers, never model arguments."""
from .twin_mcp import ID
PAYLOAD = dict(type='object', description='Exact mission payload documented at /static/missions.html. Registered file distribution or resource calibration inputs and authorized confirmations only.')
ROUTES = {
 'mission_capabilities': ('GET','/capabilities','missions:read',{},(), 'Read registered missions, learning rule, input bounds and evidence limits.'),
 'mission_list': ('GET','','missions:read',{},(), 'List own persistent missions.'),
 'mission_create': ('POST','','missions:write',{'payload':PAYLOAD},('payload',), 'Create a private registered mission. First read mission_capabilities and /static/missions.html. File distribution payload: idempotency_key (16–64 letters/digits/_/-), files (name:text map, up to 16 and 65536 bytes total), processing_permission=true, technical_scope_acknowledged=true. Resource calibration payload: kind=resource_calibration_v1, calibration={context,resource,unit,baseline,max_underprediction,data_kind,training,validation}, idempotency_key and the same confirmations. Observations have id,value,observed_at (timezone required),source; integer values 0..1000000, at least 3 training then 2 later validation records, at most 32 total. With parent_mission_id omit baseline; the completed own parent supplies it and context/resource/unit/data_kind must match, all records must be newer. A private estimate artifact may adopt a training-only median when holdout error strictly improves and maximum underprediction does not worsen or exceed the declared limit. Retrospective evidence only. Only provide confirmations within granted authority. Does not start execution.'),
 'mission_get': ('GET','/{id}','missions:read',{'id':ID},('id',), 'Read own mission status, durable stage and result.'),
 'mission_export': ('GET','/{id}/export','missions:read',{'id':ID},('id',), 'Export own mission input and empirical memory.'),
 'mission_artifact': ('GET','/{id}/artifact','missions:read',{'id':ID},('id',), 'Read verified private archive or resource estimate JSON as base64 with SHA-256.'),
 'mission_run': ('POST','/{id}/run','missions:run',{'id':ID},('id',), 'Queue or explicitly resume an own mission within shared execution quotas. A completed mission is reused. Effects are limited to its private downloadable artifact; no external actions.'),
 'mission_cancel': ('POST','/{id}/cancel','missions:run',{'id':ID},('id',), 'Cancel own pending execution; durable history remains until deletion.'),
 'mission_delete': ('DELETE','/{id}','missions:delete',{'id':ID,'confirm':dict(type='boolean',const=True)},('id','confirm'), 'Erase own mission, checkpoints, inputs and artifact, recording a backup privacy tombstone.'),
}
def definitions(tool):
    return [tool(name,description,props,required,scope=scope,read=method=='GET',destructive=method=='DELETE')
            for name,(method,path,scope,props,required,description) in ROUTES.items()]
def execute(name,args,authorization,rest):
    method,path,*_ = ROUTES[name]
    payload = args.get('payload', {'confirm':True} if name=='mission_delete' else {})
    return rest(method,'/api/missions'+path.format(**args),payload if method!='GET' else None,authorization)
