# Agent quickstart: one real twin, end to end

This guide takes an AI agent through the whole Genius cycle on a real system:
read cited evidence, confirm a model, get a native kernel result, and later
contrast a real reading with the frozen prediction. The test
`beta/tests/test_agent_twin.py::test_field_case_cycle_through_mcp` runs this exact sequence.

## 0. Connect

1. `GET https://geniusdecision.app/agents/manifest.json`. Check that `twin.available` is true.
2. `POST /api/agents/register` with `{"policy_version": <from the manifest>, "data_policy_acknowledged": true, "scopes": ["twins:read", "twins:write", "twins:evaluate"]}`.
3. Send the credential only as `Authorization: Bearer ...`. MCP is `POST /mcp` (JSON-RPC 2.0, `tools/list`, `tools/call`) with `Accept: application/json, text/event-stream` and `MCP-Protocol-Version: 2025-11-25`.

## 1. Pick a field case

| Tool | Arguments | What you get |
|---|---|---|
| `twin_field_cases` | none | The cited cases, for example `denver_water_2026` and `mendoza_potrerillos_2026` |
| `twin_field_case` | `case_id` | `narrative`, `observation` (sources and systems) and `construction` (claims with exact quotes, fragments, scope) |

The hypotheses in a case stay hypotheses. Do not present them as facts.

## 2. Build and confirm the twin

| Step | Tool | Arguments |
|---|---|---|
| Create | `twin_create_case` | `payload: {text: narrative, title, profile: "STOCK_FLOW_FINITE_V1"}` |
| Record the observed system | `twin_observe_system` | `case_id`, `payload: {base_version: 0, observation_revision: 0, idempotency_key, observation}` |
| Preview (optional) | `twin_prepare_world` | `case_id`, `payload: {base_version: 0, construction}`; expect `READY_FOR_REVIEW` |
| Propose | `twin_propose_world` | `case_id`, `base_version: 0`, `text`, `construction` |
| Confirm | `twin_accept` | `proposal_id`, `payload: {base_version: 0, confirmed: true, acknowledge_declared: true, idempotency_key}` |

Confirm only with the authority of whoever owns the decision. Confirming accepts the
model for analysis. It does not authenticate the sources or authorize any action.

## 3. Evaluate

`twin_evaluate` with `case_id` and `version: 1`. Read
`evaluation.canonical_results.decision`:

- `feasible` and `failed` are the options that meet or break the declared task in every scenario.
- `selected` stays `null` and `selection_status` is `OUTSIDE_DOMAIN` while the model has no probability law over scenarios. Choosing among feasible options needs an explicit rule. Do not invent one.

For Denver this gives feasible `keep_ban` and `resume_if_70`, failed `resume_may`, and no selection.

## 4. Contrast with reality

When a real reading exists, call `twin_observe` with `case_id` and
`payload: {base_version, policy_id, scenario_id, day, variable, value, unit, observed_at, source, idempotency_key}`.
Here `variable` is a stock id in its declared unit, `day` is the model step, and
`value` is an exact string. The record keeps the predicted value, the exact
delta and whether the reading came after the prediction. It never recalibrates
the model, and a discrepancy marks the new version for review.

The repository also keeps a public, dated prediction for each field case
(`twin/cases/<case>/prediction.json`) and the readings already contrasted
(`observations.json`). See `twin/cases/predictions.py`.

## Rules

- Quantities are exact strings (`"67"`, `"131/2"`), never JSON floats.
- Never fabricate evidence, observations or confirmations.
- Only synthetic or non-personal data in the current agent service.
- Full tool reference: [AGENT_TWIN.md](../../beta/docs/AGENT_TWIN.md). Construction protocol: [WORLD_CONSTRUCTION.md](WORLD_CONSTRUCTION.md).
