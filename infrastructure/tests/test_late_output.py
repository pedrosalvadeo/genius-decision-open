"""F5-AUD-001 author regression; retain complete delivery after extra bytes.

The synthetic peer uses the production containment bootstrap. Each response is
obtained from a real F4 evaluation first, then emitted before the anomaly.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/"infrastructure"), str(ROOT/"kernel/tests")]
from genius_infra.worker import enter_lab_containment
from fixtures import small


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--supervisor", type=Path, default=ROOT/"infrastructure/genius_infra/supervisor.py")
    parser.add_argument("--laboratory-root", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    if args.laboratory_root:
        identity = enter_lab_containment()
    else:
        identity = {"euid": os.geteuid(), "identity_scope": "NONROOT"}
    spec = importlib.util.spec_from_file_location("genius_infra.regression_subject", args.supervisor.resolve())
    subject = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = subject
    spec.loader.exec_module(subject)
    # A preserved supervisor snapshot lives outside its runtime directory.
    # Resolve its fixed worker to the unchanged packaged bootstrap explicitly.
    subject._worker_command = lambda limits, lab_single_uid_root=False: [
        sys.executable,"-I","-S","-B",str(ROOT/"infrastructure/genius_infra/worker.py"),
        str(limits.cpu_seconds),str(limits.address_space_bytes),str(os.getpid())] + (
            ["--lab-single-uid-root"] if lab_single_uid_root else [])
    caps = subject.SupervisorLimits(10, 256*1024**2, 15, 34*1024**2, 65536)
    raw = (json.dumps(small(), ensure_ascii=False)+"\n").encode()
    actual = subject.run_worker("evaluate", raw, limits=caps, lab_single_uid_root=args.laboratory_root)
    if actual.status != "DELIVERED":
        raise RuntimeError("Prerequisite real F4 evaluation failed")
    (args.output/"input.json").write_bytes(raw)
    (args.output/"expected_result.json").write_bytes(actual.artifacts["result.json"])
    results = []
    with tempfile.TemporaryDirectory(prefix="genius-late-peer-") as temp:
        peer = Path(temp)/"peer.py"
        # Keep argv parent PID and containment identical to productive bootstrap.
        peer.write_text("""import json,os,runpy,sys,time
worker=runpy.run_path(sys.argv[1],run_name='trusted_regression_bootstrap')
worker['apply_containment'](int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),lab_single_uid_root=sys.argv[5]=='1')
config=json.load(open(sys.argv[6]))
sys.stdin.buffer.readline()
sys.stdout.buffer.write(config['init'].encode());sys.stdout.buffer.flush()
sys.stdin.buffer.readline()
sys.stdout.buffer.write(config['response'].encode());sys.stdout.buffer.flush()
time.sleep(0.04)
sys.stdout.buffer.write(config['tail'].encode());sys.stdout.buffer.flush()
if config.get('sleep_after'): time.sleep(1)
""")
        original_command = subject._worker_command
        # Neighbors distinguish later noise, extra frame, EOF and bounded flood.
        for name, tail, stdout_cap in (("late_fragment", "late-junk", caps.max_stdout_bytes),
                                       ("late_frame", "{\"unexpected\":true}\n", caps.max_stdout_bytes),
                                       ("extra_lf", "\n", caps.max_stdout_bytes),
                                       ("late_flood", "x"*65536, len(actual.artifacts['worker.stdout'])+16)):
            folder = args.output/name
            folder.mkdir()
            config = Path(temp)/(name+".json")
            config.write_text(json.dumps({"init":actual.artifacts["initialization.json"].decode(),
                                          "response":actual.artifacts["response.json"].decode(), "tail":tail}))
            command = [sys.executable,"-I","-S","-B",str(peer),
                       str(ROOT/"infrastructure/genius_infra/worker.py"),"10",str(256*1024**2),
                       str(os.getpid()),"1" if args.laboratory_root else "0",str(config)]
            subject._worker_command = lambda limits, **kwargs: command
            outcome = subject.run_worker("evaluate", raw,
                limits=dataclasses.replace(caps,max_stdout_bytes=stdout_cap),lab_single_uid_root=args.laboratory_root)
            subject._worker_command = original_command
            for artifact, value in outcome.artifacts.items():
                (folder/artifact).write_bytes(value)
            checks = {"operational_failed":outcome.status=="FAILED",
                      "response_validated":outcome.metadata["response_validated"] is True,
                      "response_exact":outcome.artifacts.get("response.json")==actual.artifacts["response.json"],
                      "result_exact":outcome.artifacts.get("result.json")==actual.artifacts["result.json"],
                      "raw_response_retained":actual.artifacts["response.json"] in outcome.artifacts["worker.stdout"],
                      "raw_tail_retained_or_explicitly_capped":tail.encode() in outcome.artifacts["worker.stdout"] or outcome.metadata["stdout_is_prefix"]}
            (folder/"OUTCOME.json").write_text(json.dumps(outcome.metadata,indent=2)+"\n")
            (folder/"CHECKS.json").write_text(json.dumps(checks,indent=2)+"\n")
            results.append({"case":name,"passed":all(checks.values()),"checks":checks,"reason":outcome.reason})
    summary={"finding":"F5-AUD-001","identity":identity,"cases":results,
             "passed":all(case["passed"] for case in results),
             "source_sha256":hashlib.sha256(args.supervisor.read_bytes()).hexdigest(),
             "argv":sys.argv,"peer_kind":"Synthetic peer with real F4 response and common containment"}
    (args.output/"SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps({"passed":summary["passed"],"cases":len(results),"source_sha256":summary["source_sha256"]}))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
