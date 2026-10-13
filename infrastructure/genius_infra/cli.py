"""Non-root, single-owner local operation. stdout is an operational summary."""
from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path
import signal
import stat
import sys
import threading

from . import __version__
from .storage import Store, StoreError, BusyError
from .supervisor import SupervisorLimits, run_worker

PROFILE = "local-fp1-v1"
LAB_PROFILE = "local-fp1-single-uid-lab-v1"
PROFILES = [PROFILE, LAB_PROFILE]
INPUT_CAP = 2 * 1024**2
CANDIDATE_CAP = 8 * 1024**2


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read_bytes(path, maximum):
    """Bound reads; refuse special files/symlink components, without decoding data."""
    path = Path(os.path.abspath(path))
    for part in [*reversed(path.parents), path]:
        if part.is_symlink():
            raise ValueError("SYMLINK_INPUT")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("INPUT_NOT_REGULAR")
        if info.st_size > maximum:
            raise ValueError("INPUT_BYTES_LIMIT")
        value = stream.read(maximum + 1)
        if len(value) > maximum:
            raise ValueError("INPUT_BYTES_LIMIT")
        return value


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_KEY")
        result[key] = value
    return result


def arguments(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Create a private new store")
    init.add_argument("--store", required=True)
    init.add_argument("--profile", choices=PROFILES, required=True)
    run = commands.add_parser("run", help="Evaluate or verify once, recording the entire exchange")
    run.add_argument("--store", required=True)
    run.add_argument("--profile", choices=PROFILES, required=True)
    run.add_argument("--method", choices=["evaluate", "verify_result", "verify_certificate"], required=True)
    run.add_argument("--input", required=True)
    run.add_argument("--candidate")
    run.add_argument("--kernel-limits", help="Explicit F4 LimitMap JSON file; absent means none")
    run.add_argument("--retry-of", help="Prior run ID for correlation only; never a deduplication key")
    run.add_argument("--cpu-seconds", type=int, default=10)
    run.add_argument("--address-space-mib", type=int, default=256)
    run.add_argument("--wall-seconds", type=float, default=30.0)
    run.add_argument("--max-stdout-bytes", type=int, default=34 * 1024**2)
    run.add_argument("--max-stderr-bytes", type=int, default=64 * 1024)
    check = commands.add_parser("check", help="Verify store bytes; incomplete staging stays incomplete")
    check.add_argument("--store", required=True)
    check.add_argument("--profile", choices=PROFILES, default=PROFILE)
    backup = commands.add_parser("backup", help="Copy and verify a store into a new snapshot")
    backup.add_argument("--store", required=True)
    backup.add_argument("--destination", required=True)
    backup.add_argument("--profile", choices=PROFILES, default=PROFILE)
    for command in ["restore", "rollback"]:
        restore = commands.add_parser(command, help="Restore selected snapshot to a new store")
        restore.add_argument("--backup", required=True)
        restore.add_argument("--destination", required=True)
        restore.add_argument("--profile", choices=PROFILES, default=PROFILE)
    return parser.parse_args(argv)


def perform_run(args):
    if (args.method == "evaluate") != (args.candidate is None):
        raise ValueError("CANDIDATE_REQUIRED_ONLY_FOR_VERIFICATION")
    raw = read_bytes(args.input, INPUT_CAP)
    candidate = read_bytes(args.candidate, CANDIDATE_CAP) if args.candidate else None
    kernel_limits = None
    if args.kernel_limits:
        kernel_limits = json.loads(read_bytes(args.kernel_limits, 4096), object_pairs_hook=unique_pairs)
        if not isinstance(kernel_limits, dict):
            raise ValueError("INVALID_KERNEL_LIMIT_MAP")
    if args.retry_of and (len(args.retry_of) > 80 or not all(c.isascii() and (c.isalnum() or c == "-") for c in args.retry_of)):
        raise ValueError("INVALID_RETRY_ID")
    limits = SupervisorLimits(cpu_seconds=args.cpu_seconds,
                              address_space_bytes=args.address_space_mib * 1024**2,
                              wall_seconds=args.wall_seconds,
                              max_stdout_bytes=args.max_stdout_bytes,
                              max_stderr_bytes=args.max_stderr_bytes)
    store = Store(args.store)
    event = threading.Event()
    previous = {}
    for sig in (signal.SIGINT, signal.SIGTERM):
        previous[sig] = signal.signal(sig, lambda *_: event.set())
    try:
        with store.exclusive():
            artifacts = {"input.json": raw}
            if candidate is not None:
                artifacts["candidate.json"] = candidate
            start = {"infrastructure_version": __version__, "profile": args.profile,
                     "method": args.method, "started_utc": utc(), "kernel_limits": kernel_limits,
                     "retry_of": args.retry_of, "euid": os.geteuid(),
                     "limits": vars(limits)}
            tx = store.begin(artifacts, start)
            outcome = run_worker(args.method, raw, candidate_bytes=candidate,
                                 kernel_limits=kernel_limits, limits=limits, cancel_event=event,
                                 lab_single_uid_root=args.profile == LAB_PROFILE)
            tx.add(outcome.artifacts)
            run_id = tx.commit({**outcome.metadata, "status": outcome.status,
                                "reason": outcome.reason, "finished_utc": utc(),
                                "infrastructure_version": __version__})
            return {"status": outcome.status, "reason": outcome.reason, "run_id": run_id,
                    "result_received": "result.json" in outcome.artifacts,
                    "verification_received": "report.json" in outcome.artifacts}, 0 if outcome.status == "DELIVERED" else 1
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def main(argv=None):
    args = arguments(argv)
    if sys.platform != "linux" or (os.geteuid() == 0 and args.profile != LAB_PROFILE):
        print(json.dumps({"status": "REFUSED", "reason": "REQUIRES_LINUX_NONROOT"}), file=sys.stderr)
        return 2
    os.umask(0o077)
    try:
        if args.profile == LAB_PROFILE:
            from .worker import enter_lab_containment
            enter_lab_containment()
        if args.command == "init":
            Store.create(args.store)
            result, code = {"status": "CREATED", "profile": args.profile}, 0
        elif args.command == "run":
            result, code = perform_run(args)
        elif args.command == "check":
            store = Store(args.store)
            with store.exclusive():
                result = store.verify()
            code = 0 if result.get("status") == "PASS" else 1
        elif args.command == "backup":
            store = Store(args.store)
            with store.exclusive():
                result = store.backup(args.destination)
            code = 0
        else:
            Store.restore(args.backup, args.destination)
            result, code = {"status": "RESTORED", "operation": args.command,
                            "previous_store_modified": False}, 0
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
        return code
    except BusyError:
        print(json.dumps({"status": "BUSY", "reason": "ONE_JOB_PER_STORE_NO_QUEUE"}), file=sys.stderr)
        return 3
    except (StoreError, OSError, ValueError, TypeError) as exc:
        # Payloads and file paths are deliberately absent from shared CLI logs.
        print(json.dumps({"status": "OPERATION_FAILED", "error_type": type(exc).__name__,
                          "errno": getattr(exc, "errno", None),
                          "meaning": "No mathematical conclusion; inspect private store/staging"}), file=sys.stderr)
        return 1
