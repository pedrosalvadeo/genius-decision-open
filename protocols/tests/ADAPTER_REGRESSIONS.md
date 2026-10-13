# Author regression record — F4

## F4-ADAPTER-01: candidate syntax precedence

First author smoke, before repair, reproduced `{"a":1,"a":2}` as candidate
bytes with a correct base64/SHA-256 envelope. Observed report was
`{"valid":false,"status":"INVALID","errors":["CANDIDATE_TYPE"]}`.
The number parse hook raised before JSON duplicate-key/syntax validation
completed. Thus a malformed candidate could be classified as a type rejection
instead of the contracted `CANDIDATE_SYNTAX`. No candidate was accepted and no
Kernel verifier was invoked; the defect concerned the declared error boundary.

Before algorithm: `parse_int=parse_float=_reject_number`, with
`_reject_number` immediately raising `CandidateTypeError`.

Repair: number hooks retain a private typed sentinel without converting an
unbounded integer or coercing a number into a string. JSON parsing and Unicode
scalar validation finish first; only then is a syntactically valid candidate
containing numbers rejected as `CANDIDATE_TYPE`.

After: duplicate keys, truncated JSON containing a number, and a lone Unicode
surrogate containing a number produce `CANDIDATE_SYNTAX`; complete numeric JSON
and a 100001-digit number produce `CANDIDATE_TYPE`. A mock proves the Kernel
verifier is not called for any of them. The exact regressions are in
`test_adapter_regressions.py`. This is author evidence, not independent gate
acceptance. Code identity remains the unreleased development version 1.0.0;
neither the contract nor the inherited Kernel has changed.

The exact first-revision parser source was reconstructed from the recorded edit
by reversing this repair, and saved as `findings/F4-ADAPTER-01/wire_before.py`.
`before_after.json` binds both parser sources and all five candidate byte files
by SHA-256. Run `python3 protocols/tests/findings/F4-ADAPTER-01/reproduce.py`
from the handoff root to repeat the comparison. Four author regression methods
passed in the first post-repair execution (0.006 s); the independent consumer
and audit are separate evidence. `ADAPTER_SOURCE_SHA256.json` records the final
source snapshot after aligning initialize identity labels to the written
contract (`GENIUS-PROTOCOLS-1.0.0`, `GENIUS-KERNEL-1.0.1`).
