"""Tenant-bound, sequential predictions and later observations, without refitting history.

The final native comparison runs in a bounded child with the existing compiler
lock and job quotas. It never holds a database write transaction while computing.
"""
import fcntl
import json
from pathlib import Path
import re
import time
from flask import g, jsonify
from genius_adaptive import contextual
from .db import dump, transaction
from .mission_state import digest
from .mission_forecasts import fingerprint, event_us, iso, validate_record, now_us

FORMAT = 'resource_context_forecast_v1'
RESERVATION = 4 * 1024 * 1024
OUTPUT_LIMIT = 2 * 1024 * 1024
ID = re.compile(r'[A-Za-z0-9_-]{1,64}\Z')


def scorer_identity():
    from genius_adaptive import calibration
    from genius_twin.registry import STOCKFLOW, execution_identity
    from . import mission_forecasts
    return dict(rule=contextual.RULE, sources={p.name:digest(p.read_bytes()) for p in
        (Path(__file__),Path(contextual.__file__),Path(calibration.__file__),Path(mission_forecasts.__file__),
         Path(calibration.__file__).with_name('distribution_model.json'))}, native=execution_identity(STOCKFLOW),
        execution=dict(timeout_seconds=20,memory_mb=384,output_bytes=OUTPUT_LIMIT))


def read(db, mid):
    row = db.execute('SELECT * FROM mission_context_forecasts WHERE mission_id=?',(mid,)).fetchone()
    if row is None:
        return None
    frozen = json.loads(row['frozen_json'])
    if (fingerprint(frozen) != row['forecast_sha256'] or frozen['frozen_at_us'] != row['frozen_at_us'] or
            frozen['warmup_count'] + frozen['scored_count'] != row['total_count']):
        raise ValueError('CONTEXT_PLAN_INTEGRITY')
    predictions = db.execute('SELECT * FROM mission_context_predictions WHERE mission_id=? ORDER BY sequence',(mid,)).fetchall()
    observations = db.execute('SELECT * FROM mission_context_observations WHERE mission_id=? ORDER BY sequence',(mid,)).fetchall()
    if len(predictions) > row['total_count'] or not 0 <= len(predictions)-len(observations) <= 1:
        raise ValueError('CONTEXT_COUNT')
    pairs, previous, last_time = [], row['forecast_sha256'], row['frozen_at_us']
    for index, entry in enumerate(predictions, 1):
        receipt = json.loads(entry['receipt_json'])
        if (fingerprint(receipt) != entry['receipt_sha256'] or receipt['sequence'] != index or entry['sequence'] != index or
                receipt['previous_sha256'] != previous or receipt['forecast_sha256'] != row['forecast_sha256'] or
                receipt['prediction_id'] != entry['prediction_id'] or receipt['issued_at_us'] != entry['issued_at_us'] or
                receipt['issued_at_us'] <= last_time):
            raise ValueError('CONTEXT_PREDICTION_INTEGRITY')
        prediction = dict(receipt=receipt,sha256=entry['receipt_sha256'])
        observed = None
        previous, last_time = entry['receipt_sha256'], entry['issued_at_us']
        if index <= len(observations):
            obs = observations[index-1]; value = json.loads(obs['receipt_json'])
            event = validate_record(value['observation'])
            if (fingerprint(value) != obs['receipt_sha256'] or value['sequence'] != index or obs['sequence'] != index or
                    value['previous_sha256'] != previous or value['forecast_sha256'] != row['forecast_sha256'] or
                    value['observation']['id'] != receipt['prediction_id'] or obs['observation_id'] != receipt['prediction_id'] or
                    value['received_at_us'] != obs['received_at_us'] or not last_time < event <= value['received_at_us']):
                raise ValueError('CONTEXT_OBSERVATION_INTEGRITY')
            observed = dict(receipt=value,sha256=obs['receipt_sha256'])
            previous, last_time = obs['receipt_sha256'], obs['received_at_us']
        pairs.append(dict(prediction=prediction,observation=observed))
    report = json.loads(row['report_json']) if row['report_json'] else None
    if report is not None and (fingerprint(report) != row['report_sha256'] or len(observations) != row['total_count'] or
            report['forecast_sha256'] != row['forecast_sha256'] or report['previous_sha256'] != previous or
            report['closed_at_us'] <= last_time or report['receipt_sha256s'] !=
            [[pair['prediction']['sha256'],pair['observation']['sha256']] for pair in pairs]):
        raise ValueError('CONTEXT_REPORT_INTEGRITY')
    return dict(frozen=frozen,sha256=row['forecast_sha256'],pairs=pairs,received_count=len(observations),
                status='complete' if report is not None else 'ready_to_close' if len(observations)==row['total_count'] else
                       'awaiting_observation' if len(predictions)>len(observations) else 'ready_to_predict',
                report=report,report_sha256=row['report_sha256'])


