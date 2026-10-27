# ROADMAP: Airlock

Last updated: 2026-10-27 21:43 UTC
Roadmap version: 1

This file is the single source of truth for remaining work. It is read before every task and updated after every change.

## 0. The update rule (mandatory)

**Every contribution updates this file in the same pull request.** That covers code, rules, tests, docs, CI, configuration, dependency bumps and reverts, by humans and by agents. No exceptions.

Each PR must:

1. **Tick, untick or add tasks.** Change `[ ]` to `[x]` only when the task's "Done when" is true. Add a new task (with the next free ID in its phase) for any work discovered along the way.
2. **Add a changelog entry** in section 9: date (UTC), PR or commit, one-line summary, task IDs touched.
3. **Refresh the progress table** in section 2 (run `python scripts/roadmap_progress.py` once it exists, task 1.9; until then count by hand).
4. **Update `Last updated`** at the top of this file.
5. **Update the decision log** (section 7) if a decision was made, and the risk register (section 8) if a risk changed.

Enforcement: `scripts/check_roadmap_touched.sh` runs in CI as a required check (task 1.9) and the PR template carries a checkbox. Until task 1.9 is done, reviewers enforce this rule by hand. A PR that only edits this file is always allowed. This rule is repeated in `PRD.md` (14), `ARCHITECTURE.md` (17), `ARCHITECTURE_ESSENTIALS.md` (0), `project_structure.md`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md` and the PR template.

Conventions: sizes are relative effort, not calendar time (S under a couple of hours, M about half a day, L one to two days, XL several days). They are unmeasured guesses. "Deps" lists task IDs that must be done first. Task IDs are stable: never renumber, never reuse.

## 1. What "100% ready" means

The repository is 100% ready when every task in Phases 0 to 8 is done and every gate in section 3 is green. Phase 9 is backlog and does not count toward readiness.

- **v0.1.0** = Phases 0 to 5.
- **v0.2.0** = Phases 6 to 8.

## 2. Progress

<!-- PROGRESS:START -->
| Phase | Name | Done | Total | Progress |
|---|---|---|---|---|
| 0 | Decisions and validation | 4 | 16 | 25% |
| 1 | Repository bootstrap and self-protection | 2 | 12 | 17% |
| 2 | Core engine | 11 | 13 | 85% |
| 3 | P0 detectors | 0 | 10 | 0% |
| 4 | Action and dogfood | 0 | 7 | 0% |
| 5 | Release v0.1.0 | 0 | 6 | 0% |
| 6 | Stellar detectors | 0 | 5 | 0% |
| 7 | Hardening and edge cases | 0 | 12 | 0% |
| 8 | Release v0.2.0 and community | 0 | 5 | 0% |
| 9 (backlog) | Backlog | 0 | 10 | 0% |
| **Phases 0 to 8** | **Readiness total** | **17** | **86** | **20%** |
| Gates | G1 to G10 | 0 | 10 | 0% |
<!-- PROGRESS:END -->

Six of the thirteen Phase 2 rows were ticked late: the commits for 2.2 to 2.6 landed without a
roadmap update, which the roadmap rule does not allow, so they are recorded here as of
2026-10-27 with the tests that were run at the time.

The bootstrap tasks that read "done when merged" (1.3, 1.8, 1.10, 1.11) stay unticked until the
pull request lands, and 1.5 is not close: there is no CI workflow yet, so every check above was
run by hand on the owner's machine. Nothing reaches a user yet: `config_role` and
`wasm_manifest` are registered and policy resolution (2.7) reads the trusted base, but
suppression (2.8), the reporters (2.9) and the CLI (2.10) are stubs, so `airlock scan` still
exits 2 by design rather than reporting a scan that never ran.

## 3. Readiness gates

All must be true for 100%.

- [ ] **G1** Every P0 requirement (FR-01 to FR-15 in `PRD.md`) has passing tests.
- [ ] **G2** All seven bypass tests (PRD Appendix B) fail closed and run in CI.
- [ ] **G3** Parity test against `malware_scan.py` is green; no lost findings.
- [ ] **G4** Corpus gate: zero HIGH findings on the clean state of the six repos.
- [ ] **G5** airlock scans itself in CI with zero HIGH findings, and its Scorecard score is 8 or higher.
- [ ] **G6** Releases are attested, and the verification command is documented and tested.
- [ ] **G7** `PRD.md`, `ARCHITECTURE.md`, `ARCHITECTURE_ESSENTIALS.md`, `project_structure.md`, `AGENTS.md`, `CLAUDE.md` and `README.md` agree with the code.
- [ ] **G8** Required status checks (scan and roadmap gate) are configured on Airlock and on every dogfooded repo, and a PR that removes the scan step is blocked.
- [ ] **G9** No open item in the risk register (section 8) is rated High without a mitigation task or an accepted decision.
- [ ] **G10** This file is current: last updated within the latest merged PR.

## 4. Current focus

Phase 0, task 0.4: run the seven bypass tests against the existing `malware_scan.py`. Everything downstream depends on which of them are real.

The scaffold is landed and its gates are green, which closes 1.4 and 2.1. Next on that path
is 2.2 `collector.py`, the first module that touches untrusted input, and 1.5 CI so the same
checks stop depending on one machine. The 0.4 result still decides which Phase 3 rules are
real, so 0.4 remains the highest-value thing a person can do here.

## 5. Phases and tasks

### Phase 0: Decisions and validation (blocks everything)

- [x] **0.1** First drafts of `PRD.md`, `ARCHITECTURE.md`, `ARCHITECTURE_ESSENTIALS.md`. Done when: files exist. (done 2026-10-27)
- [x] **0.2** Red-team revision of those three docs (what breaks, missing edge cases, overengineering). Done when: `ARCHITECTURE.md` section 16 exists and the body reflects it. (done 2026-10-27)
- [x] **0.3** Draft `project_structure.md`, `AGENTS.md`, `CLAUDE.md` and this roadmap. Done when: files exist and carry the roadmap rule. (done 2026-10-27)
- [ ] **0.4** Run the seven bypass tests (PRD Appendix B) against the current `malware_scan.py` in a scratch repo. S. Done when: each test is recorded in the changelog as confirmed or refuted, and PRD 2.3 marks it Verified or Refuted.
- [x] **0.5** Decide D-01 (name), D-02 (license) and D-03 (host org). S. Done when: the decision log has an entry for each. (done 2026-10-27: Airlock, Apache-2.0, `airlock-sec/airlock`)
- [ ] **0.6** Search GitHub and the Stellar docs for existing Soroban or Stellar repo-hygiene tools. S. Done when: findings are in the changelog and PRD 2.4 is updated.
- [ ] **0.7** Check whether gitleaks and TruffleHog already detect Stellar secret seeds. S. Done when: D-06 (keep, narrow or drop `stellar_seed`) is decided.
- [ ] **0.8** Test `python3 -I -c` with an explicit `sys.path` insert in a scratch workflow on `ubuntu-latest`. S. Done when: result recorded; `ARCHITECTURE.md` 10 marked Verified or corrected.
- [ ] **0.9** Confirm GitHub limits from the docs: annotations per step, step summary size, SARIF size and result count, behavior of `github.event.before` (new branch, force push), `merge_group` events. S. Done when: numbers are in `ARCHITECTURE.md` 6.6 and 15 and marked Verified.
- [ ] **0.10** Build the clean-state corpus: copy tooling configs, Wasm fixtures and Cargo manifests from the six repos into `tests/corpus/` (no secrets). M. Done when: corpus is committed and documented. cost-profiler joins once it is public.
- [ ] **0.11** Read SEP-55 and SEP-58 text; record metadata keys and status. S. Done when: `PRD.md` 11 item 6 is answered.
- [ ] **0.12** Confirm from Cargo docs: profile handling in non-root manifests, resolver 2 feature unification for dev-dependencies, `crate-type` detection. S. Done when: `ARCHITECTURE.md` 9.3 marked Verified.
- [ ] **0.13** Confirm whether a required status check can be pinned to a trusted source, whether repository rulesets and required checks work on the `airlock-sec` org plan, whether org-level required workflows are available on that plan, and what happens when a required job is deleted. S. Done when: decision D-04 has the facts it needs.
- [ ] **0.14** Inspect `soroban-budget-assert`'s `Cargo.toml`: does it enable `testutils` under `[dependencies]`? S. Done when: B4 in `ARCHITECTURE.md` 16.2 is marked confirmed or refuted.
- [ ] **0.15** Check the name "Airlock" for collisions: PyPI package `airlock`, existing GitHub projects, security vendors and trademarks. S. Done when: result is in the changelog and risk R-8 is rated.
- [ ] **0.16** Record the `airlock-sec` org's plan, owner list and member list, and confirm which controls the plan provides (repository and org rulesets, required status checks, org-level required workflows). S. Done when: result recorded; decision D-04 and task 1.3 adjusted.

### Phase 1: Repository bootstrap and self-protection

- [x] **1.1** Create the repository under the chosen org. S. Deps: 0.5. Done when: repo exists with license and default branch. (done 2026-10-27: https://github.com/airlock-sec/airlock is public with an Apache-2.0 `LICENSE` and default branch `main`; one commit)
- [ ] **1.2** Harden maintainer accounts and the org: hardware-key or passkey 2FA, protected recovery email, review of active sessions and tokens, the org setting that requires 2FA for all members, and a minimal owner list. S. Done when: checked off by the owner (not verifiable by CI).
- [ ] **1.3** Configure rulesets: no force push, no deletion, require PR, required status checks; add `.github/CODEOWNERS` for `src/`, `rules/`, `action.yml`, `scripts/`, `.github/`, `airlock.toml`, `wasm-manifest.toml`. S. Deps: 1.1. Done when: a direct push to the default branch is rejected.
- [x] **1.4** Scaffold the package: `pyproject.toml` (hatchling, Python 3.11), `src/airlock/` skeleton, ruff, mypy and pytest config. S. Deps: 1.1. Done when: `pytest`, `ruff check` and `mypy src` run green on an empty skeleton. (done 2026-10-27: 67 tests pass, `ruff check` and `ruff format --check` clean, `mypy src --strict` clean over 24 files. `ruff` and `mypy` were installed as `uv` tools; system Python is externally managed under PEP 668, and `python3 -m venv` needs an apt package, so nothing was forced into it)
- [ ] **1.5** CI workflows for tests, lint and type check: every action pinned by hash, top-level `permissions: contents: read`. S. Deps: 1.4. Done when: CI is green on the skeleton.
- [ ] **1.6** Dependabot for GitHub Actions and pip, grouped weekly to limit noise. S. Deps: 1.1. Done when: config merged. Reminder: Dependabot PRs also need a roadmap changelog line.
- [ ] **1.7** Scorecard workflow with a fine-grained token so Branch-Protection can be read. S. Deps: 1.3. Done when: Branch-Protection returns a score, not an error.
- [ ] **1.8** `SECURITY.md`, `CONTRIBUTING.md` and `.github/pull_request_template.md` (with the roadmap checkbox), minimal issue templates. S. Deps: 1.1. Done when: each carries the roadmap rule.
- [ ] **1.9** Roadmap gate: `scripts/check_roadmap_touched.sh` (fails if the PR diff changes any file but not `ROADMAP.md`, or `Last updated` did not change), `scripts/roadmap_progress.py` (computes the progress table; `--check` fails if the table is stale) and a `roadmap-check.yml` workflow made a required check. M. Deps: 1.5. Done when: a test PR without a roadmap edit fails and one with it passes.
- [ ] **1.10** `README.md` skeleton: what it is, status, quickstart placeholder, roadmap rule. S. Deps: 1.1. Done when: merged.
- [ ] **1.11** Copy the doc set into the repo root: `PRD.md`, `ARCHITECTURE.md`, `ARCHITECTURE_ESSENTIALS.md`, `ROADMAP.md`, `AGENTS.md`, `CLAUDE.md`, `project_structure.md`. S. Deps: 1.1. Done when: merged.
- [ ] **1.12** Rename sweep: `AGENTS.md`, `ARCHITECTURE.md`, `ARCHITECTURE_ESSENTIALS.md` and `CLAUDE.md` still call the tool repo-guard in 37 places (`src/repo_guard/`, `repo-guard.toml`, `python -m repo_guard`), contradicting D-01 and the code scaffolded under `src/airlock/`. `project_structure.md` is already corrected. S. Deps: 1.1. Done when: no `repo-guard` or `repo_guard` spelling survives outside this roadmap's changelog, so gate G7 can be checked honestly.

### Phase 2: Core engine

- [x] **2.1** `model.py`: Severity, Mode, Finding, Rule, Policy, Manifest, ScanReport; policy `version` handling and `policy-unknown-key`. M. Deps: 1.4. Done when: unit tests cover construction, ordering and version errors. (done 2026-10-27 for the model half: all seven types plus `Suppression`, `ReleaseProfile` and the `BOOTSTRAP_POLICY` defaults, version rejection tested, HIGH-first ordering tested. Carve-out: the known-key sets are constants here, and the `policy-unknown-key` finding itself is emitted by the TOML loader in 2.7. `FileEntry` and `ScanContext` are drafted ahead of need and are settled by 2.13)
- [x] **2.2** `collector.py`: `git ls-files -z --stage`, submodule entries, symlinks, size limit, BOM-aware decoding, `non-utf8-text`, `nul-in-text`, line cap, no default directory skips, paths with unusual characters. L. Deps: 2.1. Done when: tests for each case pass. (done 2026-10-27: null-delimited staging, gitlinks, tracked symlinks read but never followed, oversize, unreadable, BOM and UTF-16 handling, `non-utf8-text`, `nul-in-text`, no default directory skips, paths with spaces. 24 collector tests)
- [x] **2.3** Startup checks: Python version, `git` present, repo readable (including `safe.directory`). Exit 2 with a plain message. S. Deps: 2.2. Done when: each failure path has a test. (done 2026-10-27: `check_runtime` refuses an interpreter below 3.11, a missing `git`, and a directory git will not open, returning the message the CLI turns into exit 2; tested for each path. The `safe.directory` hint is in the message, and the CLI wiring lands with 2.10)
- [x] **2.4** `roles.py` plus `rules/roles.toml`: custom glob matcher (`**`, `*` never crosses `/`), content magic for Wasm and native binaries. M. Deps: 2.1. Done when: a lone `*` pattern does not match across directories; renamed `.wasm` resolves. (done 2026-10-27: hand-written segment matcher, Wasm, Mach-O, PE and archive magic before any extension, and `known_roles` as the cross-check the rule loader uses)
- [x] **2.5** `rules.py`: rule loader and in-code validation, pattern engine with `line_cap`, `cfg-long-line` emission. M. Deps: 2.1, 2.4. Done when: invalid rule files exit 2; long lines skip regex. (done 2026-10-27: TOML rules with in-code validation, duplicate id, unknown role and unknown detector cross-checks, and the line cap split out of the pattern engine as `cap_findings` so the runner reports withheld lines whatever the registry holds)
- [x] **2.6** `fingerprint.py`: occurrence-aware fingerprints. S. Deps: 2.1. Done when: a duplicated line yields a distinct fingerprint. (done 2026-10-27: occurrence numbering over a stable sort; deleting an earlier duplicate shifts the index and un-suppresses the survivor, which fails closed)
- [x] **2.7** `policy.py`: trusted-base resolution for `pr`, `push` and `full`; `history-rewritten`, `no-trusted-base`, `policy-changed`, `untrusted-policy-source`; bootstrap defaults. L. Deps: 2.1, 2.3. Done when: the trusted-base tests (policy edit plus payload, force push, new branch, unresolvable base) pass. (done 2026-10-27: `resolve_policy` returns the policy and the manifest read from the trusted ref, plus the state findings that say why the ref is weaker; `policy_from_toml` and `manifest_from_toml` parse the two files and report unknown keys instead of dropping them; `pr` mode refuses an unresolvable base rather than reading HEAD. All four named tests pass against real temporary git repositories, including the B1 case: one commit that edits `airlock.toml`, adds a suppression for a HIGH rule and adds the payload is judged by the base copy with no suppressions at all. Two defects surfaced on the way: the dogfood `airlock.toml` was not valid TOML (an inline table written across two lines, which the 7.6 sketch copies), and a state finding with no evidence crashed `number_occurrences` instead of reporting. Verified: `pytest` 284 passed, `ruff check` and `ruff format --check` clean on 35 files, `mypy src` clean on 24 files. Not verified: suppression application, which is 2.8, and an end-to-end scan, which is 2.10)
- [x] **2.8** Suppression application: required fields, non-suppressible rules, `suppression-invalid`, `suppression-expiring` (30 days), UTC date comparison. M. Deps: 2.6, 2.7. Done when: tests cover each path. (done 2026-10-27: `suppress` takes numbered findings plus the trusted policy and returns what gets reported and what an entry covers, each in report order, with the entry's reason carried on `suppressed_by`. Matching needs rule, path and fingerprint together; an expired entry only returns the finding; `expires` within 30 days, the day itself included, warns; an entry whose rule is missing, non-suppressible or a scanner-state id is HIGH `suppression-invalid` and covers nothing. `today` is a parameter, so no test depends on the clock. All paths in `tests/unit/test_suppression.py`)
- [x] **2.9** Reporters: console, GitHub annotations (escaping, HIGH first, WARN cap), JSON, step summary (fenced, sanitized evidence). M. Deps: 2.1. Done when: injection and flooding tests pass. (done 2026-10-27: `report/console.py`, `report/github.py`, `report/jsonout.py` and `report/summary.py` each render the same `ScanReport`. Injection tests cover a newline in a message trying to forge a second annotation, a `:`/`,` in a path trying to break the property list, and evidence carrying a fence, a link or a table row; flooding tests put 500 WARNs behind 1 HIGH and 20 HIGHs behind 400 WARNs. 6.6 records that the caps are reporter constants while the GitHub limits stay unverified)
- [x] **2.10** `cli.py`: `scan` and `manifest add|check`, exit codes, deterministic ordering. M. Deps: 2.7, 2.9. Done when: CLI integration tests pass. (done 2026-10-27: `run_scan` is the pipeline in one ordered function and `main` maps every outcome onto 0, 1, 2 or 3. One numbering pass covers the collector's skips, the policy's state findings and the engine plus detector findings together, so occurrence indices cannot depend on dispatch order. `--event` maps the four known events onto a trust model and an unknown or contradicting one is a usage error. `manifest add` and `manifest check` parse and then refuse with exit 2 until 3.5 writes them. Integration tests drive real temporary git repositories: B1 through the CLI, a force push, a new branch, a suppression written from a fingerprint the scan itself printed, and an entry for a rule the shipped data marks non-suppressible)
- [x] **2.11** `runner.py`: run detectors, wrap exceptions as `detector-error`. S. Deps: 2.1. Done when: a raising detector yields HIGH and exit 1. (done 2026-10-27 for the engine: `engine_findings` runs the pattern rules and the cap account over every entry with text, `collect` dispatches the registry in order, a raising detector keeps what it already yielded and adds one HIGH `detector-error`, and the next detector still runs. Exit 1 is 2.10's, since there is no CLI path to it yet)
- [ ] **2.12** ReDoS timing harness and fixture-coverage test (every rule has a positive and a negative fixture). M. Deps: 2.5. Done when: the suite fails on a rule with no fixtures or a slow pattern.
- [ ] **2.13** Settle the `FileEntry` and `ScanContext` drafts added to `model.py`: they currently carry only the fields `ARCHITECTURE.md` 6.1 and 6.3 describe, and `ARCHITECTURE.md` 7 lists neither. S. Deps: 2.2, 2.11. Done when: no field is unused, no detector needs a field the model lacks, and 7.x documents both.

### Phase 3: P0 detectors

- [ ] **3.1** *(in progress 2026-10-27: detector and rule data written, 18 detector tests over the shipped rules; the fixture builders in `tests/fixtures/` and the coverage gate in 2.12 are what is left)* `config_role` with tiered rules (`cfg-dynamic-code`, `cfg-network-exec`, `cfg-network`, `cfg-process-spawn`, `cfg-chain-endpoint`, `cfg-appended-tail`, `cfg-long-line`, `cfg-nul`). L. Deps: 2.5, 2.11. Done when: all positive fixtures fire and no negative fixture does.
- [ ] **3.2** Synthetic fixture builders for `config_role` (strings assembled at test time). M. Deps: 2.12. Done when: no committed file contains a live-looking payload.
- [ ] **3.3** Tune `tail_max_len` and `tail_entropy` on the corpus. S. Deps: 0.10, 3.1. Done when: thresholds recorded with the evidence.
- [ ] **3.4** *(in progress 2026-10-27: detector written and tested against the shipped rules, including the LFS-pointer shape and the stale/mismatch overlap; fixtures and 2.12 pending)* `wasm_manifest`: hash-keyed matching, `wasm-unlisted`, `wasm-hash-mismatch`, `wasm-path-moved`, `wasm-manifest-stale`, `wasm-archive-skipped`. M. Deps: 2.4, 2.11. Done when: fixtures pass.
- [ ] **3.5** `manifest add` and `manifest check`, including a hand-written TOML writer. M. Deps: 3.4, 2.10. Done when: adding a fixture takes one command and round-trips.
- [ ] **3.6** Port HIGH rules from `malware_scan.py` as data rules (invisible Unicode, exfiltration endpoints, decode-and-eval, obfuscator identifiers, credential harvesting, blockchain C2, workflow secret dump, install-hook dropper, VS Code auto-run, `pull_request_target` checkout, `build.rs` network, native binary). L. Deps: 2.5. Done when: each has fixtures.
- [ ] **3.7** Port WARN rules. M. Deps: 3.6. Done when: each has fixtures.
- [ ] **3.8** Parity test harness: old script versus ported rules on a shared corpus. M. Deps: 3.6, 3.7, 0.10. Done when: no lost findings (differences explained in the changelog).
- [ ] **3.9** Bypass regression tests for all seven Appendix B cases under `tests/bypass/`. M. Deps: 0.4, 3.1, 3.4. Done when: all seven fail closed.
- [ ] **3.10** Self-scan test: Airlock passes its own scan with no `SELF` skip. S. Deps: 3.9. Done when: the test runs in CI.

### Phase 4: Action and dogfood

- [ ] **4.1** `action.yml` composite Action (`python3 -I -c` path trick, `env:` passing, events `pull_request`, `push`, `workflow_dispatch`). M. Deps: 0.8, 2.10. Done when: it runs on a scratch repo for each event.
- [ ] **4.2** Caller workflow snippet and usage docs (checkout with `fetch-depth: 0`, read-only permissions, full-SHA pin, required status check, two-step Wasm fixture flow). S. Deps: 4.1. Done when: snippet tested.
- [ ] **4.3** Dogfood on `Tollcraft/soroban-budget-assert` first; fix false positives. M. Deps: 4.1, 3.10. Done when: zero HIGH on clean state.
- [ ] **4.4** Dogfood on the remaining repos (`soroban-cost-linter`, `accensa-app`, `accensa-contracts`, `x402-facilitator-stellar`, and `soroban-cost-profiler` when public); replace the copy-pasted `malware-scan.yml` and script. L. Deps: 4.3. Done when: the old script is gone from each repo.
- [ ] **4.5** Configure the required status check on each dogfooded repo; test that a PR deleting the scan step is blocked and that a push editing policy plus a payload is caught. M. Deps: 0.13, 4.4. Done when: both tests are demonstrated and recorded. Gate G8.
- [ ] **4.6** Corpus gate in CI: zero HIGH on the clean snapshot. S. Deps: 0.10, 3.10. Done when: it blocks merges.
- [ ] **4.7** Record before and after Scorecard scores for the six repos. S. Deps: 4.4. Done when: numbers are in the changelog.

### Phase 5: Release v0.1.0

- [ ] **5.1** `README.md` complete: what it checks, what it does not, install snippet, limits, threat model summary, roadmap rule. M. Deps: 4.2. Done when: a new user can install in under five minutes.
- [ ] **5.2** Usage docs and rule reference (generated from `rules/*.toml`). M. Deps: 3.7. Done when: every rule has a documented ID, severity and rationale.
- [ ] **5.3** Release workflow with build provenance attestation; documented and tested verification command; note on reviewing Action SHA bumps. M. Deps: 1.5. Done when: a test release verifies.
- [ ] **5.4** Reach a Scorecard score of 8 or higher on the repo. M. Deps: 1.7. Done when: score recorded. Gate G5.
- [ ] **5.5** Tag `v0.1.0`; publish the commit SHA consumers should pin. S. Deps: 4.7, 5.1 to 5.4. Done when: tag exists and gates G1 to G10 are reviewed for v0.1.
- [ ] **5.6** Update the LinkedIn post with measured numbers (before and after Scorecard, bypasses found and fixed), not intentions. S. Deps: 5.5. Done when: published.

### Phase 6: Stellar detectors (v0.2)

- [ ] **6.1** `soroban_profile`: contract-crate detection, workspace-root profile check, `testutils` placement, `profile-ignored`. L. Deps: 0.12, 0.14, 3.10. Done when: no false positive on a test-support library crate.
- [ ] **6.2** `strkey.py` with reference test vectors. M. Deps: 0.7. Done when: vectors pass.
- [ ] **6.3** `stellar_seed` detector (scope per D-06). M. Deps: 6.2. Done when: fixtures pass; checksum-invalid strings do not fire.
- [ ] **6.4** `cargo_vectors`. M. Deps: 3.10. Done when: fixtures pass.
- [ ] **6.5** Fixtures and dogfood for Phase 6 detectors on the Rust repos. M. Deps: 6.1, 6.3, 6.4. Done when: zero HIGH false positives.

### Phase 7: Hardening and edge cases (v0.2)

- [ ] **7.1** Git LFS pointer handling and the Wasm-as-base64 gap documented. M. Deps: 3.4.
- [ ] **7.2** Submodule handling beyond INFO. S. Deps: 2.2.
- [ ] **7.3** Encoding tests: UTF-16 with BOM, non-UTF-8, CRLF. S. Deps: 2.2.
- [ ] **7.4** Extended config globs (`vite`, `webpack`, `rollup`, `jest`, `svelte`, `astro`, `.eslintrc.*`, `.babelrc.*`, `prettier`, `commitlint`) with false-positive review. M. Deps: 3.3.
- [ ] **7.5** Evaluate and add vector roles: `.husky/*`, `.devcontainer/devcontainer.json`, composite action files, `Makefile`, `justfile`. M. Deps: 7.4.
- [ ] **7.6** SARIF 2.1.0 output with result cap and golden tests. M. Deps: 2.9, 0.9.
- [ ] **7.7** Large-repo performance test and measured runtime target. M. Deps: 4.4.
- [ ] **7.8** Windows runner, path separator and case-insensitive path tests. S. Deps: 2.2.
- [ ] **7.9** Event matrix tests: fork PRs, `merge_group`, tag pushes, first commit, base equals head, base not an ancestor, rename detection. M. Deps: 4.1.
- [ ] **7.10** Output flooding tests: HIGH always visible despite caps. S. Deps: 2.9.
- [ ] **7.11** Suppression churn tests: expiry warning, occurrence reindexing after edits. S. Deps: 2.8.
- [ ] **7.12** Settle the SARIF `partialFingerprints` key: `ARCHITECTURE.md` 6.6 still names it `repoGuard/v1` while the package is `airlock`. Decide the spelling before 7.6 emits output consumers store. S. Deps: 1.12.

### Phase 8: Release v0.2.0 and community

- [ ] **8.1** Update every doc for v0.2 behavior (`PRD.md`, `ARCHITECTURE.md`, `ARCHITECTURE_ESSENTIALS.md`, `project_structure.md`, `README.md`, `AGENTS.md`, `CLAUDE.md`). M. Deps: Phases 6 and 7. Gate G7.
- [ ] **8.2** Tag `v0.2.0` with attestation. S. Deps: 8.1.
- [ ] **8.3** Review false-positive reports from the first external users and adjust rules. M. Deps: 8.2.
- [ ] **8.4** Decide D-05: submit to SCF or Drips Wave, and prepare the application with adoption evidence. M. Deps: 8.2.
- [ ] **8.5** Outreach to Stellar maintainers (post, docs, demo). S. Deps: 8.2.

### Phase 9: Backlog (not counted toward readiness)

- [ ] **9.1** Watch mode: scheduled job in a separate trusted repository that clones public repos, runs the scan and rejects non-fast-forward updates to the last seen SHA. Decision D-04 first. Covers B2.
- [ ] **9.2** Org scan and workflow-drift report.
- [ ] **9.3** History scan of reflog and unreachable objects.
- [ ] **9.4** Parser-based JavaScript analysis.
- [ ] **9.5** SEP-58 metadata presence check and Wasm section parser (after the SEP is final).
- [ ] **9.6** `deploy_gate` (only if a real repo deploys to mainnet from CI).
- [ ] **9.7** Release-provenance rule (motivated by `accensa-contracts` v0.2.0).
- [ ] **9.8** Workflow-combination rule: write token plus unpinned third-party action (motivated by `soroban-cost-linter`).
- [ ] **9.9** PyPI distribution with trusted publishing. Check first that the PyPI name `airlock` is free; it may be taken [Guessing].
- [ ] **9.10** Optional advisory-triage integration (consume cargo-audit or cargo-deny output).

## 6. Dependency map (critical path)

`0.4, 0.5 -> 1.1 -> 1.4 -> 2.1 -> 2.2, 2.4, 2.5, 2.7 -> 3.1, 3.4, 3.6 -> 3.9, 3.10 -> 4.1 -> 4.3 -> 4.4 -> 4.5 -> 5.5`

Parallelizable early: 0.6 to 0.14, 1.2, 1.6, 1.8, 1.10. The roadmap gate (1.9) should land before most Phase 2 work so every later PR is checked.

## 7. Decision log

| ID | Decision | Status | Notes |
|---|---|---|---|
| D-01 | Project name | Decided 2026-10-27 | Airlock; CLI `airlock`; Python package `airlock`; collision check is task 0.15 |
| D-02 | License | Decided 2026-10-27 | Apache-2.0; the `LICENSE` file is already in the repository [Verified: repository page] |
| D-03 | Host account | Decided 2026-10-27 | `airlock-sec/airlock`; `airlock-sec` is a GitHub organization (confirmed by the owner; an earlier reading of the repository page suggested a user account, which was wrong). The org plan decides which controls exist (task 0.16). A new repo likely needs its own Drips Wave application [Unverified] |
| D-04 | Build the external watcher (task 9.1)? | Open | Decide after 0.13 and after dogfooding; it is the only design that survives a stolen credential [Likely] |
| D-05 | Pursue SCF or Drips Wave funding | Open | Needs adoption evidence first |
| D-06 | Keep, narrow or drop `stellar_seed` | Open | Depends on task 0.7 |
| D-07 | Roadmap gate has no exemptions, including dependency bumps | Decided 2026-10-27 | Matches the owner's instruction; Dependabot is grouped weekly to limit noise |
| D-08 | Cut jsmask, SARIF-in-v0.1, `init`, `rules test` CLI, `deploy_gate`, SEP-58 parser from v0.1 | Decided 2026-10-27 | `ARCHITECTURE.md` 16.4 |

## 8. Risk register

| ID | Risk | Rating | Mitigation or task |
|---|---|---|---|
| R-1 | Attacker with push access removes the scanner step (B2) | High | 0.13, 4.5, decision D-04 |
| R-2 | Config-role false positives erode trust | High | 3.2, 3.3, 4.6 |
| R-3 | Bootstrap friction for new Wasm fixtures (B9) | Medium | Two-step flow documented in 4.2; revisit after dogfood |
| R-4 | Solo-maintainer burnout and scope growth | Medium | Phase 9 is closed to work until v0.1.0 ships |
| R-5 | Unverified GitHub behaviors (limits, `before`, required-check semantics) | Medium | 0.9, 0.13 |
| R-6 | Existing script's bypasses not actually real, wasting design effort | Low | 0.4 settles it early |
| R-7 | Market too narrow | Medium | Track adoption; D-05 |
| R-8 | Name collision with an existing security product, package or trademark [Unverified] | Medium | 0.15 |
| R-9 | The `airlock-sec` org plan may lack some ruleset or org-level required-workflow features [Unverified] | Low | 0.16, 1.3; if gaps remain, strengthens D-04 |

## 9. Changelog

Newest first. One row per merged change.

| Date (UTC) | Change | Tasks |
|---|---|---|
| 2026-10-27 21:43 | `cli.py` is the pipeline: startup checks, trusted base, rule data, collection, engine pass and detectors, one numbering pass, suppression, reporters. `airlock scan` runs, and the repository scanning itself clean (64 files, nothing skipped, two INFO `untrusted-policy-source` for reading policy out of the working tree in `full` mode, exit 0) is the first end-to-end proof of the design. Exit codes are as documented: 0 for nothing at or above `fail_on`, 1 for something, 2 for configuration and usage, 3 for internal error, and an unborn repository or an absent directory is 2 rather than a quiet 0. `--event` maps `pull_request`, `push`, `workflow_dispatch` and `schedule` onto a trust model; an unmapped event, or an event contradicting `--mode`, is a usage error, because choosing a trust model silently is the bypass B1 is about. All three trust models are now exercised through the CLI and not only against `resolve_policy`: a pull request whose change weakens the policy, suppresses a HIGH rule and adds the payload still exits 1 and still names the payload; a force push yields `history-rewritten`; a new branch yields `no-trusted-base` and inherits nothing. Suppression is reachable for real, which is the sequence 2.8 was written for: a `full` scan prints the fingerprint in JSON, the entry written from that digest silences exactly that finding, the JSON still lists it under `suppressed` with its reason, and an entry aimed at `cfg-dynamic-code` (which the shipped rule data marks non-suppressible) returns `suppression-invalid` with the payload still reported. The step summary goes to `$GITHUB_STEP_SUMMARY` alongside whatever `--format` chose, because annotations are for the commit author and the summary is for the reviewer who has to see every HIGH. README status and quickstart, PRD 6.3 and the runner note are corrected to match shipped behavior. Verified: `pytest` 395 passed (29 new CLI tests), `ruff check` and `ruff format --check` clean on 37 files, `mypy src` clean on 24 files, plus a manual self-scan in each of the four formats. Not verified: `pr` mode with a base SHA as GitHub supplies it, and any of this inside a workflow, which is 4.1 | 2.10, 2.7, 2.8, 2.9, B1 |
| 2026-10-27 21:32 | The four P0 reporters render a `ScanReport`. console: one line per finding plus a summary line carrying severity counts, the suppressed count and the skip accounting, with no color so the same bytes reach a pipe, a log and a TTY. github: `::error`, `::warning` and `::notice`, `%` escaped before CR, LF, `:` and `,` so nothing survives a second decode, and properties and bodies escaped by their own separate rules; findings arrive HIGH-first so the survivors of a cap are the HIGHs, and every capped severity ends with one annotation naming what went unlisted, which is what stops a WARN flood from making a HIGH look absent and a capped HIGH list from looking complete. json: the whole model with keys sorted, severities as labels, and every suppressed finding kept with its reason, so one run diffs against the next. summary: counts, the skip table, every HIGH enumerated while WARNs are counted and never listed, and evidence only ever inside a fence computed as one longer than the longest backtick run anywhere in the block, flattened and cut to 200 characters. Escaping outside the fence covers only the characters that can form markup mid-line, after an first draft escaped `-` too and turned every rule id into `cfg\-dynamic\-code`. Caps live as reporter constants rather than policy settings, because GitHub's annotation and summary limits are still unverified (0.9) and a repository must not be able to raise them. Verified: `pytest` 366 passed (49 new), `ruff check` and `ruff format --check` clean on 37 files, `mypy src` clean on 24 files. Not verified: how many annotations GitHub actually renders, and any of this reaching a real run before the CLI (2.10) | 2.9, 2.1, B8, B11 |
| 2026-10-27 21:23 | `suppress()` applies the trusted policy's entries after numbering and before the reporters: matching needs rule, path and fingerprint together, so a second copy of a suppressed line is its own occurrence and returns unsuppressed (B5); an expired entry stops applying and says nothing else, because the returning finding is the signal (B10); `expires` inside 30 days, the day itself included, yields `suppression-expiring` (WARN); the clock is a parameter, so a run is reproducible. An entry naming a rule that is missing, non-suppressible or a scanner-state id yields `suppression-invalid` (HIGH), and on the first run of this task it covered the finding as well while the report complained about it: validity is now decided before matching, which is what 7.6 said all along. Entries are checked against the rule data rather than against this scan's findings, so a renamed or retightened rule is reported even when the entry matched nothing. Suppressed findings stay in the result carrying the entry's reason, since a reader has to see what a policy hid. Verified: `pytest` 317 passed (33 new), `ruff check` and `ruff format --check` clean on 36 files, `mypy src` clean on 24 files. Not verified: suppressions reached through a real CLI run, which is 2.10 | 2.8, 2.6, 2.7, 7.6 |
| 2026-10-27 21:04 | `policy.py` resolves the trusted base and loads the two protected files. `pr` mode takes the PR base SHA and exits 2 when it is missing, malformed or unreachable, because the alternative is judging a change by the policy the change wrote. `push` mode takes `github.event.before`: all-zeros is a new branch, and anything that is not an ancestor of HEAD is a rewrite; both scan against `BOOTSTRAP_POLICY` and an empty manifest, which carry no suppressions. `full` mode reads the working tree and says so with `untrusted-policy-source` (INFO). Both files are compared with their HEAD copies, so a policy edit inside the change yields `policy-changed` (WARN) with a line-count summary and no diff text, and the base copy is what the scan runs. Unknown keys in either file come back as `policy-unknown-key` (WARN) naming the dotted key, because a misspelled setting otherwise vanishes into its default; a missing or unsupported `version`, bad TOML and a malformed suppression stay exit 2. Suppression application is 2.8, so `Policy.suppressions` is parsed and not yet used. Two defects found by writing this: the dogfood `airlock.toml` did not parse at all (an inline table across two lines is not valid TOML, and `ARCHITECTURE.md` 7.6 showed the same shape, so both are corrected), and a scanner-state finding with no evidence raised inside `number_occurrences`, which would have crashed the first scan of any repository containing a submodule, a symlink or an oversized file; state findings now key on their message, which is scanner-written and non-suppressible. 7.3 records that rule. Verified: `pytest` 284 passed (55 new, all four named trusted-base cases against real temporary git repositories), `ruff check` and `ruff format --check` clean on 35 files, `mypy src` clean on 24 files. Not verified: an end-to-end scan, and the `pr` base SHA as GitHub actually supplies it, which needs the Action (4.1) | 2.7, 2.1, 2.6, 7.3 |
| 2026-10-27 20:42 | `config_role` and `wasm_manifest` implemented over the shipped rule data, and `runner.py` dispatches them. Rules are split by owner: the engine pass runs the `pattern` rules and the `line_cap` account for every file with text, while a `builtin:` rule may carry a pattern only its detector reads. That is how `cfg-process-spawn` keeps both tiers (WARN for a build step stated up front, HIGH when the command names a downloader, a decoder or an inline script) without the same line being reported twice. `cfg-long-line` moved out of `apply_patterns` into `cap_findings` for the same reason as 2.3: a withheld line must be accounted for whatever the registry holds. `wasm_manifest` stops calling an entry stale when its declared path still holds a file, so one swapped artifact yields one finding, and a file named `.wasm` with no Wasm header is reported as the pointer shape it is. A detector that raises keeps the findings it already yielded and adds one HIGH `detector-error`. 2.11 ticked; 3.1 and 3.4 annotated as in progress with what is left. Also corrected here: 2.2 to 2.6 were merged without the roadmap update the rule requires. Verified: `pytest` 229 passed, `ruff check` and `ruff format --check` clean on 34 files, `mypy src` clean on 24 files. Not verified: an end-to-end scan, since the CLI still refuses to report a scan that did not run | 2.11, 3.1, 3.4, 2.2, 2.3, 2.4, 2.5, 2.6 |
| 2026-10-27 19:07 | Scaffold committed on branch `feat/1.4-scaffold` (not yet merged): package tree per `project_structure.md` with behavior documented in each stub and nothing implemented (`cli.py` exits 2 so an unbuilt tool cannot read as a pass), `model.py` data models with 67 unit tests, `pyproject.toml` (hatchling, ruff, mypy, pytest), `rules/roles.toml`, dogfood `airlock.toml` and `wasm-manifest.toml`, `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `.github/CODEOWNERS` and the PR template, `.gitignore`, and the doc set copied to the repo root. `project_structure.md` renamed from repo-guard to airlock. Added 1.12 (rename sweep in the four remaining docs, 37 stale references), 2.13 (`FileEntry` and `ScanContext` drafts to confirm) and 7.12 (SARIF fingerprint key spelling). 1.3, 1.8, 1.10 and 1.11 stay open until merge | 1.4, 1.8, 1.10, 1.11, 2.1, 1.12, 2.13, 7.12 |
| 2026-10-27 19:15 | Closed the scaffold gates: installed `ruff` 0.17 and `mypy` 2.4 as `uv` tools (system Python is externally managed and `python3 -m venv` needs an apt package, so neither was forced in), then fixed what they found. `ruff check` flagged three items in the tests: an unsorted import block, a `pytest.raises(match=...)` pattern carrying an unescaped alternation, and a reversed comparison. `ruff format` revealed a larger problem: it also rewrites Python fences inside Markdown, and it reformatted `ARCHITECTURE.md`. That change was reverted and `*.md` is now in `tool.ruff.extend-exclude`, because the design documents must stay reviewable and the roadmap rule depends on their diffs being legible. Verified: `pytest` 67 passed, `ruff check` clean, `ruff format --check` clean on 26 files, `mypy src --strict` clean on 24 files. Not verified: the self-scan, since `airlock scan` deliberately exits 2 until Phase 2 exists | 1.4, 2.1 |
| 2026-10-27 | Correction: `airlock-sec` is a GitHub organization, not a user account. Removed the user-account assumption from D-03, risk R-9, PRD risks and open questions; reframed 0.16 as an org plan and controls check; added the org 2FA requirement to 1.2 | 0.13, 0.16, 1.2 |
| 2026-10-27 | Project named Airlock; repository `airlock-sec/airlock` (public, Apache-2.0, default branch `main`) adopted. Renamed `repo-guard` to `airlock` across all docs (CLI, package, policy file `airlock.toml`, env prefix `AIRLOCK_`). Added name-collision and account-type checks | 0.5, 0.15, 0.16, 1.1 |
| 2026-10-27 | Drafted `project_structure.md`, `AGENTS.md`, `CLAUDE.md` and this roadmap; red-team revision of `PRD.md`, `ARCHITECTURE.md`, `ARCHITECTURE_ESSENTIALS.md` (v0.2) | 0.2, 0.3 |
| 2026-10-27 | First drafts of `PRD.md`, `ARCHITECTURE.md`, `ARCHITECTURE_ESSENTIALS.md` | 0.1 |
