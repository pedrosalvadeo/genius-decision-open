"""CLI for the resolver's local ledger; the Work agent performs reasoning."""
import argparse
import json
from pathlib import Path
from . import ledger as L
from .sources import QUERIES, search


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', default='resolver/ledger.json')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('init')
    sub.add_parser('report').add_argument('--out', default='resolver/REPORT.md')
    sub.add_parser('inspect')
    for command in ('discover', 'ingest', 'claim', 'record'):
        p = sub.add_parser(command)
        p.add_argument('--expected-revision', required=True, type=int)
        if command == 'ingest':
            p.add_argument('--snapshot', required=True)
            p.add_argument('--query', required=True)
        if command in ('claim', 'record'):
            p.add_argument('--problem', required=True)
            p.add_argument('--operator', required=True)
            p.add_argument('--receipt', required=True)
        if command == 'record':
            p.add_argument('--status', required=True, choices=L.STATES)
    args = parser.parse_args()
    if args.command == 'init':
        with L.transaction(args.ledger, 0, initialize=True):
            pass
    elif args.command == 'report':
        Path(args.out).write_text(L.report(L.load(args.ledger)))
    elif args.command == 'inspect':
        print(L.canonical(L.load(args.ledger)))
    elif args.command in ('discover', 'ingest'):
        if args.command == 'discover':
            # Partial failures never overwrite the existing ledger with an empty result.
            captures = [(q, search(q)) for q in QUERIES]
        else:
            path = Path(args.snapshot)
            L.require(path.stat().st_size <= 1024 * 1024, 'SOURCE_RESPONSE_LIMIT')
            captures = [(args.query, json.loads(path.read_text()))]
        with L.transaction(args.ledger, args.expected_revision) as state:
            for query, capture in captures:
                print(L.canonical(L.ingest(state, capture['items'], query,
                      total_count=capture.get('total_count'), incomplete=capture.get('incomplete_results', False))))
    else:
        path = Path(args.receipt)
        L.require(path.stat().st_size <= 65536, 'RECEIPT_SIZE')
        receipt = json.loads(path.read_text())
        with L.transaction(args.ledger, args.expected_revision) as state:
            if args.command == 'claim':
                L.claim(state, args.problem, args.operator, receipt['criteria'], receipt['reason'])
            else:
                L.transition(state, args.problem, args.status, args.operator, receipt)


if __name__ == '__main__':
    main()
