#!/usr/bin/env python3
"""Portable taxia: orientation, balanced assignments, and self-reported outcomes."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'beta'))
from genius_beta.taxis import ACCESS, CAPABILITIES, GOALS, orient

STAGES = ('exposed', 'selected', 'executed', 'contributed', 'accepted')


def assignments(seed, units=30):
    if type(seed) is not int or type(units) is not int or units != 30:
        raise ValueError('Pilot design fixes 30 units; changing it requires a protocol revision')
    rng = random.Random(seed)
    rows = []
    for block in range(units // 3):
        variants = ['general', 'utility', 'question']
        rng.shuffle(variants)
        rows.extend(dict(unit=f'U{3*block+i+1:03d}', block=block+1, variant=v)
                    for i, v in enumerate(variants))
    return dict(format='genius-taxis-assignment/1', seed=seed, units=rows,
                status='PLANNED_NOT_EXECUTED',
                note='Freeze source commit, model, tasks, tools, time/token limits, consent and budget before enrollment. Each block uses the same task and model configuration in fresh sessions.')


def report(plan, events):
    """Validate an opt-in event ledger. Artifact references remain unverified claims."""
    if plan.get('format') != 'genius-taxis-assignment/1':
        raise ValueError('Invalid assignment format')
    expected = assignments(plan.get('seed'))
    if plan.get('units') != expected['units']:
        raise ValueError('Assignments differ from the frozen seed')
    if not isinstance(events, list):
        raise ValueError('Events must be a JSON list')
    units = {row['unit']: row for row in plan['units']}
    progress = {uid: set() for uid in units}
    independence = {}
    seen = set()
    for event in events:
        if not isinstance(event, dict) or set(event) != {'unit', 'stage', 'evidence_ref', 'relationship', 'consent'}:
            raise ValueError('Unexpected or missing event fields')
        uid, stage = event['unit'], event['stage']
        if not isinstance(uid, str) or uid not in units or not isinstance(stage, str) or stage not in STAGES:
            raise ValueError('Unknown unit or stage')
        key = (uid, stage)
        if key in seen:
            raise ValueError('Duplicate unit/stage')
        seen.add(key)
        if event['consent'] is not True or event['relationship'] not in ('internal', 'external_declared'):
            raise ValueError('Explicit measurement consent and relationship required')
        if uid in independence and independence[uid] != event['relationship']:
            raise ValueError('Relationship cannot change within a unit')
        independence[uid] = event['relationship']
        ref = event['evidence_ref']
        if not isinstance(ref, str) or not 1 <= len(ref) <= 300:
            raise ValueError('An evidence reference is required')
        previous = STAGES[:STAGES.index(stage)]
        if not set(previous) <= progress[uid]:
            raise ValueError('Stages must be reported in order; missing events are not failures')
        progress[uid].add(stage)
    groups = {}
    for relationship in ('internal', 'external_declared'):
        groups[relationship] = {}
        for variant in ('general', 'utility', 'question'):
            ids = [uid for uid, row in units.items() if row['variant'] == variant and independence.get(uid) == relationship]
            counts = {s: sum(s in progress[uid] for uid in ids) for s in STAGES}
            groups[relationship][variant] = dict(reported_counts=counts,
                reported_execution_per_exposure=(counts['executed']/counts['exposed'] if counts['exposed'] else None))
    return dict(format='genius-taxis-report/1', groups=groups,
                planned_units=len(units), units_without_exposure=sum('exposed' not in p for p in progress.values()),
                event_log_sha256=hashlib.sha256(json.dumps(events, sort_keys=True).encode()).hexdigest(),
                verification='SELF_REPORTED_ONLY: references are not fetched or executed; review receipts, contribution acceptance and independence separately.',
                attraction_demonstrated=False, independent_adoption_verified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('orient')
    p.add_argument('--goal', choices=GOALS, default='explore')
    p.add_argument('--capability', choices=CAPABILITIES, action='append', default=[])
    p.add_argument('--access', choices=ACCESS, default='read')
    p.add_argument('--limit', type=int, default=3)
    p = sub.add_parser('plan'); p.add_argument('--seed', type=int, required=True)
    p = sub.add_parser('report'); p.add_argument('plan', type=Path); p.add_argument('events', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'orient':
            value = orient(args.goal, args.capability, args.access, args.limit)
        elif args.command == 'plan': value = assignments(args.seed)
        else: value = report(json.loads(args.plan.read_text()), json.loads(args.events.read_text()))
        print(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps(dict(error=str(exc)), ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
