---
date: 2026-10-30 19:20 UTC
tasks: 5.2, G7
summary: Close #29 (5.2): `RULES.md` is generated from `rules/builtin/*.toml` by `scripts/rule_reference.py`, whose `--check` mode the unit suite runs, replacing the four hand-copied rule tables in `README.md`.
---

Close #29 (task 5.2): generate `RULES.md` from `rules/builtin/*.toml` via
`scripts/rule_reference.py` instead of maintaining a second rule copy by hand in
`README.md`. The generator loads rule files through `airlock.rules.load_rules`,
`load_rule_file` and `load_role_globs` against `DETECTOR_NAMES` and `roles.known_roles`,
so any rule the scanner rejects raises `ValueError` and exits 2 without writing output.
`RULES.md` states the total rule count (24), per-family counts (`builtin_patterns` 6,
`ci_surface` 6, `config_role` 7, `wasm_manifest` 5) and severity breakdown (12 HIGH, 12
WARN) in the header, followed by a summary table and per-family sections listing each
rule's `id`, `title`, `severity`, `suppressible`, `detector`, `roles`, `pattern` (`kind`
and expressions for pattern-backed rules, `none (evaluated by detector code)` when
`pattern is None`), `tests` (`positive` and `negative` fixture names) and `rationale`.
`python scripts/rule_reference.py --check` regenerates in memory and exits 1 when
`RULES.md` disagrees with `rules/builtin/*.toml`, and
`tests/unit/test_rule_reference.py` runs it as a subprocess during `python -m pytest` in
the `checks` job of `.github/workflows/ci.yml` (matching how `test_roadmap_gate.py` and
`test_build_site.py` gate `ROADMAP.md` and `site/` in `checks` without editing
`.github/workflows/ci.yml`).

`README.md` drops the four hand-copied rule tables in favor of family framing and a
direct link to `RULES.md`, and `project_structure.md` and `CONTRIBUTING.md` record
`RULES.md` and `scripts/rule_reference.py`.

Fixtures and tests: Added 8 unit tests in `tests/unit/test_rule_reference.py` covering
`--check`, full rule and family count coverage, pattern vs non-pattern rendering (`pat-
decode-eval` vs `wasm-unlisted`), stale output and rule-edit failure, invalid TOML
rejection, and README/CI invariants
