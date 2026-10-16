# Draft only: not sent

Destination: https://github.com/sameeralam3127/linux-vitals/issues/149

Proposed claim comment, subject to Pedro's authorization:

> We have prepared a local candidate for #149 that pins command probe locales,
> parses OpenSSL's English months independently of LC_TIME, and surfaces
> unparseable certificate dates as unknown findings. The patch includes tests
> and was prepared with Codex assistance. May we take this issue through your
> contribution process? Full upstream lint and systemd/Molecule checks are still
> pending; nothing has been applied to managed hosts.

Proposed PR title: `Fix locale-dependent probes and certificate dates (#149)`

Proposed PR body:

Non-English managed-host locales can turn a lastb trailer into a failed-login
finding and prevent OpenSSL dates from parsing, silently omitting expiry results.

This patch fixes command probes to LC_ALL=C and parses OpenSSL's fixed English
month names without changing the process locale. Missing or malformed dates
retain the raw evidence and add an unknown cert_scan_unavailable finding. A
known expired end date still produces cert_expired even when the start date is
unreadable. Documentation and the changelog describe the additive behaviour.

The attached tests reproduce the failure before the fix. They check all twelve
months under real German/French LC_TIME, run the real Ansible probe tasks against
localized output fixtures, and verify unknown findings for both file and endpoint
certificate results. See validation.json for the exact local results and limits.

Before submitting: confirm assignment, rerun the current contribution checks
(full pytest, pre-commit, ansible-lint, syntax check, supported core versions and
at least one Molecule systemd scenario), and rebase/retest if main has changed.
Do not describe this draft as deployment or external adoption.

Disclosure: Codex assisted with diagnosis, implementation, tests and this draft.
