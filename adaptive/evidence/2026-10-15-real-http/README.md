# Real HTTP observation cycle — 15 October 2026 UTC

The operator-side observer in `adaptive/observers` completed one predeclared
real-data cycle against the existing public Genius service, from 04:02:54 to
04:07:15 UTC. Cleanup completed afterward. No synthetic values were supplied to
this live run. Source responses were read by the observer; there is no independent
attestation of its clock, network or sampling. `live-study.json` contains the
source contract, code hashes, all 16 samples, submitted inputs, frozen prediction,
server receipts, sealed report, parent/child artifacts and cleanup confirmation.

The measured quantity is elapsed client time for a public health request,
including this environment's network/proxy, connection, TLS, body read and local
JSON validation. It is not origin-server processing time or representative user
latency. All responses satisfied the declared health rule; no failed attempt was
discarded or replaced. The contract and tolerance were fixed before measuring.

| Stage | Result in milliseconds |
| --- | --- |
| Separate baseline sample | 7835 |
| Initial training, in collection order | 6872, 7780, 8257, 7886, 9245 |
| Initial chronological holdout | 7727, 8129, 7010 |
| Initial calibration | Candidate 7886; baseline error sum 1227, candidate 1278; KEEP_BASELINE 7835 |
| Five post-freeze observations | 6741, 7280, 6209, 7640, 6700 |
| Sealed prospective report | Fixed baseline and estimate both 7835; both error sums 4605 (mean 921); NO_CONFIRMED_IMPROVEMENT |
| Later child holdout | 8512, 7852 |
| Subsequent calibration | Candidate 6741; baseline error sum 694, candidate 2882; candidate maximum underprediction 1771 exceeds declared 1000; KEEP_BASELINE 7835 |

The initial candidate failed the strict lower-error condition. Because the parent
retained its baseline, the two prospective predictions were identical; that report
cannot establish a gain over the baseline. The later candidate failed all three
adoption checks. The system therefore preserved its previous estimate rather than
claiming improvement. This is a successful protocol trial with **no confirmed
predictive improvement**, not proof that all other methods fail or that this
baseline is generally optimal. No repeated trial was selected for a better outcome.

Source hashes and normalization were checked against the exact observer bytes.
The frozen scorer/calibration hashes match the unchanged service source. The
receipt chain, event/receipt chronology, fixed scoring arithmetic, child lineage
and preservation of the parent report were verified. The dedicated account was
deleted; the credential returned HTTP 401 and was removed from the private
checkpoint. No credential is part of this evidence.

`summary.json` records the local test invocations and their overlap. The new
integration test uses the real application and worker offline, but simulated
measurements, and loses a response after an accepted observation to test recovery.
`adaptive-tests.txt` is the 32-test discovery run; the later additional mapping
integrity test and the service integration are separately recorded in the summary.
GitHub CI reruns the final tests at the exact published head; its run identifiers
and merge result belong to the accompanying pull request.

`service.json` records the existing deployment, still at PR 31 commit
`2de2b7b0a1a885b62d7eb6597ea3b2d74741e90f`. This increment is an operator client,
tests and documentation. It changes none of the files copied into the deployed
service image, adds no dependencies or infrastructure and requires no Railway
Apply. It does not install a continuous collector.

These measurements do not establish reduced resource consumption, wellbeing,
PVS, causality or generalization. A future trial needs its own fixed plan and later
observations; this completed run must not be rerun merely to seek a positive result.
