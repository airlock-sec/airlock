"""`ci_surface` detector: the CI-layer rules that need two conditions at once.

Task 3.6 (`ARCHITECTURE.md` 9.6). The family's single-condition rules (`pat-privileged-trigger`,
`pat-lifecycle-fetch` and `pat-editor-command-path`) are pattern data and run in the engine pass,
so this module yields only what a line-at-a-time pattern cannot: a secret interpolation paired
with a verb that displays it, a privileged trigger paired with a head checkout, and a fetch paired
with what the same line hands it to.

Two hard rules shape it. There is no comment or string masking (ADR-013), so a YAML comment that
spells out the shape is a match by design. And no line past `line_cap` is searched, which is why the
trigger and fetch halves read their pattern out of the rule data through `rules.line_matches` rather
than carrying their own copy: an over-cap line is `cfg-long-line`'s account to give, and a second
uncapped reader of the same text would be a ReDoS hole in the one layer meant to close it.

The pairings are separate linear searches instead of one regex for the same reason. The obvious
single pattern for the dropper, a downloader then `.*` then a shell, restarts its `.*` at every
column, so it is quadratic in the line length and therefore unbounded in a file. Every matcher below
is a literal or a bounded character class, and the two that pair conditions run only on lines the
first condition already hit.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from ..fingerprint import PendingFinding
from ..model import FileEntry, Rule, ScanContext
from ..rules import finding_for, line_matches

PRIVILEGED_RULE_ID = "pat-privileged-trigger"
FETCH_RULE_ID = "pat-lifecycle-fetch"
EXEC_RULE_ID = "pat-lifecycle-exec"
SECRET_DUMP_RULE_ID = "pat-secret-dump"
HEAD_CHECKOUT_RULE_ID = "pat-ptr-head-checkout"

#: `${{ secrets.NAME }}`, the only form in which a workflow can name a credential it was given.
_SECRETS_INTERP = re.compile(r"""\$\{\{\s*secrets\.[A-Za-z0-9_]+\s*\}\}""")

#: A command that puts a value where a human or a later step can read it. Passing a secret through
#: `env:` or `with:` is not in this list, because that is how a workflow uses one, and it is the
#: negative fixture rather than a finding.
_DISPLAY_VERB = re.compile(
    r"""\b(?:echo|printf|print|cat|tee|xxd|base64)\b|\b(?:Write-Output|Add-Content|Out-File)\b"""
)

#: The one echo that is hygiene: masking a value so a later log line cannot leak it.
_MASK_MARKER = "::add-mask::"

#: A ref that resolves to the contributor's tree rather than the base. `refs/pull/N/head` and
#: `refs/pull/N/merge` are the explicit forms; `github.event.pull_request.head` covers the ref, the
#: sha and the fork clone url, which all point at the untrusted tree.
_HEAD_REF = re.compile(
    r"""github\.event\.pull_request\.head\b|refs/pull/[^/'"\s]+/(?:head|merge)\b""",
    re.VERBOSE,
)

#: A checkout step, including one pinned by owner and fork. Without it the head ref could be an
#: argument in a step that never checks anything out.
_CHECKOUT_STEP = re.compile(r"""uses:\s*(?:[\w.\-]+/)?actions/checkout@""")

#: What a fetched payload gets handed to: a shell or interpreter after a separator, PowerShell's
#: `Invoke-Expression`, a process substitution, or an `eval`. Each of these is innocent until the
#: same line also fetches, which is why the check that runs this is a two-condition one.
_EXEC_TARGET = re.compile(
    r"""
      (?:\||&&|;)\s*(?:sudo\s+)?(?:[\w.\-/]*/)?
        (?:sh|bash|dash|zsh|pwsh|powershell|python[23]?|node|perl|ruby|cmd|iex)(?:\.exe)?\b
    | \bInvoke-Expression\b
    | <\(\s*(?:curl|wget|Invoke-WebRequest)\b
    | (?<![\w.$])eval\b
    """,
    re.VERBOSE,
)


def _by_id(ctx: ScanContext) -> dict[str, Rule]:
    return {rule.id: rule for rule in ctx.rules}


def _text_lines(text: str) -> dict[int, str]:
    return {number: raw.removesuffix("\r") for number, raw in enumerate(text.split("\n"), start=1)}


def _shares_a_role(rule: Rule, entry: FileEntry) -> bool:
    """Does this rule claim a role the entry resolved to?

    The role list comes from the rule data, so a rename in `rules/builtin/ci_surface.toml` moves
    this dispatch with it instead of leaving a detector that quietly finds nothing.
    """
    return bool(set(rule.roles) & set(entry.roles))


