# Draft only: not submitted

Destination: `getsotto/sotto`, issue #612.
Before submission: Pedro must authorise the external PR; the actual contributor
must review and provide the required DCO sign-off. This package does not certify
anything on Pedro's behalf. Recheck current main and related documentation PRs.

Suggested title: `docs: explain secret removal and synchronisation (#612)`

Suggested body:

Adds a short removal section to the English README and its Spanish, French,
German and Brazilian Portuguese translations. The examples use a synthetic key
and consistently select staging for removal, push and pull. They explain login,
local-only changes, interactive selection and confirmation, cancellation, and
the limits of --yes. The non-interactive warning makes clear that a named removal
does not ask for confirmation even without --yes.

The text distinguishes hiding a secret while retaining version history from
secure erasure or provider-side revocation. It points to history/rollback help
instead of duplicating the recovery walkthrough in PR #595. No runtime behaviour
or cryptographic code changes.

Validation: README i18n checker passed, all 13 upstream checker tests passed,
7 package-level documentation checks passed, and git diff --check passed.
The patch also applied cleanly to a second checkout of
0205ad85a5790351a43c3f523aff95f15da29d9c, where the 7 package checks passed again.
Syntax and claims were inspected against the current Clap definitions and Rust
handlers. The CLI, rendered help, Rust tests and full project suite were not run.
No secrets or sessions were accessed or modified. Translations are best-effort
and welcome review by fluent speakers.

Disclosure: prepared with Codex assistance for Genius. No external adoption is
claimed. DCO remains pending; do not copy a fabricated Signed-off-by line.
