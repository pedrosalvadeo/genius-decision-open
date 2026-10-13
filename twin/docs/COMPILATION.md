# D1 compilation and native evidence

`compile_model(model, cag_mode="robust")` returns an admitted FP1 dictionary
and a correspondence manifest. `evaluate_model(model)` freezes the UTF-8
JSON bytes, calls the unmodified `genius_kernel.evaluate`, and calls
`genius_kernel.verify_result` against the same bytes and native Result.
It executes two separate inputs for CAG `robust` and `possible`; these modes
are not inserted as extra fields into closed FP1. A distinct digest binds
each input and Result. The principal decision uses robust CAG.

## Wire mapping

| Domain object | FP1 representation | Fidelity obligation |
|---|---|---|
| Shared initialization | `initialization`, common x0/i_before, assumption basis | No policy changes the initial supply or living carriers. |
| Daily committed routine | One action per policy, decisions by time/information | No future scenario enters a decision. Internal local response is declared macro-action semantics. |
| Daily evolution | Point states, transitions and observation updates | Shared prefixes days 0–9 must have identical complete records; compiler rejects discrepancy. |
| Joint event | Three outcomes in day-9 parent to day-10 child | N/H/HA branch exactly once; 25 queries per policy, 75 total, three leaves per policy. |
| Law | Rational weights on that branch; deterministic rows elsewhere | Every causal child remains, including zero mass; probabilities are not counted from drawn routes. |
| Shared water | One demand of cumulative additional water per query, budget 18 L | Cumulative use is checked at each occurrence; it is not summed again across time or plants. |
| Daily person-time | Separate A/B demands and 60-minute budgets | No cross-person compensation or temporal accumulation in the daily bound. |
| Functional profile | Hydration scalar with common identity calibration 0/1/2 | Complete point coverage; terminal hydration is only this functional criterion. |
| Multiscale record | Water-stock port, view retaining query, identity reduction | No compression or inferred independence. The manifest declares this deliberately simple relation. |
| Organizational signature | Identity by point, same native/common meanings, inclusion order | No hidden change from CAG to cardinality. Complete trace processed by native acc recipe. |
| Wellbeing | Four carriers, fixed existence/applicability, query-linked rational values | Whole time and scenario profile, not sum or terminal replacement. |
| Historical life restriction | Leaf semantic meaning from persistent violation monitor | Endpoint hydration 2 can coexist with `violated_trajectory`; full-history fact determines meaning. |
| Universal restriction | Existing `task_all` with scope `LEAVES` | Each leaf's task already quantifies its whole history. No schema extension or probability-based removal. |
| Decision | Existing four-criterion native comparison and `selection: unique` | Hydration terminal criterion is equal across candidates; CAG, historical welfare and PVS remain distinct. |

Task meanings are not merely copied from a desired score. The domain's
daily transition computes and persists historical failure; manifest rows
retain the state and event interpretation. The compiler maps a full leaf
with its monitor and living-status facts to one of the two declared
semantics. The original FP1 evaluator then performs its complete semantic
read and certificate construction. This model-to-semantics interpretation
is an external premise made inspectable, not empirically proved by the
kernel. Independent tests specifically exercise recovery after failure.

Native public schema remains unchanged. D1 does not reuse or silently extend
the `fdq` H=1 profile. All produced inputs declare `FP1_FINITE_EXACT`, H=14,
and `FORMAL_INSTANCE_ONLY`. No native `Cell` is modified, filled with `null`,
or collapsed to a product-level status. The small canonical projection is
explicitly separate: its optional selected policy may be JSON null when the
native selector is `OUTSIDE_DOMAIN`. Native reasons remain in the Result.

## Returned evidence envelope

`evaluate_model` returns:

- `canonical_results`: a consumer-friendly projection with exact rationals,
  daily trajectories, wellbeing profile, both CAG modalities, PVS/masses and
  native frontier/selection. It declares synthetic empirical admission.
- `native_input_json`: exact UTF-8 text of the principal robust input.
- `native_result`: original robust Result object, unchanged.
- `verification`: original robust verification result.
- `compilation_manifest`: compiler version, source-model JSON and digest,
  event, law, domain/point/query correspondences and both native digests.
- `native_runs`: `robust` and `possible`, each with exact input text,
  unchanged Result, lossless serialized Result text and verification.

These fields permit export as the original `input.json`/`result.json` pair
per mode. The outer service owns the new case/version/verification envelope,
optimistic concurrency and immutable persistence. RC01 is not implemented
in D1; this envelope does not claim to be an RC01 receipt. A received revision
requires fresh native input bytes and fresh results; serialization that
changes only whitespace also changes the original-byte digest.

Evaluation emits the canonical successful projection only after both runs
are COMPLETE, presentation VALID, integration DEFINED and verification
VALID. Failure raises an explicit error instead of returning canned values.
Within the current complete admitted profile, all three dimensions are
defined. Partial model admission is not implemented by silently filling
unknowns. Native partial semantics remain available to the unmodified
kernel and are tested: a missing positive-mass leaf reference yields
undecided mass and no formal PVS.

## Review and replay

From the repository root:

```bash
PYTHONPATH=twin:kernel python3 -m unittest discover -s twin/tests -p test_domain.py -v
```

Acceptance tests compare generated numbers against the independent design
oracle, prove the day-10 violation survives day-11 recovery, retain the
shared prefix before the event, check exact native digest/result pairs,
verify E_prime's two-member frontier, retain zero-mass HA in robust CAG and
universal constraints, and reject forged bytes/results. These checks are
formal and synthetic. They do not establish suitability for real gardeners
or real physiological thresholds and probability laws.
