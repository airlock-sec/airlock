---
date: 2026-10-28 14:40 UTC
tasks: 7.12, D-09
summary: Settle #22 with `partialFingerprints["airlock/v1"]` (D-09, ADR-019), replacing the draft `repoGuard/v1` before any SARIF release. Updated architecture 6.6, PRD FR-19, essentials, stub and issue draft.
---

Settle #22 with `partialFingerprints["airlock/v1"]` (D-09, ADR-019), replacing the draft
`repoGuard/v1` before any SARIF release. Updated architecture 6.6, PRD FR-19,
essentials, stub and issue draft. The algorithm is unchanged and the reporter remains
unimplemented. Two new tests failed first on the old reporter row and missing stub key,
then passed; they inspect those exact locations rather than any mention elsewhere. Local
verification: 515 tests, lint and format, mypy (24 modules), self-scan 0 HIGH/0 WARN
over 96 files, progress and diff checks. The obsolete spelling remains only in this
roadmap's historical decision/changelog records.
