---
date: 2026-10-28 14:29 UTC
tasks: 2.15
summary: Refuse scanner-state suppressions before consulting rule data (#31). The shipped `cfg-long-line` and fallback flags now agree, and finding construction cannot advertise a state as suppressible even if a rule is misdeclared.
---

Refuse scanner-state suppressions before consulting rule data (#31). The shipped
`cfg-long-line` and fallback flags now agree, and finding construction cannot advertise
a state as suppressible even if a rule is misdeclared. Added 35 cases: every state ID
with and without a loaded suppressible rule, shipped-data drift, conflicting cap-rule
metadata, and CLI reproduction using a 30,013-character comment. Before: 19 failures, 16
passes; after: all 158 suppression/rules/CLI tests pass. The maintainer must already
control trusted-base policy for this defect to apply; this is not a PR author's ability
to approve their own suppression. Updated PRD FR-14, architecture 7.6, essentials and
the structure map. The existing exact non-suppressible-rule assertion now includes
`cfg-long-line`, preserving every prior member. Verified locally: 510 tests pass, lint
and format checks pass, mypy clean on 24 modules, self-scan 0 HIGH/0 WARN over 96
tracked files. No threshold, severity or ordinary-rule suppression changed.
