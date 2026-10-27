# ARCHITECTURE: repo-guard (working name)

| | |
|---|---|
| Status | Draft v0.2 (red-team revision) |
| Date | 2026-10-27 |
| Companion docs | `PRD.md`, `ARCHITECTURE_ESSENTIALS.md`, `ROADMAP.md`, `project_structure.md`, `AGENTS.md`, `CLAUDE.md` |
| Tags | **[Verified]** checked against a source; **[Unverified]** believed or designed but untested |

---

> **Roadmap rule (every contribution):** any change to this repository, by a human or an agent, must update `ROADMAP.md` in the same pull request: tick or add tasks, add a changelog entry, refresh the progress table and the `Last updated` line. See section 17.

## 1. Context and constraints

repo-guard scans a git repository and reports supply-chain risk. It runs in two places: a developer's machine and a GitHub Actions runner. The scanned repository is untrusted input, because the scan exists to catch a repo (or a PR to it) that has been tampered with.

Hard constraints that shape everything below:

1. **The tool must not execute scanned content.** No imports, no `eval`, no shelling out with file-derived strings.
2. **The tool must not be controlled by the scanned tree.** Code, policy and suppressions need a trust path that does not run through the PR head.
3. **Unreadable means unsafe.** Any file the tool cannot fully inspect becomes a finding.
4. **A solo maintainer must be able to own it.** Small surface area, no runtime dependencies in v0.1, no services.
5. **Offline.** No network during a scan; no telemetry.

## 2. Tech stack

| Concern | Choice | Reason |
|---|---|---|
| Language | Python 3.11 or newer | Existing scanner is Python; `tomllib` is in the standard library from 3.11; GitHub-hosted Ubuntu runners ship Python 3 [Unverified: minor version on `ubuntu-latest` at release time] |
| Runtime dependencies | None (standard library only) | Smallest supply-chain surface for a supply-chain tool; no `pip install` step in the Action |
| TOML reading | `tomllib` | Standard library |
| TOML writing | Hand-written serializer for the three known schemas | The standard library has no TOML writer; the schemas are flat enough |
| YAML | Not parsed in v0.1 | No standard-library YAML; workflow checks use conservative text heuristics (see ADR-007) |
| Git access | `subprocess` calling `git` with fixed argument lists, no shell | Reads tracked files and base-ref blobs |
| Hashing | `hashlib` (SHA-256) | Standard library |
| Output formats | Console text, GitHub workflow commands, JSON, step summary (SARIF in v0.2) | CI-native; SARIF deferred because it needs an extra permission and upload step |
| Packaging | `pyproject.toml`, `src/` layout, hatchling build backend | Build-time only |
| Distribution (v0.1) | Composite GitHub Action, consumers pin a commit SHA | The trust anchor is a git SHA; nothing to download or verify |
| Distribution (later) | PyPI with trusted publishing | Convenience for local use |
| Dev tooling | pytest, ruff, mypy | Dev-only, never shipped |
| CI | GitHub Actions, every action pinned by hash, top-level `contents: read` | Dogfoods its own rules |
| Release integrity | Tagged releases with build provenance attestations | Satisfies its own release rules |

Versions are pinned at implementation time and are deliberately not stated here.

## 3. Architecture overview

```
              (trusted: pinned action SHA)               (untrusted: scanned repo)
 +-------------------------------+                +--------------------------------+
 | repo-guard code + builtin     |                | working tree / PR head         |
 | rules (rules/builtin/*.toml)  |                | policy + suppressions + manifest|
 +---------------+---------------+                +----------------+---------------+
                 |                                                 |
                 |      PR mode: policy files read from BASE ref   |
                 v                                                 v
 +-----------+   +-----------+   +--------------+   +-------------+   +-----------+
 | Collector |-->| Role      |-->| Detectors    |-->| Policy      |-->| Reporters |--> exit code
 | (git)     |   | resolver  |   | (in-tree)    |   | filter      |   | console   |
 +-----------+   +-----------+   +--------------+   | suppressions|   | github    |
                                                    +-------------+   | json/sarif|
                                                                      +-----------+
```

Pipeline stages are pure functions over immutable data where practical. A stage failure never produces a green result (see section 8).

## 4. Trust model

| Adversary | Capability | What repo-guard does | Limit |
|---|---|---|---|
| Outside contributor | Opens a PR | Scans PR head with scanner from the pinned action; policy from base ref | Cannot be fooled by edits to the scanner or allowlist |
| Compromised dependency or Action | Runs code in CI | Read-only token, no secrets, pinned SHA | A compromised repo-guard release is the residual risk; mitigated by attestation and SHA pinning |
| Maintainer credential theft (PolinRider entry) | Pushes to repo, may force-push, may edit workflows | Structural detectors flag the injected loader; `policy-changed` makes policy edits visible; `history-rewritten` finding on non-fast-forward pushes | If the attacker also controls repo settings, workflows and CODEOWNERS, repo-guard can be disabled. No in-repo tool prevents that. Hardware-key 2FA and recovery-account protection are the real controls |
| Malicious fixture or vendored Wasm | Hides a payload in an asset | Manifest hash check; unlisted Wasm is HIGH | Does not analyze Wasm contents |
| Anyone who can push workflow files | Removes or edits the step that runs repo-guard | Required status check blocks PRs whose check never reports; push-mode base check yields `history-rewritten` | A stolen credential can still disable the check. Only a scanner outside the repo (watch mode, decision D-04) is out of the attacker's reach |
| Credentialed push that edits policy | Pushes policy change and payload together | Push mode reads policy from `github.event.before` | New-branch pushes have no trusted base (WARN) |
| Determined evader | Crafts code that dodges regex rules | Capability tiers, entropy and tail checks | Regex heuristics can be beaten; parser analysis is Later |

