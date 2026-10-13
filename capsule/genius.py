#!/usr/bin/env python3
"""Portable Genius host interface. Standard library; no credentials or network."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
for folder in ('kernel', 'twin'):
    sys.path.insert(0, str(ROOT / folder))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError('Non-finite JSON number: ' + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + '\n').encode()


def local_file(root, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute() or '..' in Path(name).parts:
        raise ValueError('Expected relative artifact path')
    p = (root / name).resolve()
    if not p.is_relative_to(root.resolve()) or not p.is_file():
        raise ValueError('Artifact missing or outside bundle: ' + name)
    return p


def evidence_record(record):
    if not isinstance(record, dict) or record.get('format') != 'genius-case-evidence/1':
        raise ValueError('Expected genius-case-evidence/1')
    for field in ('case_id', 'question', 'context', 'data_authority', 'observed_at'):
        if not isinstance(record.get(field), str) or not record[field].strip():
            raise ValueError('Evidence requires ' + field)
    if record.get('origin') not in ('real', 'synthetic', 'mixed'):
        raise ValueError('Origin must distinguish real, synthetic or mixed')
    for field in ('observations', 'assumptions', 'unknowns', 'sources'):
        if not isinstance(record.get(field), list):
            raise ValueError('Evidence requires list: ' + field)
    if record['origin'] in ('real', 'mixed') and (not record['sources'] or not record['observations']):
        raise ValueError('Real context requires observations and sources')
    source_ids = set()
    for source in record['sources']:
        if not isinstance(source, dict) or any(not isinstance(source.get(k), str) or not source[k].strip()
                for k in ('id', 'reference', 'accessed_at')) or source['id'] in source_ids:
            raise ValueError('Sources require unique id, reference and accessed_at')
        source_ids.add(source['id'])
    for observation in record['observations']:
        if not isinstance(observation, dict) or not observation.get('statement') or observation.get('source_id') not in source_ids:
            raise ValueError('Observation requires statement and an identified source')
    if record.get('empirical_status') not in ('NOT_ASSESSED', 'PROTOCOL_DEFINED', 'OBSERVATIONS_COLLECTED', 'EXTERNALLY_REVIEWED'):
        raise ValueError('Explicit empirical status required')
    if record.get('publication') not in ('public', 'private'):
        raise ValueError('Explicit evidence publication scope required')
    return record


def evaluate(model_path, evidence_path, output, seconds=90):
    from genius_twin.process_runner import ProcessEvaluator
    from genius_twin.registry import execution_identity, validate, D1
    raw = model_path.read_bytes()
    model = strict_json(raw)
    evidence = evidence_record(strict_json(evidence_path.read_bytes()))
    validate(model)
    if model['profile'] == D1 and evidence['origin'] != 'synthetic':
        raise ValueError('Fixed synthetic template cannot represent a real case')
    if evidence['origin'] == 'real' and any(a.get('kind') == 'SYNTHETIC' for a in model.get('assumptions', [])):
        raise ValueError('Synthetic premises require mixed or synthetic origin')
    if output.exists():
        raise ValueError('Output directory must be new; previous receipts are immutable')
    result = ProcessEvaluator(timeout=seconds)(model)
    if result.get('verification', {}).get('valid') is not True:
        raise ValueError('Unverified execution result')
    artifacts = {'model.json': raw, 'evidence.json': encoded(evidence), 'evaluation.json': encoded(result)}
    receipt = {'format': 'genius-capsule-run/1', 'created_at': datetime.now(timezone.utc).isoformat(),
               'case_id': evidence['case_id'], 'origin': evidence['origin'],
               'claim': 'CONSEQUENCES_CONDITIONAL_ON_MODEL', 'empirical_validation_by_this_execution': False,
               'identity': execution_identity(model['profile'], {'timeout_seconds': seconds}),
               'files': {name: digest(data) for name, data in artifacts.items()}}
    output.mkdir(parents=True, exist_ok=False)
    for name, data in artifacts.items():
        (output / name).write_bytes(data)
    (output / 'receipt.json').write_bytes(encoded(receipt))
    return {'status': 'COMPLETE', 'receipt': str(output / 'receipt.json'), 'origin': evidence['origin'],
            'mathematical_verification': True, 'empirical_validation': False}


def verify(folder):
    from genius_kernel import verify_result
    from genius_twin.registry import validate, execution_identity
    receipt = strict_json((folder / 'receipt.json').read_bytes())
    if receipt.get('format') != 'genius-capsule-run/1' or set(receipt.get('files', {})) != {'model.json', 'evidence.json', 'evaluation.json'}:
        raise ValueError('Invalid run manifest')
    for name, expected in receipt['files'].items():
        if digest(local_file(folder, name).read_bytes()) != expected:
            raise ValueError('Artifact integrity mismatch: ' + name)
    model = strict_json((folder / 'model.json').read_bytes())
    validate(model)
    evidence = evidence_record(strict_json((folder / 'evidence.json').read_bytes()))
    if (receipt.get('origin') != evidence['origin'] or receipt.get('case_id') != evidence['case_id']
            or receipt.get('empirical_validation_by_this_execution') is not False
            or receipt.get('claim') != 'CONSEQUENCES_CONDITIONAL_ON_MODEL'):
        raise ValueError('Receipt claims are inconsistent with evidence or execution')
    identity = receipt.get('identity', {})
    expected_identity = execution_identity(model['profile'], identity.get('execution_context'))
    if identity != expected_identity:
        raise ValueError('Execution source differs; use the recorded source version')
    result = strict_json((folder / 'evaluation.json').read_bytes())
    # Check each native run and that it was actually compiled from this model.
    if model['profile'] != 'STOCK_FLOW_FINITE_V1':
        raise ValueError('Independent capsule verification currently supports STOCK_FLOW_FINITE_V1')
    from genius_twin.stockflow_compiler import compile_model
    from genius_twin.stockflow import canonical_json
    runs = result.get('native_runs', {})
    if set(runs) != {'robust', 'possible'}:
        raise ValueError('Expected both native CAG runs')
    for mode, run in runs.items():
        instance, _ = compile_model(model, cag_mode=mode)
        native = canonical_json(instance)
        if native != run['native_input_json']:
            raise ValueError('Native input is not bound to model')
        if verify_result(native.encode(), run['native_result']).get('valid') is not True:
            raise ValueError('Native result verification failed')
    # The product summary is also bound to the native results by recomputing it.
    from genius_twin.process_runner import ProcessEvaluator
    fresh = ProcessEvaluator()(model)
    if fresh != result:
        raise ValueError('Evaluation envelope differs from native recomputation')
    return {'status': 'VERIFIED', 'native_runs': len(runs), 'empirical_validation': False}


def contribution(path):
    data = strict_json(path.read_bytes())
    if data.get('format') != 'genius-contribution/1':
        raise ValueError('Expected genius-contribution/1')
    for field in ('id', 'author', 'summary', 'base_revision', 'kind', 'claim', 'reproduction'):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError('Contribution requires ' + field)
    if not isinstance(data.get('artifacts'), list) or not data['artifacts']:
        raise ValueError('Contribution requires artifacts')
    names = set()
    for item in data['artifacts']:
        name = item['path']
        if name in names or digest(local_file(path.parent, name).read_bytes()) != item['sha256']:
            raise ValueError('Duplicate or changed contribution artifact')
        names.add(name)
    if data.get('review_status') not in ('PROPOSED', 'REPRODUCED', 'ACCEPTED', 'REJECTED'):
        raise ValueError('Review status required')
    return {'status': 'INTEGRITY_VERIFIED', 'contribution': data['id'], 'review_status': data['review_status'],
            'commands_executed': False, 'accepted_by_this_check': False}


def handoff(path):
    data = strict_json(path.read_bytes())
    for field in ('mission', 'host', 'base_revision', 'next_work'):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError('Handoff requires ' + field)
    if data.get('format') != 'genius-handoff/1' or not isinstance(data.get('contributions'), list):
        raise ValueError('Invalid handoff format')
    for item in data['contributions']:
        contribution(local_file(path.parent, item))
    return {'status': 'HANDOFF_READY', 'next_work': data['next_work'], 'contributions': len(data['contributions']),
            'authority_transfer': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    subs.add_parser('capabilities')
    p = subs.add_parser('evaluate'); p.add_argument('model', type=Path); p.add_argument('--evidence', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True); p.add_argument('--seconds', type=int, default=90)
    for command in ('verify', 'contribution', 'handoff'):
        p = subs.add_parser(command); p.add_argument('path', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'capabilities': result = strict_json((ROOT / 'capsule/manifest.json').read_bytes())
        elif args.command == 'evaluate': result = evaluate(args.model, args.evidence, args.out, args.seconds)
        elif args.command == 'verify': result = verify(args.path)
        elif args.command == 'contribution': result = contribution(args.path)
        else: result = handoff(args.path)
        print(encoded(result).decode(), end='')
    except (ValueError, KeyError, OSError, RuntimeError, TimeoutError) as error:
        print(json.dumps({'status': 'ERROR', 'message': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
