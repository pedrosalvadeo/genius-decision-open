"""Measure a public Genius health request from this observer's vantage point.

The duration includes this host's network/proxy, TLS and response-body read. It
is neither origin-server processing time nor an independent sensor attestation.
"""
from datetime import datetime, timezone
import hashlib
import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener, getproxies

ORIGIN = 'https://geniusdecision.app'
TARGET = ORIGIN + '/api/health'
BODY_LIMIT = 65536


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def contract():
    return dict(format='genius-http-latency-source/1', target=TARGET, method='GET',
                resource='client_observed_http_response_time', unit='millisecond',
                clock='time.monotonic_ns', rounding='CEILING_NANOSECONDS_TO_MILLISECONDS',
                completion='READ_COMPLETE_BODY_UP_TO_65536_BYTES', timeout_seconds=20,
                proxy_configured=bool(getproxies().get('https')),
                redirects='REJECT', retries_per_sample=0,
                accepted_response='HTTP_200_JSON_HEALTH_OK_BACKUP_OK_NOT_SUSPENDED',
                source_truth='OBSERVER_RECORDED_NOT_INDEPENDENTLY_ATTESTED')


def observation(measurement):
    if measurement['outcome'] != 'OBSERVED':
        return None
    return dict(id=measurement['id'], value=measurement['rounded_milliseconds'],
        observed_at=measurement['completed_at'],
        source='Genius HTTP observer v1; receipt SHA256 ' + digest(measurement))


def sample(sample_id, *, opener=None, wall=utc_now, monotonic=time.monotonic_ns):
    """Return every attempt, including failures. Never silently replace a sample."""
    opener = opener or build_opener(NoRedirect())
    started_at, start = wall(), monotonic()
    status, raw, failure, health = None, b'', None, None
    request = Request(TARGET, headers={'Accept':'application/json', 'Cache-Control':'no-cache',
                                     'User-Agent':'Genius-Resource-Observer/1'})
    try:
        with opener.open(request, timeout=20) as response:
            status = response.status
            raw = response.read(BODY_LIMIT + 1)
        if status != 200:
            failure = 'HTTP_STATUS'
        elif len(raw) > BODY_LIMIT:
            failure = 'BODY_LIMIT'
        else:
            try:
                health = json.loads(raw)
            except (ValueError, UnicodeError):
                failure = 'INVALID_JSON'
            if failure is None and health != dict(status='ok', backup='ok', suspended=False):
                failure = 'HEALTH_NOT_OK'
    except HTTPError as exc:
        status, failure = exc.code, 'HTTP_STATUS'
        exc.close()
    except (URLError, OSError, TimeoutError):
        failure = 'TRANSPORT_FAILURE'
    elapsed, completed_at = monotonic() - start, wall()
    if elapsed < 0 or datetime.fromisoformat(completed_at) <= datetime.fromisoformat(started_at):
        failure = 'CLOCK_NOT_ADVANCING'
    value = (elapsed + 999999) // 1000000
    if not 0 <= value <= 1000000:
        failure = 'VALUE_RANGE'
    measurement = dict(format='genius-http-sample/1', id=sample_id,
        source_contract_sha256=digest(contract()), target=TARGET, started_at=started_at,
        completed_at=completed_at, elapsed_ns=elapsed, rounded_milliseconds=value,
        http_status=status, response_bytes=len(raw), response_sha256=hashlib.sha256(raw).hexdigest(),
        health=health, outcome='REJECTED' if failure else 'OBSERVED', failure=failure)
    checksum = digest(measurement)
    return dict(measurement=measurement, sha256=checksum, observation=observation(measurement))
