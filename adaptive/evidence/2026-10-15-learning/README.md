# Resource-learning verification — 15 October 2026 UTC

Implementation: PR 28, merge `c2aa351b05a5e6857435df86a50bf63682b0f3f6`.
Local verification: 120 service/privacy/recovery tests and 24 adaptive tests.
GitHub CI on `6ec2cd54082d393e5bf4368bfe53d0ac080fc729` passed: service
38662527605 (112 tests offline in the pinned image), adaptive 38662527622,
capsule 38662527660. Merge and tested head share tree
`ad9267c34187fdee9891377cbab88a4ebcce3591`.

Pedro applied the prepared Railway change. `deployment.json` records provider
SUCCESS and both source identities: the configured commit pin is c2aa351 while
provider deployment metadata reports 93f5be9. Every source path copied into the
runtime image has identical Git object IDs. The two repository revisions differ
only in publication metadata and outreach review records. We do not silently
choose one of these provider values as the full deployed repository identity.

`live-probe.json` is the receipt of two actual authenticated API missions using
synthetic resource data. Both completed six stages in one attempt, verified their
native result and artifact hash, and reused their completed result when run was
requested again. First baseline 50 -> estimate 100, error sum 105 -> 5. Second
cycle inherited baseline 100 and its parent artifact hash -> estimate 115,
error sum 35 -> 5. These are prediction errors, not resource savings.

The probe account was deleted and its credential returned HTTP 401 afterward.
The private state was overwritten with a secret-free deletion receipt. No bearer
credential is in this directory. `live-health.json` reports health/backup `ok`
and service not suspended. No restart was performed in this learning probe;
prior distribution restart evidence remains in `../2026-10-15-live/`.

The executed harness is `live-probe.py`. It creates one temporary synthetic agent
account, runs two missions, validates artifacts, and deletes the account in a
finally block. Arguments: a **new private state path**, an output receipt path,
and `adaptive/examples/resource-calibration.json`. It uses HTTPS with the host
proxy, rejects redirects, and never prints credentials. It is an operator probe,
not a background task. Do not rerun merely to regenerate an already valid receipt.

All observations in this experiment are synthetic and submitted together.
Prospective validation remains pending; water savings, wellbeing and sustained
life effects remain unmeasured. No claim of general learning or code modification.