def _searchable(lines: dict[int, str], line_cap: int) -> Iterable[tuple[int, str]]:
    return ((number, line) for number, line in lines.items() if len(line) <= line_cap)


def _first_hit(
    lines: dict[int, str], line_cap: int, test: re.Pattern[str]
) -> tuple[int, str] | None:
    for number, line in _searchable(lines, line_cap):
        if test.search(line):
            return number, line
    return None


def _first_pattern_hit(
    rule: Rule | None, lines: dict[int, str], line_cap: int
) -> tuple[int, str] | None:
    """First line a rule's own pattern hits, so the trigger half is not copied into code."""
    if rule is None or rule.pattern is None:
        return None
    for number, line in _searchable(lines, line_cap):
        if line_matches(rule, line):
            return number, line
    return None


def _secret_dumps(
    rule: Rule, entry: FileEntry, lines: dict[int, str], line_cap: int
) -> list[PendingFinding]:
    """Every line that names a credential and something that would print or store it."""
    findings: list[PendingFinding] = []
    for number, line in _searchable(lines, line_cap):
        if _MASK_MARKER in line:
            continue
        if not _SECRETS_INTERP.search(line) or not _DISPLAY_VERB.search(line):
            continue
        findings.append(
            finding_for(
                rule,
                entry,
                number,
                evidence=line,
                message=(
                    f"{rule.title}: the line interpolates a credential the job was given and names "
                    "a command that writes it to the log or to a later step's environment"
                ),
            )
        )
    return findings


def _head_checkout(
    rule: Rule,
    entry: FileEntry,
    lines: dict[int, str],
    trigger_rule: Rule | None,
    line_cap: int,
) -> PendingFinding | None:
    """Privileged trigger plus a head ref plus a checkout step, in one file."""
    trigger = _first_pattern_hit(trigger_rule, lines, line_cap)
    step = _first_hit(lines, line_cap, _CHECKOUT_STEP)
    head = _first_hit(lines, line_cap, _HEAD_REF)
    if trigger is None or step is None or head is None:
        return None
    number, line = head
    return finding_for(
        rule,
        entry,
        number,
        evidence=line,
        message=(
            f"{rule.title}: the trigger on line {trigger[0]} runs in the base context, and the "
            f"checkout on line {step[0]} is told to use the head ref on line {number}"
        ),
    )


def _lifecycle_execs(
    rule: Rule,
    entry: FileEntry,
    lines: dict[int, str],
    fetch_rule: Rule,
    line_cap: int,
) -> list[PendingFinding]:
    """Lines where the fetch and the handover are both present.

    The fetch half is read from `pat-lifecycle-fetch`'s pattern rather than restated, so the WARN
    and the HIGH cannot drift apart on what counts as a client verb.
    """
    findings: list[PendingFinding] = []
    for number, line in _searchable(lines, line_cap):
        if not line_matches(fetch_rule, line):
            continue
        if not _EXEC_TARGET.search(line):
            continue
        findings.append(
            finding_for(
                rule,
                entry,
                number,
                evidence=line,
                message=f"{rule.title}: the fetched result reaches a shell on line {number}",
            )
        )
    return findings


def run(ctx: ScanContext) -> Iterable[PendingFinding]:
    """Emit the CI-surface findings a single line pattern cannot decide."""
    rules = _by_id(ctx)
    line_cap = ctx.policy.line_cap
    dump_rule = rules.get(SECRET_DUMP_RULE_ID)
    head_rule = rules.get(HEAD_CHECKOUT_RULE_ID)
    exec_rule = rules.get(EXEC_RULE_ID)
    fetch_rule = rules.get(FETCH_RULE_ID)
    trigger_rule = rules.get(PRIVILEGED_RULE_ID)

    for entry in ctx.entries:
        if entry.text is None or line_cap <= 0:
            continue
        lines = _text_lines(entry.text)
        if dump_rule is not None and _shares_a_role(dump_rule, entry):
            yield from _secret_dumps(dump_rule, entry, lines, line_cap)
        if head_rule is not None and _shares_a_role(head_rule, entry):
            combination = _head_checkout(head_rule, entry, lines, trigger_rule, line_cap)
            if combination is not None:
                yield combination
        if exec_rule is not None and fetch_rule is not None and _shares_a_role(exec_rule, entry):
            yield from _lifecycle_execs(exec_rule, entry, lines, fetch_rule, line_cap)