Trust anchors:

1. The commit SHA of the repo-guard Action in the consumer's workflow.
2. The trusted base: the PR base in PR mode, the pre-push SHA in push mode.

## 5. Repository layout

Full annotated tree, ownership and import rules: `project_structure.md`. Summary:

```
repo-guard/
  action.yml                      # composite action
  pyproject.toml
  repo-guard.toml                 # dogfood policy and suppressions
  wasm-manifest.toml              # dogfood Wasm manifest
  src/repo_guard/
    cli.py  model.py  collector.py  roles.py  rules.py  policy.py  fingerprint.py  runner.py
    strkey.py                     # P1
    detectors/{config_role,wasm_manifest,builtin_patterns}.py     # P0
    detectors/{soroban_profile,stellar_seed,cargo_vectors}.py     # P1
    report/{console,github,jsonout,summary}.py                    # sarif.py in P1
  rules/{roles.toml,builtin/*.toml}
  scripts/{check_roadmap_touched.sh,roadmap_progress.py}
  tests/{unit,fixtures,bypass,corpus,golden}/
  .github/{workflows,pull_request_template.md,CODEOWNERS}
```

Removed since v0.1 of this document: `jsmask.py`, `wasmparse.py`, `detectors/deploy_gate.py`, `schema/*.json`, `templates/`, the `init` command and `report/sarif.py` (deferred). See section 16.4.

## 6. Components

### 6.1 Collector

- Lists tracked files with `git ls-files -z --stage`. Entries with mode 160000 are submodules and yield `submodule-present` (INFO, P1 hardening). Untracked files are out of scope.
- **No default directory skips.** The first draft skipped `node_modules/`, `target/`, `dist/`, `.next/` and `vendor/` and reported them as INFO. That let an attacker hide a payload in a committed vendor directory (B6). If a repo tracks a very large vendored tree, policy may list `low_priority_dirs`, which only suppress WARN-level content rules there. HIGH rules, role magic and config-role globs still apply.
- Reads each file once: size, first 4096 bytes and (lazily) the full bytes and SHA-256.
- Decoding: honor a UTF-8 or UTF-16 BOM; otherwise decode UTF-8 strictly. Undecodable text yields `non-utf8-text` (HIGH in sensitive roles, WARN elsewhere). A NUL byte after BOM handling yields `nul-in-text`.
- Never follows symlinks; a symlink is recorded as `skipped-symlink` (INFO) and its target path is not read.
- Enforces `max_file_bytes` (default 5,000,000). Oversized files yield `skipped-oversize`: WARN generally, HIGH for roles `tooling-config` and `editor-autorun`.
- Enforces `line_cap` (default 20,000 characters). Lines over the cap are not passed to regex rules and yield `cfg-long-line`.
- Startup checks: Python 3.11 or newer, `git` on PATH, repository readable (including the git `safe.directory` case). Failure exits 2 with a plain message.

### 6.2 Role resolver

A role is a label detectors use to decide what to inspect. Resolution order:

1. Content magic: `\0asm` gives `wasm`; ELF, PE and Mach-O magics give `native-binary`. Applies regardless of extension.
2. Glob rules from `rules/roles.toml`. No per-repo role overrides in v0.1.
3. Fallback: `source`, `doc` or `other` by extension.

A file may have several roles. Globs use a small internal matcher where `**` spans directories and `*` does not cross `/`, to avoid the `fnmatch` behavior that let a lone `*` match everything.

### 6.3 Detectors

A detector is a function `run(ctx) -> Iterable[Finding]` registered in a plain list. (An earlier draft used a Protocol class and a registry object; a list of functions is enough.) `ScanContext` exposes file entries with roles, the resolved policy and manifest, loaded rules and the scan mode.

Every call is wrapped: an exception becomes a HIGH `detector-error` and the remaining detectors still run. Findings a detector yielded before it raised are kept, so one failure on the tenth file costs the scan that file's coverage and nothing more. Third-party detector plugins are not supported, because loading external code would defeat the trust model.

The registry also names the valid `builtin:<name>` targets (`DETECTOR_NAMES`), so the rule loader rejects a rule pointing at a detector that does not exist. Two detectors are registered now: `config_role` and `wasm_manifest`.

`runner.engine_findings` is the pass that is not a detector: it runs the `pattern` rules over every entry with text and reports the lines `line_cap` withheld from any regex. It lives in the runner so those lines are accounted for whatever the registry holds; a registry narrowed to one family must reduce what is matched, never what is reported.

