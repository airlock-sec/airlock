---
slug: capability-rules-never-read-a-package-manifest
title: The capability rules never read a package manifest or a hook, so an inline dropper in a scripts field is invisible
labels: enhancement, complexity: medium, area: rules
roadmap: 3.1, 3.6
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** Both halves already ship: `rules/roles.toml` resolves `package-manifest` and `install-hook`, `config_role.py` carries the tiered capability logic, and `ci_surface.py` already reads those two roles for `pat-lifecycle-fetch` and `pat-lifecycle-exec`. This is one role decision plus fixtures.

## Problem

Every rule in `rules/builtin/config_role.toml` that judges what a build file can *do* claims one role. `cfg-dynamic-code` is `roles = ["tooling-config"]` at line 24, `cfg-network` at line 35, `cfg-chain-endpoint` at line 46, `cfg-network-exec` at line 75, `cfg-process-spawn` at line 85 and `cfg-appended-tail` at line 96. The role itself resolves from five filenames ([`rules/roles.toml`](https://github.com/airlock-sec/airlock/blob/main/rules/roles.toml)): `postcss.config.*`, `tailwind.config.*`, `next.config.*`, `eslint.config.*`, `babel.config.*`.

A `package.json` resolves to `package-manifest` plus the `source` fallback, so none of those six rules read it. What reads it instead is the pair in `ci_surface.toml`: `pat-lifecycle-fetch` (WARN, line 66) and `pat-lifecycle-exec` (HIGH, line 82), and that pair requires the *same line* to both fetch and hand over (`detectors/ci_surface.py:170-190`). So this line produces no HIGH anywhere:

```json
{ "scripts": { "postinstall": "node -e \"require('child_process').execFileSync(process.env.HOST)\"" } }
```

There is no downloader verb, so `pat-lifecycle-fetch` misses. There is no tooling config role, so `cfg-process-spawn` and `cfg-dynamic-code` never see the line. The manifest is the file npm executes on every install of the package, and the attack the config family was written to catch arrives in it instead.

The same gap covers a `.husky/pre-commit` that calls `node ./scripts/hook.js`: `install-hook` claims only the fetch and exec pair.

## What to build

1. **Choose the mechanism.** Either widen the capability rules to the lifecycle roles in rule data, or add lifecycle-scoped siblings (`pkg-dynamic-code`, `pkg-process-spawn`) in `ci_surface.toml`. The second keeps the two false-positive budgets separate, which is how `pat-exfil-endpoint` and `cfg-network` were already split (`rules/builtin/builtin_patterns.toml`, the paragraph above that rule), and is the recommendation.
2. **Keep the pairing honest.** `cfg-network-exec` is HIGH because network plus an execution ingredient sit in one file. State what the equivalent combination is for a manifest: a `scripts` entry that spawns plus a dependency whose install script is absent from the lockfile is out of scope here, because the lockfile is not read; say what the rule can honestly claim from the manifest alone.
3. **Do not double-report.** `pat-lifecycle-exec` already fires on a line that both fetches and hands over. Whichever shape you pick, one line yields one HIGH, so add the de-duplication the engine does not give you for free (`rules.apply_patterns` runs pattern rules and the code detector runs its own half).
4. **Fixtures.** A positive per new rule and a negative that is a real `package.json`: a `build` script invoking `next build`, a `lint` script invoking `eslint`, and a `prepare` script running `husky install`. `tests/fixtures/` already assembles lifecycle strings at test time for `pat-lifecycle-fetch`; extend that module rather than committing a payload-shaped file.

**Out of scope:** Reading `package-lock.json` or `yarn.lock`, resolving a dependency graph, and any judgement about a package's registry metadata. This issue is about what the manifest file itself says.

## Acceptance criteria

- [ ] A `package.json` whose `scripts` value spawns a shell command with an inline `-e` or `-c` argument yields a named HIGH finding, and the finding is reported once.
- [ ] A `.husky/pre-commit` with the same shape yields the same rule id or a documented reason it does not.
- [ ] Each new or widened rule has a positive and a negative fixture pair, so the fixture-coverage check in `tests/unit/test_fixtures.py` stays green for it.
- [ ] The rationale field of each rule states why the severity is what it is, in the voice the existing rules use.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`rules/builtin/config_role.toml`](https://github.com/airlock-sec/airlock/blob/main/rules/builtin/config_role.toml) (`roles` lists), [`rules/builtin/ci_surface.toml`](https://github.com/airlock-sec/airlock/blob/main/rules/builtin/ci_surface.toml) (the lifecycle family)
- [`src/airlock/detectors/ci_surface.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/detectors/ci_surface.py) (`_lifecycle_execs`, `_shares_a_role`)
- [`tests/fixtures/ci_surface.py`](https://github.com/airlock-sec/airlock/blob/main/tests/fixtures/ci_surface.py) and [`tests/unit/test_ci_surface.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_ci_surface.py)

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
