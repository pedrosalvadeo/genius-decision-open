"""Explicit local paths only; failed presentation never changes the dossier."""
import argparse
import json
import subprocess
import sys

from .reader import ViewError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    render = sub.add_parser("render")
    render.add_argument("--case-dir", required=True)
    render.add_argument("--output-dir", required=True)
    render.add_argument("--revision", type=int)
    args = parser.parse_args(argv)
    try:
        command = [sys.executable, "-B", "-m", "genius_views.worker", "--case-dir", args.case_dir,
                   "--output-dir", args.output_dir]
        if args.revision is not None:
            command.extend(["--revision", str(args.revision)])
        child = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        sys.stdout.buffer.write(child.stdout)
        sys.stderr.buffer.write(child.stderr)
        if child.returncode not in {0, 2}:
            raise ViewError("RENDER_WORKER_TERMINATED_WITHOUT_NORMAL_RECEIPT:" + str(child.returncode))
        return child.returncode
    except Exception as exc:
        print(json.dumps({"format": "genius-consumer-error/0.1.0", "error": type(exc).__name__,
                          "reason": str(exc), "publication_state": "UNKNOWN_WORKER_TERMINATION",
                          "mathematical_conclusion": "NOT_EVALUATED"}, ensure_ascii=True, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