### 6.4 Rule engine

Rules are TOML data with one of:

- `pattern`: a regex or literal set applied per line, within the rule's `roles`, on raw text.
- `detector`: a pointer to a builtin function for logic a pattern cannot express.

A `detector` rule may carry a `pattern` as well, which is the text its code detector looks for and the engine never runs. `cfg-process-spawn` needs this: the same line is a WARN or a HIGH depending on what the command runs, so the detector must stay the only reporter of it.

Rule files are validated in code at load time (no JSON schema files in v0.1). An invalid rule file is a config error (exit 2). Every pattern must pass the adversarial timing test in the suite (FR-14).

### 6.5 Trusted base and policy resolution

Policy (`repo-guard.toml`, including suppressions) and `wasm-manifest.toml` must come from a source the change under scan cannot edit.

```
mode pr:
    base = PR base SHA (error exit 2 if unresolvable; never fall back to head)
mode push:
    base = github.event.before
    - all zeros (new branch):             bootstrap defaults + finding no-trusted-base (WARN)
    - not reachable, or not an ancestor
      of HEAD (git merge-base --is-ancestor): finding history-rewritten (HIGH), bootstrap defaults
mode full (local, manual, scheduled):
    read from the working tree, emit untrusted-policy-source (INFO) so the weaker guarantee is visible

for each policy file:
    use the version at base; if the head version differs, emit policy-changed (WARN) with a diff summary
```

This closes B1: a credentialed push that edits the policy and adds a payload in one commit is judged by the old policy. It does not stop an attacker who also removes the workflow (B2).

Cost: a PR that adds a legitimate Wasm fixture fails until the manifest change merges first. The documented flow is two PRs, manifest first. [Unverified: friction level needs real use]

### 6.6 Reporters

| Reporter | Notes |
|---|---|
| console | Severity, rule, `path:line`, message; summary line |
| github | `::error` and `::warning` commands; escapes `%`, `\r`, `\n`, `:` and `,` in properties; HIGH first; WARN annotations capped |
| json | Full `ScanReport` model |
| summary | Markdown to `$GITHUB_STEP_SUMMARY`: counts, skipped-file counts, every HIGH; evidence rendered only inside fenced code blocks with the fence length chosen to exceed any backtick run in the evidence, truncated to a fixed length |
| sarif (P1) | SARIF 2.1.0 with `partialFingerprints["repoGuard/v1"]`; result count capped |

Evidence is attacker-controlled text. It is never rendered as raw markdown (B11). GitHub limits annotations per step and the size of step summaries; the design assumes truncation and so orders output by severity (B8). [Unverified: exact limits, task 0.9]

## 7. Data models

### 7.1 Severity and mode

```python
class Severity(IntEnum):
    INFO = 0
    WARN = 1
    HIGH = 2

class Mode(Enum):
    PR = "pr"
    PUSH = "push"
    FULL = "full"
```

### 7.2 Finding

```python
@dataclass(frozen=True)
class Finding:
    rule_id: str                 # stable, kebab-case, e.g. "cfg-dynamic-code"
    severity: Severity
    path: str                    # repo-relative, forward slashes
    line: int                    # 0 for file-level
    roles: tuple[str, ...]
    message: str                 # <= 200 chars
    evidence: str | None         # short, truncated, sanitized excerpt
    occurrence: int              # nth occurrence of identical normalized evidence in this file
    fingerprint: str             # "sha256:<hex>"
    suppressible: bool
    suppressed_by: str | None
```

Ordering: severity descending, then `(path, line, rule_id)`, so output is deterministic and HIGH comes first.

### 7.3 Fingerprint

```
fingerprint = sha256(rule_id \0 normalized_path \0 normalized_evidence \0 occurrence)
```

`normalized_evidence` is the matched line with outer whitespace stripped and internal whitespace runs collapsed. Line numbers are excluded so edits above a line do not invalidate a suppression. `occurrence` is the zero-based index of that identical evidence within the file, so a second copy of a suppressed line is a new, unsuppressed finding (B5). If an earlier duplicate is removed, indices shift and the suppression must be reissued; that fails closed. For file-level findings the file's SHA-256 replaces the evidence. [Unverified: churn on real edits]

### 7.4 Rule file

```toml
[[rule]]
id           = "cfg-dynamic-code"
title        = "Dynamic code execution in tooling config"
roles        = ["tooling-config"]
detector     = "pattern"                      # or "builtin:<name>"
severity     = "high"
suppressible = false
rationale    = "Build configs have no reason to evaluate strings."
pattern      = { kind = "regex", value = '(?<![\w.])(?:eval|Function)\s*\(' }
tests        = { positive = "cfg-dynamic-code", negative = "cfg-dynamic-code" }   # fixture builder names
```

### 7.5 Roles file

```toml
[roles.tooling-config]
globs = ["**/postcss.config.*", "**/tailwind.config.*", "**/next.config.*",
         "**/eslint.config.*", "**/babel.config.*"]

[roles.editor-autorun]
globs = ["**/.vscode/tasks.json"]
```

