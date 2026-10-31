---
date: 2026-10-31 09:37 UTC
tasks: 1.3
summary: Expand CODEOWNERS to cover fingerprint, model, roles, report and CLI layers that carry the same trust properties as the previously owned paths.
---

Issue #100 asked for owner review on the modules that hold the fingerprint truncation-before-hash property, the non-suppressible rule IDs and exit-code contract, the sensitive-role classification, and the reporter escaping / CLI policy-trust boundary.

Those paths are now listed in `.github/CODEOWNERS` with one-sentence reasons matching the existing voice. The additions sit after the coarser directory rules so later-rule-wins does not un-own anything already covered. Tests are not added under owner review: a regression in `tests/` is an assertion about behavior, not a change to the trust model or detection logic itself; the rules and the engine that interpret them remain the protected surface.

Task 1.3 already recorded the ruleset that makes CODEOWNERS meaningful. This change settles the complementary half: the file now names every module the issue identified as carrying the same property. The branch-protection half remains the repository ruleset from 1.3.
