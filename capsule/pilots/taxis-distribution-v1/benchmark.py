#!/usr/bin/env python3
"""Measure a pinned public source edition; no network, extraction or agent calls."""
import argparse
import copy
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import platform
import random
import statistics
import tarfile
import time
import zipfile
import zlib

SOURCE_COMMIT = '2571e0d54a4a3b1a7f25bf0398582b0b3eea4482'
MANIFEST_SHA256 = 'dbf40982b6d492fa7d594a5e2024dea08e4064e850f2519f144c2a35d5573bda'
PREFIX = 'genius-decision-open/'
FORMATS = ('tar', 'gzip', 'zip')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def source_files(source):
    manifest_raw = (source / 'PUBLICATION_MANIFEST.json').read_bytes()
    if sha(manifest_raw) != MANIFEST_SHA256:
        raise ValueError('Use the clean source edition at the pinned commit')
    expected = json.loads(manifest_raw)['files']
    expected['PUBLICATION_MANIFEST.json'] = MANIFEST_SHA256
    actual = {}
    for path in source.rglob('*'):
        if path.is_symlink():
            raise ValueError('Source symlinks are not supported')
        if path.is_file():
            actual[path.relative_to(source).as_posix()] = path.read_bytes()
    if set(actual) != set(expected) or any(sha(actual[p]) != h for p, h in expected.items()):
        raise ValueError('Source inventory or hashes differ from the pinned edition')
    return actual


