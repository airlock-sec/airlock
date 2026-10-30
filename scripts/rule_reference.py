#!/usr/bin/env python3
"""Generate `RULES.md` from `rules/builtin/*.toml` (task 5.2).

Every rule in `rules/builtin/*.toml` already carries its own `id`, `title`, `severity`,
`suppressible`, `roles`, `detector`, optional `pattern`, `rationale`, and `tests` fixture pair.
Hand-maintaining a second copy in `README.md` drifts the moment a rule lands or changes.

This script loads the rule files through `airlock.rules.load_rules` and `load_rule_file`
so any rule the scanner refuses to load cannot appear in the generated reference, and renders
`RULES.md` grouped by rule family (`rules/builtin/<family>.toml`).

Usage:
    scripts/rule_reference.py [--check] [--rules-dir DIR] [--roles FILE] [output-path]

With `--check` nothing is written: the script exits 1 when the committed file disagrees with the
rule data, and prints the reference that would be right.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from airlock import roles  # noqa: E402
from airlock.detectors import DETECTOR_NAMES  # noqa: E402
from airlock.model import Rule, Severity  # noqa: E402
from airlock.rules import load_role_globs, load_rule_file, load_rules  # noqa: E402

DEFAULT_RULES_DIR = REPO_ROOT / "rules" / "builtin"
DEFAULT_ROLES_FILE = REPO_ROOT / "rules" / "roles.toml"
DEFAULT_OUTPUT = REPO_ROOT / "RULES.md"


@dataclass(frozen=True, slots=True)
class FamilyRules:
    """One `.toml` rule family file and the validated rules it holds."""

    name: str
    source_name: str
    rules: tuple[Rule, ...]


def load_families(
    rules_dir: Path = DEFAULT_RULES_DIR,
    roles_file: Path = DEFAULT_ROLES_FILE,
) -> tuple[FamilyRules, ...]:
    """Validate the full rule directory through `airlock.rules.load_rules` and group by file."""
    role_globs = load_role_globs(roles_file)
    known_role_names = sorted(roles.known_roles(role_globs))
    # Cross-check duplicate IDs, unknown detectors, and unknown roles with the scanner's own loader.
    load_rules(
        rules_dir,
        known_detectors=DETECTOR_NAMES,
        known_roles=known_role_names,
    )

    families: list[FamilyRules] = []
    for path in sorted(rules_dir.glob("*.toml")):
        file_rules = tuple(sorted(load_rule_file(path), key=lambda item: item.id))
        families.append(
            FamilyRules(
                name=path.stem,
                source_name=f"rules/builtin/{path.name}",
                rules=file_rules,
            )
        )
    return tuple(families)


def render_rule(rule: Rule) -> str:
    """Render one `Rule` entry, distinguishing pattern rules from code-only detector rules."""
    suppressible = "yes" if rule.suppressible else "no"
    role_list = ", ".join(f"`{role}`" for role in rule.roles)
    lines = [
        f"### `{rule.id}` — {rule.title}",
        "",
        f"- **Severity:** `{rule.severity.name}`",
        f"- **Suppressible:** `{suppressible}`",
        f"- **Detector:** `{rule.detector}`",
        f"- **Roles:** {role_list}",
        f"- **Fixtures:** positive `{rule.tests.positive}`, negative `{rule.tests.negative}`",
    ]
    if rule.pattern is None:
        lines.append("- **Pattern:** none *(evaluated by detector code)*")
    else:
        count = len(rule.pattern.value)
        noun = "expression" if count == 1 else "expressions"
        lines.append(f"- **Pattern:** `{rule.pattern.kind}` ({count} {noun})")
        for expr in rule.pattern.value:
            lines.extend(["  ```text", f"  {expr}", "  ```"])
    lines.extend(["", rule.rationale])
    return "\n".join(lines)


def render_reference(families: tuple[FamilyRules, ...]) -> str:
    """Render the complete `RULES.md` document from the loaded rule families."""
    all_rules = [rule for family in families for rule in family.rules]
    sev_counts = Counter(rule.severity for rule in all_rules)
    family_summary = ", ".join(f"`{family.name}` ({len(family.rules)})" for family in families)
    sev_parts = [
        f"{sev_counts[sev]} {sev.name}"
        for sev in (Severity.HIGH, Severity.WARN, Severity.INFO)
        if sev_counts[sev]
    ]
    sev_summary = ", ".join(sev_parts) if sev_parts else "0 rules"

    lines = [
        "# Rule Reference",
        "",
        "Generated from [`rules/builtin/*.toml`](rules/builtin) by "
        "[`scripts/rule_reference.py`](scripts/rule_reference.py). "
        "Do not edit by hand; run `python scripts/rule_reference.py` after changing a rule file.",
        "",
        f"**Total:** {len(all_rules)} rules across {len(families)} families "
        f"({family_summary}) — {sev_summary}.",
        "",
        "## Summary",
        "",
        "| Rule | Family | Severity | Suppressible | Detector | Roles | Fixtures |",
        "|---|---|---|---|---|---|---|",
    ]

    for family in families:
        for rule in family.rules:
            supp = "yes" if rule.suppressible else "no"
            roles_cell = ", ".join(f"`{role}`" for role in rule.roles)
            fixtures_cell = f"`{rule.tests.positive}` / `{rule.tests.negative}`"
            lines.append(
                f"| [`{rule.id}`](#{rule.id}) | `{family.name}` | {rule.severity.name} | "
                f"{supp} | `{rule.detector}` | {roles_cell} | {fixtures_cell} |"
            )

    for family in families:
        noun = "rule" if len(family.rules) == 1 else "rules"
        lines.extend(
            [
                "",
                f"## `{family.name}` ({len(family.rules)} {noun})",
                "",
                f"Source: [`{family.source_name}`]({family.source_name})",
            ]
        )
        for rule in family.rules:
            lines.extend(["", render_rule(rule)])

    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rule_reference.py",
        description="Generate or check RULES.md against rules/builtin/*.toml.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that the committed output matches the rule files without writing.",
    )
    parser.add_argument(
        "--rules-dir",
        type=Path,
        default=DEFAULT_RULES_DIR,
        help="Directory holding rule TOML files (default: rules/builtin).",
    )
    parser.add_argument(
        "--roles",
        type=Path,
        default=DEFAULT_ROLES_FILE,
        help="Path to roles.toml (default: rules/roles.toml).",
    )
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to the generated markdown reference (default: RULES.md).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        families = load_families(args.rules_dir, args.roles)
    except ValueError as exc:
        print(f"rule_reference: {exc}", file=sys.stderr)
        return 2

    expected = render_reference(families)
    output_path: Path = args.output

    if not args.check:
        output_path.write_text(expected, encoding="utf-8")
        return 0

    if not output_path.is_file():
        print(expected, end="")
        print(
            f"rule_reference: {output_path} does not exist; "
            "run scripts/rule_reference.py without --check",
            file=sys.stderr,
        )
        return 1

    committed = output_path.read_text(encoding="utf-8")
    if committed == expected:
        return 0

    print(expected, end="")
    print(
        f"rule_reference: {output_path} disagrees with {args.rules_dir}; "
        "run scripts/rule_reference.py without --check",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
