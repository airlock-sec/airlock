---
date: 2026-10-27 22:36 UTC
tasks: 0.4, 2.3, FR-05, Appendix B
summary: The seven bypass claims in `PRD.md` 2.3 are now measured instead of reviewed, and all seven hold.
---

The seven bypass claims in `PRD.md` 2.3 are now measured instead of reviewed, and all
seven hold. `scripts/bypass_probe.py` builds a temporary git repository per Appendix B
case, copies in the external `malware_scan.py` it is handed with `--script` (read from
`Tollcraft/soroban-budget-assert@main`; the script and its payloads are never committed
here, and each trigger string is assembled from fragments at run time), commits a clean
base and then the case, and runs the script the way the workflow runs it. Every case
exits 0 and the workflow has no `continue-on-error`, so every case is a passing job. The
details that reading the script did not settle: `\0asm` is a NUL inside the first 4 KB,
so Wasm is dropped by the same test that drops any binary-looking text file while
`.wasm` sits in no extension list either; the case-2 payload still passes `node
--check`, so the silent skip costs the scan and not the attack; the inline
`malware-scan: allow` marker is checked before the rule table, so a line can exempt
itself from every rule; and `eval(decrypted)` scores one WARN with no HIGH, which is the
real PolinRider shape passing a gate written against `eval(atob(`. Two of the seven
needed more than a commit to record: item 4 is a property of where the scanner and its
allowlist live, so it is marked confirmed by inspection with the reason, and the
observed output is now in Appendix B rather than only a verdict in 2.3. PRD 2.3's
`[Unverified]` marker, Appendix B's heading and open question 3 are corrected to match.
This is what 3.9 has to fail closed against. Verified: the probe confirms `7 of 7` on
two runs, `ruff check` and `ruff format --check` clean on `scripts/`, `pytest` 433
passed unchanged, and the self-scan now covers 70 files including
`scripts/bypass_probe.py` itself with exit 0, which is the check that a file full of
fragment-assembled trigger strings does not read as a payload. Not verified: whether any
of the five dogfood repos tracks a directory in `SKIP_DIRS`, which decides how much real
exposure case 7 has
