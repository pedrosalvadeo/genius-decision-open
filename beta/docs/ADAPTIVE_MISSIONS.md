# Persistent service missions — protocol 1

This integration runs registered LangGraph distribution and resource-calibration adapters in the authenticated
service. Discovery and exact client workflow: `/static/missions.html`,
`/api/missions/capabilities`, `/agents/manifest.json`, scoped `mission_*` MCP tools.
Creation only saves a `draft`; `missions:run` is separately required to queue it.
Inputs are explicit UTF-8 text snapshots (16 files, 64 KiB), never shell commands,
URLs, arbitrary adapters, user-supplied checkpoints or claimed Git commits.

## Commit boundary and recovery

One existing worker alternates normal jobs and missions. Its mission child shares
the twin compiler lock and receives only a minimal environment without credentials.
The child is bounded to 384 MiB address space, 45 CPU seconds and a 60-second parent
wall timeout. Linux parent-death supervision terminates its private process group.
LangGraph concurrency is bounded to four; the service child limits allocator arenas
and thread stacks. No inference API or additional cloud resource is used.

After every durable journal receipt, the child bundles consistent SQLite backups
plus input, evidence, candidates and local delivery. The parent commits the bounded
bundle (4 MiB compressed / 24 MiB expanded) into its owner-scoped main database and
only then ACKs the child. A crash before ACK may redo unpublished local work; a
committed receipt is reused. Effects are private files inside the ephemeral child
workspace, exposed through the API only after the final result commit. This is not
an exactly-once guarantee for future network or physical effects.

On worker restart, running missions are requeued up to three total attempts. A
runtime identity conflict or uncertain effect becomes `needs_review`, with no blind
retry. Manual cancellation, service suspension, account expiry and erasure prevent
further durable publication. Completion reuses the existing artifact and memory.
The input snapshot and technical objective remain immutable throughout.

## Storage, privacy and rollback

Migration 008 is additive. All durable state is in `adaptive_missions` in the main
SQLite database, FK-cascaded on user erasure and covered by existing encrypted R2
backups. Individual deletion records remote privacy intent before the local delete;
restore replays that intent. Backup restore interrupts active missions and requires
explicit retry; it also revokes credentials through the existing recovery policy.
R2 recovery accepts the exact reviewed historical migration prefixes through 009.
Ninety-day mission retention and shorter account lifetime still apply.

Default service limits are three missions per account, sixteen globally, three
attempts, shared agent daily/queue quotas and per-user/global daily human quotas.
Admission reserves worst-case bundle growth inside an IMMEDIATE transaction; stage
commits recheck total service storage. Read/export/delete remain available when
`GENIUS_ADAPTIVE_ENABLED=false`; execution defaults off. Source rollback may retain
the additive table, but old code does not know its individual-erasure tombstones:
keep the current privacy-aware backup tooling for restoration. Preferred rollback
is the feature flag, not running obsolete recovery tooling.

File-distribution memory remains a measured snapshot. The new registered
`resource_calibration_v1` adapter adds bounded parameter proposals, retrospective
holdout comparison and context-bound continuation; see [RESOURCE_CALIBRATION.md](RESOURCE_CALIBRATION.md).
It uses the same table, privacy boundary, child protocol and artifact delivery,
without a new migration or external action. This does not demonstrate wellbeing/PVS
impact or code self-modification. Runtime updates require review of unfinished
missions pinned to a previous runtime; completed rows remain readable and reusable.


## Post-freeze observations

Migration 009 adds immutable forecasts and scored observations under each mission,
with cascading privacy deletion and a 128 KiB admission allowance per mission.
See [PROSPECTIVE_VALIDATION.md](PROSPECTIVE_VALIDATION.md) for freeze/observe/read
routes, MCP tools, server receipt time, code-identity checks, planned sample counts,
sealed reports and reuse of scored observations in a new calibration. Forecast
scoring uses fixed predictions and exact arithmetic; it never silently refits them.
