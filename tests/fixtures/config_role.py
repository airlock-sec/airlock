"""`config_role` fixture builders (task 2.12).

Each builder is named after the rule it proves, as `project_structure.md` 5 requires. Trigger text
is assembled from fragments at test time, so no committed file in this repository reads as a
payload, and a negative case is built to be a near miss of its own rule rather than an empty file:
an empty file proves nothing about a pattern.
"""

from __future__ import annotations

from . import LINE_CAP, TAIL_MAX_LEN, Case, File, Fixture

#: A path the shipped role globs resolve to `tooling-config`, where these rules apply.
CASE_PATH = "postcss.config.js"


def _join(*fragments: str) -> str:
    """Assemble trigger text so the repository holds fragments, never the assembled form."""
    return "".join(fragments)


def _config(*lines: str) -> Case:
    return Case(files=(File(CASE_PATH, text="\n".join(lines) + "\n"),))


def _opaque(count: int) -> str:
    """A generated high-entropy run, the shape of an appended payload line with none in it."""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/"
    value = 1_140_071_481_932_319_848_567
    out: list[str] = []
    for _ in range(count):
        value = (value * 63_641_362_238_467_930_051 + 14_426_950_408_889_633_075) % 2**64
        out.append(alphabet[(value >> 33) % len(alphabet)])
    return "".join(out)


FETCH = _join("fet", "ch")
REMOTE = _join('"https://exa', "mple.invalid/manifest")
EVAL = _join("ev", "al")
SPAWN = _join("spawn", "Sync")
DOWNLOADER = _join("wer", "get")


def cfg_dynamic_code() -> Fixture:
    return Fixture(
        positive=_config(
            "export default {",
            f"  setup: {EVAL}(payload);",
            "};",
        ),
        # `evalOrder` is a legitimate webpack key holding the same five letters. What makes the
        # positive case is the call, which is what the pattern asks for.
        negative=_config("export default {", '  evalOrder: "post",', "};"),
    )


def cfg_network() -> Fixture:
    return Fixture(
        positive=_config(
            "export default {",
            f"  manifest: {FETCH}({REMOTE}),",
            "};",
        ),
        negative=_config("export default {", '  apiBase: "example.invalid/manifest",', "};"),
    )


def cfg_chain_endpoint() -> Fixture:
    key = _join("rpc", "_", "endpoint")
    return Fixture(
        positive=_config("export default {", f"  {key}: buildTimeValue,", "};"),
        negative=_config("export default {", "  rpcRetries: 3,", "};"),
    )


def cfg_long_line() -> Fixture:
    over = "n" * (LINE_CAP + 1)
    under = "n" * 40
    return Fixture(
        positive=_config(
            "export default {",
            f'  banner: "{over}",',
            "};",
        ),
        negative=_config("export default {", f'  banner: "{under}",', "};"),
    )


def cfg_network_exec() -> Fixture:
    return Fixture(
        positive=_config(
            "export default {",
            f"  manifest: {FETCH}({REMOTE}),",
            f"  setup: {EVAL}(decoded);",
            "};",
        ),
        # Network on its own stays a WARN: some real Next.js configs fetch at build time. The
        # combination rule is the pairing, so the negative case keeps the half that is innocent.
        negative=_config("export default {", f"  manifest: {FETCH}({REMOTE}),", "};"),
    )


def cfg_process_spawn() -> Fixture:
    return Fixture(
        positive=_config(
            "export default {",
            f'  prebuild: {SPAWN}("{DOWNLOADER}", ["example.invalid/x", "-O"]);',
            "};",
        ),
        negative=_config("export default {", '  postbuild: "npm run build",', "};"),
    )


def cfg_appended_tail() -> Fixture:
    # Long enough to clear the tail limit, short enough that the line cap is not what reports it.
    return Fixture(
        positive=_config(
            "export default {",
            "  plugins: { tailwindcss: {} },",
            "};",
            _opaque(TAIL_MAX_LEN + 10),
        ),
        negative=_config(
            "export default {",
            "  plugins: { tailwindcss: {} },",
            "};",
            "// last touched by npm run build",
        ),
    )


BUILDERS = {
    "cfg_dynamic_code": cfg_dynamic_code,
    "cfg_network": cfg_network,
    "cfg_chain_endpoint": cfg_chain_endpoint,
    "cfg_long_line": cfg_long_line,
    "cfg_network_exec": cfg_network_exec,
    "cfg_process_spawn": cfg_process_spawn,
    "cfg_appended_tail": cfg_appended_tail,
}