Wasm and native binaries are resolved by content magic, not globs. The `tooling-config` defaults mirror the files named in the OpenSourceMalware reports. [Verified] Extra configs (`vite`, `webpack`, `jest`, and others) are P1 and need false-positive review. [Unverified]

### 7.6 Policy file with suppressions

```toml
# repo-guard.toml
version = 1

[policy]
fail_on        = "high"
max_file_bytes = 5000000
line_cap       = 20000
tail_max_len   = 2000        # placeholder; tune on corpus (task 3.3)
tail_entropy   = 4.5         # placeholder; tune on corpus (task 3.3)

[soroban]                    # used by soroban_profile (P1)
require_release_profile = { overflow-checks = true, panic = "abort", lto = true,
                            codegen-units = 1, debug-assertions = false }

[[suppress]]
rule        = "cfg-process-spawn"
path        = "next.config.mjs"
fingerprint = "sha256:..."
reason      = "git rev-parse HEAD for build id"
expires     = "2027-04-27"   # optional
```

Rules for suppressions:

- Match needs `rule`, `path` and `fingerprint`. No globs, no inline markers.
- `reason` is required. There is no `owner` field (git history records who added it).
- `expires` is optional. 30 days before expiry a `suppression-expiring` WARN appears; after expiry only that finding returns, so builds do not turn red for a reason unrelated to a change (B10).
- Entries for `suppressible = false` rules never apply and emit `suppression-invalid` (HIGH).
- Unknown top-level keys emit `policy-unknown-key` (WARN); a missing or unsupported `version` exits 2.

### 7.7 Wasm manifest

```toml
version = 1

[[wasm]]
sha256 = "<hex>"
paths  = ["test/fixtures/smart_account.wasm"]
origin = "built"               # built | vendored | generated
source = "contracts/smart_account"
build  = "stellar contract build --package smart_account"   # documentation only
note   = "fixture for conformance tests"
```

Keyed by hash so the same Wasm at several paths needs one entry and a rename produces a WARN instead of a HIGH.

### 7.8 ScanReport

```python
@dataclass
class ScanReport:
    tool_version: str
    mode: Mode
    repo_head: str
    base: str | None
    files_scanned: int
    files_skipped: dict[str, int]     # reason -> count
    findings: list[Finding]
    suppressed: list[Finding]
    exit_code: int
```

## 8. Fail-closed behavior

| Situation | Result |
|---|---|
| File over size limit | `skipped-oversize` (HIGH for sensitive roles, else WARN) |
| File unreadable | `skipped-unreadable` (HIGH) |
| NUL byte in text after BOM handling | `nul-in-text` (HIGH) |
| Undecodable text | `non-utf8-text` (HIGH sensitive roles, else WARN) |
| Line over `line_cap` | `cfg-long-line` (HIGH in `tooling-config`, else WARN); regex skipped for that line |
| Symlink | `skipped-symlink` (INFO) |
| Submodule | `submodule-present` (INFO) |
| Archive present | `wasm-archive-skipped` (WARN) |
| Detector raises | `detector-error` (HIGH) |
| Pushed `before` unreachable or non-ancestor | `history-rewritten` (HIGH) |
| New branch push | `no-trusted-base` (WARN) |
| Policy changed in this change | `policy-changed` (WARN) |
| Invalid policy, rule or manifest | exit 2 |
| Base unresolvable in PR mode | exit 2 |
| Python or git missing | exit 2 with a plain message |

Exit codes: 0 pass; 1 findings at or above `fail_on`; 2 configuration or usage error; 3 internal error. Anything nonzero fails the job.

## 9. Detector specifications

### 9.1 `config_role`

Applies to role `tooling-config`. Runs on raw text, no masking.

1. `cfg-long-line`: lines past `line_cap` reach no regex and are reported by the engine pass (`runner.engine_findings`), not by this detector, so the account holds even when the registry is partial.
2. Capability rules the engine runs: `cfg-dynamic-code`, `cfg-network`, `cfg-chain-endpoint`.
3. `cfg-process-spawn`, in this detector, two tiers off one pattern: WARN for a build step stated up front, HIGH when the command names a downloader, a decoder or an inline script.
4. Combination rule `cfg-network-exec`: network capability and (process spawn, dynamic code or `require()` of a non-literal) in one file is HIGH even when each alone would be WARN.
5. `cfg-appended-tail`: take the last non-empty line; flag if its length exceeds `tail_max_len` or if the entropy of its trailing window exceeds `tail_entropy`. Thresholds are placeholders until tuned on the corpus. [Unverified]
6. `cfg-nul`, reported by the collector for every role, so an unexpected role cannot hide it.

Capability rules were chosen because obfuscator fingerprints rotate while the mechanism (fetch remote content, decrypt, evaluate) stays. [Verified: OpenSourceMalware reporting] Known limit: string concatenation such as `globalThis['ev'+'al']` evades regex. The long-line and tail rules give partial coverage; parser analysis is Later.

### 9.2 `wasm_manifest`

