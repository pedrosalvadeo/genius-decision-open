"""Small input-only validators; graph dependencies stay in the isolated worker."""
import json
import re
from .mission_state import digest
from genius_adaptive.calibration import KIND, validate_input, timestamp


def distribution(data):
    if set(data) != {'idempotency_key','files','processing_permission','technical_scope_acknowledged'}:
        raise ValueError('DISTRIBUTION_FIELDS')
    files = data['files']
    if not isinstance(files, dict) or not 1 <= len(files) <= 16:
        raise ValueError('SOURCE_FILE_COUNT')
    total = 0
    for name, content in files.items():
        if (not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_-][A-Za-z0-9_./-]{0,119}', name)
                or any(not p or p.startswith('.') for p in name.split('/')) or not isinstance(content, str)):
            raise ValueError('SOURCE_PATH_OR_TEXT')
        total += len(content.encode('utf-8'))
    if any(a != b and b.startswith(a + '/') for a in files for b in files):
        raise ValueError('SOURCE_OVERLAP')
    if total > 65536:
        raise OverflowError('SOURCE_BUDGET_EXCEEDED')
    return data


def resolve(data, own, forecast_lookup=None):
    if data.get('kind', 'source_distribution_v1') == 'source_distribution_v1':
        distribution({key: value for key, value in data.items() if key != 'kind'})
        return data
    if 'forecast_mission_id' in data:
        return from_forecast(data, own, forecast_lookup)
    fields = {'kind','calibration','idempotency_key','processing_permission','technical_scope_acknowledged'}
    if data['kind'] != KIND or set(data) not in (fields, fields | {'parent_mission_id'}):
        raise ValueError('MISSION_KIND_OR_FIELDS')
    data = json.loads(json.dumps(data))
    calibration = data['calibration']
    if not isinstance(calibration, dict):
        raise ValueError('CALIBRATION_FIELDS')
    lineage = None
    if 'parent_mission_id' in data:
        mid = data['parent_mission_id']
        if not isinstance(mid, str) or not re.fullmatch('[a-f0-9]{32}', mid):
            raise ValueError('PARENT_MISSION_ID')
        parent = own(mid)
        raw = parent['artifact']
        if parent['status'] != 'completed' or raw is None or digest(raw) != parent['artifact_sha256']:
            raise ValueError('COMPLETED_PARENT_REQUIRED')
        if parent['artifact_name'] != 'resource-estimate.json':
            raise ValueError('CALIBRATION_PARENT_REQUIRED')
        memory = json.loads(raw)
        if memory.get('format') != KIND or any(calibration.get(k) != memory[k] for k in ('context','resource','unit','data_kind')):
            raise ValueError('PARENT_CONTEXT_CHANGED')
        if 'baseline' in calibration:
            raise ValueError('PARENT_SUPPLIES_BASELINE')
        calibration['baseline'] = memory['estimate']
        validate_input(calibration)
        if timestamp(calibration['training'][0]['observed_at']) <= timestamp(memory['last_observed_at']):
            raise ValueError('NEW_RECORDS_REQUIRED')
        lineage = dict(mission_id=mid, artifact_sha256=parent['artifact_sha256'], estimate=memory['estimate'])
    validate_input(calibration)
    data['lineage'] = lineage
    return data


def from_forecast(data, own, forecast_lookup):
    fields = {'kind','calibration','idempotency_key','processing_permission','technical_scope_acknowledged','forecast_mission_id'}
    if (set(data) != fields or data['kind'] != KIND or not isinstance(data['calibration'], dict)
            or set(data['calibration']) != {'validation'}):
        raise ValueError('FORECAST_LEARNING_FIELDS')
    mid = data['forecast_mission_id']
    if not isinstance(mid, str) or not re.fullmatch('[a-f0-9]{32}', mid):
        raise ValueError('FORECAST_MISSION_ID')
    own(mid)
    forecast = forecast_lookup(mid)
    frozen = forecast['frozen']
    calibration = {key:frozen[key] for key in ('context','resource','unit','data_kind','max_underprediction')}
    calibration.update(baseline=frozen['estimate'],
        training=[entry['receipt']['observation'] for entry in forecast['observations']],
        validation=data['calibration']['validation'])
    validate_input(calibration)  # New held-out dates and IDs must follow the scored training records.
    return {**data, 'calibration':calibration,
        'lineage':dict(mission_id=mid, artifact_sha256=frozen['artifact_sha256'], estimate=frozen['estimate'],
                      forecast_sha256=forecast['sha256'], report_sha256=forecast['report_sha256'])}
