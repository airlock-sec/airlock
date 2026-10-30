"""The generated half of the documentation site (task 8.6).

`scripts/build_site.py` rewrites the rule reference and the hero telemetry from the shipped
TOML, and `site/data/rules.json` carries the same rows. These tests run the script the way CI
does and then compare the published page with the data it claims to describe: a site that lists
a rule the package no longer ships is worse than no site, because it is a claim nobody checks.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "build_site.py"
SITE = REPO_ROOT / "site"
RULES = REPO_ROOT / "rules" / "builtin"


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def copy_inputs(tmp_path: Path) -> Path:
    """A repository copy holding only what the generator reads and writes."""
    root = tmp_path / "repo"
    (root / "rules").mkdir(parents=True)
    shutil.copytree(RULES, root / "rules" / "builtin")
    shutil.copytree(SITE, root / "site")
    return root


def shipped_rules() -> list[dict[str, object]]:
    rules: list[dict[str, object]] = []
    for path in sorted(RULES.glob("*.toml")):
        document = tomllib.loads(path.read_text(encoding="utf-8"))
        rules.extend(document["rule"])
    return rules


class TestCommittedSite:
    def test_the_generated_files_are_current(self) -> None:
        result = run(REPO_ROOT, "--check")

        assert result.returncode == 0, result.stderr
        assert result.stderr == ""

    def test_a_hand_edited_rule_block_is_refused(self, tmp_path: Path) -> None:
        root = copy_inputs(tmp_path)
        page = root / "site" / "rules.html"
        page.write_text(
            page.read_text(encoding="utf-8").replace(
                '<span class="sev sev--high">HIGH</span>',
                '<span class="sev sev--high">LOW</span>',
                1,
            ),
            encoding="utf-8",
        )

        result = run(root, "--check")

        assert result.returncode == 1
        assert "site/rules.html is stale" in result.stderr
        assert "scripts/build_site.py" in result.stderr

    def test_a_hand_edited_json_file_is_refused(self, tmp_path: Path) -> None:
        root = copy_inputs(tmp_path)
        path = root / "site" / "data" / "rules.json"
        path.write_text('{"rules": []}\n', encoding="utf-8")

        result = run(root, "--check")

        assert result.returncode == 1
        assert "site/data/rules.json is stale" in result.stderr

    def test_generation_is_deterministic(self, tmp_path: Path) -> None:
        root = copy_inputs(tmp_path)

        assert run(root).returncode == 0
        first = {
            path: path.read_bytes()
            for path in (root / "site" / "rules.html", root / "site" / "index.html")
        }
        assert run(root).returncode == 0
        for path, content in first.items():
            assert path.read_bytes() == content, path


class TestPublishedData:
    def test_every_shipped_rule_appears_once_with_its_severity(self) -> None:
        data = json.loads((SITE / "data" / "rules.json").read_text(encoding="utf-8"))
        shipped = {str(rule["id"]): rule for rule in shipped_rules()}

        assert data["counts"]["total"] == len(shipped) == len(data["rules"])
        for row in data["rules"]:
            source = shipped[row["id"]]
            assert row["severity"] == source["severity"]
            assert row["title"] == source["title"]
            assert row["rationale"] == source["rationale"]
            assert row["roles"] == source["roles"]
            assert row["suppressible"] is source["suppressible"]

    def test_every_rule_has_one_anchor_on_the_page(self) -> None:
        page = (SITE / "rules.html").read_text(encoding="utf-8")

        for rule in shipped_rules():
            rule_id = str(rule["id"])
            assert page.count(f'id="{rule_id}"') == 1, rule_id
            assert page.count(f'<h3 class="rule-id">{rule_id}</h3>') == 1, rule_id

    def test_the_hero_counts_match_the_page(self) -> None:
        index = (SITE / "index.html").read_text(encoding="utf-8")
        rules = shipped_rules()
        high = sum(1 for rule in rules if rule["severity"] == "high")
        warn = sum(1 for rule in rules if rule["severity"] == "warn")

        assert f'<span class="tel-v">{len(rules)}</span>' in index
        assert f'<span class="tel-v">{high} / {warn}</span>' in index

    def test_every_family_heading_carries_its_own_count(self) -> None:
        page = (SITE / "rules.html").read_text(encoding="utf-8")

        for path in sorted(RULES.glob("*.toml")):
            count = len(tomllib.loads(path.read_text(encoding="utf-8"))["rule"])
            assert f"<span>{count} RULES" in page, path.name


class TestRefusals:
    def test_an_unknown_rule_file_is_an_error(self, tmp_path: Path) -> None:
        root = copy_inputs(tmp_path)
        (root / "rules" / "builtin" / "future_family.toml").write_text(
            '[[rule]]\nid = "future-rule"\n', encoding="utf-8"
        )

        result = run(root, "--check")

        assert result.returncode == 2
        assert "unregistered rule file" in result.stderr
        assert "future_family" in result.stderr

    def test_an_unknown_severity_is_an_error(self, tmp_path: Path) -> None:
        root = copy_inputs(tmp_path)
        path = root / "rules" / "builtin" / "config_role.toml"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                'severity = "high"', 'severity = "critical"', 1
            ),
            encoding="utf-8",
        )

        result = run(root, "--check")

        assert result.returncode == 2
        assert "severity 'critical'" in result.stderr

    def test_a_missing_marker_is_an_error(self, tmp_path: Path) -> None:
        root = copy_inputs(tmp_path)
        page = root / "site" / "index.html"
        page.write_text(
            page.read_text(encoding="utf-8").replace("<!-- TELEMETRY:END -->", "", 1),
            encoding="utf-8",
        )

        result = run(root, "--check")

        assert result.returncode == 2
        assert "expected exactly one" in result.stderr