1. For every tracked file with role `wasm`, compute SHA-256.
2. Build `path -> expected hash` and `hash -> entry` maps from the trusted manifest.
3. Emit `wasm-unlisted` (hash unknown), `wasm-hash-mismatch` (listed path, different hash) or `wasm-path-moved` (known hash, unlisted path).
4. Emit `wasm-manifest-stale` for entries with no matching file. An entry whose declared path still holds a Wasm file is not called stale as well as mismatched or moved: one changed artifact, one finding.
5. Detect archives and report `wasm-archive-skipped`. Git LFS pointer files are handled in P1 (FR-20): a file named `*.wasm` that carries no Wasm header is reported as `wasm-unlisted` with that reason.

Wasm binary basics: magic `00 61 73 6D`, then version `01 00 00 00`. [Verified: Wasm binary format] No section parsing in v0.1; the SEP-58 metadata check is Later.

### 9.3 `soroban_profile` (P1)

- Contract crates are packages whose `crate-type` includes `cdylib`. Apply rules only to them.
- Check `[profile.release]` in the workspace root manifest (or the single-package root) against `policy.soroban.require_release_profile`. Missing or false `overflow-checks`: HIGH. Other deviations: WARN. A `[profile.*]` section in a non-root manifest is ignored by Cargo, so report `profile-ignored` (INFO). [Verified: Cargo behavior]
- Flag `soroban-sdk` with `testutils` in a contract crate's `[dependencies]`, including features inherited through `workspace = true`. Libraries are exempt. The rule assumes resolver 2 semantics. [Unverified: confirm against Cargo docs, task 0.12]
- Do not enforce target triple, size limit or SDK version. Stellar docs disagree with each other on them (`wasm32v1-none` versus `wasm32-unknown-unknown`; 64 KB versus 128 KB). [Verified: documentation inconsistency observed]

### 9.4 `stellar_seed` (P1)

Candidate regex `\bS[A-Z2-7]{55}\b`. For each candidate: base32 decode to 35 bytes; version byte 0x90; CRC16-XModem over the first 33 bytes equals the little-endian last 2 bytes. Report only checksum-valid candidates. Suppressible, because committed testnet seeds are common. Scope: tracked files; history scan is Later. Test against reference vectors before release. [Unverified: byte details recalled from memory]

### 9.5 `cargo_vectors` (P1)

`.cargo/config.toml` `runner`, `linker`, `rustc-wrapper` and `rustc-workspace-wrapper` containing a shell; custom `build = "<path>"`; git dependencies without `rev`; `[patch]` and `[replace]` to git or path sources; `build.rs` network or shell capability.

### 9.6 `builtin_patterns`

Line rules ported from `malware_scan.py`: invisible Unicode, exfiltration endpoints, decode-and-eval, obfuscator identifiers, credential harvesting, blockchain C2 hosts, workflow secret dump, install-hook droppers, VS Code auto-run, `pull_request_target` checkout, `build.rs` network, native binaries. HIGH rules first, then WARN rules. Intentional changes from the old script: skips become findings, directory skips are gone and the inline `malware-scan: allow` marker is dropped.

### 9.7 Deferred designs

- `deploy_gate`: text heuristics over workflow files cannot see deploys hidden in scripts, reusable workflows or `make` targets, so it would give false assurance. Reconsider only if a real repo deploys to mainnet from CI.
- SEP-58 metadata presence check and `wasmparse`: the SEP is not final and Colibri already verifies builds. [Verified: Colibri exists; Unverified: SEP final status]
- Watch mode, org scan, history scan, parser-based JS: see `ROADMAP.md` Phase 9.

## 10. Distribution: the composite Action

```yaml
# action.yml (sketch)
name: repo-guard
description: Supply-chain scan for Stellar and Soroban repositories
inputs:
  fail-on: { default: "high" }
  config:  { default: "repo-guard.toml" }
runs:
  using: composite
  steps:
    - shell: bash
      env:
        RG_EVENT:   ${{ github.event_name }}
        RG_BASE:    ${{ github.event.pull_request.base.sha }}
        RG_BEFORE:  ${{ github.event.before }}
        RG_FAIL_ON: ${{ inputs.fail-on }}
        RG_CONFIG:  ${{ inputs.config }}
      run: |
        python3 -I -c 'import sys; sys.path.insert(0, sys.argv.pop(1)); \
          from repo_guard.cli import main; raise SystemExit(main())' \
          "$GITHUB_ACTION_PATH/src" scan --event "$RG_EVENT" --base "$RG_BASE" \
          --before "$RG_BEFORE" --fail-on "$RG_FAIL_ON" --config "$RG_CONFIG" --format github
```

Notes:

- `python3 -I` ignores `PYTHONPATH` and the script directory, so the module path is passed through `argv`. The scanner code comes from `GITHUB_ACTION_PATH` (the pinned Action), never from the checkout. [Unverified: confirm with a scratch workflow, task 0.8]
- The tool never fetches. The consumer's `actions/checkout` needs `fetch-depth: 0`, or enough depth to include the base; otherwise exit 2.
- User-influenced values reach the script through `env:`, never by interpolation into the shell.
- Consumers use `permissions: contents: read` and the full commit SHA.
- Consumers should make the check a **required status check**. Without it, a PR that deletes the workflow step simply never runs the scan. [Unverified: how GitHub treats a required check whose job no longer exists; task 4.5 tests it]
- Review Action SHA bumps by hand and do not auto-merge them (B12).

