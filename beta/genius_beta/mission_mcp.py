"""Fixed routes; credentials are headers, never model arguments."""
from .twin_mcp import ID
PAYLOAD = dict(type='object', description='Exact mission payload documented at /static/missions.html. Explicit UTF-8 files and authorized confirmations only.')
ROUTES = {
 'mission_capabilities': ('GET','/capabilities','missions:read',{},(), 'Read supported mission, input bounds and evidence limits.'),
 'mission_list': ('GET','','missions:read',{},(), 'List own persistent missions.'),
 'mission_create': ('POST','','missions:write',{'payload':PAYLOAD},('payload',), 'Create a private UTF-8 file distribution mission. Payload: idempotency_key (16–64 letters/digits/_/-), files (name:text map, up to 16 and 65536 bytes total), processing_permission=true, technical_scope_acknowledged=true. Only provide confirmations within granted authority. Does not start execution.'),
 'mission_get': ('GET','/{id}','missions:read',{'id':ID},('id',), 'Read own mission status, durable stage and result.'),
 'mission_export': ('GET','/{id}/export','missions:read',{'id':ID},('id',), 'Export own mission input and empirical memory.'),
 'mission_artifact': ('GET','/{id}/artifact','missions:read',{'id':ID},('id',), 'Read verified private archive as base64 with SHA-256.'),
 'mission_run': ('POST','/{id}/run','missions:run',{'id':ID},('id',), 'Queue or explicitly resume an own mission within shared execution quotas. A completed mission is reused. Effects are limited to its private downloadable archive.'),
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
