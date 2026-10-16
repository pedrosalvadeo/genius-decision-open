"""An expiring operator capability for one bounded, read-only aggregate report."""
import hashlib
import hmac
import json
import re
import threading
import time

from flask import jsonify, request

from .observation import ObservationError, report

PATH = '/internal/operator/observation'
MAX_GRANT_SECONDS = 86400
MAX_WINDOW_SECONDS = 7 * 86400
MIN_INTERVAL_SECONDS = 60


def parse_grant(raw):
    """Malformed/missing configuration disables access without stopping the app."""
    if not isinstance(raw, str) or len(raw) > 512:
        return None
    try:
        def unique(items):
            value = {}
            for key, item in items:
                if key in value:
                    raise ValueError('duplicate')
                value[key] = item
            return value
        value = json.loads(raw, object_pairs_hook=unique)
        if not isinstance(value, dict) or set(value) != {'sha256', 'not_before', 'expires_at'}:
            return None
        if not isinstance(value['sha256'], str) or not re.fullmatch('[0-9a-f]{64}', value['sha256']):
            return None
        start, end = value['not_before'], value['expires_at']
        if type(start) is not int or type(end) is not int or start < 0 or not 0 < end-start <= MAX_GRANT_SECONDS:
            return None
        return value
    except (ValueError, RecursionError):
        return None


def install(app):
    grant = parse_grant(app.config['OPERATOR_OBSERVATION_GRANT'])
    lock = threading.Lock()
    next_read = 0.0
    reading = False

    def error(code, status):
        response = jsonify(error=dict(code=code))
        response.status_code = status
        if status == 401:
            response.headers['WWW-Authenticate'] = 'Bearer'
        if status == 429:
            response.headers['Retry-After'] = str(MIN_INTERVAL_SECONDS)
        return response

    @app.route(PATH, methods=['GET'], provide_automatic_options=False)
    def operator_observation():
        nonlocal next_read, reading
        now = int(time.time())
        if grant is None or not grant['not_before'] <= now < grant['expires_at']:
            return error('not_found', 404)
        # No ordinary user session, agent/API key, query parameter or body grants
        # operator authority. No database connection occurs before authorization.
        authorization = request.headers.get('Authorization', '')
        if not re.fullmatch(r'Bearer go_[A-Za-z0-9_-]{43}', authorization):
            return error('unauthorized', 401)
        actual = hashlib.sha256(authorization[7:].encode()).hexdigest()
        if not hmac.compare_digest(actual, grant['sha256']):
            return error('unauthorized', 401)
        if request.method != 'GET':
            return error('method_not_allowed', 405)
        if (request.headers.get('Origin') not in (None, app.config['PUBLIC_URL'])
                or request.headers.get('Sec-Fetch-Site') == 'cross-site'):
            return error('origin_denied', 403)
        args = request.args
        if set(args) != {'since', 'until'} or any(len(args.getlist(k)) != 1 for k in args):
            return error('invalid_window', 400)
        if request.content_length or request.headers.get('Transfer-Encoding'):
            return error('invalid_request', 400)
        if any(not re.fullmatch(r'[0-9]{1,12}', args[k]) for k in args):
            return error('invalid_window', 400)
        since, until = int(args['since']), int(args['until'])
        if not 0 < until-since <= MAX_WINDOW_SECONDS or until > now:
            return error('invalid_window', 400)
        # Per-process guard, also caps concurrent reads; intentionally no counter
        # writes to the application DB. Gunicorn replacement resets this guard.
        with lock:
            current = time.monotonic()
            if reading or current < next_read:
                return error('rate_limit', 429)
            next_read = current + MIN_INTERVAL_SECONDS
            reading = True
        try:
            value = report(app.config['DATABASE'], since=since, until=until,
                           source='production')
        except (ObservationError, OSError):
            return error('observation_unavailable', 503)
        finally:
            with lock:
                reading = False
        return jsonify(format='genius-operator-observation/1',
                       classification='PRIVATE_OPERATOR_REPORT',
                       runtime=dict(environment=app.config['ENV'],
                           deployment_id=app.config['DEPLOYMENT_ID'],
                           regulation_enabled=app.config['MISSION_REGULATION_ENABLED']),
                       observation=value)
