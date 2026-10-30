---
date: 2026-10-27 22:22 UTC
tasks: 2.13, 6.3, 7.9
summary: Phase 2 is complete. `FileEntry` and `ScanContext` were drafted before the code that consumes them, so 2.13 settled them by grepping every field for a reader instead of by argument.
---

Phase 2 is complete. `FileEntry` and `ScanContext` were drafted before the code that
consumes them, so 2.13 settled them by grepping every field for a reader instead of by
argument. `FileEntry.size_bytes` had none outside the collector that decides whether a
file is oversize or only partly read, so the size is a local variable there and the
entry no longer carries it; a run of the scanner over this repository shows the oversize
and change-during-read findings still stating the byte count themselves.
`ScanContext.mode`, `tool_version`, `repo_head` and `base` had no reader at all, because
the reporters render `ScanReport`, which keeps all four. The context is now entries,
policy, manifest and rules, which is what a rule needs and nothing more; losing `mode`
there also means detector code can no longer reach the trust model that chose its base,
which is the direction 6.5 wants rather than a side effect of tidying. `test_model.py`
asserts both field lists verbatim, so a re-added field has to be argued for in that test
first. `ARCHITECTURE.md` 7.9 documents both models and the reasoning, and 6.3 no longer
claims the context carries the scan mode. Verified: `pytest` 433 passed, `ruff check`
and `ruff format --check` clean on 42 files, `mypy src` clean on 24 files, self-scan
exit 0 over 69 files with nothing skipped. Not verified: whether a future detector
genuinely needs the mode, which is the one field omission likely to be revisited, and
the P0 rule set is still only as good as the synthetic fixtures that fire it (3.3, 3.6
to 3.10)
