"""Public-data-only learning, immutable proposal bytes, and held-out evaluation."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from genius_adaptive import contextual
from . import model
from .model import require

ID = re.compile(r'[a-z0-9][a-z0-9-]{0,63}\Z')
SHA = re.compile(r'[0-9a-f]{64}\Z')
REVISION = re.compile(r'[0-9a-f]{40}\Z')


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def fingerprint(value):
    # Service receipt hashes omit the trailing newline.
    return digest(encoded(value)[:-1])


def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'DUPLICATE_KEY'); result[key] = value
        return result
    def bad(_):
        raise ValueError('NONFINITE_JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)


def local(root, name, prefix=None, maximum=2*1024*1024):
    require(type(name) is str and '\\' not in name, 'LOCAL_PATH')
    p = PurePosixPath(name)
    require(not p.is_absolute() and '..' not in p.parts and str(p) == name, 'LOCAL_PATH')
    require(not prefix or name.startswith(prefix), 'PATH_SCOPE')
    target = Path(root)
    for part in p.parts:
        target = target / part
        require(not target.is_symlink(), 'SYMLINK')
    require(target.is_file() and target.stat().st_size <= maximum, 'FILE_LIMIT')
    raw = target.read_bytes()
    require(len(raw) <= maximum, 'FILE_LIMIT')
    return raw


def identity(root):
    names = sorted(str(p.relative_to(root)) for directory in ('evolution/genius_evolution', 'evolution/tests')
                   for p in (Path(root)/directory).glob('*.py'))
    names += ['adaptive/genius_adaptive/contextual.py', '.github/workflows/code-evolution.yml']
    return {name: digest(local(root, name)) for name in names}


def request(root):
    active = strict(local(root, 'evolution/active-request.json', maximum=1024))
    require(set(active) == {'format', 'request'} and active['format'] == 'genius-evolution-active/1'
            and type(active['request']) is str and ID.fullmatch(active['request']), 'ACTIVE_REQUEST')
    name = 'evolution/requests/' + active['request'] + '.json'
    raw = local(root, name, maximum=8192); spec = strict(raw)
    fields = {'format', 'id', 'data_kind', 'publication', 'unit', 'baseline', 'warmup_count',
              'under_cost', 'over_cost', 'max_underprediction', 'max_overprediction', 'training', 'evaluation'}
    require(type(spec) is dict and set(spec) == fields, 'REQUEST_FIELDS')
    require(spec['format'] == 'genius-code-evolution-request/1' and spec['id'] == active['request'], 'REQUEST_ID')
    # v1 accepts the public synthetic bootstrap only; no service DB or credentials.
    require(spec['data_kind'] == 'synthetic' and spec['publication'] == 'PUBLIC_REPOSITORY_ONLY', 'PUBLIC_DATA_ONLY')
    require(type(spec['unit']) is str and 1 <= len(spec['unit']) <= 64, 'UNIT')
    for field, low, high in [('baseline', 0, model.LIMIT), ('warmup_count', 3, 10),
                            ('under_cost', 1, 1000), ('over_cost', 1, 1000),
                            ('max_underprediction', 0, model.LIMIT), ('max_overprediction', 0, model.LIMIT)]:
        require(type(spec[field]) is int and low <= spec[field] <= high, 'OBJECTIVE_BOUNDS')
    for split in ('training', 'evaluation'):
        ref = spec[split]
        require(type(ref) is dict and set(ref) == {'path', 'sha256'} and type(ref['sha256']) is str
                and SHA.fullmatch(ref['sha256']), 'DATA_REFERENCE')
    require(spec['training']['path'] != spec['evaluation']['path'] and
            spec['training']['sha256'] != spec['evaluation']['sha256'], 'SPLIT_REUSE')
    return spec, name, digest(raw)


def dataset(root, spec, split):
    ref = spec[split]; raw = local(root, ref['path'], 'evolution/data/', maximum=64*1024)
    require(digest(raw) == ref['sha256'], 'DATA_HASH')
    data = strict(raw)
    require(set(data) == {'format', 'split', 'data_kind', 'cases', 'provenance'} and
            data['format'] == 'genius-evolution-data/1' and data['split'] == split and
            data['data_kind'] == spec['data_kind'], 'DATA_SCHEMA')
    cases = data['cases']; require(type(cases) is list and 1 <= len(cases) <= 12, 'CASE_LIMIT')
    ids = set()
    for case in cases:
        require(type(case) is dict and set(case) == {'id', 'values'} and type(case['id']) is str
                and ID.fullmatch(case['id']) and case['id'] not in ids, 'CASE_ID')
        ids.add(case['id']); values = case['values']
        require(type(values) is list and spec['warmup_count'] + 3 <= len(values) <= 128 and
                all(type(v) is int and 0 <= v <= model.LIMIT for v in values), 'VALUES')
    p = data['provenance']
    require(type(p) is dict, 'PROVENANCE')
    if split == 'training':
        require(set(p) == {'kind', 'path', 'sha256'} and p['kind'] == 'public_context_probe', 'TRAINING_PROVENANCE')
        probe_raw = local(root, p['path'], 'adaptive/evidence/')
        require(digest(probe_raw) == p['sha256'], 'PROVENANCE_HASH')
        probe = strict(probe_raw)
        require(probe['status'] == 'PASS' and probe['scope'] == 'LIVE_SYNTHETIC_SERVICE_INTEGRATION'
                and probe['account_erased'] is True and probe['credential_revoked'] is True, 'PUBLIC_PROBE_SCOPE')
        forecast = probe['steps']['closed']; frozen = forecast['frozen']
        require(fingerprint(frozen) == forecast['sha256'] and frozen['data_kind'] == 'synthetic'
                and frozen['baseline'] == spec['baseline'] and frozen['unit'] == spec['unit']
                and frozen['warmup_count'] == spec['warmup_count']
                and frozen['max_underprediction'] == spec['max_underprediction']
                and frozen['format'] == 'resource_context_forecast_v1' and frozen['rule'] == contextual.RULE
                and frozen['scorer_identity']['sources']['contextual.py'] ==
                    digest(local(root, 'adaptive/genius_adaptive/contextual.py')), 'PROBE_PLAN')
        history, previous = [], forecast['sha256']
        for pair in forecast['pairs']:
            pred, obs = pair['prediction'], pair['observation']
            require(obs is not None and fingerprint(pred['receipt']) == pred['sha256'] and
                    pred['receipt']['previous_sha256'] == previous and fingerprint(obs['receipt']) == obs['sha256']
                    and obs['receipt']['previous_sha256'] == pred['sha256'], 'PROBE_CHAIN')
            prediction = contextual.predict(history, frozen)
            require(pred['receipt']['prediction'] == prediction, 'PROBE_PREDICTION')
            history.append(dict(**prediction, value=obs['receipt']['observation']['value']))
            previous = obs['sha256']
        report = forecast['report']
        require(fingerprint(report) == forecast['report_sha256'] and report['previous_sha256'] == previous,
                'PROBE_REPORT')
        expected_report = contextual.report(history, frozen)
        expected_report['format'] = 'resource_context_forecast_v1'
        for key, value in expected_report.items():
            require(report[key] == value, 'PROBE_SCORE')
        require(len(cases) == 1 and cases[0]['values'] == [row['value'] for row in history], 'PROBE_VALUES')
    else:
        require(set(p) == {'kind', 'statement'} and p['kind'] == 'designed_fixture' and
                type(p['statement']) is str and 1 <= len(p['statement']) <= 400, 'EVALUATION_PROVENANCE')
    return cases


def compare(cases, predictions, spec):
    rows = []
    for case, candidate in zip(cases, predictions):
        history, incumbent = [], []
        plan = dict(baseline=spec['baseline'], warmup_count=spec['warmup_count'],
                    max_underprediction=spec['max_underprediction'])
        for value in case['values']:
            prediction = contextual.predict(history, plan)
            incumbent.append(prediction['predictions']['adaptive'])
            history.append(dict(**prediction, value=value))
        n = spec['warmup_count']; values = case['values'][n:]
        before, after = model.loss(incumbent[n:], values, spec), model.loss(candidate[n:], values, spec)
        checks = dict(no_worse_loss=after['weighted_loss'] <= before['weighted_loss'],
                      no_worse_underprediction=after['max_underprediction'] <= before['max_underprediction'],
                      no_worse_overprediction=after['max_overprediction'] <= before['max_overprediction'],
                      within_under_limit=after['max_underprediction'] <= spec['max_underprediction'],
                      within_over_limit=after['max_overprediction'] <= spec['max_overprediction'])
        rows.append(dict(id=case['id'], incumbent=before, candidate=after, checks=checks,
                         candidate_predictions=candidate, incumbent_predictions=incumbent))
    return rows


def prepare(root, base, *, execute=True):
    root = Path(root)
    require(type(base) is str and REVISION.fullmatch(base), 'BASE_REVISION')
    spec, request_path, request_sha = request(root)
    sources = identity(root)
    proposal_id = fingerprint(dict(request_sha256=request_sha, sources=sources))[:24]
    training = dataset(root, spec, 'training')
    chosen, search = model.discover(training, spec)
    generated = model.render(chosen['model']); source_sha = digest(generated.encode())
    # Selection and source bytes are frozen BEFORE the evaluation data is loaded.
    candidate_seal = fingerprint(dict(model=chosen['model'], source_sha256=source_sha,
                                     training_sha256=spec['training']['sha256'], request_sha256=request_sha))
    evaluation = dataset(root, spec, 'evaluation')
    require(not ({c['id'] for c in training} & {c['id'] for c in evaluation}), 'SPLIT_ID_REUSE')
    require(not ({tuple(c['values']) for c in training} & {tuple(c['values']) for c in evaluation}), 'SPLIT_VALUES_REUSE')
    def predictions(cases):
        if execute:
            return model.execute(generated, chosen['model'], cases, spec['baseline'])
        return [[model.predict(chosen['model'], c['values'][:i], spec['baseline'])
                 for i in range(len(c['values']))] for c in cases]
    before = compare(training, predictions(training), spec)
    tested = compare(evaluation, predictions(evaluation), spec)
    train_gain = sum(r['candidate']['weighted_loss'] for r in before) < sum(r['incumbent']['weighted_loss'] for r in before)
    eval_gain = sum(r['candidate']['weighted_loss'] for r in tested) < sum(r['incumbent']['weighted_loss'] for r in tested)
    checks = dict(training_improvement=train_gain, evaluation_improvement=eval_gain,
                  every_evaluation_case_guarded=all(all(r['checks'].values()) for r in tested))
    eligible = all(checks.values())
    report = dict(format='genius-code-proposal/1', proposal_id=proposal_id, base_revision=base,
                  request_path=request_path, request_sha256=request_sha, sources=sources, request=spec,
                  limitation=dict(kind='OBSERVED_PREDICTION_ERROR', scope='SYNTHETIC',
                      incumbent_weighted_loss=sum(r['incumbent']['weighted_loss'] for r in before)),
                  model=chosen['model'], candidate_sha256=source_sha, candidate_seal=candidate_seal,
                  training_search=search, training=before, evaluation=tested, checks=checks,
                  decision='ELIGIBLE_FOR_REVIEW' if eligible else 'REJECTED_BY_EVALUATION',
                  promotion_eligible=eligible, production_activated=False, generalization='UNESTABLISHED',
                  wellbeing_effect='UNMEASURED', life_sustainment_effect='UNMEASURED',
                  evaluation_scope='PREDECLARED_SYNTHETIC_REGRESSION_SUITE',
                  execution_contract='EXACT_RENDERED_SOURCE_PLUS_INTEGER_REFERENCE',
                  isolation=dict(child_timeout_seconds=5, cpu_seconds=3, memory_mb=128,
                                 credentials='NONE', ci_network='DOCKER_NONE'))
    strategy_path = f'evolution/candidates/{proposal_id}.py'
    report_path = f'evolution/proposals/{proposal_id}/proposal.json'
    readme_path = f'evolution/proposals/{proposal_id}/README.md'
    failed = [r['id'] for r in tested if not all(r['checks'].values())]
    readme = (f'# Propuesta Genius {proposal_id}\n\nEstado: **{report["decision"]}**.\n\n'
              f'Generada automáticamente desde `{request_path}`. Código: `{strategy_path}`.\n'
              'La selección del programa usa sólo entrenamiento; la evaluación queda ligada por hashes.\n'
              f'Casos que no cumplen todas las guardas: {", ".join(failed) or "ninguno"}.\n\n'
              'El informe conserva resultados negativos y positivos. Los datos son sintéticos;\n'
              'no demuestra generalización, bienestar ni PVS. No activa código en producción.\n'
              'Una propuesta rechazada no puede promoverse bajo este contrato. Para otro objetivo\n'
              'se necesita una solicitud versionada antes de nuevas evaluaciones.\n')
    files = {strategy_path: generated, report_path: encoded(report).decode(), readme_path: readme}
    return dict(format='genius-code-publication/1', proposal_id=proposal_id, base_revision=base,
                files=files, hashes={name: digest(text.encode()) for name, text in files.items()})


def verify_bundle(root, bundle):
    require(type(bundle) is dict and set(bundle) == {'format', 'proposal_id', 'base_revision', 'files', 'hashes'}, 'BUNDLE_FIELDS')
    # Independent integer recomputation; never import/execute an artifact's Python.
    expected = prepare(root, bundle['base_revision'], execute=False)
    require(bundle == expected, 'BUNDLE_RECOMPUTATION')
    return expected


def tree_files(root, bundle):
    verify_bundle(root, bundle)
    manifest = strict(local(root, 'PUBLICATION_MANIFEST.json'))
    require(manifest.get('format') == 'genius-publication-files/1' and type(manifest.get('files')) is dict, 'PUBLICATION_MANIFEST')
    for name, sha in manifest['files'].items():
        require(digest(local(root, name, maximum=16*1024*1024)) == sha, 'BASE_MANIFEST_CHANGED')
    manifest['files'].update(bundle['hashes'])
    manifest['files'] = dict(sorted(manifest['files'].items()))
    return {**bundle['files'], 'PUBLICATION_MANIFEST.json': json.dumps(manifest, ensure_ascii=False, indent=2) + '\n'}


def audit_current(root):
    """Check a generated proposal already present in the current checkout.

    Old engine identities are historical, not silently certified by a new engine.
    This v1 checks the active proposal when present (including its PR checkout).
    """
    spec, _, request_sha = request(root)
    pid = fingerprint(dict(request_sha256=request_sha, sources=identity(root)))[:24]
    name = f'evolution/proposals/{pid}/proposal.json'
    if not (Path(root)/name).exists():
        return dict(status='NO_CURRENT_PROPOSAL_IN_CHECKOUT', proposal_id=pid)
    report = strict(local(root, name, maximum=128*1024))
    expected = prepare(root, report['base_revision'], execute=False)
    for path, text in expected['files'].items():
        require(local(root, path).decode() == text, 'PUBLISHED_PROPOSAL_CHANGED')
    return dict(status='CURRENT_PROPOSAL_VERIFIED', proposal_id=pid)
