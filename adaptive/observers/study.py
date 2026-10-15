"""Resumable real-source calibration -> freeze -> score -> learn operator client.

Run with PYTHONPATH=adaptive python -m observers.study --state PRIVATE --out RECEIPT.
Only the public health URL is sampled. A dedicated temporary API account is
created, used and erased. The private checkpoint must never be published.
"""
import argparse
import base64
from contextlib import contextmanager
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import Request, build_opener
from . import http_latency as source


def atomic(path, value):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('SYMLINK_NOT_SUPPORTED')
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.observer-')
    try:
        with os.fdopen(fd, 'w') as handle:
            handle.write(source.canonical(value) + '\n')
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def exclusive(path):
    fd = os.open(str(path) + '.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


class API:
    def __init__(self):
        self.token = None
        self.opener = build_opener(source.NoRedirect())

    def request(self, method, path, payload=None, accepted=(200, 201, 202, 204)):
        if not path.startswith(('/api/', '/agents/')) or '?' in path or '#' in path:
            raise ValueError('API_PATH')
        headers = {'Accept':'application/json'}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        raw = None if payload is None else source.canonical(payload).encode()
        if raw is not None:
            headers['Content-Type'] = 'application/json'
        try:
            response = self.opener.open(Request(source.ORIGIN + path, data=raw, headers=headers, method=method), timeout=25)
        except HTTPError as exc:
            response = exc
        with response:
            raw = response.read(4*1024*1024 + 1)
            if len(raw) > 4*1024*1024:
                raise RuntimeError('API_RESPONSE_LIMIT')
            if response.status not in accepted:
                raise RuntimeError('API_HTTP_' + str(response.status))
            return json.loads(raw) if raw else None


def code_identity():
    return {name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ('http_latency.py', 'study.py')}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_forecast(forecast, samples, memory, count):
    """Recompute fixed scoring and bind receipts to actual local sample bytes."""
    frozen = forecast['frozen']
    require(source.digest(frozen) == forecast['sha256'], 'FORECAST_HASH')
    for key in ('baseline','estimate','context','resource','unit','data_kind','max_underprediction'):
        require(frozen[key] == memory[key], 'FROZEN_CONTEXT')
    require(frozen['expected_count'] == count, 'FROZEN_COUNT')
    require(forecast['status'] == 'complete' and len(forecast['observations']) == count == len(samples), 'REPORT_COUNT')
    previous, last = forecast['sha256'], frozen['frozen_at_us']
    errors = {key:[] for key in ('baseline','estimate')}
    under = {key:[] for key in errors}
    for index, (entry, sample) in enumerate(zip(forecast['observations'], samples), 1):
        receipt = entry['receipt']
        require(source.digest(sample['measurement']) == sample['sha256'], 'SOURCE_HASH')
        require(receipt['observation'] == sample['observation'], 'SOURCE_RECORD_CHANGED')
        require(source.digest(receipt) == entry['sha256'] and receipt['previous_sha256'] == previous, 'RECEIPT_CHAIN')
        require(receipt['sequence'] == index and receipt['forecast_sha256'] == forecast['sha256'], 'RECEIPT_SEQUENCE')
        require(receipt['received_at_us'] > last, 'RECEIPT_TIME')
        require(datetime.fromisoformat(sample['measurement']['started_at']) > datetime.fromisoformat(frozen['frozen_at']), 'SAMPLE_NOT_AFTER_FREEZE')
        require(datetime.fromisoformat(sample['observation']['observed_at']) <= datetime.fromisoformat(receipt['received_at']), 'EVENT_AFTER_RECEIPT')
        previous, last = entry['sha256'], receipt['received_at_us']
        for key in errors:
            value = sample['observation']['value']
            errors[key].append(abs(value - frozen[key]))
            under[key].append(max(0, value - frozen[key]))
    report = forecast['report']
    require(source.digest(report) == forecast['report_sha256'], 'REPORT_HASH')
    comparison = {key:dict(absolute_error_sum=sum(errors[key]), count=count, max_underprediction=max(under[key])) for key in errors}
    checks = dict(lower_error=sum(errors['estimate']) < sum(errors['baseline']),
        no_worse_underprediction=max(under['estimate']) <= max(under['baseline']),
        within_declared_limit=max(under['estimate']) <= frozen['max_underprediction'])
    require(report['comparison'] == comparison and report['checks'] == checks, 'REPORT_ARITHMETIC')
    expected = 'LOWER_ERROR_WITHIN_GUARDS' if all(checks.values()) else 'NO_CONFIRMED_IMPROVEMENT'
    require(report['outcome'] == expected and report['model_changed'] is False, 'REPORT_OUTCOME')
    require(report['receipt_sha256s'] == [r['sha256'] for r in forecast['observations']], 'REPORT_RECEIPTS')


class Study:
    def __init__(self, path, *, count=5, tolerance=1000, api=None, sampler=source.sample):
        require(type(count) is int and 3 <= count <= 30, 'COUNT_RANGE')
        require(type(tolerance) is int and 0 <= tolerance <= 1000000, 'TOLERANCE_RANGE')
        self.path, self.api, self.sampler = Path(path), api or API(), sampler
        config = dict(source=source.contract(), count=count, tolerance=tolerance,
                      training_count=5, validation_count=3, child_validation_count=2,
                      baseline_rule='FIRST_SEPARATE_MEASUREMENT', code=code_identity())
        require(not self.path.is_symlink(), 'SYMLINK_NOT_SUPPORTED')
        if self.path.exists():
            require(self.path.stat().st_mode & 0o077 == 0, 'PRIVATE_FILE_PERMISSIONS')
            self.state = json.loads(self.path.read_text())
            require(self.state['config'] == config, 'OBSERVER_CONFIG_CHANGED')
        else:
            self.state = dict(format='genius-real-observation-study/1', run_id=secrets.token_hex(12),
                              config=config, created_at=source.utc_now(), samples={}, steps={})
            self.save()
        self.api.token = self.state.get('token')

    def save(self):
        atomic(self.path, self.state)

    def step(self, name, action):
        if name not in self.state['steps']:
            self.state['steps'][name] = action()
            self.save()
        return self.state['steps'][name]

    def collect(self, name):
        samples = self.state['samples']
        if name not in samples:
            samples[name] = dict(status='MEASUREMENT_INTENT', reserved_at=source.utc_now())
            self.save()  # A crash after this point must not replace an unknown observation.
            samples[name] = self.sampler(self.state['run_id'] + '-' + name)
            self.save()
        entry = samples[name]
        require(entry.get('status') != 'MEASUREMENT_INTENT', 'MEASUREMENT_OUTCOME_UNKNOWN')
        require(source.digest(entry['measurement']) == entry['sha256'], 'SOURCE_HASH')
        require(entry['measurement']['source_contract_sha256'] == source.digest(self.state['config']['source']), 'SOURCE_CHANGED')
        require(entry['measurement']['outcome'] == 'OBSERVED' and entry['observation'] is not None, 'SOURCE_SAMPLE_REJECTED')
        require(entry['observation'] == source.observation(entry['measurement']), 'SOURCE_MAPPING_CHANGED')
        require(entry['measurement']['rounded_milliseconds'] == (entry['measurement']['elapsed_ns'] + 999999) // 1000000, 'SOURCE_ROUNDING_CHANGED')
        return entry

    def records(self, prefix, count):
        return [self.collect(prefix + '-' + str(i))['observation'] for i in range(count)]

    def account(self):
        if self.api.token:
            return
        require(not self.state.get('registration_attempted'), 'REGISTRATION_OUTCOME_UNKNOWN')
        manifest = self.api.request('GET', '/agents/manifest.json')
        self.state['registration_attempted'] = True
        self.save()
        issued = self.api.request('POST', '/api/agents/register', dict(policy_version=manifest['policy_version'],
            data_policy_acknowledged=True, scopes=['missions:read','missions:write','missions:run','account:delete']))
        self.api.token = self.state['token'] = issued['credential']['token']
        self.save()

    def execute(self, name, payload):
        payload = {**payload, 'idempotency_key':self.state['run_id'] + '-' + name,
                   'processing_permission':True, 'technical_scope_acknowledged':True}
        self.step(name + '_input', lambda: payload)
        require(self.state['steps'][name + '_input'] == payload, 'MISSION_INPUT_CHANGED')
        created = self.step(name + '_created', lambda:self.api.request('POST', '/api/missions', payload))
        mid = created['mission']['id']
        def finish():
            self.api.request('POST', '/api/missions/' + mid + '/run', {})
            deadline = time.monotonic() + 90
            while True:
                mission = self.api.request('GET', '/api/missions/' + mid)['mission']
                if mission['status'] == 'completed':
                    break
                require(mission['status'] in ('queued','running') and time.monotonic() < deadline, 'MISSION_NOT_COMPLETE')
                time.sleep(1)
            artifact = self.api.request('GET', '/api/missions/' + mid + '/artifact')
            raw = base64.b64decode(artifact['content_base64'], validate=True)
            require(hashlib.sha256(raw).hexdigest() == artifact['sha256'] == mission['artifact_sha256'], 'ARTIFACT_HASH')
            return dict(id=mid, artifact_sha256=artifact['sha256'], memory=json.loads(raw))
        return self.step(name + '_completed', finish)

    def run(self):
        if self.state.get('protocol_status') == 'PASS':
            return self.public()
        require(not self.state.get('account_erased'), 'STUDY_ALREADY_CLEANED')
        self.account()
        caps = self.step('capabilities', lambda:self.api.request('GET', '/api/missions/capabilities'))
        require(caps.get('forecasts',{}).get('protocol') == 'resource_forecast_v1', 'PROTOCOL_UNAVAILABLE')
        baseline = self.collect('baseline')['observation']['value']
        calibration = dict(context='Sequential public Genius health GETs from one observer and its configured network/proxy; elapsed time includes connection and complete body read.',
            resource='client_observed_http_response_time', unit='millisecond', data_kind='submitted_observations',
            baseline=baseline, max_underprediction=self.state['config']['tolerance'],
            training=self.records('training', 5), validation=self.records('validation', 3))
        parent = self.execute('parent', dict(kind='resource_calibration_v1', calibration=calibration))
        path = '/api/missions/' + parent['id']
        frozen = self.step('freeze', lambda:self.api.request('POST', path + '/forecast',
            dict(artifact_sha256=parent['artifact_sha256'], expected_count=self.state['config']['count']))['forecast'])
        require(source.digest(frozen['frozen']) == frozen['sha256'], 'FORECAST_HASH')
        prospective = []
        for i in range(self.state['config']['count']):
            entry = self.collect('prospective-' + str(i))
            prospective.append(entry)
            require(datetime.fromisoformat(entry['measurement']['started_at']) > datetime.fromisoformat(frozen['frozen']['frozen_at']), 'SAMPLE_NOT_AFTER_FREEZE')
            self.step('submitted-' + str(i), lambda:self.api.request('POST', path + '/observations',
                dict(forecast_sha256=frozen['sha256'], observation=entry['observation'])))
        forecast = self.step('report', lambda:self.api.request('GET', path + '/forecast')['forecast'])
        require(forecast['frozen'] == frozen['frozen'], 'FROZEN_CHANGED')
        verify_forecast(forecast, prospective, parent['memory'], self.state['config']['count'])
        child = self.execute('child', dict(kind='resource_calibration_v1', forecast_mission_id=parent['id'],
            calibration=dict(validation=self.records('child-validation', 2))))
        require(child['memory']['baseline'] == frozen['frozen']['estimate'], 'CHILD_BASELINE')
        lineage = child['memory']['lineage']
        require(lineage['report_sha256'] == forecast['report_sha256'] and lineage['forecast_sha256'] == forecast['sha256'], 'CHILD_LINEAGE')
        require(self.api.request('GET', path + '/forecast')['forecast'] == forecast, 'OLD_REPORT_CHANGED')
        self.state.update(protocol_status='PASS', completed_at=source.utc_now(), old_report_unchanged=True)
        self.save()
        return self.public()

    def cleanup(self):
        if not self.state.get('account_erased'):
            require(bool(self.api.token), 'NO_CREDENTIAL_FOR_CLEANUP')
            self.api.request('DELETE', '/api/agents/me', {})
            self.state['account_erased'] = True
            self.save()
        if not self.state.get('credential_revoked'):
            self.api.request('GET', '/api/missions', accepted=(401,))
            self.state['credential_revoked'] = True
            self.state.pop('token', None)
            self.save()
        self.api.token = None

    def public(self):
        # Explicit allowlist: never serialize the registration response or token.
        result = {key:self.state[key] for key in ('format','run_id','config','created_at','samples','steps',
            'protocol_status','completed_at','old_report_unchanged','account_erased','credential_revoked','last_error') if key in self.state}
        result.update(scope='REAL_CLIENT_OBSERVED_HTTP_LATENCY', independent_attestation=False,
                      generalization='NOT_ESTABLISHED', wellbeing='UNMEASURED', life_sustainment='UNMEASURED')
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--count', type=int, default=5)
    parser.add_argument('--tolerance-ms', type=int, default=1000)
    parser.add_argument('--cleanup-only', action='store_true')
    args = parser.parse_args()
    require(args.state.resolve() != args.out.resolve(), 'PUBLIC_AND_PRIVATE_PATHS_MUST_DIFFER')
    require(args.state.parent.is_dir() and args.out.parent.is_dir(), 'OUTPUT_DIRECTORIES_REQUIRED')
    require(not args.cleanup_only or args.state.is_file(), 'CLEANUP_REQUIRES_EXISTING_STATE')
    with exclusive(args.state):
        study = Study(args.state, count=args.count, tolerance=args.tolerance_ms)
        try:
            if not args.cleanup_only:
                study.run()
            study.cleanup()
        except Exception as exc:
            # Exception strings may contain URLs supplied by transport libraries.
            code = str(exc) if re.fullmatch('[A-Z_0-9]+', str(exc)) else 'DETAILS_WITHHELD'
            study.state['last_error'] = dict(type=type(exc).__name__, code=code, at=source.utc_now())
            study.save()
            atomic(args.out, study.public())
            print(source.canonical(dict(status='INCOMPLETE', error_type=type(exc).__name__, code=code,
                resume='Use the same state and options; rejected or unknown measurements require review, not resampling.')))
            return 2
        atomic(args.out, study.public())
        print(source.canonical(dict(status=study.state.get('protocol_status','CLEANED'),
            outcome=study.state['steps'].get('report',{}).get('report',{}).get('outcome'),
            samples=len(study.state['samples']), account_erased=study.state.get('account_erased'),
            credential_revoked=study.state.get('credential_revoked'))))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
