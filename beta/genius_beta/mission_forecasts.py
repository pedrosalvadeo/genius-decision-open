"""Frozen predictions and append-only, post-freeze submitted observations.

Server receipt order is evidence about this service, never a sensor attestation.
Exact arithmetic scores fixed estimates; it does not refit or deploy a model.
"""
from datetime import datetime, timedelta, timezone
import json
import re
import time
from flask import jsonify
from pathlib import Path
from .mission_state import digest as sha
from .db import dump, transaction

FORMAT = 'resource_forecast_v1'
RESERVATION = 131072
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def now_us():
    return time.time_ns() // 1000


def iso(us):
    return (EPOCH + timedelta(microseconds=us)).isoformat().replace('+00:00', 'Z')


def event_us(value):
    from genius_adaptive.calibration import timestamp
    delta = timestamp(value) - EPOCH
    return (delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds


def fingerprint(value):
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8'))


def scorer_identity():
    from genius_adaptive import calibration
    return dict(rule='FIXED_ESTIMATES_ABSOLUTE_ERROR_V1',
                scorer_sha256=sha(Path(__file__).read_bytes()),
                calibration_sha256=sha(Path(calibration.__file__).read_bytes()))


def validate_record(record):
    from genius_adaptive.calibration import integer
    if not isinstance(record, dict) or set(record) != {'id','value','observed_at','source'}:
        raise ValueError('OBSERVATION_FIELDS')
    if not isinstance(record['id'], str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', record['id']):
        raise ValueError('OBSERVATION_ID')
    if not integer(record['value']):
        raise ValueError('OBSERVATION_VALUE')
    source = record['source']
    if not isinstance(source, str) or not source.strip() or len(source) > 240:
        raise ValueError('OBSERVATION_SOURCE')
    source.encode('utf-8')
    return event_us(record['observed_at'])


def read(db, mid):
    row = db.execute('SELECT * FROM mission_forecasts WHERE mission_id=?', (mid,)).fetchone()
    if not row:
        return None
    frozen = json.loads(row['frozen_json'])
    if (fingerprint(frozen) != row['forecast_sha256'] or frozen['frozen_at_us'] != row['frozen_at_us']
            or frozen['expected_count'] != row['expected_count']):
        raise ValueError('FORECAST_INTEGRITY')
    observations, previous = [], row['forecast_sha256']
    previous_received = frozen['frozen_at_us']
    for entry in db.execute('SELECT * FROM mission_forecast_observations WHERE mission_id=? ORDER BY sequence', (mid,)):
        receipt = json.loads(entry['receipt_json'])
        if (fingerprint(receipt) != entry['receipt_sha256'] or receipt['previous_sha256'] != previous
                or receipt['sequence'] != len(observations) + 1 or receipt['sequence'] != entry['sequence']
                or receipt['received_at_us'] != entry['received_at_us'] or receipt['received_at_us'] <= previous_received
                or receipt['forecast_sha256'] != row['forecast_sha256']):
            raise ValueError('OBSERVATION_INTEGRITY')
        previous, previous_received = entry['receipt_sha256'], receipt['received_at_us']
        observations.append(dict(receipt=receipt, sha256=entry['receipt_sha256']))
    report = json.loads(row['report_json']) if row['report_json'] else None
    if (len(observations) > frozen['expected_count']
            or (len(observations) == frozen['expected_count']) != (report is not None)):
        raise ValueError('FORECAST_COUNT')
    if report is not None and (fingerprint(report) != row['report_sha256']
            or len(observations) != frozen['expected_count']
            or report['receipt_sha256s'] != [r['sha256'] for r in observations]):
        raise ValueError('REPORT_INTEGRITY')
    return dict(frozen=frozen, sha256=row['forecast_sha256'],
                status='complete' if report is not None else 'collecting',
                received_count=len(observations), observations=observations,
                report=report, report_sha256=row['report_sha256'])


def completed_training(db, mid):
    forecast = read(db, mid)
    if forecast is None or forecast['status'] != 'complete':
        raise ValueError('COMPLETE_FORECAST_REQUIRED')
    return forecast


def build_report(forecast, receipts, closed_at_us):
    from genius_adaptive.calibration import metrics
    frozen = forecast['frozen']
    records = [entry['receipt']['observation'] for entry in receipts]
    comparison = {name: metrics(frozen[name], records) for name in ('baseline','estimate')}
    base, estimate = comparison['baseline'], comparison['estimate']
    checks = dict(lower_error=estimate['absolute_error_sum'] < base['absolute_error_sum'],
                  no_worse_underprediction=estimate['max_underprediction'] <= base['max_underprediction'],
                  within_declared_limit=estimate['max_underprediction'] <= frozen['max_underprediction'])
    return dict(format=FORMAT, forecast_sha256=forecast['sha256'],
                closed_at_us=closed_at_us, closed_at=iso(closed_at_us),
                receipt_sha256s=[entry['sha256'] for entry in receipts], comparison=comparison,
                checks=checks, outcome='LOWER_ERROR_WITHIN_GUARDS' if all(checks.values()) else 'NO_CONFIRMED_IMPROVEMENT',
                baseline=frozen['baseline'], estimate=frozen['estimate'], unit=frozen['unit'],
                data_kind=frozen['data_kind'], expected_count=frozen['expected_count'],
                evidence_status='POST_FREEZE_SUBMISSIONS', event_times='DECLARED_NOT_ATTESTED',
                source_verification='NOT_INDEPENDENTLY_VERIFIED', model_changed=False,
                wellbeing_effect='UNMEASURED', life_sustainment_effect='UNMEASURED')


def install(app, db, body, error, enabled, own, capacity):
    def required(mid):
        own(mid)
        result = read(db(), mid)
        if result is None:
            raise error('forecast_not_found', 'Esta misión no tiene una predicción congelada.', 404)
        return result

    @app.get('/api/missions/<mid>/forecast')
    def forecast_get(mid):
        return jsonify(forecast=required(mid))

    @app.post('/api/missions/<mid>/forecast')
    def forecast_freeze(mid):
        enabled()
        data = body()
        if (set(data) != {'artifact_sha256','expected_count'} or type(data['expected_count']) is not int
                or not 3 <= data['expected_count'] <= 30 or not isinstance(data['artifact_sha256'], str)
                or not re.fullmatch('[a-f0-9]{64}', data['artifact_sha256'])):
            raise error('forecast_input', 'Se requieren el hash de la entrega y entre 3 y 30 observaciones previstas.')
        with transaction(db()):
            mission = own(mid)
            previous = db().execute('SELECT request_sha256 FROM mission_forecasts WHERE mission_id=?', (mid,)).fetchone()
            if previous:
                if previous['request_sha256'] != fingerprint(data):
                    raise error('forecast_conflict', 'La predicción y el número previsto ya están congelados.', 409)
                return jsonify(forecast=read(db(), mid)), 200
            raw = mission['artifact']
            if (mission['status'] != 'completed' or mission['artifact_name'] != 'resource-estimate.json'
                    or raw is None or sha(raw) != mission['artifact_sha256']):
                raise error('forecast_parent', 'Se requiere una calibración completada y verificada.', 409)
            if data['artifact_sha256'] != mission['artifact_sha256']:
                raise error('artifact_conflict', 'El hash no corresponde a la entrega de esta misión.', 409)
            memory = json.loads(raw)
            when = now_us()
            if memory['format'] != 'resource_calibration_v1' or event_us(memory['last_observed_at']) >= when:
                raise error('forecast_time', 'Las observaciones de aprendizaje deben preceder a la congelación.')
            frozen = {key: memory[key] for key in ('context','resource','unit','data_kind','baseline','estimate','max_underprediction')}
            frozen.update(format=FORMAT, mission_id=mid, artifact_sha256=mission['artifact_sha256'],
                          frozen_at_us=when, frozen_at=iso(when), expected_count=data['expected_count'],
                          event_times='DECLARED_NOT_ATTESTED', scorer_identity=scorer_identity(),
                          rule='FIXED_ESTIMATES_ABSOLUTE_ERROR_V1')
            capacity(RESERVATION)
            db().execute('INSERT INTO mission_forecasts(mission_id,request_sha256,frozen_json,forecast_sha256,frozen_at_us,expected_count) VALUES(?,?,?,?,?,?)',
                         (mid,fingerprint(data),dump(frozen),fingerprint(frozen),when,data['expected_count']))
            db().execute('UPDATE adaptive_missions SET updated_at=? WHERE id=?', (when//1_000_000,mid))
        return jsonify(forecast=read(db(), mid)), 201

    @app.post('/api/missions/<mid>/observations')
    def forecast_observe(mid):
        enabled()
        data = body()
        if set(data) != {'forecast_sha256','observation'} or not isinstance(data['forecast_sha256'], str):
            raise error('observation_input', 'Se requieren el hash de predicción y una observación.')
        record = data['observation']
        try:
            observed = validate_record(record)
            request_sha = fingerprint(data)
        except (ValueError, TypeError, OverflowError):
            raise error('observation_input', 'Revisá ID, valor entero, fuente y fecha con zona horaria.') from None
        with transaction(db()):
            forecast = required(mid)
            if data['forecast_sha256'] != forecast['sha256']:
                raise error('forecast_conflict', 'El hash no corresponde a la predicción congelada.', 409)
            old = db().execute('SELECT * FROM mission_forecast_observations WHERE mission_id=? AND observation_id=?', (mid,record['id'])).fetchone()
            if old:
                if old['request_sha256'] != request_sha:
                    raise error('observation_conflict', 'El ID ya identifica otra observación inmutable.', 409)
                return jsonify(observation=dict(receipt=json.loads(old['receipt_json']),sha256=old['receipt_sha256']),
                               forecast_status=forecast['status'], report_sha256=forecast['report_sha256']), 200
            if forecast['status'] == 'complete':
                raise error('forecast_complete', 'Se recibieron todas las observaciones previstas; el informe está cerrado.', 409)
            frozen, prior = forecast['frozen'], forecast['observations']
            if frozen['scorer_identity'] != scorer_identity():
                raise error('forecast_review_required', 'Cambió el código de evaluación; la predicción requiere revisión antes de recibir más datos.', 409)
            received = now_us()
            last_received = prior[-1]['receipt']['received_at_us'] if prior else frozen['frozen_at_us']
            if received <= last_received:
                raise error('receipt_clock', 'El reloj del servidor no avanzó; reintentá sin cambiar la observación.', 503)
            last_event = event_us(prior[-1]['receipt']['observation']['observed_at']) if prior else frozen['frozen_at_us']
            if observed <= last_event or observed > received:
                raise error('observation_time', 'La fecha declarada debe ser posterior a la congelación y al registro anterior, y no posterior a la recepción.')
            receipt = dict(sequence=len(prior)+1, forecast_sha256=forecast['sha256'],
                previous_sha256=prior[-1]['sha256'] if prior else forecast['sha256'],
                received_at_us=received, received_at=iso(received), observation=record,
                errors={name:dict(absolute=abs(record['value']-frozen[name]),
                    underprediction=max(0,record['value']-frozen[name])) for name in ('baseline','estimate')})
            receipt_sha = fingerprint(receipt)
            capacity(len(dump(receipt).encode()) * 2 + 8192)
            db().execute('INSERT INTO mission_forecast_observations VALUES(?,?,?,?,?,?,?)',
                (mid,receipt['sequence'],record['id'],request_sha,dump(receipt),receipt_sha,received))
            report_sha = None
            if receipt['sequence'] == frozen['expected_count']:
                report = build_report(forecast, prior+[dict(receipt=receipt,sha256=receipt_sha)], received)
                report_sha = fingerprint(report)
                db().execute('UPDATE mission_forecasts SET report_json=?,report_sha256=? WHERE mission_id=? AND report_json IS NULL',
                             (dump(report),report_sha,mid))
            db().execute('UPDATE adaptive_missions SET updated_at=? WHERE id=?', (received//1_000_000,mid))
        return jsonify(observation=dict(receipt=receipt,sha256=receipt_sha),
                       forecast_status='complete' if report_sha else 'collecting', report_sha256=report_sha), 201
