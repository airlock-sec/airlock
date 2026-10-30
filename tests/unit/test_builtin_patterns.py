"""The `builtin_patterns` rules (task 3.6, `ARCHITECTURE.md` 9.6).

The fixture gate proves each rule fires on its own positive case and not on its negative. What this
module adds is the reason the family exists: coverage outside the five config filenames, claimed by
the `roles` a rule names rather than enforced in detector code, and one Appendix B case carried all
the way to an exit code.

`PRD.md` Appendix B case 7 is a decode-and-eval line under `vendor/`. The old script missed it
because its `SKIP_DIRS` matched the prefix. Airlock opens the file, resolves it to role `source`,
and until this family existed no pattern rule read `source`, so the scan reported clean with the
same exit code as a repository holding nothing. Case 7 is therefore tested here through `run_scan`,
where the exit code is decided, rather than against a detector call.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from airlock import detectors
from airlock.cli import run_scan
from airlock.model import EXIT_FINDINGS, EXIT_PASS, FileEntry, Mode, Rule, Severity
from airlock.roles import known_roles, resolve_roles
from airlock.rules import apply_patterns, load_role_globs, load_rules

REPO_ROOT = Path(__file__).resolve().parents[2]
ROLE_GLOBS = load_role_globs(REPO_ROOT / "rules" / "roles.toml")
RULES = load_rules(
    REPO_ROOT / "rules" / "builtin",
    known_detectors=detectors.DETECTOR_NAMES,
    known_roles=sorted(known_roles(ROLE_GLOBS)),
)
FAMILY = (
    "pat-decode-eval",
    "pat-invisible-unicode",
    "pat-exfil-endpoint",
    "pat-obfuscator-id",
    "pat-credential-harvest",
    "pat-chain-c2",
)

#: Every role a `builtin_patterns` rule may claim: text that is code, not prose, not a binary.
CODE_ROLES = ["editor-autorun", "other", "source", "tooling-config"]

POLICY = 'version = 1\n\n[policy]\nfail_on = "high"\n'

EVAL = "ev" + "al"
BUFFER_FROM = "Buf" + "fer" + "." + "from"
ATOB = "at" + "ob"
PASTEBIN = "paste" + "bin.com"
AWS_CRED = ".aws" + "/" + "credentials"
TRONGRID = "trongrid" + "." + "io"
CASE_SEVEN = f"{EVAL}({BUFFER_FROM}(process.argv[2], 'base64'))"

#: Separators and leaf names, split the way every other trigger string in this file is split, so
#: the paths a credential rule matches exist in the committed text only as the parts they join from
#: (`AGENTS.md` 4). `Login Data`, the wallet file and the browser key databases need it most: a bare
#: file name inside a double-quoted Python string is exactly the shape the rule looks for, and a
#: committed path would report the file that names it.
SLASH = "/"
BACKSLASH = "\\"
DOT = "."
LOGIN_DATA = "Login" + " " + "Data"
WALLET_DAT = "wallet" + DOT + "dat"
KEY3_DB = "key" + "3" + DOT + "db"
KEY4_DB = "key" + "4" + DOT + "db"


def join_path(*parts: str, sep: str = SLASH) -> str:
    """Join path parts at call time, so a spelling lives in the run and not in the file."""
    return sep.join(parts)


def windows_path(*parts: str) -> str:
    """A Windows-shaped absolute path, because the rule's separator classes carry a backslash."""
    return "C:" + join_path("", *parts, sep=BACKSLASH)


#: The store paths `pat-credential-harvest` has to keep reaching now that every branch sits behind
#: the `[./\\."']` anchor: what a loader, a setup script, a browser profile or a chain CLI writes.
CREDENTIAL_SPELLINGS: dict[str, str] = {
    "posix home aws": join_path("~", ".aws", "credentials"),
    "root owned ssh key": join_path("", "root", ".ssh", "id_ed25519"),
    "ssh rsa key": join_path("", "root", ".ssh", "id_rsa"),
    "windows aws": windows_path("Users", "dev", ".aws", "credentials"),
    "windows ssh key": windows_path("Users", "dev", ".ssh", "id_ed25519"),
    "windows chrome login data": windows_path("User Data", "Default", LOGIN_DATA),
    "windows chrome local storage": windows_path(
        "User Data", "Default", "Local Storage", "leveldb"
    ),
    "macos chrome login data": join_path("", "Library", "Chrome", "Default", LOGIN_DATA),
    "solana cli keypair": join_path("~", ".config", "solana", "id.json"),
    "gnupg private dir": join_path("~", ".gnupg", "private-keys-v1" + DOT + "d"),
    "firefox key database": join_path(
        "~", ".mozilla", "firefox", "profiles", "abc.default", KEY4_DB
    ),
    "bare key database in a join": join_path(KEY3_DB),
    "bitcoin wallet": join_path("~", ".Bitcoin", WALLET_DAT),
    "electrum wallets": join_path("~", ".electrum", "Electrum", "wallets", "default_wallet"),
    "multiversx wallets": join_path("~", ".multiversx", "MultiversX", "wallets", "wallet.json"),
}


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=airlock-test",
            "-c",
            "user.email=airlock-test@example.invalid",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "--initial-branch=main")
    return root


