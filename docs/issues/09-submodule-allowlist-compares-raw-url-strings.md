---
slug: submodule-allowlist-compares-raw-url-strings
title: `policy.submodules` matches a `.gitmodules` URL byte for byte, so a spelling variant flips a WARN to a HIGH
labels: bug, complexity: medium, area: engine
roadmap: 2.10
---

> **Repo context.** `airlock` is a Python 3.11 standard-library-only scanner: `src/airlock/` holds the pipeline (collector, then rules and detectors, then fingerprints and suppressions, then reporters) behind one CLI, and the rules themselves are data in `rules/builtin/*.toml`. The repository being scanned is untrusted input, so the hard rules in [`AGENTS.md`](https://github.com/airlock-sec/airlock/blob/main/AGENTS.md) section 4 are security properties rather than style. [`ROADMAP.md`](https://github.com/airlock-sec/airlock/blob/main/ROADMAP.md) is the source of truth for what is built and what is only a docstring.

> 🟢 **Unblocked.** 7.2 landed yesterday with the allowlist, the three `submodule-*` ids and a temporary-repository fixture class, so this is a follow-up inside shipped code with tests already in place to extend.

## Problem

7.2 made submodules actionable: [`collector._submodule_findings`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/collector.py) cross-checks each
mode `160000` gitlink against `.gitmodules` and then asks one question of the policy, with `allowed_urls
= frozenset(policy.submodules)` and `allowed = url in allowed_urls`. An exact hit is
`submodule-present` at WARN; anything else is the same id at HIGH.

Comparison is on the raw string from whichever file wrote it. Git itself treats several spellings as the
same remote: `https://github.com/acme/widget` and `https://github.com/acme/widget.git` are the same
repository to `git submodule add`, `git@github.com:acme/widget.git` is the same one over ssh, and a
trailing slash is accepted in the https form. The hostnames in those forms are also case-insensitive in
a way the comparison is not.

The failure is in the false-positive direction and it is the one that costs trust: a maintainer lists
the URL as their `.gitmodules` spells it in one commit, edits the file to the `.git` form in the next,
and gets a HIGH that says the subtree is unauthorized, in a scanner whose whole job is to be believed
when it says HIGH. R-2 rates config-role false positives as a High risk for exactly that reason.

The other direction deserves a sentence in the design rather than a hack: a prefix or substring match
would let one allowlisted entry authorize a look-alike repository, so whatever normalization is chosen
has to be exact after normalization, never fuzzy.

## What to build

1. **Write down the equivalence relation you want** before coding it. Something like: lowercase the
   scheme and host, allow either scp-like (`git@host:path`) or https form, treat a trailing `/` and a
   trailing `.git` as the same remote, and require the path segment to match exactly, case-sensitively.
2. **Normalize both sides** (the `.gitmodules` value and each `policy.submodules` entry) with one shared
   function, and keep the *raw* URL in the finding text so a reviewer sees what the file says.
3. **Report an unparseable allowlist entry** rather than dropping it. `Policy.__post_init__` currently
   only refuses empty or whitespace-containing entries; an entry that cannot be normalized is a config
   error.
4. **Fixtures**: one gitlink authorized through each accepted spelling, one look-alike path that must
   still be HIGH, and one entry that cannot be normalized. `TestSubmodules` is the class to extend.
5. **Document the rule** in `ARCHITECTURE.md` where 7.2's policy key is described, and in the README
   or site page a maintainer reads when adding a submodule.

**Out of scope:** fetching, scanning or resolving submodule contents (out of scope for 7.2 too), URL
credentials handling, and any change to `submodule-unmapped` or `submodule-orphan` semantics.

## Acceptance criteria

- [ ] A `.gitmodules` URL that names the same remote in a different accepted spelling produces the same severity as the allowlisted form, and the record lists which spellings were chosen.
- [ ] A repository path that differs after normalization still produces HIGH, with a test that would fail if the match were a prefix or substring comparison.
- [ ] A `policy.submodules` entry that cannot be normalized is refused as a config error rather than silently never matching.
- [ ] The raw URL still appears in the finding, and `ARCHITECTURE.md` and the user-facing docs state the equivalence rule.
- [ ] A change record with a UTC date exists under `docs/changes/`, `ROADMAP.md` has been regenerated from it, and `python scripts/roadmap_progress.py --check` passes.
- [ ] `python -m pytest`, `ruff check .`, `ruff format --check .` and `mypy src` all pass on Linux, and `airlock scan --mode full .` reports no HIGH findings.
- [ ] PR description includes `Closes #{{issue:self}}`.

## Tech stack

- Code: [`src/airlock/collector.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/collector.py) (`_submodule_findings`), [`src/airlock/model.py`](https://github.com/airlock-sec/airlock/blob/main/src/airlock/model.py) (`Policy.submodules` validation).
- Tests: [`tests/unit/test_collector.py`](https://github.com/airlock-sec/airlock/blob/main/tests/unit/test_collector.py) `TestSubmodules`, which already builds positive and negative temporary repositories for every `submodule-*` id.
- No new dependency: normalization is string work, and `urllib.parse` is standard library. Prefer hand-rolled comparison over `urlparse` if scp-like syntax has to work, and say which you chose.
- This is a protected path, so `AGENTS.md` section 12 applies. The change must not turn a HIGH into a WARN for a repository that is not the allowlisted one.

### **Contact & Support**
- [`SUPPORT.md`](https://github.com/airlock-sec/airlock/blob/main/SUPPORT.md): where to ask, the commands CI runs, and the rules that most often get a pull request rejected
- [`SECURITY.md`](https://github.com/airlock-sec/airlock/blob/main/SECURITY.md): private disclosure only, never open an issue about a bypass
