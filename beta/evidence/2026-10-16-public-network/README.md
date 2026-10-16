# Public network release — local verification

2026-10-16. Base: `4f863fa5badf242e6c2dd2e7aa08f5d18d0651c8`.

- Integration: **79 passing tests**, including 13 network tests. Command:
  `PYTHONPATH=adaptive:beta:beta/tests:product_local:consumer_views:twin:kernel python -m unittest test_public_network test_agent_access test_direct_agents test_club_social test_r2_backup test_public_launch -v`
- Adaptive: **91 passing tests**; see the captured suite output.
- `node --check beta/genius_beta/static/network.js`: passed.
- `git diff --check`: passed.
- Docker unavailable locally; CI must build the installable node and public beta.
- The reference process retry delay was adjusted after the integration run;
  CI checks the exact published commit. Its API bootstrap is tested for restart
  idempotence. Real HTTPS and deployment are not claimed by these local logs.

Three local installations verify signed complementary synthetic views and
compute the same native model. Signature tampering, identity replay, scope,
publication consent, quotas, conflicts, rotation, deletion and restored deletion
are covered. The reference node uses the ordinary enrollment/publication API.

Deployment and live HTTPS observations will be recorded in the release PR.
No private key or access credential is included in these files.
