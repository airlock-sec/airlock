---
slug: appended-tail-inspects-only-the-last-line
title: `cfg-appended-tail` looks at one line, so a payload followed by one benign line is not a tail
labels: bug, complexity: medium, area: rules
roadmap: 3.1, 3.3
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The rule, its detector and both policy thresholds ship today (`config_role.py:139-166`, `policy.tail_max_len`, `policy.tail_entropy`), and `tests/unit/test_config_role.py` already drives the tail finding, so this is a change to one function plus fixtures.

## Problem

`_tail_finding` walks the decoded text and keeps only the last non-empty line (`src/airlock/detectors/config_role.py:143-150`), then tests that line's length and the Shannon entropy of its last `tail_max_len` characters. The rule's own justification is the appended-payload shape: a minified or valid config followed by something that is neither.

That is decided by one line, so two bytes of diff defeat it. A file ending

```js
export default { /* valid config */ };
const k="c2V0UHJvcGVydHlU...";   // high entropy, long
export const version = 2;
```

is not a finding: the last non-empty line is the benign export. Neither is a payload appended before a trailing comment, a closing brace, or a blank-line-separated `//# sourceURL` footer that a bundler writes anyway.

The residual is narrower than it looks and wider than the rule file says. `cfg-long-line` reads the same roles and reports a line over `line_cap`, but `tail_max_len` is a policy default far below `line_cap`, so a long encoded blob in the middle of a file is reported by neither rule, and at the end it is reported only if nothing follows it.

## What to build

1. **Decide the unit of the rule.** Three options, in increasing cost: test the last N non-empty lines, test every line beyond a fraction of the file's line count, or test every line and rename the rule to what it then actually checks (`long-or-high-entropy-line`). Write the choice and its false-positive reasoning into the rationale.
2. **Keep the tail semantics if you keep the name.** If you test a window of the final lines, say how many and why, and make the count a policy setting only if `airlock.toml` needs to express it; the alternative is a constant beside `tail_max_len` in `model.py` with the reason recorded.
3. **Measure the cost.** The entropy test is linear per line it runs on; widening from one line to every line of a 1 MB config is the difference between a rounding error and a scan dominated by hashing. Add a measured number to `tests/unit/test_redos.py` or state in the record why no budget changes.
4. **Fixtures.** Extend `tests/fixtures/config_role.py` with the appended-then-followed shape as a positive, and keep the existing single-tail positive. The negative must include a legitimately long final line: a minified config, and a source-map comment.

**Out of scope:** Retuning `tail_max_len` and `tail_entropy` themselves against a corpus of real repositories, which is 3.3 and needs the corpus work. This issue is the shape the rule looks at, not where the thresholds sit.

## Acceptance criteria

- [ ] A high-entropy or over-long line that is not the final non-empty line of a tooling config is either a finding or an explicitly recorded and justified non-finding.
- [ ] `_tail_finding`'s docstring and `rules/builtin/config_role.toml` rationale agree on what the rule reads.
- [ ] The per-file cost of the rule is measured and reported, with no timing budget raised to make the test pass.
- [ ] A negative fixture with a legitimately long final line stays clean.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/detectors/config_role.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/config_role.py) (`_tail_finding`, `_shannon_entropy`)
- [`rules/builtin/config_role.toml`](https://github.com/airlock-sec/airlock/blob/main/rules/builtin/config_role.toml) (`cfg-appended-tail`)
- [`src/airlock/model.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/model.py) (`tail_max_len`, `tail_entropy` defaults and their validation)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
