"""Signed trial or persistent, revocable permission for fixed Genius readers."""
from .core import fields, identifier, instant
from .network_protocol import identity, verify

FORMAT='genius-host-offer/1'
PERSISTENT='genius-host-offer/2'
CHILD='genius-host-child/1'
WORKER='genius-signed-world-reader/1'
LIMITS=dict(memory_mb=384,cpu_seconds=20,wall_seconds=120,file_bytes=8388608,interval_seconds=600)


def focus_list(value):
    if type(value) is not list or not 1<=len(value)<=8:raise ValueError('INVALID_FOCUS')
    for item in value:identifier(item)
    if value!=sorted(set(value)):raise ValueError('SORTED_UNIQUE_FOCUS_REQUIRED')
    return value


def validate_offer(signed):
    fields(signed,'offer signature')
    p=signed['offer']
    fields(p,'format node_id public_key hub worker worlds max_births lease_seconds valid_until limits automatic_acceptance')
    if p['format'] not in (FORMAT,PERSISTENT) or p['worker']!=WORKER or p['node_id']!=identity(p['public_key']):
        raise ValueError('INVALID_HOST_IDENTITY_OR_WORKER')
    from .internet import origin
    if origin(p['hub'])!=p['hub'] or p['automatic_acceptance'] is not True:raise ValueError('HOST_AUTHORIZATION_REQUIRED')
    if type(p['max_births']) is not int or not 1<=p['max_births']<=4:raise ValueError('INVALID_BIRTH_BUDGET')
    if p['format']==PERSISTENT:
        if p['lease_seconds'] is not None or p['valid_until'] is not None:raise ValueError('INVALID_PERSISTENT_AUTHORIZATION')
    else:
        if type(p['lease_seconds']) is not int or not 600<=p['lease_seconds']<=86400:raise ValueError('INVALID_LEASE')
        instant(p['valid_until'])
    if p['limits']!=LIMITS:raise ValueError('UNSUPPORTED_EXECUTION_LIMITS')
    if type(p['worlds']) is not list or not 1<=len(p['worlds'])<=4:raise ValueError('INVALID_WORLDS')
    names=[]
    for scope in p['worlds']:
        fields(scope,'world_id focus');identifier(scope['world_id']);focus_list(scope['focus']);names.append(scope['world_id'])
    if len(set(names))!=len(names):raise ValueError('DUPLICATE_WORLD')
    verify(p,p['public_key'],signed['signature'])
    return p


def expiry(p):
    return None if p['format']==PERSISTENT else int(instant(p['valid_until']).timestamp())


def expired(value,stamp):
    return value is not None and value<=stamp


def persistent_transition(old,new):
    """Only duration changes; identity, scope, limits and lifetime births stay fixed."""
    return (old['format']==FORMAT and new['format']==PERSISTENT and
            all(old[k]==new[k] for k in old if k not in ('format','lease_seconds','valid_until')))


def admitted(p,world,focus):
    identifier(world);focus_list(focus)
    return any(s['world_id']==world and s['focus']==focus for s in p['worlds'])
