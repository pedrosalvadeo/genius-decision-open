# D1: bounded synthetic domain contract

The admitted domain is the 14-day semillero demonstration defined in the
approved redesign. It is not an agronomic predictor, a universal decision
adapter or an empirically calibrated survival model. All numbers are explicit
synthetic assumptions, and all probabilities are conditional on them.

## Public functions and exact model

`default_model()` returns a fresh dictionary. `validate_model(model)` succeeds
with `None` or raises `ValueError`. `compute_trajectories(model)` returns
`policy -> scenario -> {daily, totals}`. Daily records cover days 0 through 14;
totals contain `water_liters`, `minutes_a`, and `minutes_b`.

```json
{
  "profile": "SEMILLERO_14D_SYNTHETIC_V1",
  "horizon": 14,
  "policies": ["C", "R", "E"],
  "water_budget_liters": 18,
  "law": {"N": "1/2", "H": "1/3", "HA": "1/6"},
  "require_all_scenarios": true
}
```

The only alternative family is `["C","R","E_prime"]`. The explicit joint
law can change to nonnegative canonical rational weights summing exactly to
one, including zero weights. Mass strings have an operational length bound of
32 characters. Floating point, unreduced fractions, missing law, additional
fields, extra policies, different budgets and extrapolated horizons are
rejected. `require_all_scenarios` is a boolean normative choice, not a causal
parameter. A missing law is not replaced with uniform weights. Current D1 does
not accept partially identified real models; those require a new admitted
profile. A service may record observations without silently changing this
synthetic domain.

## State, information, actions and events

The initial state contains two living plants P1/P2 sharing one tray with 2 L
of stored hydration, one additional shared supply of 18 L, organizational
signature q0, and operators A/B with 60 minutes available per day. There are
no births or deaths in this stipulated instance. Existence is explicit and
is not inferred from nonempty welfare values.

Daily state retains hydration, accumulated water used, remaining shared
water, time assigned/available by person, organizational identity, completion
of formation/verification, observed event and an irreversible violation flag.
Historical failure is part of the represented state even after hydration
recovers. Organizational identity alone is not a causal state.

Policies select committed daily **routines**, not hidden scenario-specific
actions. A routine includes its declared local observation-and-response rule
(for instance, irrigation using a sensor and a present operator). Such
within-day contingency is modelled inside a causal macro transition. The
external joint input arrives only in the day-10 transition; policies and
states before that transition cannot depend on its future value. The FP1
controller's action at the start of that transition is the same routine for
all possible events. The resulting observation records the event afterwards.
This is an explicitly coarse action semantics, not a claim that a control
decision was made with future information. It must be refined if within-day
timing is material in a real application.

The discrete hydration transition is:

`s_next = max(0, min(2, s_previous + water_applied - demand))`.

Demand is 1 L except during heat on day 10, when it is 3 L. The complete joint
event alphabet is N (normal, B present), H (heat, B present), HA (heat, B absent
in the critical window). These are not independent marginal draws. Scenarios
with zero probability remain causally admitted, retain their full welfare
profiles, and still participate in robust CAG and universal constraints.

## Executable routines

| Policy | Rules |
|---|---|
| C | A irrigates 1 L using 20 minutes each day. If the previous day's hydration is below 1, A supplies 3 L using 30 minutes. This is the one-day-late recovery response. B has no task. |
| R | Day 1 preparation uses 30 minutes for each person. From day 2, A covers even days and B odd days, 10 minutes. Reserve/protocol operable from day 7. A supplies day-10 demand in all scenarios. |
| E | Same routine as R through day 7. On days 8–14 A uses 30 minutes, except 60 minutes of formation on day 10. B uses 20 minutes for care/verification, unless absent on day 10. If absent, no irrigation occurs in that window; B restores with 3 L and 30 minutes on day 11. |
| E_prime | Formation and verification move to day 9. A does 30 minutes on day 10 and adds 10 minutes of emergency irrigation if B is absent. B then needs only the ordinary 20 minutes on day 11. |

