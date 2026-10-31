---
slug: explain-command-for-a-rule
title: There is no way to ask the installed scanner what a rule id means
labels: enhancement, complexity: medium, area: engine
roadmap: 5.2, 2.10
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The rule loader already parses every field a reviewer wants (`rules.load_rules`, `model.Rule` carries title, severity, rationale, suppressibility and roles), and `cli.py` already shows how a command with `--rules-dir` and `--roles` is wired, so this is a new subcommand over an existing reader.

## Problem

A rule id arrives in a pull request as `cfg-network-exec`. The maintainer's next question is what it wants them to do, and the answers today live in three places that can disagree: the `rationale` string in `rules/builtin/*.toml`, the table in `README.md`, and the generated site pages. The scanner itself answers nothing: `airlock --help` lists `scan` and `manifest`, and the only way to read a rationale from an installed wheel is to find `rules/builtin/config_role.toml` inside it and open a TOML file.

That matters most for the two questions a suppression conversation turns on: is this finding suppressible at all, and what exactly would the rule accept instead. Both are already in rule data (`Rule.suppressible`, `Rule.rationale`, and the fixture names in `Rule.tests` that say which positive and negative cases the rule was checked against), and the report only prints the title and a truncated message (`MAX_MESSAGE_CHARS` in `model.py`).

2.10 built the CLI's command surface and 5.2 is the documentation task; a command that reads the shipped rule data is the version of 5.2 that stays true when a rule changes.

## What to build

1. **Add `airlock explain RULE-ID`.** Print title, severity, suppressibility and why (the `STATE_RULE_IDS` intersection is the reason), roles, rationale, the rule file it came from, and the fixture names in `Rule.tests`. Non-zero exit and a plain message for an unknown id, in the style of `_mode_for`'s refusals.
2. **Answer the scanner-state case too.** A caller can be handed a state id such as `skipped-oversize` or `detector-error`, which live in `model.STATE_RULE_IDS` rather than in rule data; explain those from their own text so the command's contract is every id the report can carry, not every id in a file.
3. **Make it scriptable.** `--format json` on the command, returning the same field names the JSON report uses, so a bot answering an issue can quote the rationale verbatim rather than paraphrase it.
4. **Reuse the loader, do not re-read the files.** `rules_root` in `cli.py:69-84` already resolves the shipped rules directory; the command must explain the rules an actual scan with the same `--rules-dir` would load, or it becomes a second source of truth and the drift returns.
5. **Tests.** One end-to-end CLI test per family: a pattern rule, a code rule with a `builtin:` pointer, a state id, and an unknown id.

**Out of scope:** Regenerating `README.md`'s tables or the site from this command (that is 33 in this batch and the open issue #29), and any interactive triage flow.

## Acceptance criteria

- [ ] `airlock explain cfg-network-exec` prints the rule's severity, suppressibility, roles, rationale and fixture names from the loaded rule data.
- [ ] `airlock explain` covers every scanner-state id the JSON report can carry.
- [ ] An unknown id exits non-zero with a message naming the rules directory it searched.
- [ ] A test proves the command reports what a scan with the same `--rules-dir` would enforce, so the two cannot drift.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`src/airlock/cli.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/cli.py) (`build_parser`, `rules_root`, the command dispatch in `main`)
- [`src/airlock/rules.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/rules.py) (`load_rules`, `Rule` fields)
- [`tests/unit/test_cli.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_cli.py)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
