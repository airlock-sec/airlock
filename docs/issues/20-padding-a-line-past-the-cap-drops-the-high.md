---
slug: padding-a-line-past-the-cap-drops-the-high
title: A line one character over `line_cap` is read by no pattern rule, and the stand-in finding is only a WARN
labels: bug, complexity: high, area: engine
roadmap: 2.5, 3.11
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The cap, the stand-in rule and the timing harness all ship and are green (2.5, 2.12), and the residual this issue closes is written down in `rules/builtin/builtin_patterns.toml` above `pat-invisible-unicode`, so the work is to answer a documented limitation with code rather than to discover one.

## Problem

`line_cap` exists because a regex over an unbounded line is the one input shape that can hang the scanner, and the rule is enforced by skipping: `rules.apply_patterns` continues past any line longer than the cap (`src/airlock/rules.py:285-287`), and every code detector repeats the same filter (`ci_surface.py:96-98`, `config_role.py:60-70`).

The accounting for what was skipped is `cap_findings` (`rules.py:300-333`): one `cfg-long-line` finding naming the first over-cap line and counting the rest. Its severity is then reduced by `_cap_severity` (`rules.py:262-270`), which keeps the authored HIGH only inside `SENSITIVE_ROLES` and returns WARN anywhere else.
The result is an evasion with two characters in it. In a file whose role is `source`, a payload padded to 20001 characters turns three HIGHs (`pat-decode-eval`, `pat-invisible-unicode`, `cfg-long-line`'s authored severity) into one WARN, and only HIGH affects the exit code, so the change that was written to avoid the regex also avoids the gate. The rule file says this out right (`rules/builtin/builtin_patterns.toml`, the paragraph after `pat-invisible-unicode`): "padding costs the exit-code gate and never the report". A finding that never blocks a merge is a note, not a control.

The cap cannot simply be raised. 2.12's harness measures the cost of a near-miss line at exactly `line_cap`, and 3.11 already records that `cfg-network` runs at about 63 ms per megabyte against a 50 ms target.

## What to build

1. **Give the over-cap stand-in the authored severity.** Decide and implement whether `cfg-long-line` stays HIGH for every role that a pattern rule claims, on the ground that the line was withheld rather than clean. The counter-argument is a minified bundle in `source` becoming a HIGH on every repository that ships one, which is a false-positive budget question, so write the decision down with the number that motivated it.
2. **Or read the line in bounded pieces.** The alternative that keeps both properties is to run the pattern rules over fixed windows of an over-cap line with a bounded overlap, which turns one unbounded match into several bounded ones. If you take this route: the overlap has to be at least the longest pattern's context, a hit's reported line is the file's line rather than the window, and the total work per file must stay linear in bytes. Say which you chose.
3. **Measure what you add.** Add the padded-line case to `tests/unit/test_redos.py` as a cost assertion, and do not adjust any existing budget to make a test pass.
4. **Keep the message honest.** `cap_findings` already says "no pattern ran on it". Whatever the new behaviour is, the message and the rationale in `rules/builtin/config_role.toml` have to agree with it, and so must `ARCHITECTURE.md` 8 where the severity reduction is described.
5. **A fixture that proves the gate.** A padded `pat-decode-eval` payload in a `source`-role file, asserted to affect the exit code, plus the unpadded negative.

**Out of scope:** Raising `line_cap`, changing the regexes themselves, and any parser-based approach to long lines (9.4). This issue is the accounting for text the engine declines to match.

## Acceptance criteria

- [ ] A padded payload in a file with no sensitive role either affects the exit code or is recorded as an accepted limitation with a named decision id.
- [ ] The padded case is a bypass regression alongside the seven Appendix B modules, not only a unit test.
- [ ] `tests/unit/test_redos.py` covers the new per-file cost, with no pre-existing budget changed.
- [ ] `rules/builtin/builtin_patterns.toml` and `ARCHITECTURE.md` no longer describe the padding residual as unlimited, or say precisely where the limit now sits.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/rules.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/rules.py) (`apply_patterns`, `cap_findings`, `_cap_severity`)
- [`rules/builtin/config_role.toml`](https://github.com/airlock-sec/airlock/blob/main/rules/builtin/config_role.toml) (`cfg-long-line`)
- [`tests/unit/test_redos.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_redos.py) and [`tests/bypass/`](https://github.com/airlock-sec/airlock/blob/main/tests/bypass)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
