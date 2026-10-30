"""Collector tests (tasks 2.2 and 2.3).

These run against real temporary git repositories: the collector's job is to read a git
index honestly, and a mock index would not prove anything about `-z --stage` parsing or
about what a symlink does to a scanner.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from tests.fixtures import assemble

from airlock import runner
from airlock.collector import (
    SKIP_ENCODING,
    SKIP_OVERSIZE,
    SKIP_SUBMODULE,
    SKIP_SYMLINK,
    SKIP_UNMERGED,
    check_runtime,
    collect,
    git_text,
    list_tracked_files,
)
from airlock.detectors import DETECTOR_NAMES
from airlock.fingerprint import number_occurrences
from airlock.model import EMPTY_MANIFEST, STATE_RULE_IDS, Finding, Policy, ScanContext, Severity
from airlock.roles import ARCHIVE_ROLE, NATIVE_ROLE, SOURCE_ROLE, WASM_ROLE, known_roles
from airlock.rules import load_role_globs, load_rules

ROLE_GLOBS = {
    "tooling-config": ("**/postcss.config.*", "**/next.config.*"),
    "editor-autorun": ("**/.vscode/tasks.json",),
}

WASM_HEAD = b"\x00asm\x01\x00\x00\x00"
GITLINK_SHA = "e3" + "0" * 38

# Assembled at call time rather than committed whole (`AGENTS.md` 4). A skipped file's contents are
# still bytes on disk here, and the `pat-` rules read every `.py` file in this repository.
DROPPER = f"{assemble('ev', 'al')}({assemble('Buf', 'fer.from')}(a,'base64'))\n"


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


def git_lenient(root: Path, *args: str) -> int:
    """Run git where a non-zero exit is the expected outcome, as it is for a conflicted merge."""
    return subprocess.run(
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
        check=False,
    ).returncode


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "--initial-branch=main")
    return root


def write(root: Path, rel: str, data: bytes | str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data.encode() if isinstance(data, str) else data)
    return path


def conflict(root: Path, *rels: str) -> None:
    """Leave every path in `rels` unmerged in the index, as a real merge conflict does.

    Two branches edit the same lines, so `git merge` exits non-zero and the paths sit at
    stages 1, 2 and 3 with no stage 0 entry. All paths conflict in one merge: git refuses to
    start a second one while any path is unmerged.
    """
    if not rels:
        rels = ("app.py",)
    for rel in rels:
        write(root, rel, "value = base\n")
    commit(root)
    git(root, "checkout", "-q", "-b", "other")
    for rel in rels:
        write(root, rel, "value = theirs\n")
    commit(root)
    git(root, "checkout", "-q", "main")
    for rel in rels:
        write(root, rel, "value = ours\n")
    commit(root)
    assert git_lenient(root, "merge", "-q", "--no-edit", "other") != 0


def commit(root: Path) -> str:
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "fixture")
    return git(root, "rev-parse", "HEAD").strip()


def scan(root: Path, policy: Policy | None = None):
    return collect(root, policy or Policy(), ROLE_GLOBS)


def rule_ids(findings) -> list[str]:
    return [finding.rule_id for finding in findings]


def entry_of(result, rel: str):
    for entry in result.entries:
        if entry.path == rel:
            return entry
    raise AssertionError(f"{rel} is not in the collected entries")


class TestListing:
    def test_tracked_files_are_returned_in_path_order(self, repo: Path) -> None:
        write(repo, "z.py", "x = 1\n")
        write(repo, "a.py", "y = 2\n")
        head = commit(repo)
        listing = list_tracked_files(repo)
        assert [entry.path for entry in listing] == ["a.py", "z.py"]
        assert check_runtime(repo) == head

    def test_untracked_files_are_out_of_scope(self, repo: Path) -> None:
        write(repo, "tracked.py", "x = 1\n")
        commit(repo)
        write(repo, "added_later.py", "eval(payload)\n")
        assert [entry.path for entry in scan(repo).entries] == ["tracked.py"]

    def test_a_path_with_spaces_survives_the_null_delimited_listing(self, repo: Path) -> None:
        write(repo, "docs/my file.py", "x = 1\n")
        commit(repo)
        assert [entry.path for entry in scan(repo).entries] == ["docs/my file.py"]


class TestRolesAndReads:
    def test_content_magic_beats_the_extension(self, repo: Path) -> None:
        write(repo, "not_python.py", WASM_HEAD + b"\x00\x00")
        commit(repo)
        result = scan(repo)
        entry = entry_of(result, "not_python.py")
        assert entry.roles == (WASM_ROLE,)
        assert entry.text is None
        assert entry.sha256 == hashlib.sha256(WASM_HEAD + b"\x00\x00").hexdigest()
        # A real Wasm binary is full of NUL bytes; it must not be reported as broken text.
        assert "nul-in-text" not in rule_ids(result.pending)

    def test_native_and_archive_magic_are_recognised(self, repo: Path) -> None:
        write(repo, "blob.rs", b"\x7fELF\x02\x01\x01\x01" + b"\0" * 20)
        write(repo, "bundle.gz", b"\x1f\x8b\x08\x00fake")
        commit(repo)
        result = scan(repo)
        assert entry_of(result, "blob.rs").roles == (NATIVE_ROLE,)
        assert entry_of(result, "bundle.gz").roles == (ARCHIVE_ROLE,)

    def test_sha256_covers_the_whole_file(self, repo: Path) -> None:
        data = "x" * 9000
        write(repo, "long.py", data)
        commit(repo)
        entry = entry_of(scan(repo), "long.py")
        assert entry.sha256 == hashlib.sha256(data.encode()).hexdigest()
        assert entry.skip_reason is None

    def test_no_default_directory_skip(self, repo: Path) -> None:
        write(repo, "node_modules/left-pad/index.js", "module.exports = 1\n")
        write(repo, "vendor/thing.py", "x = 1\n")
        write(repo, "dist/bundle.js", "eval(payload)\n")
        commit(repo)
        paths = [entry.path for entry in scan(repo).entries]
        assert len(paths) == 3

    def test_a_config_file_keeps_the_tooling_role_alongside_its_fallback(self, repo: Path) -> None:
        write(repo, "postcss.config.mjs", "export default {}\n")
        commit(repo)
        assert entry_of(scan(repo), "postcss.config.mjs").roles == (
            "tooling-config",
            "source",
        )


class TestSymlinks:
    def test_a_tracked_symlink_is_recorded_not_followed(self, repo: Path, tmp_path: Path) -> None:
        secret = tmp_path / "outside.txt"
        secret.write_text(DROPPER)
        link = repo / "postcss.config.mjs"
        link.symlink_to(secret)
        git(repo, "add", "-A")
        commit(repo)
        result = scan(repo)
        entry = entry_of(result, "postcss.config.mjs")
        assert entry.skip_reason == SKIP_SYMLINK
        assert entry.text is None
        assert "skipped-symlink" in rule_ids(result.pending)
        assert "eval" not in repr(result)


class TestSubmodules:
    SUBMODULE_URL = "https://example.invalid/stellar/lib.git"
    OTHER_URL = "https://example.invalid/other/fork.git"

    @staticmethod
    def add_gitlink(root: Path, rel: str = "vendor/lib", sha: str = GITLINK_SHA) -> None:
        git(root, "update-index", "--add", "--cacheinfo", f"160000,{sha},{rel}")

    @staticmethod
    def write_gitmodules(root: Path, rel: str = "vendor/lib", url: str = SUBMODULE_URL) -> None:
        write(
            root,
            ".gitmodules",
            f'[submodule "{rel}"]\n\tpath = {rel}\n\turl = {url}\n',
        )

    def test_a_gitlink_yields_submodule_present(self, repo: Path) -> None:
        write(repo, "keep.py", "x = 1\n")
        self.write_gitmodules(repo)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "seed")
        # A gitlink added straight to the index: a real submodule clone would need the
        # network, and the collector only ever looks at the index mode.
        self.add_gitlink(repo)

        result = scan(repo)

        assert rule_ids(result.pending) == ["submodule-present"]
        finding = result.pending[0]
        assert finding.severity is Severity.HIGH
        assert finding.path == "vendor/lib"
        assert finding.suppressible is False
        assert GITLINK_SHA[:12] in finding.message
        assert self.SUBMODULE_URL in finding.message
        assert "not listed in policy.submodules" in finding.message
        assert "scanned by its own pipeline" not in finding.message
        assert entry_of(result, "vendor/lib").skip_reason == SKIP_SUBMODULE

    def test_an_allowed_submodule_url_lowers_submodule_present_to_warn(self, repo: Path) -> None:
        write(repo, "keep.py", "x = 1\n")
        self.write_gitmodules(repo)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "seed")
        self.add_gitlink(repo)

        result = scan(repo, Policy(submodules=(self.SUBMODULE_URL,)))

        assert rule_ids(result.pending) == ["submodule-present"]
        finding = result.pending[0]
        assert finding.severity is Severity.WARN
        assert finding.suppressible is False
        assert "allowed by policy.submodules" in finding.message
        assert entry_of(result, "vendor/lib").skip_reason == SKIP_SUBMODULE

    def test_a_gitlink_without_a_gitmodules_entry_yields_submodule_unmapped(
        self, repo: Path
    ) -> None:
        write(repo, "keep.py", "x = 1\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "seed")
        self.add_gitlink(repo)

        result = scan(repo, Policy(submodules=(self.SUBMODULE_URL,)))

        assert rule_ids(result.pending) == ["submodule-unmapped"]
        finding = result.pending[0]
        assert finding.severity is Severity.HIGH
        assert finding.path == "vendor/lib"
        assert finding.suppressible is False
        assert GITLINK_SHA[:12] in finding.message
        assert entry_of(result, "vendor/lib").skip_reason == SKIP_SUBMODULE

    def test_a_gitmodules_entry_without_a_gitlink_yields_submodule_orphan(self, repo: Path) -> None:
        write(repo, "vendor/lib/regular.py", "x = 1\n")
        self.write_gitmodules(repo)
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "seed")

        result = scan(repo)

        assert rule_ids(result.pending) == ["submodule-orphan"]
        finding = result.pending[0]
        assert finding.severity is Severity.WARN
        assert finding.path == ".gitmodules"
        assert finding.line == 1
        assert finding.suppressible is False
        assert "vendor/lib" in finding.message
        assert self.SUBMODULE_URL in finding.message

    def test_duplicate_gitmodules_entries_for_one_path_fail_closed_as_unmapped(
        self, repo: Path
    ) -> None:
        write(
            repo,
            ".gitmodules",
            f'[submodule "first"]\n\tpath = vendor/lib\n\turl = {self.SUBMODULE_URL}\n'
            f'[submodule "second"]\n\tpath = vendor/lib\n\turl = {self.OTHER_URL}\n',
        )
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "seed")
        self.add_gitlink(repo)

        result = scan(repo, Policy(submodules=(self.SUBMODULE_URL,)))

        assert rule_ids(result.pending) == ["submodule-unmapped"]
        assert result.pending[0].severity is Severity.HIGH
        assert "multiple entries in .gitmodules" in result.pending[0].message

    def test_damaged_or_incomplete_gitmodules_cannot_authorize_a_gitlink(self, repo: Path) -> None:
        write(
            repo,
            ".gitmodules",
            '# \x00\n[submodule "vendor/lib"]\n\tpath = vendor/lib\n'
            f"\turl = {self.SUBMODULE_URL}\n",
        )
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "seed")
        self.add_gitlink(repo)

        result = scan(repo, Policy(submodules=(self.SUBMODULE_URL,)))

        assert {"nul-in-text", "submodule-unmapped"} <= set(rule_ids(result.pending))
        assert "submodule-present" not in rule_ids(result.pending)

    @pytest.mark.parametrize(
        "rule_id",
        sorted(rid for rid in STATE_RULE_IDS if rid.startswith("submodule-")),
    )
    def test_every_submodule_state_rule_has_a_positive_and_a_negative_repo_case(
        self, tmp_path: Path, rule_id: str
    ) -> None:
        def make_repo(name: str) -> Path:
            root = tmp_path / name
            root.mkdir()
            git(root, "init", "-q", "--initial-branch=main")
            write(root, "keep.py", "x = 1\n")
            return root

        pos = make_repo(f"pos-{rule_id}")
        neg = make_repo(f"neg-{rule_id}")

        if rule_id == "submodule-present":
            self.write_gitmodules(pos)
            commit(pos)
            self.add_gitlink(pos)
            commit(neg)
        elif rule_id == "submodule-unmapped":
            commit(pos)
            self.add_gitlink(pos)
            self.write_gitmodules(neg)
            commit(neg)
            self.add_gitlink(neg)
        elif rule_id == "submodule-orphan":
            self.write_gitmodules(pos)
            commit(pos)
            self.write_gitmodules(neg)
            commit(neg)
            self.add_gitlink(neg)
        else:
            pytest.fail(f"no positive/negative repository fixture defined for {rule_id}")

        assert rule_id in rule_ids(scan(pos).pending)
        assert rule_id not in rule_ids(scan(neg).pending)


class TestUnmergedPaths:
    """A file in the middle of a merge conflict has no committed version to scan (task 2.14).

    The index holds stages 1, 2 and 3 for it and no stage 0, and the working copy holds
    conflict markers. Dropping the path because none of those is the answer would be the
    silent skip the hard rules forbid, so it is reported as a skip with a reason.
    """

    def test_a_conflicted_path_is_reported_instead_of_dropped(self, repo: Path) -> None:
        conflict(repo)
        result = scan(repo)
        entry = entry_of(result, "app.py")
        assert entry.skip_reason == SKIP_UNMERGED
        assert entry.text is None
        assert entry.sha256 is None
        assert "skipped-unmerged" in rule_ids(result.pending)
        assert result.files_skipped == {SKIP_UNMERGED: 1}

    def test_the_listing_keeps_the_path_and_marks_it_unmerged(self, repo: Path) -> None:
        conflict(repo)
        app = [entry for entry in list_tracked_files(repo) if entry.path == "app.py"]
        assert len(app) == 1
        assert app[0].is_unmerged

    def test_one_conflicted_path_yields_one_finding_not_one_per_staged_version(
        self, repo: Path
    ) -> None:
        conflict(repo)
        ids = rule_ids(scan(repo).pending)
        assert ids.count("skipped-unmerged") == 1
        assert [entry.path for entry in scan(repo).entries].count("app.py") == 1

    def test_a_conflict_in_a_tooling_config_is_high_elsewhere_warn(self, repo: Path) -> None:
        conflict(repo, "postcss.config.mjs", "app.py")
        severities = {
            finding.rule_id: finding.severity
            for finding in scan(repo).pending
            if finding.path == "postcss.config.mjs"
        }
        assert severities["skipped-unmerged"] is Severity.HIGH
        plain = {
            finding.rule_id: finding.severity
            for finding in scan(repo).pending
            if finding.path == "app.py"
        }
        assert plain["skipped-unmerged"] is Severity.WARN

    def test_a_conflicted_path_survives_numbering_into_a_finding(self, repo: Path) -> None:
        conflict(repo)
        unmerged = [
            finding
            for finding in number_occurrences(scan(repo).pending)
            if finding.rule_id == "skipped-unmerged"
        ]
        assert len(unmerged) == 1
        assert unmerged[0].fingerprint.startswith("sha256:")
        assert unmerged[0].suppressible is False


class TestLimits:
    def test_oversize_is_warn_for_ordinary_roles(self, repo: Path) -> None:
        write(repo, "big.py", "x" * 500)
        commit(repo)
        result = scan(repo, Policy(max_file_bytes=200))
        assert "skipped-oversize" in rule_ids(result.pending)
        finding = next(f for f in result.pending if f.rule_id == "skipped-oversize")
        assert finding.severity is Severity.WARN
        assert entry_of(result, "big.py").skip_reason == SKIP_OVERSIZE

    def test_oversize_is_high_in_a_tooling_config(self, repo: Path) -> None:
        write(repo, "postcss.config.mjs", "x" * 500)
        commit(repo)
        result = scan(repo, Policy(max_file_bytes=200))
        finding = next(f for f in result.pending if f.rule_id == "skipped-oversize")
        assert finding.severity is Severity.HIGH

    @pytest.mark.skipif(os.geteuid() == 0, reason="root ignores file permissions")
    def test_unreadable_is_high(self, repo: Path) -> None:
        path = write(repo, "locked.py", "x = 1\n")
        commit(repo)
        path.chmod(0o000)
        try:
            result = scan(repo)
        finally:
            path.chmod(0o644)
        assert "skipped-unreadable" in rule_ids(result.pending)
        assert entry_of(result, "locked.py").skip_reason == "unreadable"


class TestDecoding:
    def test_a_nul_byte_is_a_finding_and_the_text_is_still_scanned(self, repo: Path) -> None:
        write(repo, "next.config.mjs", "// \x00\neval(x)\n")
        commit(repo)
        result = scan(repo)
        assert "nul-in-text" in rule_ids(result.pending)
        entry = entry_of(result, "next.config.mjs")
        assert entry.text is not None
        assert "eval(x)" in entry.text
        assert entry.skip_reason is None

    def test_utf16_with_a_bom_does_not_trip_the_nul_rule(self, repo: Path) -> None:
        write(repo, "postcss.config.mjs", "export default {}\n".encode("utf-16"))
        commit(repo)
        result = scan(repo)
        assert "nul-in-text" not in rule_ids(result.pending)
        assert "export default" in entry_of(result, "postcss.config.mjs").text

    def test_utf16_without_a_bom_is_still_reported(self, repo: Path) -> None:
        write(repo, "postcss.config.mjs", "export default {}\n".encode("utf-16-le"))
        commit(repo)
        assert "nul-in-text" in rule_ids(scan(repo).pending)

    def test_utf8_bom_is_stripped(self, repo: Path) -> None:
        write(repo, "a.py", "\ufeffx = 1\n")
        commit(repo)
        assert entry_of(scan(repo), "a.py").text == "x = 1\n"

    @pytest.mark.parametrize("newline", ["\n", "\r\n"], ids=["lf", "crlf"])
    def test_tracked_line_endings_preserve_decoded_text(self, repo: Path, newline: str) -> None:
        rel = "postcss.config.mjs"
        text = newline.join(("// café", "", "export default {}", ""))
        data = text.encode("utf-8")
        write(repo, rel, data)
        git(repo, "add", "--", rel)

        result = scan(repo)

        assert [entry.path for entry in result.entries] == [rel]
        entry = entry_of(result, rel)
        assert entry.text == text
        assert entry.sha256 == hashlib.sha256(data).hexdigest()
        assert entry.skip_reason is None
        assert result.pending == ()
        assert result.files_skipped == {}

    def test_lf_and_crlf_keep_runner_lines_and_fingerprints_on_the_same_path(
        self, repo: Path
    ) -> None:
        rules_root = Path(__file__).resolve().parents[2] / "rules"
        role_globs = load_role_globs(rules_root / "roles.toml")
        rules = load_rules(
            rules_root / "builtin",
            known_detectors=DETECTOR_NAMES,
            known_roles=known_roles(role_globs),
        )
        policy = Policy()
        rel = "postcss.config.mjs"
        trigger = "".join(("ev", "al", "(input);"))
        findings_by_ending: dict[str, list[Finding]] = {}
        hashes: list[str | None] = []
        for newline in ("\n", "\r\n"):
            # Rewrite one tracked path so the path component cannot explain fingerprint changes.
            text = newline.join(("// café", "", trigger, "", trigger, ""))
            write(repo, rel, text.encode("utf-8"))
            git(repo, "add", "--", rel)
            collection = collect(repo, policy, role_globs)
            assert collection.pending == ()
            assert collection.files_skipped == {}
            assert len(collection.entries) == 1
            entry = collection.entries[0]
            assert entry.text == text
            hashes.append(entry.sha256)

            findings = runner.scan(
                ScanContext(
                    entries=collection.entries,
                    policy=policy,
                    manifest=EMPTY_MANIFEST,
                    rules=rules,
                )
            )
            assert [(item.rule_id, item.path, item.line, item.severity) for item in findings] == [
                ("cfg-dynamic-code", rel, 3, Severity.HIGH),
                ("cfg-dynamic-code", rel, 5, Severity.HIGH),
            ]
            assert [item.evidence for item in findings] == [trigger, trigger]
            assert [item.occurrence for item in findings] == [0, 1]
            assert len({item.fingerprint for item in findings}) == 2
            findings_by_ending[newline] = findings

        assert hashes[0] != hashes[1]
        assert [item.fingerprint for item in findings_by_ending["\n"]] == [
            item.fingerprint for item in findings_by_ending["\r\n"]
        ]

    def test_undecodable_bytes_in_a_source_file_are_still_scanned(self, repo: Path) -> None:
        write(repo, "broken.py", b"x = 1\nname = caf\xe9\n")
        commit(repo)
        result = scan(repo)
        assert "non-utf8-text" in rule_ids(result.pending)
        entry = entry_of(result, "broken.py")
        assert entry.skip_reason is None
        assert entry.text is not None and "name = caf" in entry.text
        assert entry.roles == (SOURCE_ROLE,)

    def test_undecodable_bytes_elsewhere_are_a_warn_and_a_skip(self, repo: Path) -> None:
        write(repo, "notes.txt", b"\xff\xff\xfe\x01")
        commit(repo)
        result = scan(repo)
        finding = next(f for f in result.pending if f.rule_id == "non-utf8-text")
        assert finding.severity is Severity.WARN
        assert entry_of(result, "notes.txt").skip_reason == SKIP_ENCODING

    def test_files_skipped_counts_by_reason(self, repo: Path) -> None:
        write(repo, "notes.txt", b"\xff\xff\xfe\x01")
        write(repo, "ok.py", "x = 1\n")
        commit(repo)
        assert scan(repo).files_skipped == {SKIP_ENCODING: 1}


class TestStartupChecks:
    def test_a_directory_that_is_not_a_repository_is_a_plain_error(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="cannot read the repository"):
            check_runtime(tmp_path / "nothing")

    def test_no_git_on_path_is_reported(self, repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(shutil, "which", lambda _name: None)
        with pytest.raises(ValueError, match="needs git on PATH"):
            check_runtime(repo)

    def test_an_ancient_interpreter_is_reported(
        self, repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("airlock.collector.sys.version_info", (3, 10, 0))
        with pytest.raises(ValueError, match=r"needs Python 3\.11"):
            check_runtime(repo)

    def test_git_text_returns_stdout_without_a_shell(self, repo: Path) -> None:
        write(repo, "a.py", "x = 1\n")
        commit(repo)
        assert git_text(repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"

    def test_git_text_carries_the_failure_message(self, repo: Path) -> None:
        with pytest.raises(ValueError):
            git_text(repo, "rev-parse", "--verify", "HEAD")

    def test_a_git_timeout_is_a_config_error_from_either_caller(
        self, repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The listing call has its own git invocation, so it has to fail the same way (2.14)."""

        def raise_timeout(*_args: object, **_kwargs: object) -> None:
            raise subprocess.TimeoutExpired(["git"], 1)

        monkeypatch.setattr(subprocess, "run", raise_timeout)
        with pytest.raises(ValueError, match="git failed to run"):
            git_text(repo, "status", "--short")
        with pytest.raises(ValueError, match="git failed to run"):
            list_tracked_files(repo)


