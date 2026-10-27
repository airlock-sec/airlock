# Airlock

A CLI and composite GitHub Action that audits Stellar and Soroban open-source repositories
for supply-chain compromise and release-integrity gaps. Python 3.11+, standard library only.

## Status

Pre-implementation scaffold. The repository holds the design documents, the package layout
and the core data models. There is **no working scanner yet**: `airlock scan` exits 2 by
design, so nothing can mistake an unbuilt tool for a passing one. Progress is in
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

Not usable yet. Planned shape (task 4.1 and 4.2):

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
