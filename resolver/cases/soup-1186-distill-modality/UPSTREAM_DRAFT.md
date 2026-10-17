# Drafts only — not submitted

Requires Pedro's authorization to contact the external project. Recheck #1186
and open PRs before claiming; this local package does not reserve the issue there.

## Proposed claim comment

I'd like to take item 1 only: refuse task=distill with vision/audio at config
load, since both modes currently process text only. The patch would preserve
text distillation and unrelated SFT modalities, exercise both loaders and
doctor --config, and include a removal-mutation check. I inspected the shipped
recipes, templates and examples and found no distillation configuration that
would need warning-first staging. Item 2 stays separate. Is this scope still free?

## Proposed PR

Title: fix(config): refuse non-text distillation (refs #1186 item 1)

Adds a modality gate to the existing distillation schema validator, after the
existing backend/teacher checks. The diagnostic names the modality, explains
the text-only trainer and points to text data with modality: text. Adds docs,
a fixed changelog fragment and 29 tests, including four real doctor CLI calls.

Validation against 3da204fadbd278c01ad5a4b23906b443d15e9dd1:

- Initial 25-test set: 16 failed before, 25 passed after.
- Final focused/regression subset: 129 passed (29 new + 100 existing).
- Applying the patch in a clean copy: all 29 new tests passed.
- Removing only the new gate: 20 failed, 9 passed; restoring it: 29 passed.
- Full ruff source/scripts/tests/benchmarks check passed.
- Static inventory: 205 shipped configs, no task=distill config.

Tests used Python 3.12.14, a core-only environment, cleared credential environment
and blocked IPv4/IPv6 sockets. No models were downloaded or trained. Full suite,
global coverage and the OS/Python CI matrix are not claimed and remain pending.

This does not fix item 2 or claim credit for #1193, #1746 or #1782. Use refs, not
a closing keyword for the whole aggregate issue. Rename the provisional
1186.fixed.md fragment to the PR number if requested. Prepared with Codex
assistance for Genius; no external application or adoption has been observed.
