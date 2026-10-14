"""Operator CLI. New mission directories only; no background execution."""
import argparse
import json
import os
from pathlib import Path
import resource
import signal


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--source", type=Path, required=True)
    init.add_argument("--commit", required=True)
    init.add_argument("--state", type=Path, required=True)
    for name in ("run", "inspect"):
        sub.add_parser(name).add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
    resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024 * 1024,) * 2)
    signal.alarm(120)
    from .distribution import Distribution, prepare
    from .journal import Journal
    if args.command == "init":
        value = prepare(args.source, args.commit, args.state)
    elif args.command == "run":
        from .runtime import run
        value = run(args.state, Distribution())
    else:
        if not (args.state / "journal.sqlite3").is_file():
            parser.error("Mission has not run yet")
        value = Journal(args.state / "journal.sqlite3").export()
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
