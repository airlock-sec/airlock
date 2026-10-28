# project_structure.md: Airlock

Where everything lives, who may change it, and which way imports may point. Read this before creating or moving a file. Decisions behind the layout: `ARCHITECTURE.md` section 5. Work queue: `ROADMAP.md`.

> **Roadmap rule (every contribution):** any change to this repository, by a human or an agent, must update `ROADMAP.md` in the same pull request: tick or add tasks, add a changelog entry, refresh the progress table and the `Last updated` line. If you add, move or remove a file, also update this document.

Status: layout for v0.1.0 and v0.2.0. The directories, the package skeleton and `model.py`
exist; the task reference on each line says which task makes that entry real. A stub module
carries its planned behavior in its docstring and implements none of it, and the CLI exits 2
until the engine exists.

## 1. Annotated tree

```
airlock/
  .gitignore                       # git ignores only, never scan skips (no default skips)                 (1.4)
  README.md                        # user-facing: what it checks, install snippet, limits, roadmap rule      (1.10, 5.1)
  PRD.md                           # what and for whom                                                       (done)
  ARCHITECTURE.md                  # full design, data models, ADRs, red-team review                         (done)
  ARCHITECTURE_ESSENTIALS.md       # outline for agents: hard rules and key decisions                        (done)
  ROADMAP.md                       # all remaining work; updated on every contribution                       (done)
  AGENTS.md                        # how any coding agent works in this repo                                 (done)
  CLAUDE.md                        # Claude Code entry point; imports AGENTS.md                              (done)
  project_structure.md             # this file                                                               (done)
  CONTRIBUTING.md                  # human contributor guide; carries the roadmap rule                       (1.8)
  SECURITY.md                      # how to report a vulnerability in airlock itself                         (1.8)
  LICENSE                          # per decision D-02                                                       (1.1)
  action.yml                       # composite GitHub Action (protected)                                     (4.1)
  pyproject.toml                   # package metadata, ruff, mypy, pytest config                             (1.4)
  airlock.toml                     # dogfood policy and suppressions (protected)                             (4.3)
  wasm-manifest.toml               # dogfood Wasm manifest, keyed by hash (protected)                        (4.3)

  src/airlock/
    __init__.py                    # package docstring and __version__, the tool_version the report carries
    __main__.py                    # python -m airlock
    cli.py                         # argument parsing, command dispatch, exit codes                          (2.10)
    model.py                       # Severity, Mode, Finding, Rule, Policy, Manifest, ScanReport, FileEntry, ScanContext (2.1)
    collector.py                   # git ls-files, reads, decoding, limits, startup checks                   (2.2, 2.3)
    roles.py                       # glob matcher and content-magic role resolution                          (2.4)
    rules.py                       # rule loading, in-code validation, pattern engine, line cap              (2.5)
    fingerprint.py                 # occurrence-aware fingerprints                                           (2.6)
    policy.py                      # trusted-base resolution, suppressions, manifest loading                 (2.7, 2.8)
    runner.py                      # runs detectors, wraps exceptions as detector-error                      (2.11)
    strkey.py                      # Stellar strkey decode and CRC16-XModem (P1)                             (6.2)
    detectors/
      __init__.py                  # plain list of detector functions
      config_role.py               # P0                                                                      (3.1)
      wasm_manifest.py             # P0                                                                      (3.4)
      builtin_patterns.py          # P0, runs ported data rules                                              (3.6, 3.7)
      soroban_profile.py           # P1                                                                      (6.1)
      stellar_seed.py              # P1                                                                      (6.3)
      cargo_vectors.py             # P1                                                                      (6.4)
    report/
      console.py                   # (2.9)
      github.py                    # annotations with escaping, HIGH first, caps                             (2.9)
      jsonout.py                   # (2.9)
      summary.py                   # step summary with fenced, sanitized evidence                            (2.9)
      sarif.py                     # P1                                                                      (7.6)

  rules/
    roles.toml                     # role globs (protected)
    builtin/*.toml                 # data rules, one file per detector family (protected)

  scripts/
    bypass_probe.py                # roadmap 0.4: runs Appendix B against the external script it is given
    check_roadmap_touched.sh       # CI gate: PR must change ROADMAP.md                                      (1.9)
    roadmap_progress.py            # computes and checks the progress table                                  (1.9)

  tests/
    unit/                          # one test module per source module
    fixtures/                      # fixture BUILDERS (python), never live payload files
    bypass/                        # the seven regression tests from PRD Appendix B
    corpus/                        # clean-state snapshot of the six repos (no secrets)                      (0.10)
    golden/                        # JSON (and later SARIF) snapshots

  .github/
    CODEOWNERS                     # protected paths
    ISSUE_TEMPLATE/                # false positive, and missed detection or coverage gap
    pull_request_template.md       # includes the ROADMAP checkbox
    workflows/                     # tests, lint, scorecard, scan (dogfood), roadmap-check, release
```

Removed on purpose (do not recreate without a roadmap decision): `jsmask.py`, `wasmparse.py`, `detectors/deploy_gate.py`, `schema/`, `templates/`, an `init` command, a `rules test` command. See `ARCHITECTURE.md` 16.4.