The propagation unit becomes operable on day 14 if formation and verification
are both complete; its test consumes 2 L. The unit prepares a subsequent
cycle: it does not introduce new plants into this horizon. It does not
promise water inputs or persistence after day 14. In E, absence on day 10
prevents verification; in E_prime the verification is complete on day 9.
The implemented transition functions generate all water/time totals. No
precomputed response JSON or expected outcome table is used by the engine.

## Three distinct evaluations

**Wellbeing:** a profile of conditions, not a universal index. A/B have daily
available minutes (60 minus assigned time), and P1/P2 have daily tray
hydration. The four carriers, applicability and complete daily coverage are
retained. Their dimensions are ordered within a common reference; units and
species are not added. The two plant cells share the same hydric cause and
are not independent measurements. C/R are incomparable on this full history:
R involves initial work and transfers some care burden to B. Total minutes
remain a separate exact query, never a substitute for this comparison.

**CAG:** q0 means manual care; q1 adds reserve equipment, response protocol
and trained operators; q2 adds an operable, verified propagation unit.
Conservation is inclusion of the declared organizational components. Daily
presence or water quantity is not part of that signature; a trained team
may fail to exercise its capabilities under a particular routine. Recipe
`acc` requires preservation on every transition from origin to achievement.
The native kernel constructs CAG from whole identity traces, adding the
origin and aggregating by union (`possible`) or intersection (`robust`). It
does not count routes or use cardinality as an order.

**Sustained-life task:** keep living P1/P2 within hydration margin at least
1 at every declared state, days 0–14. Living status is stipulated in this
fixture; the hydric restriction discriminates outcomes. The result is a
conditional probability of the declared trajectory task, not an empirical
probability of mortality/survival. A historical violation cannot be erased
by recovery. Daily granularity does not establish continuous-time biological
coverage. The kernel returns the success/failure/undecided mass vector and
PVS only within the original FP1 domain. D1's complete synthetic references
have no indeterminate mass, but the native checker still governs that gate.

## Independent acceptance oracle

These rows are test expectations derived in the approved design, not data
consumed by the transition implementation.

| Policy/scenario | Total L | Minutes A/B | s10 | CAG acc robust | PVS under default law |
|---|---:|---|---:|---|---|
| C/N | 14 | 280/0 | 2 | {q0} | 1/2 |
| C/H and C/HA | 16 | 290/0 | 0 | {q0} | 1/2 |
| R/N | 14 | 100/90 | 2 | {q0,q1} | 1 |
| R/H and R/HA | 16 | 100/90 | 2 | {q0,q1} | 1 |
| E/N | 16 | 300/200 | 2 | {q0,q1} | 5/6 |
| E/H | 18 | 300/200 | 2 | {q0,q1} | 5/6 |
| E/HA | 15 | 300/190 | 0 | {q0,q1} | 5/6 |
| E_prime/N | 16 | 300/200 | 2 | {q0,q1,q2} | 1 |
| E_prime/H | 18 | 300/200 | 2 | {q0,q1,q2} | 1 |
| E_prime/HA | 18 | 310/180 | 2 | {q0,q1,q2} | 1 |

All terminal hydric states equal 2; terminal success has probability one for
every policy and is a different event. Under the universal constraint the
base family admits only R. The edited family admits R and E_prime; R saves
time while E_prime adds robust q2, so the integrated frontier has both and
there is no selected winner under the declared singleton-only selection.

Mathematical source: *Matemática Genius - Modulos - Astra 01*, 23 September
2026: MIII definitions 5.1–5.12; MIV 6.1–6.5; MV 7.4–7.8 and 7.12; MVI
8.1, 8.7, 8.9–8.11; MVII 9.1–9.6. Implementation conformity and empirical
validation remain distinct claims.
