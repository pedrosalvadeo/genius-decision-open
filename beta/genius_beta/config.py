import os
from pathlib import Path
from urllib.parse import urlsplit


def settings(overrides=None):
    data = Path(os.environ.get('GENIUS_DATA_DIR', './var/genius-beta')).resolve()
    c = dict(DATA_DIR=data, DATABASE=data / 'genius.sqlite3', PUBLIC_URL=os.environ.get('GENIUS_PUBLIC_URL', 'http://127.0.0.1:8080').rstrip('/'), ENV=os.environ.get('GENIUS_ENV', 'development'), MAX_CONTENT_LENGTH=131072, MAX_CASES=20, MAX_REVISIONS=20, MAX_JOBS_DAILY=20, MAX_GLOBAL_JOBS_DAILY=200, MAX_COMPARE_DAILY=20, MAX_GLOBAL_COMPARE_DAILY=200, MAX_COMPARE_RECALCULATIONS_DAILY=200, MAX_GLOBAL_USERS=100, MAX_QUEUE=40, MAX_TOKENS=10, RETENTION_DAYS=90, ENGINE_TIMEOUT=30, ENGINE_MEMORY_MB=1024, ENGINE_OUTPUT_BYTES=2097152, MAX_DATABASE_BYTES=134217728, MIN_FREE_BYTES=67108864, SESSION_TTL=86400, PRIVACY_VERSION='beta-2026-10-05-v2', PRIVACY_CONTROLLER=os.environ.get('GENIUS_PRIVACY_CONTROLLER', ''), PRIVACY_CONTACT=os.environ.get('GENIUS_PRIVACY_CONTACT', ''), SUSPEND_FILE=data / 'SUSPENDED', TESTING=False)
    c.update(overrides or {})
    c.setdefault('OPERATOR_OBSERVATION_GRANT', os.environ.get('GENIUS_OPERATOR_OBSERVATION_GRANT', ''))
    c.setdefault('DEPLOYMENT_ID', os.environ.get('RAILWAY_DEPLOYMENT_ID'))
    c.setdefault('MISSION_REGULATION_ENABLED', os.environ.get('GENIUS_MISSION_REGULATION_ENABLED', 'false') == 'true')
    if os.environ.get('GENIUS_MISSION_REGULATION_ENABLED', 'false') not in ('true','false') or type(c['MISSION_REGULATION_ENABLED']) is not bool:
        raise ValueError('GENIUS_MISSION_REGULATION_ENABLED must be true or false')
    c.setdefault('ADAPTIVE_ENABLED', os.environ.get('GENIUS_ADAPTIVE_ENABLED', 'false') == 'true')
    if os.environ.get('GENIUS_ADAPTIVE_ENABLED', 'false') not in ('true', 'false') or type(c['ADAPTIVE_ENABLED']) is not bool:
        raise ValueError('GENIUS_ADAPTIVE_ENABLED must be true or false')
    if c['ADAPTIVE_ENABLED']:
        c['MAX_CONTENT_LENGTH'] = max(c['MAX_CONTENT_LENGTH'],524288)
    c.setdefault('TWIN_ENABLED', os.environ.get('GENIUS_TWIN_ENABLED', '0') == '1')
    c.setdefault('TWIN_TIMEOUT', 90)
    c.setdefault('TWIN_MEMORY_MB', 384)
    c.setdefault('TWIN_OUTPUT_BYTES', 16777216)
    c.setdefault('TWIN_STORAGE_BYTES', 134217728)
    if c['TWIN_ENABLED']:
        c['MAX_CONTENT_LENGTH'] = max(c['MAX_CONTENT_LENGTH'], 262144)
    c.setdefault('CLUB_ENABLED', os.environ.get('GENIUS_CLUB_ENABLED', 'true') == 'true')
    if os.environ.get('GENIUS_CLUB_ENABLED', 'true') not in ('true', 'false') or type(c['CLUB_ENABLED']) is not bool:
        raise ValueError('GENIUS_CLUB_ENABLED must be true or false')
    for key, value in dict(CLUB_MAX_FILES=20, CLUB_MAX_VERSIONS=20, CLUB_FILE_BYTES=65536,
                           CLUB_MEMBER_BYTES=1048576, CLUB_GLOBAL_BYTES=16777216, CLUB_WRITES_DAILY=100).items():
        c.setdefault(key, value)
        if type(c[key]) is not int or c[key] < 1:
            raise ValueError(key + ' must be a positive integer')
    agent_defaults = dict(MAX_AGENT_ACCOUNTS=20, MAX_AGENT_REGISTRATIONS_DAILY=5,
        MAX_AGENT_DEMOS_DAILY=20, MAX_AGENT_CASES=5, MAX_AGENT_REVISIONS=5,
        MAX_AGENT_JOBS_DAILY=5, MAX_AGENT_GLOBAL_JOBS_DAILY=20, MAX_AGENT_QUEUE=4,
        AGENT_TOKEN_TTL=7*86400, AGENT_DEMO_TTL=3600)
    for key, value in agent_defaults.items():
        c.setdefault(key,value)
        if type(c[key]) is not int or c[key] < 1:
            raise ValueError(key+' must be a positive integer')
    if 'AGENT_ACCESS_ENABLED' not in c:
        enabled = os.environ.get('GENIUS_AGENT_ACCESS_ENABLED','true')
        if enabled not in ('true','false'):
            raise ValueError('GENIUS_AGENT_ACCESS_ENABLED must be true or false')
        c['AGENT_ACCESS_ENABLED'] = enabled == 'true'
    if type(c['AGENT_ACCESS_ENABLED']) is not bool:
        raise ValueError('AGENT_ACCESS_ENABLED must be a boolean')
    if 'MCP_ENABLED' not in c:
        enabled = os.environ.get('GENIUS_MCP_ENABLED','true')
        if enabled not in ('true','false'):
            raise ValueError('GENIUS_MCP_ENABLED must be true or false')
        c['MCP_ENABLED'] = enabled == 'true'
    if type(c['MCP_ENABLED']) is not bool:
        raise ValueError('MCP_ENABLED must be a boolean')
    for key,value in dict(MAX_MCP_REQUESTS_DAILY=2000,MAX_MCP_REQUESTS_MINUTE=300,MCP_DEMO_WAIT_SECONDS=10).items():
        c.setdefault(key,value)
        if type(c[key]) is not int or c[key]<1:
            raise ValueError(key+' must be a positive integer')
    if 'REGISTRATION_OPEN' not in c:
        opening = os.environ.get('GENIUS_REGISTRATION_OPEN', 'false' if c['ENV'] == 'production' else 'true')
        if opening not in ('true', 'false'):
            raise ValueError('GENIUS_REGISTRATION_OPEN must be true or false')
        c['REGISTRATION_OPEN'] = opening == 'true'
    if type(c['REGISTRATION_OPEN']) is not bool:
        raise ValueError('REGISTRATION_OPEN must be a boolean')
    c['DATA_DIR'] = Path(c['DATA_DIR'])
    c['DATABASE'] = Path(c['DATABASE'])
    c['SUSPEND_FILE'] = Path(c['SUSPEND_FILE'])
    url = urlsplit(c['PUBLIC_URL'])
    if url.scheme not in ('http', 'https') or not url.netloc or url.path not in ('', '/') or url.query or url.fragment or url.username:
        raise ValueError('GENIUS_PUBLIC_URL must be an absolute origin without path')
    c['COOKIE_SECURE'] = url.scheme == 'https'
    if c['ENV'] == 'production':
        if not c['COOKIE_SECURE'] or not all(c[k] for k in ('PRIVACY_CONTROLLER','PRIVACY_CONTACT')):
            raise ValueError('Production requires HTTPS origin and privacy controller and contact')
    return c