## 11. Self-protection of the repo-guard repo

- Every Action pinned by hash; top-level `permissions: contents: read`; write only on the release job.
- Rulesets: no force pushes, no deletion, required status checks; `CODEOWNERS` on `src/`, `rules/`, `action.yml`, `scripts/` and `.github/`.
- Maintainer accounts use hardware-key 2FA and a protected recovery email. These controls matter more than any code here.
- Releases carry build provenance attestations; the README documents the verification command.
- The tool scans itself. There is no `SELF` skip. Fixtures that intentionally trigger rules are built at test time, not committed.
- Scorecard runs on the repo; target 8 or higher.
- `scripts/check_roadmap_touched.sh` runs as a required check (section 17).

## 12. Testing strategy

- **Unit tests** for every module.
- **Fixtures:** every rule has one positive and one negative fixture, enforced inside the pytest suite.
- **Synthetic only.** Trigger strings are assembled at test time from fragments (for example `'ev' + 'al('`), written to a temp directory and scanned. The repository never stores a live-looking payload. Wasm fixtures are minimal generated byte strings (`\0asm\x01\0\0\0` plus a trivial section).
- **Bypass regression tests:** the seven cases in `PRD.md` Appendix B, plus any later discovered evasion, each asserting fail-closed.
- **ReDoS timing test:** each pattern runs against adversarial inputs (long runs of a single character, nested repeats) and must finish within the budget.
- **Trusted-base tests:** a pushed commit that edits policy and adds a payload; a force push; a new branch; an unresolvable base.
- **Parity test:** old `malware_scan.py` versus the ported rules on a shared corpus; no lost findings.
- **Golden outputs:** JSON (and SARIF once it exists).
- **Corpus gate:** a clean-state snapshot of the six repos (`tests/corpus/`) must yield zero HIGH findings.
- **Self-scan test:** the repo-guard repo passes its own scan in CI.
- **Roadmap gate test:** the script fails a diff that omits `ROADMAP.md` and passes one that includes it.

## 13. Architecture decision records

| ID | Decision | Reason | Cost |
|---|---|---|---|
| ADR-001 | Python standard library only, 3.11 or newer | Smallest supply-chain surface; existing code is Python | No YAML parser; hand-written TOML writer; Python version floor |
| ADR-002 | One repository | Solo maintainer; no second tool has a reason to exist yet | Rules and code release together |
| ADR-003 | Trusted base for policy: PR base in `pr`, pre-push SHA in `push` | A change must not approve its own findings, including a credentialed push | Bootstrap friction; new-branch pushes are weaker |
| ADR-004 | Fail closed on skips, errors and unreadable input | A green result must mean something | More findings to triage at first |
| ADR-005 | No inline suppressions; fingerprint-keyed, occurrence-aware, with a reason | Inline markers are an attacker's bypass manual | Slightly slower suppression flow |
| ADR-006 | Rules are data, detectors are code, no plugins | Loading external code defeats the trust model | Contributors add rules via PR |
| ADR-007 | No YAML parsing in v0.1 | Avoid a runtime dependency | Workflow-aware rules are deferred |
| ADR-008 | SARIF deferred to P1 | Needs an extra permission and upload step; step summary and annotations suffice at first | Less code-scanning integration at launch |
| ADR-009 | Composite Action pinned by SHA, no Docker image | A container adds an unpinned layer and a registry trust hop | Depends on the runner's Python |
| ADR-010 | Wasm identified by magic bytes, never by extension | `.wasm` was silently skipped by the old gate | None material |
| ADR-011 | Soroban expectations from policy, not constants | Stellar docs disagree on size limit, target and SDK version | Defaults need maintenance |
| ADR-012 | Detect capabilities, not signatures | PolinRider rotated fingerprints but kept its mechanism | Higher false-positive risk; tiers and tuning needed |
| ADR-013 | No comment or string masking in `config_role` | A lexer that mis-tracks state hands attackers a hiding place; configs rarely contain `eval(` anywhere | Rare false positives, handled by suppression |
| ADR-014 | No default directory skips | Tracked `vendor/` and `dist/` were a hiding place | Slower on repos that track vendored trees |
| ADR-015 | Occurrence-aware fingerprints | A duplicate of a suppressed line must not inherit the suppression | Suppressions can need reissue after edits |
| ADR-016 | Soroban rules apply to contract crates only | Test-support libraries legitimately enable `testutils` | Needs `crate-type` detection |
| ADR-017 | Roadmap gate as a required CI check | The roadmap rots unless a machine enforces it | Friction on tiny PRs |
| ADR-018 | Line cap instead of regex timeouts | Python `re` cannot be interrupted safely mid-match | Lines over the cap are inspected only by length and entropy |

## 14. Roadmap

All remaining work, with task IDs, dependencies and exit criteria: `ROADMAP.md`.

