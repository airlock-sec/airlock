"""`builtin_patterns` fixture builders (task 3.6, `ARCHITECTURE.md` 9.6).

Same discipline as `config_role.py`: trigger text is assembled from fragments at call time, so
this repository holds fragments and never the assembled form (`AGENTS.md` 4). The paths are ones
the old script dropped outright (`dist/`) or that no config glob would ever have claimed, because
that is the coverage these four rules add.

A negative case is a near miss of its own rule rather than an empty file: an empty file proves
nothing about a pattern.
"""

from __future__ import annotations

from . import Case, File, Fixture, assemble

#: A file that is code, is not one of the five config names, and is not prose: the role the
#: `config_role` family never reaches.
CASE_PATH = "lib/loader.js"

#: An obfuscated artifact committed to a build directory, which the old `SKIP_DIRS` dropped.
BUNDLE_PATH = "dist/bundle.js"


def _case(path: str, *lines: str) -> Case:
    return Case(files=(File(path, text="\n".join(lines) + "\n"),))


def _source(*lines: str) -> Case:
    return _case(CASE_PATH, *lines)


EVAL = assemble("ev", "al")
EXEC = assemble("ex", "ec")
FUNC = assemble("Func", "tion")
TIMEOUT = assemble("set", "Timeout")
ATOB = assemble("at", "ob")
B64DECODE = assemble("b64", "decode")
BUFFER_FROM = assemble("Buffer", ".", "from")
URL_HEAD = assemble("http", "s://")
PASTEBIN = assemble("paste", "bin.com")
NGROK = assemble("ng", "rok.io")
WEBHOOK_SITE = assemble("webhook", ".site")
OBFUSCATED = assemble("_0x", "1a", "2b")
SHORT_HEX = assemble("_0x", "1f")

#: Built from code points: the rule is about a character no file in this repository may hold.
ZWSP = chr(0x200B)
RLM = chr(0x200F)


def pat_decode_eval() -> Fixture:
    return Fixture(
        positive=_source(
            "export function run(payload) {",
            f"  return {EVAL}({ATOB}(payload));",
            "}",
            # The member-expression form, which `cfg-dynamic-code`'s lookbehind lets pass, and the
            # Python form, where the verb is not `eval` at all.
            f"window.{FUNC}({BUFFER_FROM}(blob, 'base64'));",
            f"{EXEC}({B64DECODE}(code));",
        ),
        # `evaluate` is not `eval`, and a decoder on its own is not somebody asking to be run. Each
        # half of the pair shows up here once, innocent alone: the rule asks for both.
        negative=_source(
            f"const size = evaluate({ATOB}(token));",
            f"const decoded = {BUFFER_FROM}(blob, 'base64');",
            f"{TIMEOUT}(render, 0);",
            f"{EVAL}(state.callback);",
        ),
    )


def pat_invisible_unicode() -> Fixture:
    return Fixture(
        positive=_source(
            f"const target{RLM}Url = remote;",
            f"const pay{ZWSP}load = decoded;",
        ),
        # An escape sequence naming the character is not the character. Raw-text matching means the
        # first line here is a run of ASCII bytes, and the rule has to be able to say so.
        negative=_source(
            'const ZWSP = "\\u200b";',
            "const spaced = a\tb;",
        ),
    )


def pat_exfil_endpoint() -> Fixture:
    return Fixture(
        positive=_source(
            f'const drop = "{URL_HEAD}{PASTEBIN}/raw/Q1w2";',
            f"const tunnel = {NGROK};",
            f'notify("{URL_HEAD}{WEBHOOK_SITE}/beacon");',
        ),
        # A paste-site word with no host behind it, a host on the project's own domain, and a
        # substring that reads like a listed host until the word boundary is applied.
        negative=_source(
            'const label = "pastebin";',
            f'const docs = "{URL_HEAD}example.com/pastebin";',
            'const icon = "profile.ico";',
            f'const self = "{URL_HEAD}hooks.example.com/beacon";',
        ),
    )


def pat_obfuscator_id() -> Fixture:
    return Fixture(
        positive=_case(
            BUNDLE_PATH,
            f"var {OBFUSCATED} = ['A', 'B'];",
            f"function decode({OBFUSCATED}, offset) {{",
            f"  return String.fromCharCode({OBFUSCATED}[offset]);",
            "}",
        ),
        # Two hex digits is a minifier's short name rather than the four-digit grammar, and a
        # bare hex literal with no `_0x` prefix is what an address or a colour looks like in code.
        negative=_case(
            BUNDLE_PATH,
            f"var {SHORT_HEX} = 0;",
            'const colour = "0xdeadbeef";',
            "const a1 = 0, b2 = 1;",
        ),
    )


BUILDERS = {
    "pat_decode_eval": pat_decode_eval,
    "pat_invisible_unicode": pat_invisible_unicode,
    "pat_exfil_endpoint": pat_exfil_endpoint,
    "pat_obfuscator_id": pat_obfuscator_id,
}
