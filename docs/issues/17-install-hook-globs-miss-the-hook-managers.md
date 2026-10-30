---
slug: install-hook-globs-miss-the-hook-managers
title: `install-hook` covers `.husky` and `.githooks` only, so a pre-commit or lefthook configuration is read by no lifecycle rule
labels: enhancement, complexity: trivial, area: rules
roadmap: 3.6, 7.5
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** The lifecycle family, the role resolver and the fixture builders all ship, and this is an addition to one `globs` list plus a fixture pair, which is the smallest useful coverage change in the rule set.

## Problem

`install-hook` resolves from two globs: `**/.husky/**` and `**/.githooks/**` (`rules/roles.toml`). `pat-lifecycle-fetch` (WARN) and `pat-lifecycle-exec` (HIGH) claim that role plus `package-manifest` (`rules/builtin/ci_surface.toml:68,84`), so a hook written in any other supported framework is invisible to both.

The frameworks it misses are the ones a Python, Rust or polyglot repository actually uses:

- `.pre-commit-config.yaml`, whose `repo:` may be a git URL and whose `hook:` entry is a command line; the file resolves to `source` only, so the lifecycle pair does not read it and the config family does not either.
- `lefthook.yml` and `.lefthook/`, whose `commands:` block is a shell string executed on commit.
- A `gitHooks` field in `package.json` (yarn) and a `lint-staged` command list, which do resolve to `package-manifest` and so are read, but with no notion that a hook is what they declare.

The `.git/hooks` directory itself is correctly absent: it is not tracked, and a scanner that read the working directory's git internals would be reading state the change under review did not necessarily author. That boundary should stay.

## What to build

1. **Add the globs.** `**/.pre-commit-config.yaml`, `**/lefthook.yml`, `**/lefthook.yaml` and `**/.lefthook/**` to `install-hook`, and the `hooks:` key shape of a `pyproject.toml` only if the reviewer's decision says so.
2. **Check the pattern still fits.** `pat-lifecycle-fetch` matches client verbs (curl, wget, and friends). A `.pre-commit-config.yaml` whose `repo:` is `https://github.com/someone/else` is a fetch of a different kind: decide whether the existing pattern covers it, whether the rule needs a second branch, or whether a new WARN rule is honest and a HIGH pairing is not. Each choice has to be written down.
3. **Fixtures.** A positive per added glob assembled at test time, and a negative that is the ordinary shape of each file: a `.pre-commit-config.yaml` pinned to an official repository at a full commit SHA, and a lefthook config running a local formatter.
4. **Say what sensitive-role treatment means here.** `install-hook` participates in `SENSITIVE_ROLES`, so widening the globs also widens which unreadable files become HIGH. Confirm that is the intent in one sentence.

**Out of scope:** Any new rule grammar for YAML hook structures, and hook frameworks that live in `package.json` fields rather than in their own file.

## Acceptance criteria

- [ ] A dropper shape in `.pre-commit-config.yaml` and in `lefthook.yml` reaches `pat-lifecycle-exec` and is HIGH.
- [ ] The ordinary, pinned form of each file stays clean, with a negative fixture naming that case.
- [ ] `rules/roles.toml`'s comment for `install-hook` explains the added frameworks rather than leaving the glob list unexplained.
- [ ] The fixture-coverage check accepts the new cases without any rule id being invented in prose that does not exist in data.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- [`rules/roles.toml`](https://github.com/airlock-sec/airlock/blob/main/rules/roles.toml) (`install-hook`)
- [`rules/builtin/ci_surface.toml`](https://github.com/airlock-sec/airlock/blob/main/rules/builtin/ci_surface.toml)
- [`tests/fixtures/ci_surface.py`](https://github.com/airlock-sec/airlock/blob/main/tests/fixtures/ci_surface.py)
- The `pre-commit` and `lefthook` configuration references, read from their own documentation

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