def commit_files(root: Path, files: dict[str, str]) -> None:
    """Write and commit, so the collector sees the tree the way a push would."""
    for rel, text in {"airlock.toml": POLICY, **files}.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "fixture")


def entry(path: str, roles: tuple[str, ...], text: str) -> FileEntry:
    return FileEntry(path=path, sha256=None, roles=roles, text=text)


def hits(path: str, roles: tuple[str, ...], text: str) -> set[str]:
    """Which rules the engine would report for one file, roles and all."""
    return {finding.rule_id for finding in apply_patterns(RULES, entry(path, roles, text), 20_000)}


def shipped_rule(rule_id: str) -> Rule:
    return next(rule for rule in RULES if rule.id == rule_id)


class TestRoleCoverageIsData:
    @pytest.mark.parametrize("rule_id", FAMILY)
    def test_a_rule_claims_the_roles_it_runs_on(self, rule_id: str) -> None:
        assert sorted(shipped_rule(rule_id).roles) == CODE_ROLES

    @pytest.mark.parametrize(
        "path",
        [
            "vendor/thing/loader.js",
            "src/app.py",
            "bin/release",
            "postcss.config.mjs",
            ".vscode/tasks.json",
        ],
    )
    def test_the_family_reaches_every_code_path_a_config_glob_misses(self, path: str) -> None:
        """None of these names is in `rules/roles.toml`, and four of five are not tooling at all."""
        roles = resolve_roles(path, b"", ROLE_GLOBS)
        assert "pat-decode-eval" in hits(path, roles, CASE_SEVEN)

    def test_prose_is_out_of_scope_because_of_the_roles_list_not_a_skip(self) -> None:
        assert "doc" not in {role for rule_id in FAMILY for role in shipped_rule(rule_id).roles}
        names = hits("docs/notes.md", ("doc",), CASE_SEVEN)
        assert not any(name.startswith("pat-") for name in names)


class TestAppendixBCase7:
    def test_a_decode_and_eval_under_vendor_changes_the_exit_code(self, repo: Path) -> None:
        commit_files(repo, {"vendor/thing/loader.js": CASE_SEVEN + "\n"})

        report = run_scan(repo, Mode.FULL)

        assert report.exit_code == EXIT_FINDINGS
        found = [item for item in report.findings if item.rule_id == "pat-decode-eval"]
        assert found, [item.rule_id for item in report.findings]
        assert found[0].severity is Severity.HIGH
        assert found[0].path == "vendor/thing/loader.js"
        assert found[0].roles == ("source",)

    def test_the_same_line_in_a_prose_file_reaches_no_verdict(self, repo: Path) -> None:
        commit_files(repo, {"docs/payload-notes.md": CASE_SEVEN + "\n"})

        report = run_scan(repo, Mode.FULL)

        assert not any(item.rule_id.startswith("pat-") for item in report.findings)

    def test_a_named_endpoint_on_its_own_stays_below_the_threshold(self, repo: Path) -> None:
        """The tier choice is a real one: an endpoint mention names itself but never stops a job."""
        commit_files(repo, {"src/beacon.js": f'const drop = "https://{PASTEBIN}/raw/x";\n'})

        report = run_scan(repo, Mode.FULL)

        assert report.exit_code == EXIT_PASS
        tiers = [item.severity for item in report.findings if item.rule_id == "pat-exfil-endpoint"]
        assert tiers == [Severity.WARN]

    def test_a_named_credential_store_is_a_warn_on_its_own(self, repo: Path) -> None:
        """3.7 owns the HIGH here: a path becomes the attack when a line reads it and sends it."""
        commit_files(repo, {"scripts/provision.py": f'KEYS = os.path.expanduser("~/{AWS_CRED}")\n'})

        report = run_scan(repo, Mode.FULL)

        assert report.exit_code == EXIT_PASS
        found = [item for item in report.findings if item.rule_id == "pat-credential-harvest"]
        assert [item.severity for item in found] == [Severity.WARN]
        assert found[0].path == "scripts/provision.py"

    def test_a_public_chain_node_is_named_without_borrowing_the_configs_verdict(
        self, repo: Path
    ) -> None:
        """A host in application code is a WARN; the same host configured in a build config is the
        HIGH that `cfg-chain-endpoint` already reports, and this rule does not claim that."""
        line = f'const NODE = "https://nile.{TRONGRID}/wallet/fullnode";\n'
        commit_files(repo, {"src/rpc.js": line})

        report = run_scan(repo, Mode.FULL)

        assert report.exit_code == EXIT_PASS
        assert [item.severity for item in report.findings if item.rule_id == "pat-chain-c2"] == [
            Severity.WARN
        ]
        assert "cfg-chain-endpoint" not in {item.rule_id for item in report.findings}