def encode(kind, files):
    out = io.BytesIO()
    if kind in ('tar', 'gzip'):
        with tarfile.open(fileobj=out, mode='w', format=tarfile.PAX_FORMAT) as archive:
            for name, raw in sorted(files.items()):
                info = tarfile.TarInfo(PREFIX + name)
                info.size, info.mode, info.mtime = len(raw), 0o644, 0
                archive.addfile(info, io.BytesIO(raw))
        raw = out.getvalue()
        return gzip.compress(raw, mtime=0) if kind == 'gzip' else raw
    if kind != 'zip':
        raise ValueError('Unsupported archive format')
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(PREFIX + name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    return out.getvalue()


def decode_and_hash(kind, raw):
    result = {}
    if kind == 'zip':
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            for member in archive.infolist():
                if member.filename in result or member.is_dir():
                    raise ValueError('Duplicate or non-file archive entry')
                result[member.filename] = sha(archive.read(member))
    else:
        with tarfile.open(fileobj=io.BytesIO(raw), mode='r:*') as archive:
            for member in archive:
                if member.name in result or not member.isfile():
                    raise ValueError('Duplicate or non-file archive entry')
                result[member.name] = sha(archive.extractfile(member).read())
    return result


def timed(fn):
    wall, cpu = time.perf_counter_ns(), time.process_time_ns()
    value = fn()
    return value, {'wall_ns': time.perf_counter_ns() - wall, 'cpu_ns': time.process_time_ns() - cpu}


def measure(source, output):
    if output.exists():
        raise ValueError('Output must be new; preserve earlier measurements')
    files = source_files(source)
    expected = {PREFIX + p: sha(raw) for p, raw in files.items()}
    rows, artifacts = [], {}
    for kind in FORMATS:
        raw = encode(kind, files)
        if decode_and_hash(kind, raw) != expected:
            raise ValueError('Warm-up round trip failed')
        artifacts[kind] = {'bytes': len(raw), 'sha256': sha(raw)}
    rng = random.Random(20261014)
    for repeat in range(1, 6):
        order = list(FORMATS)
        rng.shuffle(order)
        for position, kind in enumerate(order, 1):
            raw, creation = timed(lambda: encode(kind, files))
            decoded, reading = timed(lambda: decode_and_hash(kind, raw))
            if decoded != expected or sha(raw) != artifacts[kind]['sha256']:
                raise ValueError('Round-trip integrity or reproducibility failed')
            rows.append({'repeat': repeat, 'position': position, 'format': kind,
                         'create': creation, 'read_and_hash': reading, 'integrity_verified': True})
    for kind in FORMATS:
        samples = [r for r in rows if r['format'] == kind]
        artifacts[kind]['median_read_cpu_ns'] = statistics.median(r['read_and_hash']['cpu_ns'] for r in samples)
        artifacts[kind]['median_create_cpu_ns'] = statistics.median(r['create']['cpu_ns'] for r in samples)
    now = datetime.now(timezone.utc).isoformat()
    measurement = {
        'format': 'genius-distribution-benchmark/1', 'source_commit': SOURCE_COMMIT,
        'manifest_sha256': MANIFEST_SHA256, 'observed_at': now, 'files': len(files),
        'environment': {'python': platform.python_version(), 'implementation': platform.python_implementation(),
                        'system': platform.system(), 'machine': platform.machine(),
                        'zlib_compile_version': zlib.ZLIB_VERSION, 'zlib_runtime_version': zlib.ZLIB_RUNTIME_VERSION},
        'method': 'In-memory creation and reading/hash verification of every file; one warm-up per format, five measured repetitions in seeded order. No network or disk extraction.',
        'artifacts': artifacts, 'samples': rows,
        'limits': ['CPU timings vary across runs and machines; medians are observations, not universal constants.',
                   'Wall time includes scheduling; CPU time is local process time.',
                   'Only this Python reader was tested; external-client compatibility is unknown.',
                   'Network latency, transfer success, retries, peak memory and disk extraction were not measured.'],
        'experiment_sessions': 0, 'independent_external_operators': 0
    }
    model = copy.deepcopy(json.loads(files['capsule/cases/distribution/model.json']))
    max_bytes = max(a['bytes'] for a in artifacts.values())
    max_cpu = max(a['median_read_cpu_ns'] for a in artifacts.values())
    model['name'] = 'Distribución de cápsula publicada — bytes y CPU de lectura observados'
    model['stocks'][0].update(initial=f'{max_bytes}/1', capacity=f'{max_bytes}/1')
    model['stocks'].append({'id': 'cpu_remaining', 'label': 'Margen comparativo de CPU de lectura',
                           'unit': 'cpu_nanosecond', 'kind': 'persistent',
                           'initial': f'{max_cpu}/1', 'capacity': f'{max_cpu}/1'})
    for action in model['actions']:
        a = artifacts[action['id'].removeprefix('send_')]
        action['withdrawals'] = {'remaining': f"{a['bytes']}/1", 'cpu_remaining': f"{a['median_read_cpu_ns']}/1"}
    model['welfare'].append({'carrier': 'project', 'dimension': 'read_cpu_margin',
                            'label': 'Margen de CPU local observada; sin agregación con bytes',
                            'stock': 'cpu_remaining', 'direction': 'higher'})
    model['task']['conditions'].append({'stock': 'cpu_remaining', 'op': 'ge', 'threshold': '0/1'})
    model['task']['label'] = 'Conservar todas las fuentes dentro de presupuestos comparativos declarados'
    model['assumptions'] = [
        {'id': 'Measurement', 'kind': 'CALIBRATION', 'statement': 'Tamaños y mediana de CPU de lectura/hash medidos en measurement.json. Análisis retrospectivo del snapshot.', 'provenance': 'Medición interna directa; no evaluación externa'},
        {'id': 'Scope', 'kind': 'MODEL', 'statement': 'Una lectura local completa, en memoria, con este Python. Excluye red, reintentos, memoria máxima, escritura a disco y otros clientes.', 'provenance': 'Método de benchmark.py'},
        {'id': 'Criterion', 'kind': 'NORMATIVE', 'statement': 'Reducir bytes y CPU de lectura sin sumar unidades ni inventar ponderaciones. Presupuestos comparativos iguales al máximo observado por dimensión; no son límites de producción.', 'provenance': 'Criterio técnico propuesto; sujeto a revisión del receptor'},
        {'id': 'SnapshotLaw', 'kind': 'PROBABILITY', 'statement': 'Masa unitaria sobre el inventario observado. No estima distribuciones futuras de CPU, éxito de red ni PVS.', 'provenance': 'Modelo determinista de observaciones ya recogidas'}
    ]
    evidence = {
        'format': 'genius-case-evidence/1', 'case_id': 'genius-distribution-public-2026-10-14',
        'question': '¿Qué formatos preservan las fuentes y qué compromisos presentan entre bytes y CPU de lectura local?',
        'context': 'Decisión operacional real sobre la cápsula pública; análisis retrospectivo interno.',
        'origin': 'real', 'observed_at': now, 'data_authority': 'Fuentes Genius públicas Apache-2.0; mediciones locales sin datos personales.',
        'sources': [{'id': 'measurement', 'reference': 'measurement.json', 'accessed_at': now},
                    {'id': 'source', 'reference': 'https://github.com/pedrosalvadeo/genius-decision-open/tree/' + SOURCE_COMMIT, 'accessed_at': now}],
        'observations': [{'source_id': 'measurement', 'statement': f"{kind}: {a['bytes']} bytes, SHA256 {a['sha256']}, mediana CPU de lectura {a['median_read_cpu_ns']} ns; 409 archivos íntegros en cada repetición."} for kind, a in artifacts.items()],
        'assumptions': [a['statement'] for a in model['assumptions']], 'unknowns': measurement['limits'],
        'empirical_status': 'OBSERVATIONS_COLLECTED', 'publication': 'public'
    }
    # Direct two-coordinate Pareto comparison, independent of Genius machinery.
    coords = {k: (a['bytes'], a['median_read_cpu_ns']) for k, a in artifacts.items()}
    frontier = sorted(k for k, v in coords.items() if not any(
        other != k and all(a <= b for a, b in zip(w, v)) and any(a < b for a, b in zip(w, v))
        for other, w in coords.items()))
    baseline = {'format': 'genius-distribution-baseline/1', 'minimize': ['bytes', 'median_read_cpu_ns'],
                'coordinates': coords, 'pareto_frontier': frontier,
                'bytes_only_choice': min(artifacts, key=lambda k: artifacts[k]['bytes']),
                'selection_rule': 'Select only a singleton Pareto frontier; otherwise preserve trade-offs.',
                'scope': 'Observed inventory only; excludes the common initial state and equal capability/task cells.'}
    output.mkdir(parents=True)
    for name, value in [('measurement', measurement), ('model', model), ('evidence', evidence), ('baseline', baseline)]:
        (output / (name + '.json')).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    return {'status': 'MEASURED_NOT_AN_AGENT_EXPERIMENT', 'files': len(files), 'artifacts': artifacts,
            'pareto_frontier': frontier, 'output': str(output)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(measure(args.source, args.out), ensure_ascii=False, indent=2))
