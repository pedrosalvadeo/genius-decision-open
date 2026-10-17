# Drafts — not sent

Permission is required before posting either draft. Re-read #423 and its comments
first; CONTRIBUTING and #317 request a comment before claiming work. No assignment
has been obtained. Coordinate before offering an already prepared local patch.

## Coordination comment

I have a small local documentation draft for #423 and would like to coordinate
before opening a PR. Is this still available? It adds the same nine-line recall
section to Claude Code, Cursor, Codex and Gemini, plus an explicit Rho no-notes
exception. It preserves setup commands and current live-verification caveats.
I have not changed runtime behavior or verified clients live.

## Proposed PR

Title: docs(integrations): explain possible and confirmed recall fixes

Addresses #423 with four matching short sections and the Rho exception. The text
explains the two-episode threshold, last-agent/terminal provenance, shared local
store and `MEMORYWHALE_HOOK_FEEDBACK=0`; observed history is not causal proof.
It links 0.20.0 and replaces stale certainty in Cursor/Codex/Gemini.

Reviewed against `format_hint`, `fix_candidates`, `ran_by`, hook feedback routing
and 0.20.0 at 07e6ac952dbbb7b527fe78578271cd57937f0890. Nine external static
documentation checks pass, including unchanged command blocks, Status claims and
the eight required headings; the same checks pass on a clean patch application.
No `fix that worked` matches remain under integrations/. No Rust, frontend,
hook setup or client-verification claims change.

Not run: full npm/Rust suites, runtime documentation-reference script (Cargo
unavailable), or live-client sessions. This is a documentation-only patch;
please run the project's normal checks before merging.
