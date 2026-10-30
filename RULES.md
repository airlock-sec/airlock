# Rule Reference

Generated from [`rules/builtin/*.toml`](rules/builtin) by [`scripts/rule_reference.py`](scripts/rule_reference.py). Do not edit by hand; run `python scripts/rule_reference.py` after changing a rule file.

**Total:** 24 rules across 4 families (`builtin_patterns` (6), `ci_surface` (6), `config_role` (7), `wasm_manifest` (5)) — 12 HIGH, 12 WARN.

## Summary

| Rule | Family | Severity | Suppressible | Detector | Roles | Fixtures |
|---|---|---|---|---|---|---|
| [`pat-chain-c2`](#pat-chain-c2) | `builtin_patterns` | WARN | yes | `pattern` | `source`, `tooling-config`, `editor-autorun`, `other` | `pat_chain_c2` (+/-) |
| [`pat-credential-harvest`](#pat-credential-harvest) | `builtin_patterns` | WARN | yes | `pattern` | `source`, `tooling-config`, `editor-autorun`, `other` | `pat_credential_harvest` (+/-) |
| [`pat-decode-eval`](#pat-decode-eval) | `builtin_patterns` | HIGH | yes | `pattern` | `source`, `tooling-config`, `editor-autorun`, `other` | `pat_decode_eval` (+/-) |
| [`pat-exfil-endpoint`](#pat-exfil-endpoint) | `builtin_patterns` | WARN | yes | `pattern` | `source`, `tooling-config`, `editor-autorun`, `other` | `pat_exfil_endpoint` (+/-) |
| [`pat-invisible-unicode`](#pat-invisible-unicode) | `builtin_patterns` | HIGH | yes | `pattern` | `source`, `tooling-config`, `editor-autorun`, `other` | `pat_invisible_unicode` (+/-) |
| [`pat-obfuscator-id`](#pat-obfuscator-id) | `builtin_patterns` | WARN | yes | `pattern` | `source`, `tooling-config`, `editor-autorun`, `other` | `pat_obfuscator_id` (+/-) |
| [`pat-editor-command-path`](#pat-editor-command-path) | `ci_surface` | WARN | yes | `pattern` | `editor-autorun` | `ci_editor_command_path` (+/-) |
| [`pat-lifecycle-exec`](#pat-lifecycle-exec) | `ci_surface` | HIGH | yes | `builtin:ci_surface` | `package-manifest`, `install-hook` | `ci_lifecycle_exec` (+/-) |
| [`pat-lifecycle-fetch`](#pat-lifecycle-fetch) | `ci_surface` | WARN | yes | `pattern` | `package-manifest`, `install-hook` | `ci_lifecycle_fetch` (+/-) |
| [`pat-privileged-trigger`](#pat-privileged-trigger) | `ci_surface` | WARN | yes | `pattern` | `workflow` | `ci_privileged_trigger` (+/-) |
| [`pat-ptr-head-checkout`](#pat-ptr-head-checkout) | `ci_surface` | HIGH | yes | `builtin:ci_surface` | `workflow` | `ci_ptr_head_checkout` (+/-) |
| [`pat-secret-dump`](#pat-secret-dump) | `ci_surface` | HIGH | yes | `builtin:ci_surface` | `workflow` | `ci_secret_dump` (+/-) |
| [`cfg-appended-tail`](#cfg-appended-tail) | `config_role` | HIGH | yes | `builtin:config_role` | `tooling-config` | `cfg_appended_tail` (+/-) |
| [`cfg-chain-endpoint`](#cfg-chain-endpoint) | `config_role` | HIGH | yes | `pattern` | `tooling-config` | `cfg_chain_endpoint` (+/-) |
| [`cfg-dynamic-code`](#cfg-dynamic-code) | `config_role` | HIGH | no | `pattern` | `tooling-config` | `cfg_dynamic_code` (+/-) |
| [`cfg-long-line`](#cfg-long-line) | `config_role` | HIGH | no | `pattern` | `tooling-config`, `editor-autorun`, `source`, `doc`, `other` | `cfg_long_line` (+/-) |
| [`cfg-network`](#cfg-network) | `config_role` | WARN | yes | `pattern` | `tooling-config` | `cfg_network` (+/-) |
| [`cfg-network-exec`](#cfg-network-exec) | `config_role` | HIGH | no | `builtin:config_role` | `tooling-config` | `cfg_network_exec` (+/-) |
| [`cfg-process-spawn`](#cfg-process-spawn) | `config_role` | WARN | yes | `builtin:config_role` | `tooling-config` | `cfg_process_spawn` (+/-) |
| [`wasm-archive-skipped`](#wasm-archive-skipped) | `wasm_manifest` | WARN | yes | `builtin:wasm_manifest` | `archive` | `wasm_archive_skipped` (+/-) |
| [`wasm-hash-mismatch`](#wasm-hash-mismatch) | `wasm_manifest` | HIGH | no | `builtin:wasm_manifest` | `wasm` | `wasm_hash_mismatch` (+/-) |
| [`wasm-manifest-stale`](#wasm-manifest-stale) | `wasm_manifest` | WARN | yes | `builtin:wasm_manifest` | `wasm` | `wasm_manifest_stale` (+/-) |
| [`wasm-path-moved`](#wasm-path-moved) | `wasm_manifest` | WARN | yes | `builtin:wasm_manifest` | `wasm` | `wasm_path_moved` (+/-) |
| [`wasm-unlisted`](#wasm-unlisted) | `wasm_manifest` | HIGH | no | `builtin:wasm_manifest` | `wasm` | `wasm_unlisted` (+/-) |

## `builtin_patterns` (6 rules)

Source: [`rules/builtin/builtin_patterns.toml`](rules/builtin/builtin_patterns.toml)

### `pat-chain-c2`

**Public chain RPC or explorer host in code**

- **Severity:** `WARN`
- **Suppressible:** `yes`
- **Detector:** `pattern`
- **Roles:** `source`, `tooling-config`, `editor-autorun`, `other`
- **Fixtures:** positive `pat_chain_c2`, negative `pat_chain_c2`
- **Pattern:** `regex` (1 expression)
  ```text
  trongrid\.io|tronscan\.org|bsc-dataseed\.(?:binance|bnbchain)\.org
  ```

The reported campaigns did not host their own endpoints. They pointed the payload at public chain infrastructure it could reach without a key and without a notice, which is why this list holds a Tron node provider and a Binance Smart Chain data seed rather than attacker-owned domains, and why those names are data: a campaign that moves to another public node is a one-line edit here and a rewrite nowhere else. This is the reach half of `cfg-chain-endpoint`, which stays the stricter rule and the only one that can fail a build: that rule reads one of five config filenames and fires on an endpoint being *configured*, which no innocent build step does, while this one reads every file that is code and fires on a host being named, which a dApp integration does every day. The two tiers are the trade, and a line that hits both is one finding each by design. Case-sensitive for the measured reason at the top of this file, with the same residual recorded there: a defanged or shouty host is an evasion of a WARN.

### `pat-credential-harvest`

**A credential, key or wallet store named in code**

- **Severity:** `WARN`
- **Suppressible:** `yes`
- **Detector:** `pattern`
- **Roles:** `source`, `tooling-config`, `editor-autorun`, `other`
- **Fixtures:** positive `pat_credential_harvest`, negative `pat_credential_harvest`
- **Pattern:** `regex` (1 expression)
  ```text
  [./\\."'](?:aws[/\\]credentials|ssh[/\\]id_(?:rsa|ed25519|ecdsa|dsa)(?![\w.])|config[/\\]solana[/\\]id\.json|gnupg[/\\]private-keys-v1\.d|Local Storage[/\\]leveldb|Login Data|key[34]\.db(?![\w.])|wallet\.dat(?![\w.])|Electrum[/\\]wallets|MultiversX[/\\]wallets)
  ```

A loader collects before it sends, and what it collects is a short list of files whose only purpose is to be secret: an AWS credentials file, an OpenSSH private key, a GnuPG private-key directory, a Solana CLI keypair, the browser database that holds saved logins, and the wallet files of the chains whose keys are one file in a known place. The old script carried this list at HIGH and matched the directory rather than the file, which is how a rule about paths becomes a rule about false positives. Each branch names the store and not the folder it sits in, and the trailing guard on the key branches is what keeps a provisioned public key out of the report, because a pub file in a setup script is ordinary infrastructure. A chain's own keypair path is listed because a CLI writes a signing key to one fixed location, which is the shape worth naming; a secret handed over as an environment value is not a path, and stays with the workflow rules in `ci_surface.toml`.

### `pat-decode-eval`

**Encoded payload fed to an evaluator**

- **Severity:** `HIGH`
- **Suppressible:** `yes`
- **Detector:** `pattern`
- **Roles:** `source`, `tooling-config`, `editor-autorun`, `other`
- **Fixtures:** positive `pat_decode_eval`, negative `pat_decode_eval`
- **Pattern:** `regex` (1 expression)
  ```text
  (?i)\b(?:eval|exec|function|setTimeout|setInterval)\b\s*\(\s*[\w.$]{0,24}?(?:atob|b64[_-]?decode|base64[_-]?decode|decode[_-]?base64|from[_-]?base64|decodeUri\w*|unescape|unhex\w*|decrypt|Buffer\s*\.\s*from)\s*\(
  ```

A string that has to be decoded before it runs was written to be read by the machine and not by the reviewer, which is the shape the reported campaigns used. The old script scored it WARN unless the payload spelled the call with no space between the verb and the decoder, and said nothing at all once the file sat under a vendored directory (PRD.md 2.3 items 5 and 7). What separates this from cfg-dynamic-code is what each asks for: that rule fires on an evaluator call in one of five config filenames, this one fires on a decoder feeding an evaluator in any file that is code.

### `pat-exfil-endpoint`

**Paste, webhook or tunnel endpoint in code**

- **Severity:** `WARN`
- **Suppressible:** `yes`
- **Detector:** `pattern`
- **Roles:** `source`, `tooling-config`, `editor-autorun`, `other`
- **Fixtures:** positive `pat_exfil_endpoint`, negative `pat_exfil_endpoint`
- **Pattern:** `regex` (1 expression)
  ```text
  \b(?:pastebin\.com|hastebin\.com|controlc\.cc|rentry\.co|dpaste\.org|paste\.ee|termbin\.com|0x0\.st|transfer\.sh|file\.io|webhook\.site|requestbin\.(?:com|net)|hookbin\.com|pipedream\.(?:net|com)|ngrok\.(?:io|com)|trycloudflare\.com|localtunnel\.me|serveo\.net|bore\.pub|interact\.sh|burpcollaborator\.net|canarytokens\.com|oast\.(?:com|fun|pro|site)|dnslog\.cn|requestrepo\.com|ghostbin\.(?:com|co|site))
  ```

A loader needs somewhere to put what it collected and somewhere to be told what to fetch, and the free services it uses for that are a short list that changes slowly. This is a separate rule from cfg-network rather than a wider role on that pattern: a named paste or tunnel host and a bare capability to open a socket have different false-positive profiles and different reasons to be suppressed, and only one of them is already a WARN inside a build config. The list is paste sites, tunnels and webhook or out-of-band callback hosts, kept as data so that adding a host never reads like a change to the matching logic.

### `pat-invisible-unicode`

**Invisible or direction-flipping character in code**

- **Severity:** `HIGH`
- **Suppressible:** `yes`
- **Detector:** `pattern`
- **Roles:** `source`, `tooling-config`, `editor-autorun`, `other`
- **Fixtures:** positive `pat_invisible_unicode`, negative `pat_invisible_unicode`
- **Pattern:** `regex` (1 expression)
  ```text
  [\u00ad\u034f\u061c\u180e\u200b\u200c\u2060\u200e\u200f\u202a-\u202e\u2062-\u2064\ufeff]
  ```

A zero-width or bidi-override character inside an identifier is invisible in a diff, survives a reviewer reading the line out loud, and defeats a grep for the payload name, because the name on the screen is not the name in the file. This is why matching raw text with no masking is a hard rule rather than a style choice. U+200D is deliberately absent from the class: a zero-width joiner is how emoji sequences and several writing systems are spelled, and it is the one character in this neighbourhood that code carries legitimately.

### `pat-obfuscator-id`

**Obfuscator identifier grammar**

- **Severity:** `WARN`
- **Suppressible:** `yes`
- **Detector:** `pattern`
- **Roles:** `source`, `tooling-config`, `editor-autorun`, `other`
- **Fixtures:** positive `pat_obfuscator_id`, negative `pat_obfuscator_id`
- **Pattern:** `regex` (1 expression)
  ```text
  \b_0x[0-9a-fA-F]{4,}\b
  ```

The `_0x` plus hex identifier is the naming scheme the JavaScript obfuscators emit, and it survives a rename of the tool because it is a property of the output rather than of a banner. ARCHITECTURE.md 9.6 is explicit that obfuscator fingerprints rotate weekly while the mechanism stays, so this keys on the identifier grammar and not on a list of tool names. It is a WARN because the shape has one ordinary owner: a minified or packed bundle committed to the repository, which is a release-integrity question for the artifact rules rather than a payload by itself.

## `ci_surface` (6 rules)

Source: [`rules/builtin/ci_surface.toml`](rules/builtin/ci_surface.toml)

### `pat-editor-command-path`

**Editor setting that names an interpreter or executable**

- **Severity:** `WARN`
- **Suppressible:** `yes`
- **Detector:** `pattern`
- **Roles:** `editor-autorun`
- **Fixtures:** positive `ci_editor_command_path`, negative `ci_editor_command_path`
- **Pattern:** `regex` (1 expression)
  ```text
  "(?:[\w.-]+\.)?(?:defaultInterpreterPath|executablePath|execPath|binPath|interpreterPath|pythonPath|nodeExecutable|alternateTools|defaultProfile|shellArgs|tsdk)"\s*:
  ```

`.vscode/settings.json` is the second half of the editor auto-run surface: `tasks.json` says what can run, and these keys say what the editor runs by itself when a folder opens. A path to an interpreter or a compiler directory is loaded by the extension host, so a planted one needs no user action. Preferences with nothing executable behind them are not reported, which is what keeps this a WARN about a handful of key names rather than about the file.

### `pat-lifecycle-exec`

**Lifecycle script or hook runs what it fetched**

- **Severity:** `HIGH`
- **Suppressible:** `yes`
- **Detector:** `builtin:ci_surface`
- **Roles:** `package-manifest`, `install-hook`
- **Fixtures:** positive `ci_lifecycle_exec`, negative `ci_lifecycle_exec`
- **Pattern:** none *(evaluated by detector code)*

The fetch rule becomes this one when the same line also hands the result to an interpreter or a shell, which is the PolinRider dropper shape: the server chooses the payload after install, so nothing in the repository or the lockfile describes what runs. An interpreter named without a fetch is a build step, and a fetch without an interpreter is the WARN above.

### `pat-lifecycle-fetch`

**Install hook or lifecycle script reaches the network**

- **Severity:** `WARN`
- **Suppressible:** `yes`
- **Detector:** `pattern`
- **Roles:** `package-manifest`, `install-hook`
- **Fixtures:** positive `ci_lifecycle_fetch`, negative `ci_lifecycle_fetch`
- **Pattern:** `regex` (1 expression)
  ```text
  (?x)
  \b(?:curl|wget)\b
  | \bInvoke-(?:WebRequest|RestMethod)\b
  | \bgit\s+(?:clone|fetch|pull|submodule\s+update)\b
  | \b(?:npm|pnpm|yarn)\s+(?:install|i|add)\s+["'`]?(?:git\+)?(?:https?://|git://|ssh://)

  ```

A `postinstall` script and a commit hook both run without a developer choosing them, so a downloader named in one is a payload server the reviewer cannot see in a lockfile. The bare host name stays out of this: a `repository.url` in the same manifest is not a fetch, which is why the pattern asks for a client verb or an install-from-URL argument rather than any `https://` text.

### `pat-privileged-trigger`

**Workflow trigger that runs base-context code with a write token**

- **Severity:** `WARN`
- **Suppressible:** `yes`
- **Detector:** `pattern`
- **Roles:** `workflow`
- **Fixtures:** positive `ci_privileged_trigger`, negative `ci_privileged_trigger`
- **Pattern:** `regex` (1 expression)
  ```text
  \bpull_request_target\b
  ```

`pull_request_target` runs in the base repository with a writable token while the code it runs came from an outside fork. The trigger is not an attack on its own, so it is a WARN that tells a reviewer which files to read; what makes it fatal is the checkout of the head, which is the rule below. `workflow_run` and `issue_comment` are deliberately not in this pattern: both are real vectors and neither is the reported shape, so naming them here would cost coverage in false positives instead of buying it.

### `pat-ptr-head-checkout`

**Privileged trigger combined with a checkout of the pull request head**

- **Severity:** `HIGH`
- **Suppressible:** `yes`
- **Detector:** `builtin:ci_surface`
- **Roles:** `workflow`
- **Fixtures:** positive `ci_ptr_head_checkout`, negative `ci_ptr_head_checkout`
- **Pattern:** none *(evaluated by detector code)*

This is the combination that turns a fork pull request into code execution with a write token: the trigger gives the base context and permissions, and the head ref gives the attacker's tree to run. A `pull_request` trigger with the same checkout is reviewed code, and a `pull_request_target` that leaves the default base ref is the safe form, so the rule needs the trigger, a head ref and a checkout step in one file. `ARCHITECTURE.md` 11 worries about exactly this class of weakness in the design document itself.

### `pat-secret-dump`

**Secret interpolated into something that displays or writes it**

- **Severity:** `HIGH`
- **Suppressible:** `yes`
- **Detector:** `builtin:ci_surface`
- **Roles:** `workflow`
- **Fixtures:** positive `ci_secret_dump`, negative `ci_secret_dump`
- **Pattern:** none *(evaluated by detector code)*

`${{ secrets.X }}` in a `run:` line reaches the job log, where it stays readable to anyone who can see the artifact, and into `GITHUB_ENV`, where every later step inherits it. Passing a secret to a step through `env:` or `with:` is not this rule: that is how a workflow uses a secret, and it is the negative case. A line that masks the value first (`::add-mask::`) is the one echo that is deliberate hygiene.

## `config_role` (7 rules)

Source: [`rules/builtin/config_role.toml`](rules/builtin/config_role.toml)

### `cfg-appended-tail`

**Payload appended to the end of a build config**

- **Severity:** `HIGH`
- **Suppressible:** `yes`
- **Detector:** `builtin:config_role`
- **Roles:** `tooling-config`
- **Fixtures:** positive `cfg_appended_tail`, negative `cfg_appended_tail`
- **Pattern:** none *(evaluated by detector code)*

Campaigns append a long high-entropy line after a valid config rather than editing one, so the diff looks like one more line. Thresholds are placeholders until tuned on the corpus (ARCHITECTURE.md 15).

### `cfg-chain-endpoint`

**Blockchain endpoint inside build tooling**

- **Severity:** `HIGH`
- **Suppressible:** `yes`
- **Detector:** `pattern`
- **Roles:** `tooling-config`
- **Fixtures:** positive `cfg_chain_endpoint`, negative `cfg_chain_endpoint`
- **Pattern:** `regex` (1 expression)
  ```text
  (?i)\b(?:tronweb|tronscan|bsc-dataseed|json-rpc|json_rpc)\b|nile[.-][a-z]|\brpc[._-]?(?:url|endpoint|host|node|provider)\b|/json_rpc\b
  ```

The reported campaigns configured a chain RPC or JSON-RPC client inside tooling so the payload could sign and broadcast from the victim machine. A build config naming any chain endpoint is out of place, whichever chain it is. Bare SDK names stay out of this pattern: web tooling legitimately lists them in a webpack config, and the endpoint or its configuration variable is the signal. Specific C2 hosts belong in builtin_patterns once task 0.4 confirms the published list.

### `cfg-dynamic-code`

**Dynamic code execution in a build config**

- **Severity:** `HIGH`
- **Suppressible:** `no`
- **Detector:** `pattern`
- **Roles:** `tooling-config`
- **Fixtures:** positive `cfg_dynamic_code`, negative `cfg_dynamic_code`
- **Pattern:** `regex` (1 expression)
  ```text
  (?<![\w.$])(?:eval|Function)\s*\(|\bvm\.runIn|\bimport\s*\(
  ```

Build configs are evaluated at install and build time. Evaluating a string there is how this class of attack turns a dependency install into remote code execution.

### `cfg-long-line`

**Line longer than the configured cap**

- **Severity:** `HIGH`
- **Suppressible:** `no`
- **Detector:** `pattern`
- **Roles:** `tooling-config`, `editor-autorun`, `source`, `doc`, `other`
- **Fixtures:** positive `cfg_long_line`, negative `cfg_long_line`
- **Pattern:** `literal` (1 expression)
  ```text
  no literal ever matches this text
  ```

Regexes are not run on lines past line_cap, because a minified bundle is a backtracking target. The line still has to be accounted for, so its length is the finding.

### `cfg-network`

**Network access from a build config**

- **Severity:** `WARN`
- **Suppressible:** `yes`
- **Detector:** `pattern`
- **Roles:** `tooling-config`
- **Fixtures:** positive `cfg_network`, negative `cfg_network`
- **Pattern:** `regex` (1 expression)
  ```text
  \brequire\s*\(\s*["'](?:node:)?(?:https?|net|dns|tls|child_process)["']\s*\)|\bfrom\s+["'](?:node:)?(?:https?|net)["']|\bfetch\s*\(|\baxios\b|node-fetch|XMLHttpRequest|WebSocket|\.request\s*\(|https?://
  ```

A build step that reaches the network can be handed its payload after install, which no lockfile review would have seen. Alone this is a WARN: some legitimate Next.js configs fetch at build time.

### `cfg-network-exec`

**Network access combined with execution in one build config**

- **Severity:** `HIGH`
- **Suppressible:** `no`
- **Detector:** `builtin:config_role`
- **Roles:** `tooling-config`
- **Fixtures:** positive `cfg_network_exec`, negative `cfg_network_exec`
- **Pattern:** none *(evaluated by detector code)*

Remote content plus a way to run it is the whole attack. Each half alone can be legitimate; together they are the fetch-decrypt-evaluate shape, which is why the combination is HIGH even when neither capability would be on its own.

### `cfg-process-spawn`

**Process execution from a build config**

- **Severity:** `WARN`
- **Suppressible:** `yes`
- **Detector:** `builtin:config_role`
- **Roles:** `tooling-config`
- **Fixtures:** positive `cfg_process_spawn`, negative `cfg_process_spawn`
- **Pattern:** `regex` (1 expression)
  ```text
  (?<![\w.$])(?:execSync|execFileSync|spawnSync|spawn|execFile|exec|child_process)\b|\brequire\s*\(\s*["'](?:node:)?child_process["']\s*\)
  ```

Spawning a shell from a build config is the install-hook dropper path. The detector escalates to HIGH when the command is not a build step stated up front but a downloader, a decoder or an inline script.

## `wasm_manifest` (5 rules)

Source: [`rules/builtin/wasm_manifest.toml`](rules/builtin/wasm_manifest.toml)

### `wasm-archive-skipped`

**Archive in the tree was not looked inside**

- **Severity:** `WARN`
- **Suppressible:** `yes`
- **Detector:** `builtin:wasm_manifest`
- **Roles:** `archive`
- **Fixtures:** positive `wasm_archive_skipped`, negative `wasm_archive_skipped`
- **Pattern:** none *(evaluated by detector code)*

A zip or tarball can carry a Wasm artifact past every check in this file. The scanner reads bytes, never unpacks them, so the archive is reported as an unexamined hole rather than passed over.

### `wasm-hash-mismatch`

**Listed Wasm path holds a different artifact**

- **Severity:** `HIGH`
- **Suppressible:** `no`
- **Detector:** `builtin:wasm_manifest`
- **Roles:** `wasm`
- **Fixtures:** positive `wasm_hash_mismatch`, negative `wasm_hash_mismatch`
- **Pattern:** none *(evaluated by detector code)*

The path was declared as one build and now holds another. Rebuilding a contract changes the hash, so this is a deliberate swap until proven otherwise.

### `wasm-manifest-stale`

**Manifest entry matches no tracked file**

- **Severity:** `WARN`
- **Suppressible:** `yes`
- **Detector:** `builtin:wasm_manifest`
- **Roles:** `wasm`
- **Fixtures:** positive `wasm_manifest_stale`, negative `wasm_manifest_stale`
- **Pattern:** none *(evaluated by detector code)*

A manifest that no longer describes the tree is a manifest nobody checks. It also hides the case where the artifact was deleted here and shipped from somewhere else.

### `wasm-path-moved`

**Known artifact moved to an unlisted path**

- **Severity:** `WARN`
- **Suppressible:** `yes`
- **Detector:** `builtin:wasm_manifest`
- **Roles:** `wasm`
- **Fixtures:** positive `wasm_path_moved`, negative `wasm_path_moved`
- **Pattern:** none *(evaluated by detector code)*

The bytes are known, the location is not. A move is usually a refactor; it is also how an artifact gets in front of a release step that no longer checks for it.

### `wasm-unlisted`

**Committed Wasm with no manifest entry**

- **Severity:** `HIGH`
- **Suppressible:** `no`
- **Detector:** `builtin:wasm_manifest`
- **Roles:** `wasm`
- **Fixtures:** positive `wasm_unlisted`, negative `wasm_unlisted`
- **Pattern:** none *(evaluated by detector code)*

A binary artifact nobody declared is the payload delivery channel this class of attack ends in. A Wasm file the manifest does not carry, or that the scanner could not hash, has no stated origin, source or build command.
