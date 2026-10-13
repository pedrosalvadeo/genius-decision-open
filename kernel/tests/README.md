# Reference-kernel tests

Run from the handoff root:

```bash
python3 tools/run_tests.py --output GENIUS_PROGRAM/validation/TEST_EXECUTION_F2.json
```

Or run without rewriting execution artifacts:

```bash
PYTHONPATH=kernel python3 -m unittest discover -s kernel/tests -v
```

`test_conformance.py` tests all 26 FP1 catalogue IDs through the public byte API. `fixtures.py` creates explicit wire inputs without importing implementation code. `test_theory_boundaries.py` contains 10 mathematical probes for out-of-profile catalogue IDs; their success does not promise an FP1 extension. `test_adversarial.py` is the separate audit author's finite enumeration and mutation suite.

The reporting runner records actual raw bytes and API returns under `executed/<test-id>/<call-number>_<operation>/`. Evaluation calls contain `input.json` and `result.json`. Verification calls contain `input.json`, `candidate.json`, and `verification.json`. Applied caller limits are in `limits.json`; the evaluator also records its captured environmental recursion bound in Result. Invalid JSON inputs deliberately remain byte-exact, including malformed UTF-8 and duplicate keys.

Each invocation replaces the execution corpus and the selected JSON report. The report binds code/test source hashes, test IDs, status, CF mapping, interpreter version, and relative artifact paths. It is execution evidence for these tests, not a performance benchmark, proof of universal correctness, or empirical validation of formal assumptions.

The frozen F1 expected projection is used only as an oracle. Its DESIGNED status and original bytes remain unchanged; F2 execution evidence lives separately. `GENIUS_PROGRAM/validation/CONFORMANCE_MATRIX.md` explains the correspondence and boundary cases.
