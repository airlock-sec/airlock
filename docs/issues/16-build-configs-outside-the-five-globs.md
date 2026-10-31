---
slug: build-configs-outside-the-five-globs
title: Vite, webpack, jest and the other common build configs run code at build time and are read by no capability rule
labels: enhancement, complexity: medium, area: rules
roadmap: 7.4, 3.1
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The glob matcher, the role resolver and the capability rules all ship and are green (2.4, 3.1), and the false-positive review this task asks for can be run against the fixtures already in `tests/fixtures/` and this repository's own files, so no corpus is needed to start.

## Problem

`tooling-config` resolves from five filenames (`rules/roles.toml`), and the comment at the foot of that file records the rest as deliberately absent: "Extra configs (vite, webpack, jest and others) are P1 and need false-positive review against `tests/corpus` before they are added here."

The consequence is measured rather than theoretical. `vite.config.js`, `webpack.config.js`, `rollup.config.mjs`, `jest.config.js`, `svelte.config.js`, `astro.config.mjs`, `.eslintrc.cjs`, `.babelrc`, `prettier.config.js` and `commitlint.config.js` all end in a suffix that `roles.SOURCE_SUFFIXES` lists (`src/airlock/roles.py:110-113` includes `.js`, `.cjs`, `.mjs`, `.json`), so each resolves to `source` and nothing else. The six `cfg-*` capability rules claim `tooling-config` alone, so none of them fires. What those files do instead is run arbitrary Node at build time, which is the exact capability `cfg-dynamic-code` and `cfg-network-exec` were written to gate.

They are not silent: `pat-decode-eval`, `pat-invisible-unicode`, `pat-exfil-endpoint`, `pat-obfuscator-id`, `pat-credential-harvest` and `pat-chain-c2` all claim `source`, which is why issue #30's port exists. But the combination HIGH, the spawn tiers and `cfg-appended-tail`, the three pieces of logic the config family was built for, do not read a webpack config today.

The reason recorded for the gap is a false-positive budget, not an oversight, so the work here is the measurement rather than five glob lines.

## What to build

1. **Add the role, not the rules.** Introduce `tooling-config-extra` in `rules/roles.toml` with the candidate globs, and give `cfg-dynamic-code`, `cfg-network`, `cfg-chain-endpoint`, `cfg-network-exec`, `cfg-process-spawn` and `cfg-appended-tail` that second role in data. A separate role keeps the original five filenames' severity contract untouched, which is what makes the review tractable.
2. **Do the review with what is in the tree.** Run the widened set over `tests/fixtures/config_role.py`'s negatives, this repository, and a documented sweep of public frontend repositories the contributor clones locally (outside any scan; the no-network rule applies to `airlock` itself, not to a maintainer's measurement). Record the counts in the change record: findings per file, how many are plausible false positives, and which globs you therefore did not add.
3. **Name the globs you refuse.** `.eslintrc.*` and `prettier.config.*` can only reference a plugin by name, which is not an execution capability; say whether each candidate belongs in the role and give the reason in one line each.
4. **Keep the ordering honest.** `resolve_roles` appends the fallback role after the matched roles (`roles.py:199-215`), so a `vite.config.js` becomes `(tooling-config-extra, source)`. Check that `SENSITIVE_ROLES` treatment of the new role is a decision rather than an accident, because that set is what turns an unreadable file into a HIGH.

**Out of scope:** `Makefile`, `justfile`, `.devcontainer/devcontainer.json` and composite action files, which 7.5 covers, and any change to the five shipped globs. Adding a rule for a tool-specific grammar (a webpack `eval: true` devtool flag) is out too.

## Acceptance criteria

- [ ] `vite.config.js`, `webpack.config.js`, `rollup.config.mjs` and `jest.config.js` each resolve to a role the capability rules claim, and a dropper shape in one of them is a HIGH.
- [ ] The candidate globs the review rejected are listed with one-line reasons in the change record and in `rules/roles.toml`'s comment.
- [ ] A count of new findings across the fixtures and the swept repositories is recorded, so the false-positive budget is evidence rather than assertion.
- [ ] Positive and negative fixtures exist for the widened role, and no existing fixture expectation changes.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`rules/roles.toml`](https://github.com/airlock-sec/airlock/blob/main/rules/roles.toml)
- [`rules/builtin/config_role.toml`](https://github.com/airlock-sec/airlock/blob/main/rules/builtin/config_role.toml)
- [`src/airlock/roles.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/roles.py) (`SOURCE_SUFFIXES`, `SENSITIVE_ROLES`, `resolve_roles`)
- Node build-tool documentation for each candidate config, read rather than assumed

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