class TestStateFindingsAreFindings:
    """A skip is reported, which means it has to survive numbering into a `Finding`.

    Numbering needs something to key on, and a skipped file has no bytes, no text and no hash.
    Before task 2.7 these findings crashed the scan that tried to report them.
    """

    def test_every_state_finding_from_a_skipping_repo_gets_a_fingerprint(self, repo: Path) -> None:
        write(repo, "outside.txt", DROPPER)
        write(repo, "big.js", "b" * 200)
        write(
            repo,
            ".gitmodules",
            '[submodule "vendored"]\n\tpath = vendored\n\turl = https://example.invalid/v.git\n'
            '[submodule "gone"]\n\tpath = gone\n\turl = https://example.invalid/g.git\n',
        )
        (repo / "link.py").symlink_to(repo / "outside.txt")
        git(repo, "add", "-A")
        commit(repo)
        # After the commit, because `commit` stages the working tree and a fresh `git add -A`
        # would drop a mode the working tree cannot produce.
        git(repo, "update-index", "--add", "--cacheinfo", f"160000,{GITLINK_SHA},vendored")
        git(repo, "update-index", "--add", "--cacheinfo", f"160000,{GITLINK_SHA},unmapped")

        collection = collect(repo, Policy(max_file_bytes=160), ROLE_GLOBS)

        assert {
            "submodule-present",
            "submodule-unmapped",
            "submodule-orphan",
            "skipped-symlink",
            "skipped-oversize",
        } <= set(rule_ids(collection.pending))
        findings = number_occurrences(collection.pending)
        assert all(finding.fingerprint.startswith("sha256:") for finding in findings)
        assert len({finding.fingerprint for finding in findings}) == len(findings)
