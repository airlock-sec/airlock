# Airlock

A CLI and composite GitHub Action that audits Stellar and Soroban open-source repositories
for supply-chain compromise and release-integrity gaps. Python 3.11+, standard library only.

## Status

Building. The core engine runs: `airlock scan` collects a repository, applies the registered
rules and reports findings with exit codes 0/1/2/3, in console, GitHub-annotation, JSON and
step-summary form. Two P0 detectors are registered (`config_role` for JS/TS build tooling,
`wasm_manifest` for Wasm artifact integrity); the Soroban-side detectors and the composite
GitHub Action are not built yet, so there is no `uses: airlock-sec/airlock@…` line to copy into
a workflow. Do not treat a scan from this build as complete coverage. Progress is in
[`ROADMAP.md`](ROADMAP.md); the design is in [`ARCHITECTURE.md`](ARCHITECTURE.md).

## What it will check

1. A generic injection layer aimed at the PolinRider class of attack: loaders appended to
   tooling configs (`postcss.config.*`, `tailwind.config.*`, `next.config.*`,
   `eslint.config.*`, `babel.config.*`), editor auto-run tasks, and hidden payloads.
   It looks for capabilities, not signatures.
2. Soroban-aware layers generic scanners do not have: release-profile hygiene, Wasm
   artifact integrity against a hash-keyed manifest, Stellar secret-key leakage, and Cargo
   build vectors.

It reads policy from a trusted base, not from the commit under scan, so a pull request or a
stolen maintainer credential cannot quietly relax the rules it is judged by.

## What it does not do

It does not execute, import or evaluate scanned content. It does not fetch, and a scan makes
no network calls and sends no telemetry. It does not skip directories by default, and every
file it cannot read is reported instead of dropped. It is not an antivirus, not a
dependency-viability tool and not a replacement for a code review.

## Quickstart

Run a scan against the repository you are standing in:

```bash
PYTHONPATH=src python3 -m airlock scan --mode full
```

`--mode full` reads policy from the working tree and says so in the report with an INFO finding.
The trust models a scan really depends on are `--event pull_request --base <sha>` and
`--event push --before <sha>`, which read policy from the commit the change started at; both need
a checkout with history, so `actions/checkout` has to run with `fetch-depth: 0`.

The Action shape below is planned (tasks 4.1 and 4.2) and is not usable yet:

```yaml
- uses: airlock-sec/airlock@<full commit sha>   # pin the SHA, not a tag
  with:
    mode: pr
```

## Working in this repository

[`AGENTS.md`](AGENTS.md) is the entry point for coding agents and [`CONTRIBUTING.md`](CONTRIBUTING.md)
for humans. One rule applies to every contribution, however small: **the same pull request
must update `ROADMAP.md`** (tasks, changelog row, progress table, `Last updated`).

## License

Apache-2.0. See [`LICENSE`](LICENSE) and report vulnerabilities per [`SECURITY.md`](SECURITY.md).