## 15. Open technical questions

1. Does `python3 -I -c` with an explicit `sys.path` insert behave as designed on `ubuntu-latest`? (0.8)
2. What are the real `tail_max_len` and `tail_entropy` values on the six-repo corpus? (3.3)
3. Can GitHub pin a required status check to a trusted source, and what happens when the job is deleted? (0.13, 4.5)
4. What are GitHub's limits on annotations, step summaries and SARIF? (0.9)
5. Exact SEP-58 metadata keys and Soroban metadata section names. (0.11)
6. Resolver-2 feature behavior for `testutils` inherited via the workspace. (0.12)
7. Should watch mode exist? (decision D-04)

## 16. Red-team review

This is design-review analysis. Nothing here has been run. Every item is a hypothesis that should become a test or a task. GitHub-specific claims are marked [Unverified] until checked (tasks 0.9 and 0.13).

### 16.1 Ranking

Likelihood and impact are rough judgments (H, M, L).

### 16.2 What would break

| ID | Scenario | Why it breaks | L / I | Resolution | Task |
|---|---|---|---|---|---|
| B1 | A credentialed push edits `repo-guard.toml` and adds a payload in one commit | `push` and `full` modes read policy from HEAD, so the push approves itself. This is the PolinRider scenario | H / H | Push mode reads policy from `github.event.before`; non-ancestor `before` yields `history-rewritten` | 2.7, 4.5 |
| B2 | The attacker deletes or edits the workflow step that runs repo-guard | A push-triggered run uses the workflow from the pushed commit, so it is attacker-controlled. A scheduled run uses the default branch file, also editable | H / H | Required status check for PRs; maintainer-account hardening; an external watcher that clones from outside and checks ancestry is the only detector the attacker cannot edit. Decision D-04 | 0.13, 4.5, 9.1 |
| B3 | A minified 5 MB single-line file | Regex rules can take quadratic time or worse and hang CI | M / M | `line_cap`, `cfg-long-line`, adversarial timing test per pattern | 2.5, 2.12 |
| B4 | The `testutils` rule fires on a test-support library | `soroban-budget-assert` plausibly needs `testutils` as a normal dependency, so dogfooding would fail on your own repo [Unverified: Cargo.toml not inspected] | H / M | Apply only to contract crates; profile rule only at the workspace root | 6.1, 6.5 |
| B5 | A suppressed line is duplicated elsewhere in the same file | Line-free fingerprints suppress the copy too | M / H | Occurrence-aware fingerprints | 2.6 |
| B6 | A payload is committed under `vendor/`, `dist/` or `node_modules/` | The old script and the first draft of this design skip those paths | M / H | No default directory skips; bypass test 7 | 2.2, 3.9 |
| B7 | Runner has Python older than 3.11, no `git`, or git `safe.directory` errors | Every repo goes red with an opaque exit 3 and users disable the tool | M / M | Startup checks with plain messages, exit 2 | 2.3 |
| B8 | A flood of WARNs buries a HIGH | GitHub truncates annotations and summaries [Unverified] | M / H | HIGH first, caps, every HIGH in the summary | 2.9, 7.10 |
| B9 | New Wasm fixture fails its own PR | Base-ref manifest does not yet list it | H / M | Documented two-step flow; revisit if adoption suffers | risk register |
| B10 | Suppression expiry turns CI red on a date | Users learn to bulk-extend | M / L | Optional `expires`, 30-day warning, only that finding returns | 2.8, 7.11 |
| B11 | Evidence text injects markdown or annotation syntax | Evidence is a line of attacker-controlled code | M / M | Fenced evidence with safe fence length; escaped annotations | 2.9 |
| B12 | Consumers auto-merge bot bumps of the Action SHA | A compromised repo-guard release would propagate | L / H | Attested releases; document manual review of SHA bumps | 5.3 |
| B13 | UTF-16 config files trip `nul-in-text` | NULs appear in every other byte | L / L | BOM detection and decoding | 2.2, 7.3 |
| B14 | Policy schema changes between Action versions | Old policy files fail on new releases | M / L | `version` field; unknown keys WARN | 2.1, 2.7 |
| B15 | The force-push workflow template | It runs from the attacker's workflow, so it protects nothing against a credentialed push | M / L | Removed; `history-rewritten` covers the detectable case | 2.7 |

### 16.3 Edge cases missing from the first draft

