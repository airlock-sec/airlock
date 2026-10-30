---
date: 2026-10-27 20:42 UTC
tasks: 2.11, 3.1, 3.4, 2.2, 2.3, 2.4, 2.5, 2.6
summary: `config_role` and `wasm_manifest` implemented over the shipped rule data, and `runner.py` dispatches them.
---

`config_role` and `wasm_manifest` implemented over the shipped rule data, and
`runner.py` dispatches them. Rules are split by owner: the engine pass runs the
`pattern` rules and the `line_cap` account for every file with text, while a `builtin:`
rule may carry a pattern only its detector reads. That is how `cfg-process-spawn` keeps
both tiers (WARN for a build step stated up front, HIGH when the command names a
downloader, a decoder or an inline script) without the same line being reported twice.
`cfg-long-line` moved out of `apply_patterns` into `cap_findings` for the same reason as
2.3: a withheld line must be accounted for whatever the registry holds. `wasm_manifest`
stops calling an entry stale when its declared path still holds a file, so one swapped
artifact yields one finding, and a file named `.wasm` with no Wasm header is reported as
the pointer shape it is. A detector that raises keeps the findings it already yielded
and adds one HIGH `detector-error`. 2.11 ticked; 3.1 and 3.4 annotated as in progress
with what is left. Also corrected here: 2.2 to 2.6 were merged without the roadmap
update the rule requires. Verified: `pytest` 229 passed, `ruff check` and `ruff format
--check` clean on 34 files, `mypy src` clean on 24 files. Not verified: an end-to-end
scan, since the CLI still refuses to report a scan that did not run
