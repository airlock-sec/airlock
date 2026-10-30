"""The generated rule reference (`RULES.md` and `scripts/rule_reference.py`, task 5.2)."""

from __future__ import annotations

import inspect
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from scripts import rule_reference

from airlock import roles
from airlock.detectors import DETECTOR_NAMES
from airlock.model import Rule
from airlock.rules import load_role_globs, load_rules

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "rule_reference.py"
RULES_MD = REPO_ROOT / "RULES.md"
README_MD = REPO_ROOT / "README.md"
CI_YML = REPO_ROOT / ".github" / "workflows" / "ci.yml"
RULES_DIR = REPO_ROOT / "rules" / "builtin"
ROLES_FILE = REPO_ROOT / "rules" / "roles.toml"
SITE_RULES_JSON = REPO_ROOT / "site" / "data" / "rules.json"


def shipped_rules() -> tuple[Rule, ...]:
    role_globs = load_role_globs(ROLES_FILE)
    return load_rules(
        RULES_DIR,
        known_detectors=DETECTOR_NAMES,
        known_roles=sorted(roles.known_roles(role_globs)),
    )


def shipped_rule(rule_id: str) -> Rule:
    return next(item for item in shipped_rules() if item.id == rule_id)


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )


class TestRuleReferenceGenerator:
    def test_the_committed_rule_reference_is_current(self) -> None:
        result = run_cli("--check")
        assert result.returncode == 0, result.stdout + result.stderr

    def test_every_shipped_rule_and_family_count_is_in_the_generated_reference(self) -> None:
        families = rule_reference.load_families()
        rendered = rule_reference.render_reference(families)
        rules = shipped_rules()

        assert f"**Total:** {len(rules)} rules across {len(families)} families" in rendered
        for family in families:
            assert f"`{family.name}` ({len(family.rules)})" in rendered
            noun = "rule" if len(family.rules) == 1 else "rules"
            assert f"## `{family.name}` ({len(family.rules)} {noun})" in rendered

        for item in rules:
            suppressible = "yes" if item.suppressible else "no"
            assert f"### `{item.id}`\n\n**{item.title}**" in rendered
            assert f"- **Severity:** `{item.severity.name}`" in rendered
            assert f"- **Suppressible:** `{suppressible}`" in rendered
            assert f"- **Detector:** `{item.detector}`" in rendered
            for role_name in item.roles:
                assert f"`{role_name}`" in rendered
            assert (
                f"- **Fixtures:** positive `{item.tests.positive}`, "
                f"negative `{item.tests.negative}`"
            ) in rendered
            assert item.rationale in rendered

    def test_every_internal_anchor_in_generated_reference_resolves_to_a_heading_slug(
        self,
    ) -> None:
        rendered = RULES_MD.read_text(encoding="utf-8")
        heading_slugs = {
            rule_reference.heading_slug(line)
            for line in rendered.splitlines()
            if line.startswith("#")
        }
        anchors = re.findall(r"\]\(#([^)]+)\)", rendered)
        assert len(anchors) == len(shipped_rules())
        missing = [anchor for anchor in anchors if anchor not in heading_slugs]
        assert not missing, f"dead anchor(s) in RULES.md: {missing}"

    def test_rule_reference_and_site_rules_json_agree_on_every_rule(self) -> None:
        families = rule_reference.load_families()
        ref_by_id = {
            rule.id: (
                family.name,
                rule.title,
                rule.severity.name,
                rule.suppressible,
                rule.detector,
                list(rule.roles),
            )
            for family in families
            for rule in family.rules
        }
        site_payload = json.loads(SITE_RULES_JSON.read_text(encoding="utf-8"))
        site_rules = site_payload["rules"]
        site_by_id = {
            entry["id"]: (
                entry["family"],
                entry["title"],
                entry["severity"].upper(),
                entry["suppressible"],
                entry["detector"],
                entry["roles"],
            )
            for entry in site_rules
        }
        assert ref_by_id == site_by_id

    def test_render_rule_distinguishes_pattern_rule_from_code_detector_rule(self) -> None:
        with_pattern = shipped_rule("pat-decode-eval")
        without_pattern = shipped_rule("wasm-unlisted")

        assert with_pattern.pattern is not None
        assert without_pattern.pattern is None

        rendered_with = rule_reference.render_rule(with_pattern)
        rendered_without = rule_reference.render_rule(without_pattern)

        assert "- **Pattern:** `regex` (1 expression)" in rendered_with
        assert with_pattern.pattern.value[0] in rendered_with
        assert "evaluated by detector code" not in rendered_with

        assert "- **Pattern:** none *(evaluated by detector code)*" in rendered_without
        assert "```text" not in rendered_without

    def test_check_fails_when_committed_output_is_stale_or_missing(self, tmp_path: Path) -> None:
        missing = tmp_path / "RULES.md"
        assert rule_reference.main(["--check", str(missing)]) == 1

        assert rule_reference.main([str(missing)]) == 0
        assert rule_reference.main(["--check", str(missing)]) == 0

        missing.write_text(
            missing.read_text(encoding="utf-8").replace("wasm-unlisted", "wasm-stale-copy"),
            encoding="utf-8",
        )
        result = run_cli("--check", str(missing))
        assert result.returncode == 1
        assert "disagrees with" in result.stderr
        assert "### `wasm-unlisted`" in result.stdout

    def test_check_fails_when_a_rule_file_changes_without_regenerating_output(
        self, tmp_path: Path
    ) -> None:
        rules_copy = tmp_path / "builtin"
        shutil.copytree(RULES_DIR, rules_copy)
        output = tmp_path / "RULES.md"
        shutil.copyfile(RULES_MD, output)

        wasm_toml = rules_copy / "wasm_manifest.toml"
        original_title = shipped_rule("wasm-unlisted").title
        wasm_toml.write_text(
            wasm_toml.read_text(encoding="utf-8").replace(
                original_title, "Edited title without regenerating reference"
            ),
            encoding="utf-8",
        )

        result = run_cli("--check", "--rules-dir", str(rules_copy), str(output))
        assert result.returncode == 1
        assert "Edited title without regenerating reference" in result.stdout

    def test_invalid_rule_file_is_rejected_by_the_scanner_loader(self, tmp_path: Path) -> None:
        bad_dir = tmp_path / "builtin"
        bad_dir.mkdir()
        (bad_dir / "broken.toml").write_text(
            '[[rule]]\nid = "bad-rule"\ntitle = "Missing required fields"\n',
            encoding="utf-8",
        )
        output = tmp_path / "RULES.md"
        result = run_cli("--rules-dir", str(bad_dir), str(output))
        assert result.returncode == 2
        assert "missing required key(s)" in result.stderr
        assert not output.exists()

    def test_readme_links_to_generated_reference_and_carries_no_second_rule_table(self) -> None:
        readme = README_MD.read_text(encoding="utf-8")
        assert "[`RULES.md`](RULES.md)" in readme
        assert "| Rule | Severity | Shape |" not in readme

    def test_ci_checks_job_runs_pytest_and_this_suite_gates_the_reference(self) -> None:
        workflow = CI_YML.read_text(encoding="utf-8")
        assert "checks:" in workflow
        assert "run: python -m pytest" in workflow
        gate_source = inspect.getsource(
            TestRuleReferenceGenerator.test_the_committed_rule_reference_is_current
        )
        assert 'run_cli("--check")' in gate_source
        assert "result.returncode == 0" in gate_source
