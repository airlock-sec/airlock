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

#: Credential stores and chain endpoints, same discipline: the assembled form exists only during a
#: test run, so neither this file nor its positive case is a finding against this repository.
AWS_CRED = assemble("~", "/", ".aws", "/", "credentials")
SSH_PRIVATE = assemble("~", "/", ".ssh", "/", "id_ed25519")
SOLANA_KEYPAIR = assemble("~", "/", ".config", "/solana/", "id.json")
GNUPG_PRIVATE = assemble("~", "/", ".gnupg", "/", "private-keys-v1.d")
CHROME_LOGIN = assemble("User Data", "/", "Default", "/", "Login", " Data")
FIREFOX_KEYS = assemble("profile", "/", "key4", ".", "db")
BITCOIN_WALLET = assemble("Bitcoin", "/", "wallet", ".", "dat")
#: The near misses of each: a sibling file in the same directory, and a public key.
AWS_CONFIG = assemble("~", "/", ".aws", "/", "config")
SSH_PUBLIC = assemble(SSH_PRIVATE, ".", "pub")
GNUPG_PUBLIC = assemble("~", "/", ".gnupg", "/", "pubring.kbx")
ELECTRUM_DB = assemble("Electrum", "/", "blocks.db")
WALLET_BACKUP = assemble(BITCOIN_WALLET, ".", "bak")

TRONGRID = assemble("nile", ".", "trongrid", ".", "io")
TRONSCAN = assemble("tronscan", ".", "org")
BSC_SEED = assemble("bsc-dataseed", ".", "binance", ".", "org")
#: Near misses: an SDK name, a host that shares a listed prefix, and an explorer elsewhere.
TRON_WEB = assemble("tron", "web")
BSC_MIRROR = assemble("bsc-dataseed", ".", "example", ".", "com")
EXPLORER_OTHER = assemble("etherscan", ".", "io")

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


def pat_credential_harvest() -> Fixture:
    return Fixture(
        positive=_source(
            f'const keys = load("{AWS_CRED}");',
            f'const signer = load("{SSH_PRIVATE}");',
            f'const cli = load("{SOLANA_KEYPAIR}");',
            f'const ring = load("{GNUPG_PRIVATE}");',
            f'const browser = load("{CHROME_LOGIN}");',
            f'const nss = load("{FIREFOX_KEYS}");',
            f'const node = load("{BITCOIN_WALLET}");',
        ),
        # Each line keeps the directory the store lives in and loses the store: a config file, a
        # public key, a public keyring, a chain database, and a backup of a wallet file the rule
        # does name, one extension further than the pattern asks for.
        negative=_source(
            f'const region = load("{AWS_CONFIG}");',
            f'const authorised = load("{SSH_PUBLIC}");',
            f'const certs = load("{GNUPG_PUBLIC}");',
            f'const headers = load("{ELECTRUM_DB}");',
            f'const archive = load("{WALLET_BACKUP}");',
        ),
    )


def pat_chain_c2() -> Fixture:
    return Fixture(
        positive=_source(
            f'const rpc = "{URL_HEAD}{TRONGRID}/wallet/fullnode";',
            f'const broadcast = "{URL_HEAD}api.{TRONSCAN}/solidityapicall";',
            f'const fork = "{URL_HEAD}{BSC_SEED}";',
        ),
        # The SDK name and a host that borrows a listed prefix are what an ordinary integration
        # looks like, and an explorer on another domain is what a reviewer would call unrelated.
        # `cfg-chain-endpoint` is the rule that reads the SDK name, inside a build config.
        negative=_source(
            f"import {TRON_WEB} from '{TRON_WEB}';",
            f'const mirror = "{URL_HEAD}{BSC_MIRROR}";',
            f'const lookup = "{URL_HEAD}{EXPLORER_OTHER}/tx/1";',
        ),
    )


BUILDERS = {
    "pat_decode_eval": pat_decode_eval,
    "pat_invisible_unicode": pat_invisible_unicode,
    "pat_exfil_endpoint": pat_exfil_endpoint,
    "pat_obfuscator_id": pat_obfuscator_id,
    "pat_credential_harvest": pat_credential_harvest,
    "pat_chain_c2": pat_chain_c2,
}
