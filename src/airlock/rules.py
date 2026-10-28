"""Rule loading, in-code validation and the line-oriented pattern engine.

Task 2.5 (`ARCHITECTURE.md` 6.4). Rules are TOML data; there is no schema file and no plugin
loader. An unparsable or invalid rule file raises `ValueError`, which the CLI turns into exit
code 2, because a silently dropped rule would look like a clean scan.

The pattern engine is where `line_cap` is enforced. A line longer than the cap is never handed
to a regex (ADR-018): a minified bundle is the attack surface for catastrophic backtracking,
so the length itself becomes the finding.
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Iterable, Mapping
from pathlib import Path

from .fingerprint import PendingFinding, truncate_evidence
from .model import (
    MAX_MESSAGE_CHARS,
    STATE_RULE_IDS,
    FileEntry,
    Rule,
    RulePattern,
    RuleTests,
    Severity,
    severity_from_name,
)
from .roles import SENSITIVE_ROLES

#: The one pattern rule whose hits come from line length rather than from its pattern.
LONG_LINE_RULE_ID = "cfg-long-line"

RULE_FILE_KEYS = frozenset({"rule"})
ROLE_FILE_KEYS = frozenset({"roles"})
RULE_KEYS = frozenset(
    {
        "id",
        "title",
        "roles",
        "detector",
        "severity",
        "suppressible",
        "rationale",
        "pattern",
        "tests",
    }
)
RULE_REQUIRED = RULE_KEYS - {"pattern", "suppressible"}
PATTERN_KEYS = frozenset({"kind", "value"})
TESTS_KEYS = frozenset({"positive", "negative"})

#: Used when a loaded rule set carries no `cfg-long-line` rule, so an over-cap line can never
#: be withheld from the patterns in silence. The shipped rules file defines the same id; this
#: constant only exists as the floor.
FALLBACK_LONG_LINE = Rule(
    id=LONG_LINE_RULE_ID,
    title="Line longer than the configured cap",
    roles=("source", "doc", "other"),
    detector="pattern",
    severity=Severity.HIGH,
    suppressible=False,
    rationale="Unbounded lines are a regex denial of service and a hiding place.",
    pattern=RulePattern(kind="literal", value=("no literal ever matches this text",)),
    tests=RuleTests(positive="cfg_long_line", negative="cfg_long_line"),
)


def _check_keys(
    table: Mapping[str, object],
    *,
    allowed: frozenset[str],
    required: frozenset[str],
    context: str,
) -> None:
    unknown = sorted(set(table) - allowed)
    if unknown:
        raise ValueError(f"{context}: unknown key(s) {', '.join(unknown)}")
    missing = sorted(required - set(table))
    if missing:
        raise ValueError(f"{context}: missing required key(s) {', '.join(missing)}")


def _as_str(value: object, field: str, context: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{context}: {field} must be a string")
    return value


def _rule_from_toml(table: Mapping[str, object], source: Path, index: int) -> Rule:
    context = f"{source} [[rule]] #{index}"
    _check_keys(table, allowed=RULE_KEYS, required=RULE_REQUIRED, context=context)

    pattern: RulePattern | None = None
    pattern_table = table.get("pattern")
    if pattern_table is not None:
        if not isinstance(pattern_table, Mapping):
            raise ValueError(f"{context}: pattern must be a table")
        _check_keys(pattern_table, allowed=PATTERN_KEYS, required=PATTERN_KEYS, context=context)
        kind = _as_str(pattern_table["kind"], "pattern.kind", context)
        value = pattern_table["value"]
        if not isinstance(value, (str, list)):
            raise ValueError(f"{context}: pattern.value must be a string or a list of strings")
        pattern = RulePattern.from_toml(kind, value)

    tests_table = table.get("tests")
    if not isinstance(tests_table, Mapping):
        raise ValueError(f"{context}: tests must name a positive and a negative fixture builder")
    _check_keys(tests_table, allowed=TESTS_KEYS, required=TESTS_KEYS, context=context)

    roles = table.get("roles")
    if not isinstance(roles, list) or not all(isinstance(role, str) for role in roles):
        raise ValueError(f"{context}: roles must be a list of role names")
    if not roles:
        raise ValueError(f"{context}: roles must not be empty")

    suppressible = table.get("suppressible", True)
    if not isinstance(suppressible, bool):
        raise ValueError(f"{context}: suppressible must be a boolean")

    return Rule(
        id=_as_str(table["id"], "id", context),
        title=_as_str(table["title"], "title", context),
        roles=tuple(roles),
        detector=_as_str(table["detector"], "detector", context),
        severity=severity_from_name(_as_str(table["severity"], "severity", context)),
        suppressible=suppressible,
        rationale=_as_str(table["rationale"], "rationale", context),
        pattern=pattern,
        tests=RuleTests(
            positive=_as_str(tests_table["positive"], "tests.positive", context),
            negative=_as_str(tests_table["negative"], "tests.negative", context),
        ),
    )


def load_rule_file(path: Path) -> tuple[Rule, ...]:
    """Parse and validate one rule file. Every failure is a config error."""
    document = _load_toml(path)
    _check_keys(document, allowed=RULE_FILE_KEYS, required=RULE_FILE_KEYS, context=str(path))
    entries = document["rule"]
    if not isinstance(entries, list) or not entries:
        raise ValueError(f"{path}: must hold at least one [[rule]] table")
    rules: list[Rule] = []
    for index, table in enumerate(entries, start=1):
        if not isinstance(table, Mapping):
            raise ValueError(f"{path}: [[rule]] #{index} must be a table")
        rules.append(_rule_from_toml(table, path, index))
    return tuple(rules)


def _load_toml(path: Path) -> dict[str, object]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc


def load_rules(
    rules_dir: Path,
    *,
    known_detectors: Iterable[str] = (),
    known_roles: Iterable[str] = (),
) -> tuple[Rule, ...]:
    """Load every rule file in a directory and cross-check the set.

    Duplicate ids, a role no file can ever resolve to, and a detector the runner cannot
    dispatch to are all config errors. A typo in a role name would otherwise silence that
    rule forever while every check stayed green.
    """
    files = sorted(rules_dir.glob("*.toml"))
    if not files:
        raise ValueError(f"no rule files found in {rules_dir}")
    rules: list[Rule] = []
    for path in files:
        for rule in load_rule_file(path):
            if any(existing.id == rule.id for existing in rules):
                raise ValueError(f"duplicate rule id {rule.id} (in {path})")
            rules.append(rule)

    detector_names = frozenset(known_detectors)
    role_names = frozenset(known_roles)
    for rule in rules:
        if detector_names and rule.detector != "pattern":
            name = rule.detector.removeprefix("builtin:")
            if name not in detector_names:
                raise ValueError(f"rule {rule.id} names unknown detector {rule.detector}")
        if role_names:
            unknown = sorted(set(rule.roles) - role_names)
            if unknown:
                raise ValueError(f"rule {rule.id} names unknown role(s) {', '.join(unknown)}")
    return tuple(sorted(rules, key=lambda rule: rule.id))


def load_role_globs(path: Path) -> dict[str, tuple[str, ...]]:
    """Read `[roles.<name>] globs = [...]` from a roles file (`ARCHITECTURE.md` 7.5)."""
    document = _load_toml(path)
    _check_keys(document, allowed=ROLE_FILE_KEYS, required=ROLE_FILE_KEYS, context=str(path))
    roles = document["roles"]
    if not isinstance(roles, Mapping):
        raise ValueError(f"{path}: [roles] must be a table of role names")
    globs: dict[str, tuple[str, ...]] = {}
    for name, table in roles.items():
        context = f"{path}: role {name}"
        if not isinstance(table, Mapping):
            raise ValueError(f"{context}: must be a table holding globs")
        _check_keys(
            table, allowed=frozenset({"globs"}), required=frozenset({"globs"}), context=context
        )
        values = table["globs"]
        if not isinstance(values, list) or not values:
            raise ValueError(f"{context}: globs must be a non-empty list")
        if not all(isinstance(value, str) and value for value in values):
            raise ValueError(f"{context}: globs must be non-empty strings")
        globs[str(name)] = tuple(values)
    return globs


def line_matches(rule: Rule, line: str) -> bool:
    """Does this rule's pattern hit this line? Raw text, no masking (ADR-013).

    `re.search` keeps its own bounded cache of compiled expressions, so there is no
    module-level matcher state to leak between scans.
    """
    pattern = rule.pattern
    if pattern is None:
        raise ValueError(f"rule {rule.id} has no pattern to match with")
    if pattern.kind == "regex":
        return re.search(pattern.value[0], line) is not None
    return any(literal in line for literal in pattern.value)


def finding_for(
    rule: Rule,
    entry: FileEntry,
    line_number: int,
    *,
    evidence: str | None = None,
    message: str | None = None,
    severity: Severity | None = None,
) -> PendingFinding:
    """Build a pending finding from rule data plus the file and line it hit."""
    return PendingFinding(
        rule_id=rule.id,
        severity=rule.severity if severity is None else severity,
        path=entry.path,
        line=line_number,
        roles=entry.roles,
        message=((message or rule.title)[:MAX_MESSAGE_CHARS]),
        evidence=truncate_evidence(entry.text if evidence is None else evidence),
        suppressible=rule.suppressible and rule.id not in STATE_RULE_IDS,
        file_sha256=entry.sha256,
    )


def _long_line_rule(rules: Iterable[Rule]) -> Rule | None:
    return next((rule for rule in rules if rule.id == LONG_LINE_RULE_ID), None)


def _cap_severity(authored: Severity, roles: Iterable[str]) -> Severity:
    """A cap finding is HIGH inside a build config and WARN anywhere else (`ARCHITECTURE.md` 8).

    The rule file carries the sensitive-role severity, because that is the case that matters.
    """
    if SENSITIVE_ROLES.intersection(roles):
        return authored
    return Severity.WARN if authored is Severity.HIGH else authored


def apply_patterns(
    rules: Iterable[Rule], entry: FileEntry, line_cap: int
) -> tuple[PendingFinding, ...]:
    """Run every pattern rule that applies to one file, line by line.

    Only rules with `detector = "pattern"` are handled here; code detectors dispatch in the
    runner. Lines past `line_cap` never reach a regex and are accounted for by
    `cap_findings`, so the two paths cannot double up on the same line.
    """
    if entry.text is None or line_cap <= 0:
        return ()
    applicable = [
        rule
        for rule in rules
        if rule.detector == "pattern"
        and rule.id != LONG_LINE_RULE_ID
        and set(rule.roles).intersection(entry.roles)
    ]
    if not applicable:
        return ()
    findings: list[PendingFinding] = []
    for number, raw_line in enumerate(entry.text.split("\n"), start=1):
        line = raw_line.removesuffix("\r")
        if len(line) > line_cap:
            continue
        for rule in applicable:
            if line_matches(rule, line):
                findings.append(finding_for(rule, entry, number, evidence=line))
    return tuple(findings)


def cap_findings(
    rules: Iterable[Rule], entry: FileEntry, line_cap: int
) -> tuple[PendingFinding, ...]:
    """One finding per file for the lines past `line_cap`, naming the first and the count.

    The runner calls this for every file it has text for, whatever detectors exist: a line
    withheld from the regexes must never go unmentioned. There is no role filter, because an
    entry with text is text by construction and this is about its shape.
    """
    if entry.text is None or line_cap <= 0:
        return ()
    over_cap: list[tuple[int, str]] = []
    for number, raw_line in enumerate(entry.text.split("\n"), start=1):
        line = raw_line.removesuffix("\r")
        if len(line) > line_cap:
            over_cap.append((number, line))
    if not over_cap:
        return ()
    rule = _long_line_rule(rules) or FALLBACK_LONG_LINE
    first_number, first_line = over_cap[0]
    extra = "" if len(over_cap) == 1 else f", and {len(over_cap) - 1} more over-cap line(s) here"
    return (
        finding_for(
            rule,
            entry,
            first_number,
            evidence=first_line,
            message=(
                f"{rule.title}: line {first_number} is {len(first_line)} characters against a "
                f"{line_cap} character cap{extra}, so no pattern ran on it"
            ),
            severity=_cap_severity(rule.severity, entry.roles),
        ),
    )
