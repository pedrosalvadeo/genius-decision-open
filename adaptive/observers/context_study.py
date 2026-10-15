"""On-demand HTTP study: durable past-only predictions, then measurements.

Local immutable receipts are operator evidence, not a third-party timestamp.
An interrupted measurement is never replaced; the attempt remains reviewable.
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import platform

from genius_adaptive.journal import exclusive, publish
from genius_twin.registry import STOCKFLOW, execution_identity
from . import http_latency as source, strategies


def identity():
    from genius_adaptive import journal, calibration
    files = [Path(__file__), Path(source.__file__), Path(strategies.__file__),
             Path(journal.__file__), Path(calibration.__file__).with_name('distribution_model.json')]
    return dict(python=platform.python_version(), source=source.contract(),
                files={path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
                native=execution_identity(STOCKFLOW))


def validate_plan(plan):
    if not isinstance(plan, dict) or set(plan) != {'format', 'rule', 'baseline', 'baseline_reference',
            'max_underprediction', 'warmup_count', 'scored_count', 'context', 'strategies', 'selection', 'stopping'}:
        raise ValueError('PLAN_FIELDS')
    if (plan['format'] != 'genius-context-study/1' or plan['rule'] != strategies.RULE or
            plan['context'] != 'PREVIOUS_VALUE_GT_FROZEN_BASELINE' or plan['strategies'] != list(strategies.ORDER) or
            plan['selection'] != 'PAST_SCORED_SAME_CONTEXT_MIN3_GUARDED_LOWEST_ERROR_FIXED_TIES' or
            plan['stopping'] != 'FIXED_COUNT_OR_FIRST_FAILED_OR_UNKNOWN_MEASUREMENT'):
        raise ValueError('PLAN_RULE')
    for key, low, high in (('baseline', 0, 1000000), ('max_underprediction', 0, 1000000),
                           ('warmup_count', 3, 10), ('scored_count', 6, 30)):
        if type(plan[key]) is not int or not low <= plan[key] <= high:
            raise ValueError('PLAN_RANGE')
    if not isinstance(plan['baseline_reference'], str) or not 1 <= len(plan['baseline_reference']) <= 500:
        raise ValueError('PLAN_BASELINE_REFERENCE')


def instant(value):
    when = datetime.fromisoformat(value)
    if when.tzinfo is None:
        raise ValueError('TIMEZONE_REQUIRED')
    return when


class Study:
    def __init__(self, directory, plan, *, sampler=None, wall=source.utc_now):
        validate_plan(plan)
        self.directory, self.plan = Path(directory), json.loads(json.dumps(plan))
        self.sampler, self.wall = sampler or source.sample, wall
        self.binding = dict(plan=self.plan, identity=identity())
        self.entries = []

    def load(self):
        if self.directory.is_symlink() or any(path.is_symlink() for path in self.directory.rglob('*')):
            raise ValueError('STATE_SYMLINK')
        entries, previous, last_time = [], None, None
        paths = sorted((self.directory / 'events').glob('*.json'))
        for number, path in enumerate(paths):
            if path.name != f'{number:04d}.json' or path.stat().st_size > 1024 * 1024:
                raise ValueError('EVENT_SEQUENCE')
            item = json.loads(path.read_text())
            event = item['event']
            when = instant(event['at'])
            if (source.digest(event) != item['sha256'] or event['previous_sha256'] != previous or
                    event['sequence'] != number or (last_time is not None and when <= last_time)):
                raise ValueError('EVENT_INTEGRITY')
            entries.append(item)
            previous, last_time = item['sha256'], when
        self.entries = entries
        if entries and (entries[0]['event']['kind'] != 'PLAN' or entries[0]['event']['body'] != self.binding):
            raise ValueError('PLAN_OR_CODE_CHANGED')

    def append(self, kind, body):
        at = self.wall()
        if self.entries and instant(at) <= instant(self.entries[-1]['event']['at']):
            raise ValueError('EVENT_CLOCK_NOT_ADVANCING')
        event = dict(sequence=len(self.entries), previous_sha256=self.entries[-1]['sha256'] if self.entries else None,
                     at=at, kind=kind, body=body)
        item = dict(event=event, sha256=source.digest(event))
        publish(self.directory / 'events' / f'{len(self.entries):04d}.json', (source.canonical(item) + '\n').encode())
        self.entries.append(item)
        return event

    def validate_sample(self, item, intent, saved_at):
        measurement, observation = item['measurement'], item['observation']
        if source.digest(measurement) != item['sha256']:
            raise ValueError('SOURCE_HASH')
        if (measurement['id'] != intent['body']['sample_id'] or
                measurement['source_contract_sha256'] != source.digest(self.binding['identity']['source']) or
                measurement['target'] != source.TARGET or observation != source.observation(measurement)):
            raise ValueError('SOURCE_MAPPING')
        if not (instant(intent['at']) < instant(measurement['started_at']) <
                instant(measurement['completed_at']) <= instant(saved_at)):
            raise ValueError('SOURCE_CHRONOLOGY')
        if measurement['outcome'] != 'OBSERVED':
            raise ValueError('SOURCE_SAMPLE_REJECTED')
        elapsed, value = measurement['elapsed_ns'], measurement['rounded_milliseconds']
        if (type(elapsed) is not int or elapsed < 0 or type(value) is not int or
                not 0 <= value <= 1000000 or value != (elapsed + 999999) // 1000000 or
                measurement['http_status'] != 200 or measurement['failure'] is not None or
                measurement['health'] != dict(status='ok', backup='ok', suspended=False) or
                not 0 <= measurement['response_bytes'] <= source.BODY_LIMIT):
            raise ValueError('SOURCE_VALUE')
        return value

    def replay(self):
        history, pending, result = [], None, None
        for entry in self.entries[1:]:
            event = entry['event']
            if result is not None:
                raise ValueError('EVENT_AFTER_REPORT')
            if event['kind'] == 'PREDICT' and pending is None:
                if len(history) >= self.plan['warmup_count'] + self.plan['scored_count']:
                    raise ValueError('EXTRA_MEASUREMENT')
                expected = dict(sample_id=f'context-{len(history):03d}', **strategies.predict(history, self.plan))
                if event['body'] != expected:
                    raise ValueError('PREDICTION_NOT_PAST_ONLY')
                pending = event
            elif event['kind'] == 'OBSERVE' and pending is not None:
                value = self.validate_sample(event['body'], pending, event['at'])
                history.append(dict(**pending['body'], value=value))
                pending = None
            elif event['kind'] == 'REPORT' and pending is None:
                result = strategies.report(history, self.plan)
                if event['body'] != result:
                    raise ValueError('REPORT_CHANGED')
            else:
                raise ValueError('EVENT_ORDER')
        return history, pending, result

    def run(self):
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.directory.is_symlink() or (self.directory / 'mission.lock').is_symlink():
            raise ValueError('STATE_SYMLINK')
        with exclusive(self.directory):
            self.load()
            if not self.entries:
                self.append('PLAN', self.binding)
            history, pending, result = self.replay()
            if pending:
                raise ValueError('MEASUREMENT_OUTCOME_UNKNOWN')
            while len(history) < self.plan['warmup_count'] + self.plan['scored_count']:
                prediction = dict(sample_id=f'context-{len(history):03d}', **strategies.predict(history, self.plan))
                intent = self.append('PREDICT', prediction)
                # Intent is durable before any I/O. Failure never triggers resampling.
                item = self.sampler(prediction['sample_id'])
                observed = self.append('OBSERVE', item)
                value = self.validate_sample(item, intent, observed['at'])
                history.append(dict(**prediction, value=value))
            if result is None:
                result = strategies.report(history, self.plan)
                self.append('REPORT', result)
            public = dict(format='genius-context-evidence/1', status='COMPLETE',
                          independent_timestamp_attestation=False, events=self.entries)
            publish(self.directory / 'evidence.json', (source.canonical(public) + '\n').encode())
            return public


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--state', type=Path, required=True)
    args = parser.parse_args()
    study = Study(args.state, json.loads(args.plan.read_text()))
    try:
        result = study.run()
    except Exception as exc:
        # Every durable receipt remains in --state/events, including failed samples.
        print(json.dumps(dict(status='STOPPED', error=type(exc).__name__,
                              code=str(exc) if str(exc).isupper() else 'REVIEW_LOCAL_EVENTS')))
        raise SystemExit(2) from None
    report = result['events'][-1]['event']['body']
    print(json.dumps(dict(status=result['status'], outcome=report['outcome'],
                          comparison=report['comparison'], selected_counts=report['selected_counts'])))


if __name__ == '__main__':
    main()
