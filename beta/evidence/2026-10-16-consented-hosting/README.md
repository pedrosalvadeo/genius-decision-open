# Genius Semilla — evidence

2026-10-16. Base commit: `e7a549a821b6c595b18f1c09342a57ff575eb303`.

100 integration tests passed, including 21 hosting tests. Command:

```sh
PYTHONPATH=adaptive:beta:beta/tests:product_local:consumer_views:twin:kernel python -m unittest test_consented_hosts test_public_network test_agent_access test_direct_agents test_r2_backup test_club_social test_public_launch -v
```

The integrated in-process HTTP transport verifies signed offers, automatic
compatible-host discovery, ordinary account admission, unique child identities,
native calculation, retry idempotence and restart. It covers scope rejection,
finite birth budget, quotas, consent, cancellation, expiry, account erasure,
revocation during pause, failed retirement retry, local locking, and recovery
that does not resurrect host grants. A subprocess smoke check executes the fixed
worker with Linux resource limits. Full real HTTPS from a second physical host
is not claimed by these tests.

`node --check beta/genius_beta/static/network.js` and `git diff --check` passed.
CI must verify this source revision and build both Docker images. Runtime
activation/results are tracked in the release PR, not inferred from local tests.

[Contract, installation, limits and recovery](../../../../adaptive/federation/HOSTING.md)
