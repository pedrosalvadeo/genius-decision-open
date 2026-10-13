"""Explicit-path local CLI. No network acquisition or remote service."""
import argparse
import json
from pathlib import Path
import sys

from .controller import execute, recover, inspect, PublicationBudgetExceeded
from .store import Store


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "continue"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--request", required=True, type=Path)
        sub.add_argument("--case", required=True, type=Path)
        sub.add_argument("--r1", required=True, type=Path)
        sub.add_argument("--baseline", required=True, type=Path)
        sub.add_argument("--cancel-file", type=Path)
    for name in ("inspect", "verify", "recover"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--case", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command in ("run", "continue"):
            if args.command == "continue" and not (args.case / "HEAD").exists():
                raise ValueError("CONTINUATION_REQUIRES_EXISTING_CASE")
            result = execute(args.request, args.case, args.baseline, args.r1, args.cancel_file)
        elif args.command == "recover":
            result = recover(args.case)
        else:
            inspected = inspect(args.case)
            result = inspected if args.command == "inspect" else {"status": "VERIFIED_LOCAL_CHAIN", "head": inspected["head"], "revision_count": len(inspected["revisions"]), "uncommitted_revisions": inspected["uncommitted_revisions"], "temporary_files": inspected["temporary_files"]}
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
        return 0
    except Exception as exc:
        # This receipt is a CLI/controller error, never an FP1 Result.
        result = {"format": "genius-local-cli-error/0.1.0", "error": type(exc).__name__, "reason": str(exc), "mathematical_conclusion": "NOT_EVALUATED"}
        if isinstance(exc, PublicationBudgetExceeded):
            result.update({"transport": {"state": "PT_FAILED", "reason": "LOCAL_PUBLICATION_BUDGET"}, "execution": {"state": "PE_BUDGET_EXHAUSTED", "reason": str(exc)}, "evidence": {"state": "RETAINED_IN_CASE", "head": exc.head}, "decisions": {"state": "NOT_PUBLISHED", "reason": "Prior verified receipts remain in the immutable case; no truncated conclusion is published."}, "closure": {"state": "PC_BUDGET_EXHAUSTED", "reason": str(exc)}})
        print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
