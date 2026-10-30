---
date: 2026-10-30 15:52 UTC
tasks: 7.2, FR-20
summary: Close #27 (task 7.2): make submodules actionable scanner-state findings instead of an `INFO` note.
---

Close #27 (task 7.2): make submodules actionable scanner-state findings instead of an
`INFO` note. `[policy]` in `airlock.toml` gains `submodules: tuple[str, ...] = ()`, read
from the trusted base in `pr` and `push` modes and validated as a list of non-empty URL
strings without whitespace. `collector.py` records each index entry's SHA from `git
ls-files -z --stage`, parses `.gitmodules` with a non-regex line parser bounded by
`policy.line_cap` (refusing `.gitmodules` when it carries a skip or encoding state
finding), and cross-checks mode `160000` gitlinks and `.gitmodules` sections in both
directions: a mapped gitlink emits `submodule-present` at HIGH when its `.gitmodules`
URL is not in `policy.submodules` and at WARN when listed, naming both the index commit
and the `.gitmodules` URL and dropping the unverifiable third-party pipeline claim; a
gitlink with no `.gitmodules` entry or conflicting entries emits `submodule-unmapped` at
HIGH; and a `.gitmodules` section missing a single `path`/`url` or pointing at a path
with no mode `160000` gitlink emits `submodule-orphan` at WARN. All three IDs are in
`STATE_RULE_IDS` (non-suppressible), and `TestSubmodules` enforces a
positive-and-negative real temporary-repository fixture gate across every `submodule-*`
ID in `STATE_RULE_IDS` while `tests/unit/test_fixtures.py` (which feeds in-memory
`FileEntry` values to `runner.scan()` without a git index) passes untouched.
Trusted-base tests in `test_policy.py` and `test_cli.py` verify that a pull request
adding a gitlink, `.gitmodules` and `submodules = [...]` in the same change is judged by
the base commit's empty allow list (`submodule-present` HIGH, `policy-changed` WARN,
exit 1), whereas a gitlink whose URL is already listed in the base commit's
`airlock.toml` reports `submodule-present` at WARN and exits 0. Updated
`ARCHITECTURE.md` 6.1, 7.6 and 8, `ARCHITECTURE_ESSENTIALS.md` 5 and 6, `PRD.md` FR-20,
`README.md`, `site/index.html`, `site/usage.html`, `site/trust.html` and `ROADMAP.md`
