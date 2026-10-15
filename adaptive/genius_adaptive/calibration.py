"""A bounded learning rule for a constant resource-use estimate.

Submitted records are not sensor attestations. Chronologically later holdout
records test a training-only median retrospectively, not future causal benefit.
"""
from datetime import datetime
import json
from pathlib import Path
import re
from .journal import Conflict, canonical, publish, sha

KIND = 'resource_calibration_v1'
ARTIFACT = 'resource-estimate.json'
RULE = 'LOWER_MEDIAN_HOLDOUT_MAE_V1'
MAX_VALUE = 1_000_000


def timestamp(value):
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError('OBSERVATION_TIME')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError('OBSERVATION_TIME') from None
    if result.tzinfo is None:
        raise ValueError('OBSERVATION_TIMEZONE_REQUIRED')
    return result


def integer(value):
    return type(value) is int and 0 <= value <= MAX_VALUE


def validate_input(data):
    fields = {'context', 'resource', 'unit', 'baseline', 'max_underprediction',
              'data_kind', 'training', 'validation'}
    if not isinstance(data, dict) or set(data) != fields:
        raise ValueError('CALIBRATION_FIELDS')
    for key, limit in (('context', 500), ('resource', 64), ('unit', 64)):
        value = data[key]
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            raise ValueError('CALIBRATION_CONTEXT')
        value.encode('utf-8')
    if not integer(data['baseline']) or not integer(data['max_underprediction']):
        raise ValueError('CALIBRATION_INTEGER_RANGE')
    if data['data_kind'] not in ('synthetic', 'submitted_observations'):
        raise ValueError('CALIBRATION_PROVENANCE')
    training, validation = data['training'], data['validation']
    if (not isinstance(training, list) or not isinstance(validation, list)
            or len(training) < 3 or len(validation) < 2 or len(training) + len(validation) > 32):
        raise ValueError('CALIBRATION_SAMPLE_COUNT')
    ids, previous = set(), None
    for record in training + validation:
        if not isinstance(record, dict) or set(record) != {'id', 'value', 'observed_at', 'source'}:
            raise ValueError('OBSERVATION_FIELDS')
        if not isinstance(record['id'], str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', record['id']) or record['id'] in ids:
            raise ValueError('OBSERVATION_ID')
        ids.add(record['id'])
        if not integer(record['value']):
            raise ValueError('OBSERVATION_INTEGER_RANGE')
        if not isinstance(record['source'], str) or not record['source'].strip() or len(record['source']) > 240:
            raise ValueError('OBSERVATION_SOURCE')
        record['source'].encode('utf-8')
        when = timestamp(record['observed_at'])
        if previous is not None and when <= previous:
            raise ValueError('CHRONOLOGICAL_DISJOINT_SPLIT_REQUIRED')
        previous = when


def prepare(data, directory, mission_id, lineage=None):
    validate_input(data)
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    raw = (canonical(data) + '\n').encode()
    publish(directory / 'input' / 'observations.json', raw)
    spec = dict(id=mission_id, kind=KIND, input_sha256=sha(raw), rule=RULE,
                lineage=lineage, scope='RETROSPECTIVE_RESOURCE_ESTIMATION')
    publish(directory / 'mission.json', (canonical(spec) + '\n').encode())
    return spec


def metrics(estimate, records):
    errors = [abs(estimate - row['value']) for row in records]
    return dict(absolute_error_sum=sum(errors), count=len(errors),
                max_underprediction=max(max(0, row['value'] - estimate) for row in records))


class Calibration:
    def data(self, directory):
        return json.loads((directory / 'input' / 'observations.json').read_text())

    def validate(self, directory, spec):
        if spec['kind'] != KIND or spec['rule'] != RULE:
            raise ValueError('UNSUPPORTED_MISSION')
        if any(p.is_symlink() for p in directory.rglob('*')):
            raise Conflict('STATE_SYMLINK_NOT_SUPPORTED')
        raw = (directory / 'input' / 'observations.json').read_bytes()
        if len(raw) > 65536 or sha(raw) != spec['input_sha256']:
            raise Conflict('OBSERVATIONS_CHANGED')
        validate_input(self.data(directory))

    def measure(self, directory, spec, history, journal):
        data = self.data(directory)
        ordered = sorted(row['value'] for row in data['training'])
        proposal = ordered[(len(ordered) - 1) // 2]
        return dict(input_sha256=spec['input_sha256'], rule=RULE,
                    baseline=data['baseline'], proposal=proposal,
                    training_sha256=sha(canonical(data['training']).encode()),
                    validation_sha256=sha(canonical(data['validation']).encode()),
                    training_count=len(ordered), validation_count=len(data['validation']),
                    comparison={name: metrics(value, data['validation']) for name, value in
                                (('baseline', data['baseline']), ('proposal', proposal))},
                    evidence_kind=data['data_kind'], provenance='SUBMITTED_NOT_INDEPENDENTLY_VERIFIED',
                    validation_design='RETROSPECTIVE_CHRONOLOGICAL_HOLDOUT')

    def represent(self, directory, spec, history, journal):
        # Reuse the accepted native one-step operational comparison. Its stock
        # is an error allowance, never a physical water or human wellbeing stock.
        model = json.loads(Path(__file__).with_name('distribution_model.json').read_text())
        rows = history['measure']['comparison']
        budget = max(row['absolute_error_sum'] for row in rows.values())
        model['name'] = 'Comparación retrospectiva de error de estimación'
        model['stocks'][0].update(label='Margen de error absoluto en unidades declaradas',
                                  unit='declared_error_unit', initial=f'{budget}/1', capacity=f'{budget}/1')
        model['capabilities'][0]['label'] = 'Conservar una estimación auditable'
        model['actions'] = [dict(id='use_' + key, label=key, requires=['deliver'],
            withdrawals={'remaining':str(row['absolute_error_sum']) + '/1'}, deposits={},
            add_capabilities=[], remove_capabilities=[]) for key, row in rows.items()]
        model['policies'] = [dict(id=key, label=key, default_action='use_' + key, rules=[]) for key in rows]
        model['scenarios'][0]['label'] = 'Errores calculados sobre la partición de comprobación enviada'
        model['welfare'][0].update(dimension='error_margin', label='Menor error absoluto; criterio operacional')
        model['task']['label'] = 'Comparar estimaciones dentro del margen de error observado'
        model['assumptions'] = [dict(id='Scope', kind='MODEL',
            statement='El margen representa error de estimación, no recurso físico ni bienestar. La masa unitaria sólo describe esta comparación retrospectiva; no estima el futuro.',
            provenance='Contrato resource_calibration_v1'), dict(id='Criterion', kind='NORMATIVE',
            statement='Menor suma de errores absolutos en las mismas observaciones. La adopción además requiere no aumentar la máxima subestimación y cumplir el límite declarado.',
            provenance='Regla LOWER_MEDIAN_HOLDOUT_MAE_V1')]
        return model

    def evaluate(self, directory, spec, history, journal):
        from genius_twin.registry import evaluate
        native = evaluate(history['represent'])
        if native['verification']['valid'] is not True:
            raise ValueError('NATIVE_RESULT_NOT_VERIFIED')
        rows = history['measure']['comparison']
        baseline, proposed = rows['baseline'], rows['proposal']
        losses = {key: row['absolute_error_sum'] for key, row in rows.items()}
        best = [key for key, value in losses.items() if value == min(losses.values())]
        selected = native['canonical_results']['decision']['selected']
        if selected != (best[0] if len(best) == 1 else None):
            raise ValueError('NATIVE_ARITHMETIC_DISAGREEMENT')
        data = self.data(directory)
        checks = dict(lower_holdout_error=proposed['absolute_error_sum'] < baseline['absolute_error_sum'],
                      no_worse_underprediction=proposed['max_underprediction'] <= baseline['max_underprediction'],
                      within_declared_limit=proposed['max_underprediction'] <= data['max_underprediction'])
        adopted = all(checks.values())
        return dict(native=native, checks=checks, adopted=adopted,
                    decision='ADOPT_PROPOSAL' if adopted else 'KEEP_BASELINE',
                    selected_estimate=history['measure']['proposal'] if adopted else data['baseline'],
                    baseline_within_declared_limit=baseline['max_underprediction'] <= data['max_underprediction'],
                    interpretation='Internal estimate only; retrospective evidence, prospective validation pending')

    def act(self, directory, spec, history, journal):
        data, result = self.data(directory), history['evaluate']
        memory = dict(format=KIND, rule=RULE, mission_id=spec['id'], input_sha256=spec['input_sha256'],
            context=data['context'], resource=data['resource'], unit=data['unit'], data_kind=data['data_kind'],
            baseline=data['baseline'], proposal=history['measure']['proposal'],
            estimate=result['selected_estimate'], decision=result['decision'], checks=result['checks'],
            comparison=history['measure']['comparison'], max_underprediction=data['max_underprediction'],
            last_observed_at=data['validation'][-1]['observed_at'], lineage=spec['lineage'],
            validation='RETROSPECTIVE_ONLY', prospective_validation='PENDING',
            provenance='SUBMITTED_NOT_INDEPENDENTLY_VERIFIED', external_actions=0,
            wellbeing_effect='UNMEASURED', life_sustainment_effect='UNMEASURED')
        raw = (canonical(memory) + '\n').encode()
        destination = directory / 'delivery' / ARTIFACT
        request = dict(kind='PRIVATE_RESOURCE_ESTIMATE', destination='delivery/' + ARTIFACT,
                       sha256=sha(raw), bytes=len(raw))
        def reconcile():
            if not destination.exists():
                return None
            if destination.read_bytes() != raw:
                raise Conflict('ESTIMATE_CHANGED')
            return {**request, 'confirmed': True}
        def apply():
            publish(destination, raw)
            return reconcile()
        return journal.effect('publish_resource_estimate', request, apply, reconcile)

    def observe(self, directory, spec, history, journal):
        action = history['act']
        raw = (directory / action['destination']).read_bytes()
        if len(raw) != action['bytes'] or sha(raw) != action['sha256']:
            raise Conflict('ESTIMATE_READBACK_FAILED')
        return dict(readback_verified=True, artifact_sha256=sha(raw),
                    external_actions=0, prospective_validation='PENDING')

    def remember(self, directory, spec, history, journal):
        return dict(kind='RESOURCE_ESTIMATE_MEMORY', decision=history['evaluate']['decision'],
                    estimate=history['evaluate']['selected_estimate'],
                    baseline=history['measure']['baseline'], proposal=history['measure']['proposal'],
                    comparison=history['measure']['comparison'], checks=history['evaluate']['checks'],
                    artifact_sha256=history['observe']['artifact_sha256'], lineage=spec['lineage'],
                    learning_status='BOUNDED_PARAMETER_UPDATE; NO_CODE_SELF_MODIFICATION',
                    reuse_condition='Same context, resource, unit and data kind; only later records in a new cycle',
                    prospective_validation='PENDING', wellbeing_effect='UNMEASURED', life_sustainment_effect='UNMEASURED')
