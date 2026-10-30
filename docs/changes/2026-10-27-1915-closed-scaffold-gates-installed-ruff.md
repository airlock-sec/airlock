---
date: 2026-10-27 19:15 UTC
tasks: 1.4, 2.1
summary: Closed the scaffold gates: installed `ruff` 0.17 and `mypy` 2.4 as `uv` tools (system Python is externally managed and `python3 -m venv` needs an apt package, so neither was forced in), then fixed what they found.
---

Closed the scaffold gates: installed `ruff` 0.17 and `mypy` 2.4 as `uv` tools (system
Python is externally managed and `python3 -m venv` needs an apt package, so neither was
forced in), then fixed what they found. `ruff check` flagged three items in the tests:
an unsorted import block, a `pytest.raises(match=...)` pattern carrying an unescaped
alternation, and a reversed comparison. `ruff format` revealed a larger problem: it also
rewrites Python fences inside Markdown, and it reformatted `ARCHITECTURE.md`. That
change was reverted and `*.md` is now in `tool.ruff.extend-exclude`, because the design
documents must stay reviewable and the roadmap rule depends on their diffs being
legible. Verified: `pytest` 67 passed, `ruff check` clean, `ruff format --check` clean
on 26 files, `mypy src --strict` clean on 24 files. Not verified: the self-scan, since
`airlock scan` deliberately exits 2 until Phase 2 exists
