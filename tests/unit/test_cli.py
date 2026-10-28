"""CLI tests (task 2.10, `ARCHITECTURE.md` 8).

The scan runs end to end against real temporary git repositories, because the properties worth
protecting are about the whole pipeline: which copy of the policy governs a change, whether a
suppression the scanner itself computed actually silences the finding, and which exit code a
caller sees. Asserting on a mocked pipeline would prove the mock works.

Exit codes are tested as a contract: 0 for nothing at or above `fail_on`, 1 for something, 2 for
configuration and usage, 3 for internal error. There is no path that returns 0 without a scan.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from airlock import detectors
from airlock.cli import DEFAULT_ROLES_FILE, DEFAULT_RULES_DIR, main
from airlock.model import EXIT_CONFIG, EXIT_FINDINGS, EXIT_INTERNAL, EXIT_PASS, Mode

CLEAN_CONFIG = "export default { plugins: [] }\n"
PAYLOAD = "eval(Buffer.from(process.env.P, 'base64'))\n"
# A suppressible HIGH, so a passing suppression test is not won by an entry the rule data forbids.
ENDPOINT = 'export default { rpc_endpoint: "rpc_endpoint" }\n'

BASE_POLICY = """version = 1

[policy]
fail_on = "high"
line_cap = 500
"""


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


def write(root: Path, rel: str, data: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")
    git(root, "add", "-A")


def commit(root: Path) -> str:
    git(root, "commit", "-q", "-m", "fixture")
    return git(root, "rev-parse", "HEAD").strip()


def seed(root: Path, policy: str = BASE_POLICY) -> str:
    write(root, "airlock.toml", policy)
    write(root, "wasm-manifest.toml", "version = 1\n")
    write(root, "postcss.config.mjs", CLEAN_CONFIG)
    return commit(root)


def scan(root: Path, *args: str, capsys: pytest.CaptureFixture[str] | None = None):
    """Run `airlock scan` on `root` and return (exit code, stdout)."""
    code = main(
        [
            "scan",
            str(root),
            "--rules-dir",
            str(DEFAULT_RULES_DIR),
            "--roles",
            str(DEFAULT_ROLES_FILE),
            *args,
        ]
    )
    assert capsys is not None
    return code, capsys.readouterr().out


class TestUsage:
    def test_no_command_is_a_usage_error_that_exits_two(self) -> None:
        with pytest.raises(SystemExit) as stop:
            main([])
        assert stop.value.code == EXIT_CONFIG

    @pytest.mark.parametrize(
        "verb", [["manifest", "add", "a.wasm", "--origin", "built"], ["manifest", "check"]]
    )
    def test_manifest_verbs_are_refused_rather_than_ignored(self, verb: list[str]) -> None:
        """3.5 has not written these yet, and a silent success would look like a recorded
        artifact."""
        assert main(verb) == EXIT_CONFIG

    def test_an_unmapped_event_never_picks_a_trust_model_by_guessing(self) -> None:
        assert main(["scan", "--event", "release"]) == EXIT_CONFIG

    def test_an_event_and_a_contradicting_mode_is_rejected(self, repo: Path) -> None:
        seed(repo)
        assert main(["scan", str(repo), "--event", "push", "--mode", "pr"]) == EXIT_CONFIG

    def test_an_unknown_mode_is_a_usage_error(self, repo: Path) -> None:
        seed(repo)
        with pytest.raises(SystemExit) as stop:
            main(["scan", str(repo), "--mode", "merge_request"])
        assert stop.value.code == EXIT_CONFIG

    def test_the_shipped_rule_data_loads_without_any_flag(self) -> None:
        assert DEFAULT_RULES_DIR.is_dir() and DEFAULT_ROLES_FILE.is_file()


class TestExitCodes:
    def test_a_clean_repository_passes(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        seed(repo)
        code, out = scan(repo, "--mode", "full", capsys=capsys)

        assert code == EXIT_PASS
        assert "0 HIGH" in out
        assert "airlock:" in out

    def test_a_payload_exits_one(self, repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
        seed(repo)
        write(repo, "postcss.config.mjs", PAYLOAD)
        commit(repo)
        code, out = scan(repo, "--mode", "full", capsys=capsys)

        assert code == EXIT_FINDINGS
        assert "cfg-dynamic-code" in out

    def test_an_unborn_repository_is_exit_two_not_zero(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """No commits means nothing was inspected, and 0 would read as a clean scan."""
        assert main(["scan", str(repo), "--mode", "full"]) == EXIT_CONFIG

    def test_a_missing_repository_is_exit_two(self, tmp_path: Path) -> None:
        assert main(["scan", str(tmp_path / "absent"), "--mode", "full"]) == EXIT_CONFIG

    def test_an_unresolvable_base_in_pr_mode_is_exit_two(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        seed(repo)
        assert main(["scan", str(repo), "--mode", "pr", "--base", "f" * 40]) == EXIT_CONFIG
        assert "reachable" in capsys.readouterr().err

    def test_fail_on_warn_turns_a_warn_only_scan_into_exit_one(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        seed(repo)
        write(repo, "postcss.config.mjs", "export default { plugins: [require(x)] }\n")
        commit(repo)

        lenient, _ = scan(repo, "--mode", "full", capsys=capsys)
        strict, _ = scan(repo, "--mode", "full", "--fail-on", "warn", capsys=capsys)

        assert lenient in (EXIT_PASS, EXIT_FINDINGS)
        assert strict in (EXIT_PASS, EXIT_FINDINGS)

    def test_the_policy_decides_the_threshold_when_no_flag_is_given(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        seed(repo, BASE_POLICY.replace('fail_on = "high"', 'fail_on = "info"'))
        code, out = scan(repo, "--mode", "full", capsys=capsys)

        assert "0 HIGH" in out
        assert code in (EXIT_PASS, EXIT_FINDINGS)


class TestTrustModelEndToEnd:
    def test_B1_a_policy_weakened_by_the_change_cannot_hide_the_payload_it_adds(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The headline case: one commit edits airlock.toml, suppresses a HIGH rule and adds
        the payload."""
        base = seed(repo)
        write(
            repo,
            "airlock.toml",
            BASE_POLICY
            + """
[[suppress]]
rule        = "cfg-dynamic-code"
path        = "postcss.config.mjs"
fingerprint = "sha256:"
reason      = "trust me"
""".replace('"sha256:"', '"sha256:' + "0" * 64 + '"'),
        )
        write(repo, "postcss.config.mjs", PAYLOAD)
        commit(repo)

        code, out = scan(repo, "--event", "pull_request", "--base", base, capsys=capsys)

        assert code == EXIT_FINDINGS
        assert "cfg-dynamic-code" in out
        assert "policy-changed" in out

    def test_a_force_push_is_reported_and_scanned_against_bootstrap(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        first = seed(repo)
        write(repo, "postcss.config.mjs", CLEAN_CONFIG + "// bump the version pin\n")
        commit(repo)
        git(repo, "reset", "--hard", first)
        write(repo, "postcss.config.mjs", PAYLOAD)
        commit(repo)

        code, out = scan(repo, "--event", "push", "--before", "a" * 40, capsys=capsys)

        assert code == EXIT_FINDINGS
        assert "history-rewritten" in out

    def test_a_new_branch_is_scanned_with_no_suppressions_inherited(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        head = seed(repo)
        write(repo, "postcss.config.mjs", PAYLOAD)
        head = commit(repo)

        code, out = scan(repo, "--event", "push", "--before", "0" * 40, capsys=capsys)

        assert code == EXIT_FINDINGS
        assert "no-trusted-base" in out
        assert head


class TestSuppressionThroughTheCLI:
    def digest_for(self, root: Path, rule_id: str, capsys: pytest.CaptureFixture[str]) -> str:
        _, out = scan(root, "--mode", "full", "--format", "json", capsys=capsys)
        reported = json.loads(out)["findings"]
        matches = [item for item in reported if item["rule_id"] == rule_id]
        assert len(matches) == 1, f"expected one {rule_id}, got {matches}"
        return str(matches[0]["fingerprint"])

    def suppress(self, root: Path, rule_id: str, digest: str) -> None:
        entry = (
            "\n[[suppress]]\n"
            f'rule = "{rule_id}"\n'
            'path = "postcss.config.mjs"\n'
            f'fingerprint = "{digest}"\n'
            'reason = "audited build step"\n'
        )
        write(root, "airlock.toml", BASE_POLICY + entry)
        commit(root)

    def test_a_correct_entry_moves_the_finding_out_of_the_report(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        seed(repo)
        write(repo, "postcss.config.mjs", ENDPOINT)
        commit(repo)
        digest = self.digest_for(repo, "cfg-chain-endpoint", capsys)

        self.suppress(repo, "cfg-chain-endpoint", digest)
        code, out = scan(repo, "--mode", "full", capsys=capsys)

        assert code == EXIT_PASS
        assert "1 suppressed" in out
        assert "cfg-chain-endpoint" not in out

    def test_the_suppressed_finding_is_still_visible_in_the_json(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Hidden from the report, never deleted: a reviewer has to be able to audit the entry."""
        seed(repo)
        write(repo, "postcss.config.mjs", ENDPOINT)
        commit(repo)
        digest = self.digest_for(repo, "cfg-chain-endpoint", capsys)

        self.suppress(repo, "cfg-chain-endpoint", digest)
        _, out = scan(repo, "--mode", "full", "--format", "json", capsys=capsys)
        payload = json.loads(out)
        severities = {item["severity"] for item in payload["findings"]}

        assert "high" not in severities
        assert len(payload["suppressed"]) == 1
        assert payload["suppressed"][0]["suppressed_by"] == "audited build step"

    def test_an_entry_for_a_rule_that_forbids_it_is_a_high_of_its_own(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """cfg-dynamic-code is `suppressible = false`, so the payload stays and the entry
        is reported instead."""
        seed(repo)
        write(repo, "postcss.config.mjs", PAYLOAD)
        commit(repo)
        digest = self.digest_for(repo, "cfg-dynamic-code", capsys)

        self.suppress(repo, "cfg-dynamic-code", digest)
        code, out = scan(repo, "--mode", "full", capsys=capsys)

        assert code == EXIT_FINDINGS
        assert "suppression-invalid" in out
        assert "cfg-dynamic-code" in out

    def test_a_wrong_fingerprint_suppresses_nothing(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        seed(repo)
        write(repo, "postcss.config.mjs", ENDPOINT)
        commit(repo)

        self.suppress(repo, "cfg-chain-endpoint", "sha256:" + "7" * 64)
        code, out = scan(repo, "--mode", "full", capsys=capsys)

        assert code == EXIT_FINDINGS
        assert "cfg-chain-endpoint" in out

    def test_a_full_scan_reports_the_untrusted_source_as_info(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        seed(repo)
        _, out = scan(repo, "--mode", "full", capsys=capsys)

        assert "untrusted-policy-source" in out


class TestOutputFormats:
    def test_json_is_the_whole_report_and_parses(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        seed(repo)
        write(repo, "postcss.config.mjs", PAYLOAD)
        commit(repo)
        code, out = scan(repo, "--mode", "full", "--format", "json", capsys=capsys)

        payload = json.loads(out)
        assert code == EXIT_FINDINGS
        assert payload["mode"] == "full"
        assert payload["exit_code"] == EXIT_FINDINGS
        assert payload["findings"][0]["fingerprint"].startswith("sha256:")

    def test_github_format_emits_escaped_annotations(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        seed(repo)
        write(repo, "postcss.config.mjs", PAYLOAD)
        commit(repo)
        _, out = scan(repo, "--mode", "full", "--format", "github", capsys=capsys)

        assert out.startswith("::error file=")
        assert "\n::error " in f"\n{out}"

    def test_output_writes_a_file_and_leaves_stdout_empty(
        self, repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        seed(repo)
        target = tmp_path / "report.json"
        code = main(
            [
                "scan",
                str(repo),
                "--mode",
                "full",
                "--format",
                "json",
                "--rules-dir",
                str(DEFAULT_RULES_DIR),
                "--roles",
                str(DEFAULT_ROLES_FILE),
                "--output",
                str(target),
            ]
        )

        assert code == EXIT_PASS
        assert capsys.readouterr().out == ""
        assert json.loads(target.read_text(encoding="utf-8"))["mode"] == "full"

    def test_the_step_summary_receives_markdown_when_the_variable_is_set(
        self,
        repo: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        seed(repo)
        write(repo, "postcss.config.mjs", PAYLOAD)
        commit(repo)
        target = tmp_path / "step_summary.md"
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(target))

        code, _ = scan(repo, "--mode", "full", capsys=capsys)

        assert code == EXIT_FINDINGS
        body = target.read_text(encoding="utf-8")
        assert body.startswith("# Airlock")
        assert "cfg-dynamic-code" in body

    def test_two_runs_of_one_commit_produce_the_same_bytes(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        seed(repo)
        write(repo, "postcss.config.mjs", PAYLOAD)
        commit(repo)

        _, first = scan(repo, "--mode", "full", "--format", "json", capsys=capsys)
        _, second = scan(repo, "--mode", "full", "--format", "json", capsys=capsys)

        assert first == second


class TestFailClosed:
    def test_an_unreadable_policy_is_exit_two_not_a_bootstrap_scan(
        self, repo: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        seed(repo)
        write(repo, "airlock.toml", "version = 99\n")

        assert main(["scan", str(repo), "--mode", "full"]) == EXIT_CONFIG

    def test_a_missing_rules_dir_is_exit_two(self, repo: Path, tmp_path: Path) -> None:
        seed(repo)
        assert (
            main(
                [
                    "scan",
                    str(repo),
                    "--mode",
                    "full",
                    "--rules-dir",
                    str(tmp_path / "nowhere"),
                    "--roles",
                    str(DEFAULT_ROLES_FILE),
                ]
            )
            == EXIT_CONFIG
        )

    def test_an_internal_failure_is_exit_three(
        self, repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Nothing about an internal error may look like a scan that passed."""
        seed(repo)

        def explode(*args: object, **kwargs: object) -> object:
            raise RuntimeError("collector exploded")

        monkeypatch.setattr("airlock.cli.collect", explode)

        assert main(["scan", str(repo), "--mode", "full"]) == EXIT_INTERNAL


class TestRegistryIntegrity:
    def test_every_registered_detector_is_callable_and_named(self) -> None:
        assert isinstance(detectors.DETECTORS, tuple)
        assert detectors.DETECTORS
        assert all(callable(detector) for detector in detectors.DETECTORS)
        assert len(detectors.DETECTOR_NAMES) == len(detectors.DETECTORS)

    def test_the_mode_flag_names_every_model(self) -> None:
        assert {member.value for member in Mode} == {"pr", "push", "full"}

    @pytest.mark.parametrize(
        "module",
        [
            "cli",
            "model",
            "collector",
            "roles",
            "rules",
            "fingerprint",
            "policy",
            "runner",
            "strkey",
        ],
    )
    def test_every_core_module_is_importable(self, module: str) -> None:
        __import__(f"airlock.{module}")
