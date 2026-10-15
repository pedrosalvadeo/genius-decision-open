# Frozen estimates and later submissions — resource_forecast_v1

This increment separates prediction from receipt of its checking data. A completed
resource-calibration mission may freeze its selected estimate, original baseline,
context, units, source type, underprediction tolerance and planned sample count.
Observations arrive in separate later requests. The service scores those fixed
estimates without changing them. A complete report can supply training records
to a separately authorized new calibration mission.

This proves ordering of submissions to this service. It does not attest sensor
truth, independence, complete sampling or when an event actually occurred.
Synthetic data stay synthetic. Resource savings, wellbeing and PVS remain unmeasured.

## API and MCP

All paths are under `/api/missions/ID`, restricted to the mission owner. Existing
`missions:write` allows freezing/submitting; `missions:read` allows reading/export;
`missions:run` is still required to execute a new learning mission. `ADAPTIVE_ENABLED`
gates all new writes; reads and erasure remain available when disabled.

1. POST `/forecast` with exactly `artifact_sha256` (the completed private resource
   estimate artifact) and `expected_count` (integer 3..30). The server returns
   `forecast.frozen` and `forecast.sha256`. One immutable forecast per mission.
   Identical repeated requests reuse it; changed hash/count returns 409. Future-dated
   calibration inputs cannot be used to freeze a prediction before those dates.
2. POST `/observations` with exactly `forecast_sha256` and `observation`.
   Observation fields: `id`, `value`, `observed_at`, `source`, with the same integer,
   ID and source bounds as resource calibration. The declared event must follow
   the freeze and all previous declared events, and cannot exceed server receipt
   time. Timezones are required. Server `received_at` cannot be supplied by clients.
3. GET `/forecast` returns the frozen prediction, receipt sequence and report.
   `status=collecting` is incomplete, never presented as a final validation. Exactly
   the predetermined number of distinct accepted records atomically closes it.
   Further records are rejected. Duplicate IDs with identical input reuse the
   original receipt; changed content returns 409, including after completion.

MCP equivalents: `mission_freeze`, `mission_observe`, `mission_forecast`. Write tools
use `id` and `payload`; the read tool uses `id`. Existing `mission_export` and account
export include the forecast, observations and report. No separate deletion identity
is needed: deleting the mission or account removes the associated records.

Example freeze payload (replace the hash with the artifact hash):

```json
{"artifact_sha256":"64_HEXADECIMAL_CHARACTERS_FROM_ARTIFACT","expected_count":3}
```

Example observation payload (substitute a real ISO datetime with timezone after
`frozen_at`, no later than submission, and preserve the declared source):

```json
{
  "forecast_sha256": "HASH_RETURNED_BY_FREEZE",
  "observation": {
    "id": "observation-1",
    "value": 110,
    "observed_at": "POST_FREEZE_ISO_DATETIME_WITH_TIMEZONE",
    "source": "Synthetic test generated after the freeze"
  }
}
```

## Time, scoring and integrity

`frozen_at` and `received_at` are server UTC ISO datetimes. Corresponding `_us`
fields are Unix microseconds as integers (within JavaScript's exact integer range
for current dates). The server refuses new receipts if its clock has not advanced;
it does not fabricate a later time. Event time and source remain unverified client
statements. Source-code hashes of the scorer and shared calibration functions are
frozen too: changed scoring code blocks new observations pending review while
read/export/erasure and replay of existing receipts remain possible.

Each receipt contains sequence, event, server receipt time, forecast hash, previous
receipt hash and the fixed baseline/estimate absolute error and underprediction.
The first links to the forecast hash. SHA-256 uses canonical sorted-key compact
UTF-8 JSON. This is an integrity chain, not a signature or independent timestamp.
SQLite triggers disallow updating frozen parameters, accepted receipts or a sealed
report. Database transactions serialize concurrent writes and commit the final
observation together with its report; a crash cannot expose an unscored final row.

The report computes exact integer error sums, common count and maximum
underprediction. `LOWER_ERROR_WITHIN_GUARDS` means strictly lower error than the
frozen baseline, no larger maximum underprediction, and compliance with the frozen
tolerance **on these submissions only**. Otherwise it says
`NO_CONFIRMED_IMPROVEMENT`. Neither outcome changes the prediction or proves future
accuracy. This score is arithmetic over fixed predictions, not another native
model evaluation; subsequent calibration continues through the existing kernel.

## Learning after scoring

Create a new mission using:

```json
{
  "kind": "resource_calibration_v1",
  "forecast_mission_id": "OWN_COMPLETED_FORECAST_MISSION_ID",
  "idempotency_key": "new-learning-cycle-001",
  "processing_permission": true,
  "technical_scope_acknowledged": true,
  "calibration": {"validation": ["NEW_LATER_RECORD_1", "NEW_LATER_RECORD_2"]}
}
```

The placeholders in `validation` must be actual observation objects. The server
requires the forecast report to be complete, takes all its scored observations
as training, and inherits the frozen estimate as baseline plus context, resource,
unit, source type and tolerance. The supplied validation records must have new
IDs and later declared event dates; they cannot reuse the training partition.
The maximum forecast size 30 leaves room for the existing minimum two validation
records within calibration's 32-record limit. More validation records can be sent
when the total still fits. The child snapshots the training records and forecast,
report and artifact hashes. It stays usable and idempotent after parent deletion.
Deleting the parent alone does not erase already-derived child data; account
erasure covers both. Permissions/consent apply to all submitted records.

This integrated reuse path cannot train on a partial forecast. The service cannot
identify data copied manually into unrelated retrospective submissions; that does
not acquire this forecast's lineage or post-freeze evidence status. The new fitted
estimate is itself retrospective until it is frozen and checked with another set
of later submissions. Reusing the old report does not validate the new estimate.

## Recovery, capacity and limits

Additive migration 009 introduces forecast and observation tables, both cascading
from the existing private mission. No old migration is modified. Existing encrypted
backups include them. R2 recovery admits reviewed exact schema prefixes through 009;
unknown/reordered/modified histories remain rejected. Tests cover upgrade from
production schema 8 and older supported schemas, partial forecast recovery, account
and mission erasure, remote tombstones and retention. Readiness after restore still
requires the existing operator process; credentials are revoked by recovery policy.

A 128 KiB forecast allowance is added to each mission's storage reservation. Writes
also recheck storage; maximum 30 bounded receipts and one report prevent growth from
being unbounded. Existing mission/account/retention and execution quotas remain.
No new infrastructure, inference provider, scheduler or paid dependency is required.
Disable the adaptive feature flag for rollback; retain schema-009-aware recovery
code for backups rather than attempting a destructive schema downgrade.

Freezing does not prove the sender could not already know the future-looking
values, and users can omit data or abandon an incomplete study. No independent
experiment registration, sampling audit, sensor authentication or causal study is
provided. These are explicit limits, not grounds for upgrading submitted records
to verified empirical or wellbeing evidence.
