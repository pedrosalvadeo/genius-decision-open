#!/usr/bin/env python3
"""Reproducible real-source mission with a hard restart before its effect.

Use the locked environment, PYTHONPATH=adaptive:twin:kernel, and fresh state and
output directories. The output is suitable for review when the source is public.
"""
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time

from genius_adaptive.journal import Journal, canonical
from genius_adaptive.runtime import identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError("EVIDENCE_DIRECTORY_MUST_BE_NEW")
    stages = []

    def call(label, argv, expected=0):
        started = time.perf_counter()
        result = subprocess.run([sys.executable, *argv], capture_output=True, text=True, timeout=125)
        stages.append({"stage": label, "exit_code": result.returncode,
                       "wall_seconds": time.perf_counter() - started})
        if result.returncode != expected:
            raise RuntimeError(label + ": " + result.stderr[-2000:])
        return json.loads(result.stdout) if result.stdout.strip() else None

    init = call("capture", ["-m", "genius_adaptive", "init", "--source", str(args.source),
                           "--commit", args.commit, "--state", str(args.state)])
    # A real process exit after journaling the evaluated decision, before its
    # graph task can checkpoint the return and before any delivery effect.
    program = """
import os, resource, signal, sys
from pathlib import Path
from genius_adaptive.distribution import Distribution
from genius_adaptive.runtime import run
resource.setrlimit(resource.RLIMIT_AS, (512*1024*1024,)*2)
resource.setrlimit(resource.RLIMIT_CPU, (90,90))
signal.alarm(120)
def stop(stage):
    if stage == 'evaluate':
        os._exit(73)
run(Path(sys.argv[1]), Distribution(), after_stage=stop)
"""
    call("stop_after_decision", ["-c", program, str(args.state)], expected=73)
    journal = Journal(args.state / "journal.sqlite3")
    before = journal.export()
    assert set(before["receipts"]) == {"measure", "represent", "evaluate"}
    assert before["effects"] == []
    result = call("resume", ["-m", "genius_adaptive", "run", "--state", str(args.state)])
    completed = journal.export()
    assert all(completed["receipts"][k] == v for k, v in before["receipts"].items())
    repeated = call("repeat_completed", ["-m", "genius_adaptive", "run", "--state", str(args.state)])
    assert repeated["reused"] is True and completed == journal.export()
    assert len(completed["effects"]) == 1 and completed["effects"][0]["state"] == "confirmed"
    args.out.mkdir(parents=True)
    for path in sorted((args.state / "evidence").glob("*.json")):
        shutil.copyfile(path, args.out / path.name)
    shutil.copyfile(args.state / "mission.json", args.out / "mission.json")
    report = {"format": "genius-adaptive-probe/1", "input": init, "runtime_identity": identity(),
              "processes": stages, "max_child_rss_kib": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
              "recovered_previous_receipts_unchanged": True, "repeat_did_not_change_journal": True,
              "effects": completed["effects"], "result": result,
              "external_model_calls": 0, "deployment_scope": "LOCAL_OPERATOR_PROTOTYPE",
              "metrics_scope": "RSS is the maximum reported for child processes on this Linux host; not a concurrent service capacity guarantee"}
    (args.out / "probe.json").write_text(canonical(report) + "\n")
    print(json.dumps({"status": "verified", "files": init["files"],
                      "selected": result["memory"]["selected"],
                      "max_child_rss_kib": report["max_child_rss_kib"], "processes": stages}, indent=2))


if __name__ == "__main__":
    main()