def history_of(forecast, verify=False):
    history = []
    for pair in forecast['pairs']:
        prediction = pair['prediction']['receipt']['prediction']
        if verify and prediction != contextual.predict(history, forecast['frozen']):
            raise ValueError('CONTEXT_PREFIX_DISAGREEMENT')
        if pair['observation'] is not None:
            history.append(dict(**prediction,value=pair['observation']['receipt']['observation']['value']))
    return history


def install(app, db, body, error, enabled, own, capacity):
    def required(mid):
        own(mid)
        result = read(db(), mid)
        if result is None:
            raise error('context_not_found','Esta misión no tiene un plan contextual.',404)
        return result

    def current(forecast):
        if forecast['frozen']['scorer_identity'] != scorer_identity():
            raise error('context_review_required','Cambió el evaluador; se conserva lectura y exportación, pero continuar requiere revisión.',409)
        history_of(forecast, verify=True)

    def matches(data, forecast):
        if data['forecast_sha256'] != forecast['sha256']:
            raise error('context_conflict','El hash no corresponde al plan congelado.',409)

    def tick(previous):
        when = now_us()
        if when <= previous:
            raise error('receipt_clock','El reloj no avanzó; reintentá la misma solicitud.',503)
        return when

    def touch(mid, when):
        db().execute('UPDATE adaptive_missions SET updated_at=? WHERE id=?',(when//1000000,mid))

    @app.get('/api/missions/<mid>/context-forecast')
    def context_get(mid):
        return jsonify(forecast=required(mid))

    @app.post('/api/missions/<mid>/context-forecast')
    def context_freeze(mid):
        enabled(); data = body()
        if (set(data) != {'artifact_sha256','warmup_count','scored_count'} or
                not isinstance(data['artifact_sha256'],str) or not re.fullmatch('[a-f0-9]{64}',data['artifact_sha256']) or
                type(data['warmup_count']) is not int or not 3 <= data['warmup_count'] <= 10 or
                type(data['scored_count']) is not int or not 6 <= data['scored_count'] <= 30):
            raise error('context_input','Se requieren hash de entrega, warmup_count (3..10) y scored_count (6..30).')
        with transaction(db()):
            mission = own(mid)
            old = db().execute('SELECT request_sha256 FROM mission_context_forecasts WHERE mission_id=?',(mid,)).fetchone()
            if old:
                if old['request_sha256'] != fingerprint(data):
                    raise error('context_conflict','El plan contextual ya es inmutable.',409)
                return jsonify(forecast=read(db(),mid)),200
            raw = mission['artifact']
            if (mission['status'] != 'completed' or mission['artifact_name'] != 'resource-estimate.json' or
                    raw is None or digest(raw) != mission['artifact_sha256'] or data['artifact_sha256'] != mission['artifact_sha256']):
                raise error('context_parent','Se requiere una calibración propia completada y su hash de entrega.',409)
            memory = json.loads(raw); when = now_us()
            if memory['format'] != 'resource_calibration_v1' or event_us(memory['last_observed_at']) >= when:
                raise error('context_parent_time','El aprendizaje debe preceder al plan contextual.')
            frozen = {key:memory[key] for key in ('context','resource','unit','data_kind','max_underprediction')}
            frozen.update(format=FORMAT,rule=contextual.RULE,mission_id=mid,artifact_sha256=mission['artifact_sha256'],
                baseline=memory['estimate'],warmup_count=data['warmup_count'],scored_count=data['scored_count'],
                context_rule='PREVIOUS_VALUE_GT_FROZEN_BASELINE',strategies=list(contextual.ORDER),
                frozen_at_us=when,frozen_at=iso(when),scorer_identity=scorer_identity(),
                source_verification='SUBMITTED_NOT_INDEPENDENTLY_VERIFIED',event_times='DECLARED_NOT_ATTESTED')
            capacity(RESERVATION)
            db().execute('INSERT INTO mission_context_forecasts(mission_id,request_sha256,frozen_json,forecast_sha256,frozen_at_us,total_count) VALUES(?,?,?,?,?,?)',
                (mid,fingerprint(data),dump(frozen),fingerprint(frozen),when,data['warmup_count']+data['scored_count']))
            touch(mid,when)
        return jsonify(forecast=read(db(),mid)),201

    @app.post('/api/missions/<mid>/context-forecast/predictions')
    def context_predict(mid):
        enabled(); data = body()
        if (set(data) != {'forecast_sha256','prediction_id'} or not isinstance(data['forecast_sha256'],str) or
                not isinstance(data['prediction_id'],str) or not ID.fullmatch(data['prediction_id'])):
            raise error('context_input','Se requieren forecast_sha256 y prediction_id (1..64 letras, números, _ o -).')
        with transaction(db()):
            forecast = required(mid); matches(data,forecast)
            old = db().execute('SELECT * FROM mission_context_predictions WHERE mission_id=? AND prediction_id=?',(mid,data['prediction_id'])).fetchone()
            if old:
                if old['request_sha256'] != fingerprint(data):
                    raise error('context_conflict','El ID ya identifica otra predicción.',409)
                return jsonify(prediction=dict(receipt=json.loads(old['receipt_json']),sha256=old['receipt_sha256'])),200
            if forecast['status'] != 'ready_to_predict':
                raise error('context_sequence','Hay una observación pendiente o se completó el número previsto.',409)
            current(forecast)
            prior = forecast['pairs'][-1]['observation'] if forecast['pairs'] else None
            when = tick(prior['receipt']['received_at_us'] if prior else forecast['frozen']['frozen_at_us'])
            receipt = dict(sequence=len(forecast['pairs'])+1,forecast_sha256=forecast['sha256'],
                previous_sha256=prior['sha256'] if prior else forecast['sha256'],prediction_id=data['prediction_id'],
                issued_at_us=when,issued_at=iso(when),prediction=contextual.predict(history_of(forecast),forecast['frozen']))
            checksum = fingerprint(receipt); capacity(len(dump(receipt).encode())*2+8192)
            db().execute('INSERT INTO mission_context_predictions VALUES(?,?,?,?,?,?,?)',
                (mid,receipt['sequence'],data['prediction_id'],fingerprint(data),dump(receipt),checksum,when))
            touch(mid,when)
        return jsonify(prediction=dict(receipt=receipt,sha256=checksum)),201

    @app.post('/api/missions/<mid>/context-forecast/observations')
    def context_observe(mid):
        enabled(); data = body()
        if (set(data) != {'forecast_sha256','prediction_sha256','observation'} or
                not isinstance(data['forecast_sha256'],str) or not isinstance(data['prediction_sha256'],str)):
            raise error('context_input','Se requieren hashes de plan y predicción y la observación.')
        try:
            observed = validate_record(data['observation']); request_sha = fingerprint(data)
        except (ValueError,TypeError,OverflowError):
            raise error('context_input','Revisá ID, valor entero, fecha con zona horaria y fuente.') from None
        with transaction(db()):
            forecast = required(mid); matches(data,forecast)
            old = db().execute('SELECT * FROM mission_context_observations WHERE mission_id=? AND observation_id=?',(mid,data['observation']['id'])).fetchone()
            if old:
                if old['request_sha256'] != request_sha:
                    raise error('context_conflict','El ID ya identifica una observación inmutable.',409)
                return jsonify(observation=dict(receipt=json.loads(old['receipt_json']),sha256=old['receipt_sha256']),status=forecast['status']),200
            if forecast['status'] != 'awaiting_observation':
                raise error('context_sequence','Se requiere una predicción emitida y todavía sin observación.',409)
            current(forecast); prediction = forecast['pairs'][-1]['prediction']
            if data['prediction_sha256'] != prediction['sha256'] or data['observation']['id'] != prediction['receipt']['prediction_id']:
                raise error('context_conflict','La observación debe identificar la predicción pendiente.',409)
            received = tick(prediction['receipt']['issued_at_us'])
            if not prediction['receipt']['issued_at_us'] < observed <= received:
                raise error('context_time','La fecha declarada debe ser posterior a la predicción y no posterior a su recepción.')
            receipt = dict(sequence=prediction['receipt']['sequence'],forecast_sha256=forecast['sha256'],
                previous_sha256=prediction['sha256'],received_at_us=received,received_at=iso(received),observation=data['observation'])
            checksum = fingerprint(receipt); capacity(len(dump(receipt).encode())*2+8192)
            db().execute('INSERT INTO mission_context_observations VALUES(?,?,?,?,?,?,?)',
                (mid,receipt['sequence'],data['observation']['id'],request_sha,dump(receipt),checksum,received))
            touch(mid,received)
        return jsonify(observation=dict(receipt=receipt,sha256=checksum),status=read(db(),mid)['status']),201

    @app.post('/api/missions/<mid>/context-forecast/close')
    def context_close(mid):
        enabled(); data = body()
        if set(data) != {'forecast_sha256'} or not isinstance(data['forecast_sha256'],str):
            raise error('context_input','Se requiere forecast_sha256.')
        forecast = required(mid); matches(data,forecast)
        if forecast['status'] == 'complete':
            return jsonify(forecast=forecast),200
        if forecast['status'] != 'ready_to_close':
            raise error('context_incomplete','Todavía faltan observaciones del plan.',409)
        current(forecast)
        folder = Path(app.config['DATA_DIR'])/'twin-locks'; folder.mkdir(mode=0o700,parents=True,exist_ok=True)
        with (folder/'compiler.lock').open('a+b') as lock:
            try:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:
                raise error('compute_capacity','Hay otra evaluación en curso; reintentá el cierre.',429) from None
            # Recheck after locking; replay of a completed report consumes no quota.
            forecast = required(mid)
            if forecast['status'] == 'complete':
                return jsonify(forecast=forecast),200
            current(forecast); capacity(RESERVATION)
            with transaction(db()):
                own(mid)
                now = int(time.time()); day = now//86400*86400
                for key,limit in (('missions-global',app.config['MAX_GLOBAL_JOBS_DAILY']),
                                  ('missions-user:'+g.user['id'],app.config['MAX_JOBS_DAILY'])):
                    count = db().execute('SELECT count FROM counters WHERE key=? AND bucket=?',(key,day)).fetchone()
                    if count and count[0] >= limit:
                        raise error('mission_daily_limit','Cuota diaria de ejecución alcanzada.',429)
                    db().execute('INSERT INTO counters VALUES(?,?,1) ON CONFLICT(key,bucket) DO UPDATE SET count=count+1',(key,day))
                if g.agent_account:
                    from .agent_access import reserve_agent_job
                    reserve_agent_job(db(),app.config,g.user['id'],now,error)
            report = contextual.report(history_of(forecast,verify=True),forecast['frozen'])
            from genius_twin.process_runner import ProcessEvaluator
            try:
                native = ProcessEvaluator(timeout=20,memory_mb=384,output_bytes=OUTPUT_LIMIT)(contextual.comparison_model(report['comparison']))
                losses = {key:value['absolute_error_sum'] for key,value in report['comparison'].items()}
                best = [key for key,value in losses.items() if value==min(losses.values())]
                if (native['verification']['valid'] is not True or
                        native['canonical_results']['decision']['selected'] != (best[0] if len(best)==1 else None)):
                    raise ValueError('NATIVE_ARITHMETIC_DISAGREEMENT')
            except (TimeoutError,RuntimeError,ValueError,KeyError,OSError):
                raise error('context_evaluation_failed','No se obtuvo una comprobación nativa válida; observaciones conservadas y cierre pendiente.',503) from None
            with transaction(db()):
                fresh = required(mid); current(fresh)
                if fresh != forecast:
                    raise error('context_conflict','El expediente cambió durante la evaluación.',409)
                if ((g.agent_grant and g.agent_grant['expires_at'] <= int(time.time())) or
                        (g.agent_account and g.agent_account['expires_at'] is not None and
                         g.agent_account['expires_at'] <= int(time.time()))):
                    raise error('unauthorized','La credencial venció durante la evaluación.',401)
                closed = tick(forecast['pairs'][-1]['observation']['receipt']['received_at_us'])
                report.update(format=FORMAT,forecast_sha256=forecast['sha256'],closed_at_us=closed,closed_at=iso(closed),
                    previous_sha256=forecast['pairs'][-1]['observation']['sha256'],
                    receipt_sha256s=[[p['prediction']['sha256'],p['observation']['sha256']] for p in forecast['pairs']],
                    unit=forecast['frozen']['unit'],data_kind=forecast['frozen']['data_kind'],native=native,
                    evidence_status='SERVER_PREDICTIONS_BEFORE_SUBMITTED_TARGETS',event_times='DECLARED_NOT_ATTESTED')
                encoded = dump(report)
                if len(encoded.encode()) > RESERVATION//2:
                    raise error('context_output_limit','El informe supera el límite; datos conservados.',503)
                capacity(len(encoded.encode())*2+8192)
                db().execute('UPDATE mission_context_forecasts SET report_json=?,report_sha256=? WHERE mission_id=?',
                             (encoded,fingerprint(report),mid)); touch(mid,closed)
        return jsonify(forecast=read(db(),mid)),201