## 2. Protected paths

Changes here are security-relevant. They need CODEOWNERS review and extra care from agents. Agents must not weaken any check in these paths without an explicit instruction from the owner.

| Path | Why |
|---|---|
| `src/airlock/policy.py`, `collector.py`, `runner.py` | Trust model and fail-closed behavior |
| `rules/` | Detection logic |
| `action.yml`, `.github/workflows/` | Supply chain of the tool itself |
| `airlock.toml`, `wasm-manifest.toml` | Dogfood policy; a bad edit disables checks |
| `scripts/` | The roadmap gate |
| `.github/CODEOWNERS` | Review enforcement |

## 3. Import rules (dependency direction)

```
model  <-  fingerprint, roles, rules  <-  collector, policy  <-  detectors  <-  runner  <-  report  <-  cli
```

- `model.py` imports nothing from the package.
- `detectors/*` import only from `model`, `roles`, `rules` and `fingerprint`. A detector never imports `report`, `cli` or another detector.
- `report/*` import only from `model`.
- Only `collector.py` and `policy.py` may call `subprocess`, always with a fixed argument list and never with a shell. `scripts/` may call `git`, and `bypass_probe.py` additionally runs the external script it is handed from the scratch repository it built; neither is under scan, since scanned content is never executed (README, "What it does not do").
- No module opens a network connection. No module imports third-party packages at runtime in v0.1.
- No import cycles. No module-level mutable state.

## 4. Where do I make a change?

| I want to | Edit | Also do |
|---|---|---|
| Add a detection rule | `rules/builtin/*.toml` | Add a fixture builder in `tests/fixtures/` with a positive and a negative case, and name it in the rule's `tests` table; the suite fails without them |
| Add a detector | `src/airlock/detectors/<name>.py`, register in `detectors/__init__.py` | Rule entries, fixtures, ROADMAP task, `ARCHITECTURE.md` 9, `ARCHITECTURE_ESSENTIALS.md` 7 |
| Add a file role | `rules/roles.toml` | Fixture for a matching and a non-matching path; false-positive check on `tests/corpus/` |
| Change policy fields | `model.py`, `policy.py`, `ARCHITECTURE.md` 7.6 | Bump handling of `version` if the change is breaking |
| Add an output format | `report/<name>.py` | Sanitization test; golden test |
| Add a bypass regression | `tests/bypass/` | Link it in `PRD.md` Appendix B |
| Change the Action | `action.yml` | Re-run task 4.1 and 4.5 style checks; `ARCHITECTURE.md` 10 |
| Change a hard rule or decision | `ARCHITECTURE_ESSENTIALS.md`, `ARCHITECTURE.md` section 13 | New ADR row; owner approval |
| Record a decision | `ROADMAP.md` section 7 | |

## 5. Naming conventions

- Rule IDs: kebab-case, prefixed by family (`cfg-`, `wasm-`, `soroban-`, `seed-`, `cargo-`). Stable once released; never reused.
- Finding IDs for states (not rules) use the same style (`history-rewritten`, `skipped-oversize`).
- Detector module: snake_case, same as its family (`config_role.py`).
- Fixture builder names match the rule ID with underscores (`cfg_dynamic_code`), one positive and one negative per rule.
- Test modules: `tests/unit/test_<module>.py`; bypass tests: `tests/bypass/test_bypass_<n>_<slug>.py`.
- Commits: Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`), subject under 72 characters.

## 6. Fixtures and corpus

- Fixtures that trigger rules are built at test time from fragments in `tests/fixtures/` builders and handed to the scanner as collected files (path, bytes, roles, hash), then run through the engine pass and the detector registry. The repository never stores a live-looking payload.
- `tests/corpus/` holds real, clean files copied from the six repos for false-positive and parity checks. Never copy secrets, tokens, real seeds or `.env` files into it. Review each added file by eye.
- Wasm fixtures are generated byte strings (`\0asm\x01\0\0\0` plus a trivial section), not compiled contracts.

## 7. Documentation map and sync rules

| Document | Purpose | Update when |
|---|---|---|
| `PRD.md` | Scope, users, requirements | A requirement, priority or metric changes |
| `ARCHITECTURE.md` | Design and decisions | Behavior, data models or ADRs change |
| `ARCHITECTURE_ESSENTIALS.md` | Short outline for agents; keep under about 150 lines | Any hard rule, decision or detector list changes |
| `ROADMAP.md` | Work queue, progress, changelog | **Every contribution** |
| `AGENTS.md`, `CLAUDE.md` | Agent instructions | Workflow, commands or boundaries change |
| `project_structure.md` | This map | A file or directory is added, moved or removed |
| `README.md`, `CONTRIBUTING.md` | Users and contributors | User-visible behavior or process changes |

If a code change contradicts a doc, fix the doc in the same PR. If a doc statement is [Unverified], do not build on it; run the task that verifies it (Phase 0).

## 8. Generated and derived files

- Rule reference docs are generated from `rules/*.toml` (task 5.2). Do not edit generated output by hand.
- The progress table in `ROADMAP.md` is computed by `scripts/roadmap_progress.py`. Do not edit the numbers by hand once the script exists.
