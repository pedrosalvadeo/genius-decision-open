"""Past-only prediction strategies and a guarded context-dependent selector.

This is an operator-side experiment, not a deployed mission or a claim about
future safety. Every score compares predictions made before the target arrived.
"""
import json
from pathlib import Path

RULE = 'PAST_ONLY_CONTEXT_SELECTOR_V1'
ORDER = ('baseline', 'rolling_median', 'last_value', 'context_median')
WINDOW = 3
MIN_CONTEXT_SCORES = 3


def median(values):
    return sorted(values)[(len(values) - 1) // 2]


def metrics(rows, name):
    errors = [abs(row['predictions'][name] - row['value']) for row in rows]
    return dict(count=len(rows), absolute_error_sum=sum(errors),
                max_underprediction=max((max(0, row['value'] - row['predictions'][name])
                                         for row in rows), default=0))


def guards(candidate, baseline, limit):
    return dict(lower_error=candidate['absolute_error_sum'] < baseline['absolute_error_sum'],
                no_worse_underprediction=candidate['max_underprediction'] <= baseline['max_underprediction'],
                within_declared_limit=candidate['max_underprediction'] <= limit)


def predict(history, plan):
    """History contains only completed earlier predictions and observations."""
    baseline = plan['baseline']
    context = ('unknown' if not history else
               'previous_above_baseline' if history[-1]['value'] > baseline else
               'previous_at_or_below_baseline')
    values = [row['value'] for row in history]
    matching = [row['value'] for row in history if row['context'] == context]
    rolling = median(values[-WINDOW:]) if values else baseline
    predictions = dict(baseline=baseline, rolling_median=rolling,
                       last_value=values[-1] if values else baseline,
                       context_median=median(matching[-WINDOW:]) if len(matching) >= 2 else rolling)
    # Warmup values initialize predictors, but never count as selection evidence.
    prior = [row for row in history if row['phase'] == 'scored' and row['context'] == context]
    comparison = {name: metrics(prior, name) for name in ORDER}
    checks = {name: guards(comparison[name], comparison['baseline'], plan['max_underprediction'])
              for name in ORDER[1:]}
    eligible = [name for name in ORDER[1:] if len(prior) >= MIN_CONTEXT_SCORES and all(checks[name].values())]
    selected = min(eligible, key=lambda name: (comparison[name]['absolute_error_sum'], ORDER.index(name))) if eligible else 'baseline'
    predictions['adaptive'] = predictions[selected]
    return dict(context=context, predictions=predictions, selected=selected,
                selection_count=len(prior), selection_comparison=comparison, selection_checks=checks,
                context_fallback=len(matching) < 2,
                phase='warmup' if len(history) < plan['warmup_count'] else 'scored')


def native_comparison(comparison):
    """Verify the measured loss comparison with the existing exact native core."""
    from genius_adaptive import calibration
    from genius_twin.registry import evaluate
    model = json.loads(Path(calibration.__file__).with_name('distribution_model.json').read_text())
    budget = max(row['absolute_error_sum'] for row in comparison.values())
    model['name'] = 'Comparación de predicciones anteriores a cada observación'
    model['stocks'][0].update(label='Margen de error observado', unit='millisecond_error',
                              initial=f'{budget}/1', capacity=f'{budget}/1')
    model['capabilities'][0]['label'] = 'Conservar predicciones auditables'
    model['actions'] = [dict(id='use_' + name, label=name, requires=['deliver'],
        withdrawals={'remaining': str(row['absolute_error_sum']) + '/1'}, deposits={},
        add_capabilities=[], remove_capabilities=[]) for name, row in comparison.items()]
    model['policies'] = [dict(id=name, label=name, default_action='use_' + name, rules=[]) for name in comparison]
    model['scenarios'][0]['label'] = 'Mismas observaciones recibidas después de las predicciones'
    model['welfare'][0].update(dimension='error_margin', label='Menor error; criterio operacional')
    model['task']['label'] = 'Comparar errores medidos, sin inferir beneficio futuro'
    model['assumptions'] = [dict(id='Scope', kind='MODEL',
        statement='El margen representa error observado, no bienestar ni PVS. La masa unitaria describe esta comparación ya observada; no estima el futuro.',
        provenance=RULE), dict(id='Criterion', kind='NORMATIVE',
        statement='Menor error absoluto sobre los mismos objetivos. Las guardas adicionales y la selección histórica se comprueban fuera del modelo.', provenance=RULE)]
    result = evaluate(model)
    best = [name for name, row in comparison.items() if row['absolute_error_sum'] ==
            min(entry['absolute_error_sum'] for entry in comparison.values())]
    if (result['verification']['valid'] is not True or
            result['canonical_results']['decision']['selected'] != (best[0] if len(best) == 1 else None)):
        raise ValueError('NATIVE_ARITHMETIC_DISAGREEMENT')
    return result


def report(history, plan):
    rows = [row for row in history if row['phase'] == 'scored']
    if len(rows) != plan['scored_count']:
        raise ValueError('INCOMPLETE_STUDY')
    comparison = {name: metrics(rows, name) for name in (*ORDER, 'adaptive')}
    checks = guards(comparison['adaptive'], comparison['baseline'], plan['max_underprediction'])
    return dict(format='genius-context-report/1', rule=RULE, comparison=comparison, checks=checks,
                outcome='OBSERVED_GUARDED_IMPROVEMENT' if all(checks.values()) else 'NO_CONFIRMED_IMPROVEMENT',
                selected_counts={name: sum(row['selected'] == name for row in rows) for name in ORDER},
                baseline_within_declared_limit=comparison['baseline']['max_underprediction'] <= plan['max_underprediction'],
                context_counts={ctx: sum(row['context'] == ctx for row in rows) for ctx in sorted({row['context'] for row in rows})},
                native=native_comparison(comparison),
                interpretation='Adaptive policy assessed as executed; shadow strategy scores are descriptive, not a post-hoc policy choice',
                deployment='OPERATOR_ONLY', generalization='UNKNOWN', source_attestation='NONE',
                wellbeing_effect='UNMEASURED', life_sustainment_effect='UNMEASURED')
