# Prospective verification — 15 October 2026 UTC

Implementation: [PR 31](https://github.com/pedrosalvadeo/genius-decision-open/pull/31),
merge `2de2b7b0a1a885b62d7eb6597ea3b2d74741e90f`. All 129 local service,
privacy and recovery tests passed, including nine new tests. GitHub CI passed on
`d9454ba0ab8db1e35bcb2d142b58f98ce2488aef`: Club workspace
[38675859990](https://github.com/pedrosalvadeo/genius-decision-open/actions/runs/38675859990),
adaptive recovery [38675859984](https://github.com/pedrosalvadeo/genius-decision-open/actions/runs/38675859984),
and capsule [38675860002](https://github.com/pedrosalvadeo/genius-decision-open/actions/runs/38675860002).
Tested head and merge share tree `448b73f291d653f44b2cc97f1f7f7b9c4bbc2d51`.

Pedro applied the prepared Railway change. `deployment.json` records deployment
`1d736e8d-65a0-4abf-9d96-f1f0b23b2e99` in terminal SUCCESS, with matching configured
source and provider commit metadata. There are no pending staged changes. The
existing volume and single replica remain. `live-health.json` reports health and
backup `ok`, service not suspended. No extra restart was performed for this probe.

`live-probe.json` records an actual authenticated synthetic trial completed at
03:37:47 UTC. The operator harness is `beta/deploy/prospective_probe.py` at the
deployed commit. It verified artifact, frozen prediction, receipts and report
hashes, plus deployed scorer/calibration source hashes against the local files.
The saved receipt chain, sequence and strictly increasing server times were also
checked offline. The parent report remained unchanged after child learning.

| Stage | Observed result |
| --- | --- |
| Freeze | Baseline 50, estimate 100, tolerance 10, planned count 3; frozen at 03:36:41.648772 UTC |
| Later submissions | Synthetic values 110, 115, 120; received at 03:36:47.657808, 03:36:53.621150 and 03:36:59.640090 UTC |
| Fixed scoring | Absolute error sum 195 for baseline and 45 for estimate; maximum underprediction 70 and 20 respectively |
| Sealed report | `NO_CONFIRMED_IMPROVEMENT`: lower error did not override tolerance 10 |
| Subsequent learning | Scored observations became training; fresh later validation produced estimate 115 from inherited baseline 100 |
| Cleanup | Temporary account deleted; old credential returned HTTP 401; private state overwritten without a secret |

PASS describes correct protocol behavior, including refusal to confirm an
improvement outside the declared guard. The numerical errors are not water
savings. Source and event timestamps are declared, not independently attested;
only server receipt order is observed. Inputs were synthetic and generated after
the freeze. The child calibration remains retrospective until its own prediction
is frozen and independently checked. No generalization, sensor truth, causal
wellbeing or sustained-life benefit is established. No automatic code rewrite or
physical action occurred.

The prior learning and distribution evidence remains in sibling directories.
This evidence update changes no runtime source and requires no new deployment.
Do not rerun the successful operator trial merely to regenerate this receipt.
