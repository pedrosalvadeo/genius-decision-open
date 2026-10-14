<!-- Keep this PR as draft until it is ready for review. -->

<!-- AI/LLM agents:
Do not edit the HUMAN section.
-->

HUMAN:

<!--
Human author: please replace this comment with a short note (at least 20 visible
characters) before marking ready for review.
AI agents: you must not edit this section.
-->

---

AGENT:

## Why

Genius Decision exposes a hosted MCP service for versioned decision-model evaluation, but it is absent from the integration catalog. Users currently need to discover its endpoint, machine-token authentication and opt-in twin permissions separately.

## Summary

- Add one canonical `integrations/catalog/genius-decision.json` with one Streamable HTTP MCP connection and scoped Bearer authentication.
- Regenerate `integrations/catalog-index.js` using `npm run build:integrations`.
- Document the hosted synthetic/non-personal data policy, explicit twin scopes and absence of OAuth in the entry's setup metadata.

## Issue Number

Closes #770.

## How to Test

Base tested: `OpenHands/extensions@f1919e4e3e02c0bab65c2417761aee775f1ffbaa`.

```sh
npm run build:integrations
python -m pytest -q tests/test_catalog_schema.py tests/test_catalogs.py tests/test_integration_catalog_in_sync.py
python scripts/sync_extensions.py --check
git diff --check
```

Result: 117 tests passed. The sync check exited 0 with an unrelated non-blocking coverage warning for `plugins/issue-duplicate-checker`. Both `appUrl` and `docsUrl` returned HTTP 200.

End-to-end verification used the released PyPI package `openhands-sdk==1.54.0` with FastMCP 3.4.8 and MCP 1.30.0, against `https://geniusdecision.app/mcp`. The harness uses `create_mcp_tools`, `MCPToolDefinition.action_from_arguments` and `MCPToolExecutor`; it does not substitute a hand-written JSON-RPC client for the OpenHands tool calls.

The reproduction harness, exact installed dependency versions and sanitized receipts are published in the provider repository:
https://github.com/pedrosalvadeo/genius-decision-open/tree/main/capsule/integrations/openhands

From that repository, with the documented Python 3.12 environment:

```sh
python capsule/integrations/openhands/verify_client.py --live --out /tmp/genius-openhands-live.json
```

The live command creates and deletes one disposable machine space and consumes one model evaluation. Do not run it without authorization for those operations. It keeps the token only in memory and never writes it to the receipt.

## Video/Screenshots

No UI changes. The machine-readable receipt records 18 passed checks, including:

```text
sdk_public_discovery PASS
sdk_private_discovery PASS
sdk_explicit_fixture_acceptance PASS
sdk_engine_completed_and_verified PASS
sdk_export PASS
sdk_case_deleted PASS
sdk_space_deleted PASS
temporary_token_revoked PASS
OUTCOME PASSED
```

The SDK discovered 3 public tools and 19 tools with the requested scopes, including all 15 twin tools. It created a case, proposed and explicitly accepted the published synthetic `stockflow_care` fixture, evaluated it, received `completed` / `VALID`, read back the job, exported the case, deleted the case and the space via MCP, and confirmed token revocation with HTTP 401.

## Notes

This updates the original issue's deployment status: the service is live and the released SDK round trip has now been verified by the Genius team. It is not evidence of independent OpenHands adoption, a human maintainer approval, or empirical model validity. There were zero LLM calls; Cloud/GUI/CLI account-connection flows were not tested.

The typed client requests `twins:read`, `twins:write`, `twins:evaluate`, `twins:delete` and `account:delete`. Default registration permissions do not include twin operations. The entry omits optional `connectionModel` metadata and does not claim per-resource isolation beyond the provider's own agent space.

Observed non-fatal SDK warnings: LiteLLM fell back to its local public price map after a fetch timeout; FastMCP reported the legacy `sse_read_timeout` option as deprecated. Neither prevented the recorded result. No provider-specific runtime code, OAuth option, token value, SDK documentation, new schema or aggregate catalog asset is proposed for this repository.

Prepared with AI assistance. The HUMAN section remains for the human author, as required by the template; keep this PR as draft until that review is complete.