| Area | Case | Decision |
|---|---|---|
| Git | Submodules (gitlinks) | INFO in v0.1; hardening P1 (7.2) |
| Git | LFS pointer files in place of Wasm | Report in v0.1 as unverifiable; manifest check by pointer hash P1 (7.1) |
| Git | Shallow clones, sparse checkout, missing base | Exit 2 with a message (2.3) |
| Git | Paths with spaces, quotes, newlines | Use `-z` throughout; test (2.2) |
| Git | Case-insensitive duplicate paths | Test; low priority (7.8) |
| Events | Fork PRs, `merge_group`, tag pushes, first commit, base equals head, base not an ancestor | Test matrix (7.9) |
| Files | Empty files, CRLF, BOM, UTF-16, non-UTF-8 | Handled in the collector (2.2, 7.3) |
| Files | Symlinks to paths outside the repo | Never followed (2.2) |
| Config role | `next.config.ts`, `vite.config.*`, `webpack.config.*`, `jest.config.*`, `svelte.config.js`, `astro.config.*`, `.eslintrc.*`, `.babelrc.*`, `prettier` and `commitlint` configs | P1 globs, each reviewed for false positives (7.4) |
| Config role | Hooks and lifecycle files run by tools: `.husky/*`, `.devcontainer/devcontainer.json`, composite `action.yml`, `Makefile`, `justfile` | Evaluate for P1 (7.5) |
| Config role | Legitimate configs that fetch or spawn at build time | Network alone is WARN; combination is HIGH (3.1) |
| Wasm | Wasm embedded as base64 in TS or Rust (`include_bytes!` is a path, base64 is a string), `.wasm.gz`, `.optimized.wasm` variants | `long-line`, archive and manifest rules cover part; document the gap (7.1) |
| Wasm | Same Wasm at several paths; rebuilt fixtures with new hashes | Hash-keyed manifest; rebuild friction accepted |
| Cargo | Dependency rename (`package = "soroban-sdk"`), target-specific dependency tables, legacy `.cargo/config` (no extension), nested workspaces, proc-macro crates running code at compile time | Handle rename and legacy name; proc-macros are undetectable, documented (6.1, 6.4) |
| Seeds | Testnet seeds in tests and docs; seeds split across lines, encoded or hex-encoded; mnemonic phrases; seeds in git history | Suppressible with reason; encoded forms and history are documented gaps (6.3) |
| Suppressions | Duplicate evidence lines; expiry; reissue after edits | Occurrence index; expiry warning (2.6, 2.8) |
| Reporting | Huge finding counts, SARIF size limits, summary size, annotation caps | Severity-first order, caps (2.9, 7.6, 7.10) |
| Platform | Windows runners, path separators, `core.quotepath`, locale | Test (7.8) |
| Time | Expiry compared in local time | Compare UTC dates only (2.8) |

### 16.4 What is overengineered

| ID | Item | Verdict | Reason |
|---|---|---|---|
| O1 | `jsmask.py` comment and string masking lexer | Cut | JavaScript lexing is hard (regex literals, nested templates). A bug hides code from the scanner. Configs rarely contain `eval(`, so raw text matching costs little |
| O2 | SARIF in v0.1 | Defer to P1 | Needs `security-events: write` and an upload step. Summary and annotations serve a solo maintainer |
| O3 | `init` command | Cut | A README snippet does the same job |
| O4 | `rules test` CLI command | Cut | The pytest suite enforces fixtures |
| O5 | `deploy_gate` | Defer | Heuristic over files, misses scripts and reusable workflows, and no in-scope repo deploys from CI |
| O6 | `wasmparse.py` and the SEP-58 metadata check | Defer | SEP not final; Colibri already verifies builds |
| O7 | Suppression `owner` field | Cut | Git history records authorship |
| O8 | `read_policy_from` and `roles.overrides` policy fields | Cut | The first is fixed by mode, the second has no user |
| O9 | A separate suppressions file | Merge | Three base-ref reads become two |
| O10 | JSON schema files | Cut | Validate in code; schemas can be generated later |
| O11 | Force-push workflow template | Cut | Attacker-controlled (B15) |
| O12 | `hypothesis` fuzzing | Cut | Only needed for the Wasm parser, which is deferred |
| O13 | Detector Protocol and registry object | Simplify | A list of functions is enough |
| O14 | Porting every builtin rule before shipping | Phase | HIGH rules first, WARN rules after (3.6, 3.7) |
| O15 | PyPI distribution, org scan, history scan, parser-based JS | Defer | Backlog, no design needed now |

Not overengineered, but under-built: an **external watcher** (D-04). It is the only design that survives a stolen credential, and it can start as one scheduled job in a separate repository that clones public repos, runs the scan and refuses any non-fast-forward update to the last seen SHA. [Likely] That claim stays a hypothesis until built.

### 16.5 Net effect

- P0 moves from 13 broad requirements to 15 narrower ones: SARIF, `init`, the `rules test` command and the SEP-58 check moved out; the trusted base, no-skips, ReDoS bound and roadmap gate moved in.
- Two design flaws are fixed (B1, B6). One open risk is explicit (B2).
- The first release needs fewer parts: no lexer, no SARIF, no WASM parser, no `init`.

## 17. Documentation and roadmap maintenance rule

`ROADMAP.md` must be updated on every contribution (code, rules, tests, docs, CI, configuration, dependency bumps, reverts), by humans and agents alike. The same pull request must tick, untick or add the affected tasks, add a changelog entry, and refresh the progress table and `Last updated` line. Enforcement is `scripts/check_roadmap_touched.sh` in CI plus a PR template checkbox (task 1.9); until then, reviewers enforce it. Changes to behavior described here must also update `PRD.md`, `ARCHITECTURE_ESSENTIALS.md` and `project_structure.md` in the same PR.
