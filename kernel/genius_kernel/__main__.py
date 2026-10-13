"""Offline command line for exact evaluation and independent artifact checking."""
import argparse
import json
from pathlib import Path
import sys

from . import __version__, evaluate, verify_result, verify_decisive_certificate
from .common import LIMIT_NAMES, validate_limits


def _limits(items):
    limits = {}
    for item in items:
        name, sep, bound = item.partition("=")
        if not sep or name in limits or not bound.isascii() or not bound.isdecimal():
            raise ValueError("Use unique NAME=NONNEGATIVE_INTEGER limits")
        limits[name] = int(bound)
    return validate_limits(limits)


def _json_file(path):
    # JSON duplicate keys in certificates/results must not disappear before the
    # checker sees them. The input instance is passed as original bytes instead.
    def pairs(items):
        result = {}
        for key, val in items:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = val
        return result
    def constant(val):
        raise ValueError("Non-JSON numeric constant: " + val)
    return json.loads(Path(path).read_bytes().decode("utf-8"),
                      object_pairs_hook=pairs, parse_constant=constant)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Genius finite exact reference Kernel (offline)")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("evaluate", help="Evaluate original input bytes; export input.json and result.json")
    run.add_argument("input", type=Path)
    run.add_argument("--out", required=True, type=Path, help="New or empty output directory")
    run.add_argument("--limit", action="append", default=[], metavar="NAME=N",
                     help="Operational limit: " + ", ".join(sorted(LIMIT_NAMES)))
    for name, help_text in (("verify", "Recompute and verify a complete result artifact"),
                            ("verify-certificate", "Verify a digest-bound DECISIVE_SET envelope")):
        cmd = sub.add_parser(name, help=help_text)
        cmd.add_argument("input", type=Path)
        cmd.add_argument("artifact", type=Path)
        cmd.add_argument("--limit", action="append", default=[], metavar="NAME=N")
    args = parser.parse_args(argv)
    try:
        limits = _limits(args.limit)
        raw = args.input.read_bytes()
        if args.command == "evaluate":
            if args.out.exists() and (not args.out.is_dir() or any(args.out.iterdir())):
                raise ValueError("Output directory must be new or empty; existing artifacts are preserved")
            result = evaluate(raw, limits)
            args.out.mkdir(parents=True, exist_ok=True)
            (args.out / "input.json").write_bytes(raw)
            (args.out / "result.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            summary = {"execution": result["execution"]["status"],
                       "presentation": result["presentation"],
                       "input_digest": result["input_digest"],
                       "output_directory": str(args.out.resolve()),
                       "integration": result["integration"]["state"]}
            if result["decision"]["state"] == "DEFINED":
                d = result["decision"]["value"]
                summary.update(coverage=d["coverage"], frontier=d["frontier"],
                               selection=d["selection"])
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            if result["execution"]["status"] == "LIMITED":
                return 3
            if result["execution"]["status"] == "ERROR":
                return 4
            return 2 if result["presentation"] == "INVALID" else 0
        artifact = _json_file(args.artifact)
        check = verify_result if args.command == "verify" else verify_decisive_certificate
        report = check(raw, artifact, limits)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["valid"] is True else 3 if report["valid"] is None else 2
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "COMMAND_ERROR", "message": str(exc)}, ensure_ascii=False),
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