class TestTheCiSurfaceIsReachedByTheFallback:
    def test_a_workflow_is_read_because_its_extension_resolves_to_source(self) -> None:
        """`pat-*` names no workflow role, and reads a workflow anyway: the claim in the rule file
        is that the four code roles already cover the CI surface."""
        path = ".github/workflows/release.yml"
        roles = resolve_roles(path, b"", ROLE_GLOBS)
        assert {"workflow", "source"} <= set(roles)
        assert "pat-credential-harvest" in hits(path, roles, f'run: cat "$HOME/{AWS_CRED}"\n')

    def test_a_package_manifest_is_read_for_the_same_reason(self) -> None:
        path = "package.json"
        roles = resolve_roles(path, b"", ROLE_GLOBS)
        assert {"package-manifest", "source"} <= set(roles)
        assert "pat-chain-c2" in hits(path, roles, f'"rpc": "https://api.{TRONGRID}/"\n')


class TestTheCredentialAnchorKeepsItsRecall:
    """The path rule is anchored behind a one-character class, which is what makes it cheap.

    That shape is a trade, so the trade is checked rather than claimed. The flat alternation the
    first draft shipped with matched a store name anywhere on a line; the shipped form matches it
    only behind a separator, a quote or a dot, which is also why one adversarial cap-length line
    costs 1.2 ms instead of 10.3 (`ARCHITECTURE.md` 9.6). Each spelling below is a path a real
    loader, a setup script or a browser profile writes, assembled at import time from the separator
    constants so this file holds parts rather than payloads, and every one has to fire. An anchor
    is only free if it costs no reach this list already had.
    """

    @pytest.mark.parametrize(
        "spelling", list(CREDENTIAL_SPELLINGS.values()), ids=list(CREDENTIAL_SPELLINGS)
    )
    def test_a_store_named_behind_a_separator_still_fires(self, spelling: str) -> None:
        assert "pat-credential-harvest" in hits(
            "lib/collect.js", ("source",), f'const blob = load("{spelling}");'
        )


class TestInvisibleCharacters:
    def test_a_bidi_mark_inside_an_identifier_is_a_finding(self) -> None:
        names = hits("a.js", ("source",), "const target\u200fUrl = remote;")
        assert "pat-invisible-unicode" in names

    def test_the_escape_sequence_that_names_the_character_is_not_the_character(self) -> None:
        """Raw-text matching means six ASCII bytes are not one invisible character."""
        assert "pat-invisible-unicode" not in hits("a.js", ("source",), r'const z = "\u200b";')

    def test_a_zero_width_joiner_is_left_alone(self) -> None:
        """U+200D is how an emoji sequence is spelled, so the class does not carry it."""
        flag = "\U0001f1fa\U0001f3f4\u200d\U0001f1e6\U0001f1ff"
        assert "pat-invisible-unicode" not in hits("a.js", ("source",), f"const flag = '{flag}';")


class TestTheRepositoryDoesNotTriggerItsOwnRules:
    """`AGENTS.md` 4 says a committed file must not read as a payload. These are the rules that make
    that checkable, so they run over the files that define and prove them."""

    @pytest.mark.parametrize("rule_id", FAMILY)
    def test_the_file_holding_the_patterns_does_not_trigger_them(self, rule_id: str) -> None:
        path = "rules/builtin/builtin_patterns.toml"
        text = (REPO_ROOT / path).read_text(encoding="utf-8")
        assert rule_id not in hits(path, ("source",), text)

    def test_the_fixture_builders_and_these_tests_hold_only_fragments(self) -> None:
        for path in ("tests/fixtures/builtin_patterns.py", "tests/unit/test_builtin_patterns.py"):
            text = (REPO_ROOT / path).read_text(encoding="utf-8")
            fired = sorted(n for n in hits(path, ("source",), text) if n.startswith("pat-"))
            assert fired == [], (path, fired)
