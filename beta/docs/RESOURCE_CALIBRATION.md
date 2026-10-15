# Resource estimation learning — resource_calibration_v1

The service can propose, compare and adopt a constant resource-use estimate for
one explicitly declared operation/context. Water in millilitres and time in seconds
are possible units; no domain-specific sufficiency or biological threshold is
inferred. This is a parameter-learning adapter with a fixed reviewed rule, not a
universal model or autonomous code rewrite. No extra dependencies or infrastructure.

## Request and continuation

POST `/api/missions`, then POST `/api/missions/ID/run` with `{}`. The same
`mission_create`, `mission_run`, export/artifact and deletion MCP tools apply.

Required top-level fields: `kind=resource_calibration_v1`, `idempotency_key`
(16–64 ASCII alphanumeric/_/-), `processing_permission=true`,
`technical_scope_acknowledged=true`, and `calibration`.
Optional `parent_mission_id` identifies a completed mission belonging to the same
account. Arbitrary lineage, adapter names, checkpoints or code are never accepted.

`calibration` contains exactly:

- `context` (1–500 nonblank characters): the operation and conditions assumed constant.
- `resource`, `unit` (1–64 nonblank characters each): no unit conversion is inferred.
- `baseline`: integer 0–1,000,000, omitted when a parent supplies it.
- `max_underprediction`: integer 0–1,000,000, tolerance for this experiment, not a health threshold.
- `data_kind`: `synthetic` or `submitted_observations`.
- `training`: at least three records; `validation`: at least two; total at most 32.

Each record has exactly `id` (1–64 ASCII alphanumeric/_/-), `value` (integer
0–1,000,000), `observed_at` (ISO datetime with timezone, at most 40 characters),
`source` (1–240 nonblank characters). Booleans, floats and negative quantities are
rejected. IDs are unique across both partitions, and timestamps are strictly
increasing in the concatenated training/validation sequence. Inputs are immutable.
Data and times are submitted claims, not attested measurements or receipt times.

For continuation the server loads and verifies the parent's private artifact,
requires identical context/resource/unit/data_kind, copies its selected estimate
as the new baseline and requires all new records later than the parent's last
record. It freezes parent ID, artifact hash and estimate in the child. It does not
copy raw parent records or a recursive history. The request hash refers to the
original request, so an idempotent retry still works after deletion of the parent.
A child remains self-contained after parent deletion. Account erasure removes all
cycles; deleting only the parent does not delete already-derived child estimates.
The existing three-mission capacity permits rolling export/delete/continuation.
Branching from a completed parent is allowed; there is no global mutable estimate.

## Proposal, native comparison and adoption

`LOWER_MEDIAN_HOLDOUT_MAE_V1` takes the lower median of **training only** (the
lower middle value for even counts). It is one absolute-error-minimizing constant
on that training sample. It does not search validation data or tune multiple rules.

On the identical validation records, calculate integer absolute-error sum, sample
count and maximum underprediction for both baseline and proposal. Dividing the
sum by the common count gives mean absolute error; selection needs no rounding.
An accepted STOCK_FLOW_FINITE_V1 one-step operational model represents the error
allowance and evaluates both options through the existing native kernel. Its
verified unique selection must agree with an independent exact arithmetic oracle;
a tie has no native unique selection. The one scenario's unit mass describes this
retrospective comparison only, not future likelihood or empirical admission.
Its error allowance is not a physical resource or human wellbeing stock.

Adopt the proposal **only when all three conditions hold**:

1. Validation absolute-error sum is strictly lower than baseline.
2. Maximum underprediction does not exceed baseline's maximum underprediction.
3. Maximum underprediction is within the caller's declared tolerance.

Otherwise retain baseline, including ties, worsening performance or failed guards.
Retention is not approval: baseline can itself exceed tolerance, reported explicitly
in the evaluation receipt. A low error alone never overrides either guard.

Six receipts preserve input/split digests, training rule, proposal, native model and
verified result, adoption checks, artifact readback and reusable memory. The only
effect is immutable private `resource-estimate.json`; the source code, deployment,
other missions and the real-world operation do not change. Result adoption means
an estimate was chosen for this artifact and can become a later cycle's baseline.

## Evidence limits and recovery

Validation is a **retrospective chronological holdout**, not an independent,
preregistered or prospective experiment. All records are submitted together and
source statements are unverified. Repeated selection against such data can overfit;
the adapter does not infer future accuracy, causality, savings, wellbeing or PVS.
Artifacts label prospective validation `PENDING` and wellbeing/life effects
`UNMEASURED`. Synthetic examples stay synthetic through continuation.

Inputs, checkpoints, native evidence, derived memory and artifact remain in the
existing owner-scoped mission row with the same encrypted backup, restore and
erasure handling. ACK-after-commit, runtime pinning, isolated process bounds,
review on identity conflict and completed-result reuse all apply. An interruption
after local publication reconciles exact bytes; no arbitrary external effects run.

Example: [resource-calibration.json](../../adaptive/examples/resource-calibration.json).
With training 90,100,110 and validation 100,105, baseline 50 has error sum 105;
the proposed 100 has error sum 5 and maximum underprediction 5 instead of 55.
With tolerance 10 it is adopted. With baseline 150, the same proposal has smaller
error but worsens maximum underprediction from 0 to 5, so 150 is retained.
These are synthetic arithmetic checks, not measured water savings.


## Subsequent checking

The completed artifact can now be frozen through `/api/missions/ID/forecast`, then
checked against separately received observations. The original artifact remains
unchanged. A complete report may supply training for a new mission through
`forecast_mission_id`; newly supplied later validation records test that new fit.
See [PROSPECTIVE_VALIDATION.md](PROSPECTIVE_VALIDATION.md). This does not retrospectively
upgrade the calibration artifact's original holdout or its provenance.
