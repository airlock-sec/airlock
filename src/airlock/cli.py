"""Argument parsing, command dispatch and exit codes. Task 2.10 (`ARCHITECTURE.md` 8).

`scan` is the whole pipeline in one place, in the order the design fixes: startup checks, trusted
base, rule data, collection, engine pass and detectors, numbering, suppression, reporters. The
CLI is the only module that knows that sequence, which is why it lives here rather than in a
`pipeline.py` the layout does not list (project_structure.md 3).

Exit codes: 0 nothing at or above `fail_on`; 1 something is; 2 configuration or usage error;
3 internal error. Anything nonzero fails the job, and nothing here returns 0 on a path where the
scan did not complete, so a green run always means a scan actually ran.

Two rules the rest of the design depends on:

- The tool never fetches and never reads policy from the tree under review except in `full` mode.
  `--mode` and `--event` decide which of the three trust models apply, and an event name that is
  not one of the four mapped ones is a usage error rather than a guess.
- Rule data ships with the tool, not with the repository being scanned (B1). `--rules-dir` and
  `--roles` point at the copy that came from the pinned Action, and a scanned repository cannot
  add, edit or delete a rule by doing anything to its own files.

`manifest add` and `manifest check` are parsed and refused with exit 2 until task 3.5 writes
them: a command that accepts arguments and then does nothing would let a documented two-step Wasm
flow look like it worked.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Callable, Mapping
from pathlib import Path

from . import __version__
from . import runner as runner_module
from .collector import check_runtime, collect
from .detectors import DETECTOR_NAMES
from .fingerprint import number_occurrences
from .model import (
    EXIT_CONFIG,
    EXIT_FINDINGS,
    EXIT_INTERNAL,
    EXIT_PASS,
    Mode,
    ScanContext,
    ScanReport,
    Severity,
    severity_from_name,
)
from .policy import MANIFEST_FILENAME, POLICY_FILENAME, resolve_policy, suppress
from .report import console, github, jsonout, summary
from .roles import known_roles
from .rules import load_role_globs, load_rules

#: The rule data that came with this copy of the tool. `parents[2]` is the repository root in a
#: source checkout, which is also what `$GITHUB_ACTION_PATH` holds when the Action runs
#: (`ARCHITECTURE.md` 10), so the default needs no flag in either case.
PACKAGE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES_DIR = PACKAGE_ROOT / "rules" / "builtin"
DEFAULT_ROLES_FILE = PACKAGE_ROOT / "rules" / "roles.toml"

#: Every event this build knows how to judge. An unmapped event is a usage error, because
#: defaulting it would pick a trust model the caller never asked for.
EVENT_MODES: Mapping[str, Mode] = {
    "pull_request": Mode.PR,
    "push": Mode.PUSH,
    "workflow_dispatch": Mode.FULL,
    "schedule": Mode.FULL,
}

RENDERERS: Mapping[str, Callable[[ScanReport], str]] = {
    "console": console.render,
    "github": github.render,
    "json": jsonout.render,
}

STEP_SUMMARY_ENV = "GITHUB_STEP_SUMMARY"


class UsageError(ValueError):
    """A configuration or usage problem: exit 2 with a plain message, never a traceback."""


def _add_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", nargs="?", default=".", help="repository to scan (default: cwd)")
    parser.add_argument("--mode", choices=[member.value for member in Mode], help="trust model")
    parser.add_argument(
        "--event",
        help=f"github event name; implies a mode from {', '.join(sorted(EVENT_MODES))}",
    )
    parser.add_argument("--base", help="pull request base SHA (pr mode)")
    parser.add_argument("--before", help="github.event.before (push mode)")
    parser.add_argument(
        "--fail-on", choices=[severity.name.lower() for severity in Severity], dest="fail_on"
    )
    parser.add_argument("--config", default=POLICY_FILENAME, help="policy file, repo-relative")
    parser.add_argument(
        "--wasm-manifest", default=MANIFEST_FILENAME, dest="manifest", help="manifest file"
    )
    parser.add_argument("--rules-dir", type=Path, default=DEFAULT_RULES_DIR, dest="rules_dir")
    parser.add_argument("--roles", type=Path, default=DEFAULT_ROLES_FILE)
    parser.add_argument("--format", choices=sorted(RENDERERS), default="console", dest="format")
    parser.add_argument("--output", help="write the report here instead of stdout")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="airlock",
        description="Scan a repository for supply-chain compromise and release-integrity gaps.",
    )
    parser.add_argument("--version", action="version", version=f"airlock {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    _add_flags(commands.add_parser("scan", help="collect, detect, suppress and report"))

    manifest = commands.add_parser(
        "manifest", help="Wasm manifest maintenance (refused until task 3.5)"
    )
    verbs = manifest.add_subparsers(dest="verb", required=True)
    add = verbs.add_parser("add", help="record one Wasm artifact")
    add.add_argument("target")
    add.add_argument("--origin", choices=["built", "vendored", "generated"], required=True)
    add.add_argument("--source")
    verbs.add_parser("check", help="verify the manifest against the tree")
    return parser


def _mode_for(args: argparse.Namespace) -> Mode:
    """Resolve `--mode` and `--event` into the one trust model that governs the scan."""
    if args.event is not None:
        implied = EVENT_MODES.get(args.event)
        if implied is None:
            raise UsageError(
                f"airlock has no trust model for event {args.event!r}; "
                f"known events are {', '.join(sorted(EVENT_MODES))}"
            )
        if args.mode is not None and args.mode != implied.value:
            raise UsageError(
                f"--event {args.event} implies mode {implied.value}, not --mode {args.mode}"
            )
        return implied
    if args.mode is not None:
        return Mode(args.mode)
    return Mode.FULL


def run_scan(
    repo: Path,
    mode: Mode,
    *,
    base: str | None = None,
    before: str | None = None,
    config: str = POLICY_FILENAME,
    manifest: str = MANIFEST_FILENAME,
    fail_on: Severity | None = None,
    rules_dir: Path = DEFAULT_RULES_DIR,
    roles_file: Path = DEFAULT_ROLES_FILE,
) -> ScanReport:
    """Run one scan end to end and return the report, with its exit code already decided.

    Raises `ValueError` for anything the operator must fix: a repository git will not open, an
    unresolvable base, unreadable rule data, a policy that does not parse.
    """
    head = check_runtime(repo)
    trusted = resolve_policy(
        repo, mode, head, base=base, before=before, policy_path=config, manifest_path=manifest
    )
    role_globs = load_role_globs(roles_file)
    rules = load_rules(
        rules_dir, known_detectors=DETECTOR_NAMES, known_roles=known_roles(role_globs)
    )
    collection = collect(repo, trusted.policy, role_globs)
    context = ScanContext(
        mode=mode,
        tool_version=__version__,
        repo_head=head,
        base=trusted.base,
        entries=collection.entries,
        policy=trusted.policy,
        manifest=trusted.manifest,
        rules=rules,
    )

    # One numbering pass over every source, so occurrence indices cannot depend on which
    # detector finished first: the collector's skips, the policy's state findings and the
    # findings the engine and detectors produced.
    pending = [
        *collection.pending,
        *trusted.pending,
        *runner_module.collect(context),
    ]
    threshold = fail_on if fail_on is not None else trusted.policy.fail_on
    outcome = suppress(number_occurrences(pending), trusted.policy, rules, policy_path=config)
    return ScanReport(
        tool_version=__version__,
        mode=mode,
        repo_head=head,
        base=trusted.base,
        files_scanned=len(collection.entries),
        files_skipped=collection.files_skipped,
        findings=outcome.findings,
        suppressed=outcome.suppressed,
        exit_code=(
            EXIT_FINDINGS
            if any(item.severity >= threshold for item in outcome.findings)
            else EXIT_PASS
        ),
    )


def _scan_command(args: argparse.Namespace) -> int:
    repo = Path(args.path)
    report = run_scan(
        repo,
        _mode_for(args),
        base=args.base,
        before=args.before,
        config=args.config,
        manifest=args.manifest,
        fail_on=severity_from_name(args.fail_on) if args.fail_on else None,
        rules_dir=args.rules_dir,
        roles_file=args.roles,
    )
    text = RENDERERS[args.format](report)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    _write_step_summary(report)
    return report.exit_code


def _write_step_summary(report: ScanReport) -> None:
    """Append the Markdown summary when running as a GitHub step.

    Written separately from `--format` because the annotation stream and the summary are read by
    different people: the check line is for the author, the summary is for the reviewer who has
    to see every HIGH without opening a log.
    """
    target = os.environ.get(STEP_SUMMARY_ENV)
    if not target:
        return
    try:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(summary.render(report))
    except OSError as exc:
        raise UsageError(f"cannot write the step summary to {target}: {exc}") from exc


def _refused(command: str) -> int:
    raise UsageError(
        f"airlock {command} is not implemented yet (ROADMAP.md task 3.5); "
        "edit wasm-manifest.toml by hand or wait for that release"
    )


def main(argv: list[str] | None = None) -> int:
    """Dispatch one command and map every failure onto the documented exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "scan":
            return _scan_command(args)
        if args.command == "manifest":
            return _refused(f"manifest {args.verb}")
        raise UsageError(f"no such command: {args.command!r}")
    except ValueError as error:
        print(f"airlock: {error}", file=sys.stderr)
        return EXIT_CONFIG
    except Exception as error:  # an unexpected failure is exit 3, never a traceback
        print(
            f"airlock: internal error: {type(error).__name__}: {error}",
            file=sys.stderr,
        )
        return EXIT_INTERNAL
