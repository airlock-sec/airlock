#!/usr/bin/env python3
"""Recompute the derived regions of `ROADMAP.md`: the progress table, the changelog and the
timestamp (tasks 1.9 and 1.15).

Both are derived data, and this repository has already been wrong about each of them. The table
was written by hand and drifted from the checklist twice: six rows were ticked on branches that
had not reached the default branch, and three bootstrap rows stayed unticked after the files they
describe merged. The changelog drifted the same way in a different axis: every change appended one
line at the same anchor, so two branches landing near each other both rewrote the head of the file,
and a row is a single line of up to six thousand characters, which is not a mergeable unit. So the
checklist is the source for the table, and `docs/changes/*.md` is the source for the changelog.

One file per change means two changes never edit the same path, and a conflict in the generated
block is resolved by taking either side and running this script again.

Usage:
    scripts/roadmap_progress.py [--check] [path-to-ROADMAP.md]

With `--check` nothing is written: the script exits 1 when a committed region disagrees with its
source and prints what would be right. Without it, the blocks between the PROGRESS and CHANGELOG
markers are replaced and the `Last updated:` line is set to the newest change entry.

Change files live in `docs/changes/` and are named `YYYY-MM-DD-HHMM-<slug>.md`, where the date and
time in the name are the ones in the file. The front matter is `date:`, `tasks:` and `summary:`;
the summary is the sentence that appears in the table and the rest of the file is the record
itself. A record is a fact about work that already happened, so a future date is refused, and a
file nested below `docs/changes/` is refused rather than silently left out of the render. A
roadmap with no CHANGELOG markers and no change files is a roadmap that has not adopted the
changelog yet, and only the table is rendered.
"""

from __future__ import annotations

import difflib
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn

START = "<!-- PROGRESS:START -->"
END = "<!-- PROGRESS:END -->"
HEADER = ["| Phase | Name | Done | Total | Progress |", "|---|---|---|---|---|"]

CHANGELOG_START = "<!-- CHANGELOG:START -->"
CHANGELOG_END = "<!-- CHANGELOG:END -->"
CHANGELOG_HEADER = ["| Date (UTC) | Change | Tasks |", "|---|---|---|"]
CHANGE_DIR = "docs/changes"
CHANGE_SUFFIX = ".md"
FRONT_KEYS = ("date", "tasks", "summary")
SUMMARY_MAX = 240

# `[~]` counts as unfinished: a half-landed task is not a done task.
TASK_RE = re.compile(r"^- \[([ x~])\] \*\*(\d+\.\d+)\*\*")
GATE_RE = re.compile(r"^- \[([ x~])\] \*\*(G\d+)\*\*")
PHASE_RE = re.compile(r"^### Phase (\d+): (.+)$")
TIMESTAMP_RE = re.compile(r"^Last updated: .*$", re.MULTILINE)
CHANGE_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(\d{4})-([a-z0-9][a-z0-9-]{1,58}[a-z0-9])\.md$")
# `key:` with nothing after it parses as an empty value, so the key-specific check says which
# field is missing rather than blaming the line's shape.
FRONT_RE = re.compile(r"^([a-z_]+):\s*(.*)$")
# A summary becomes a table cell, so the only backslash it may carry is the one that escapes a
# pipe. `[^\\|]` plus `\\\|` is the whole alphabet; `\\|` in the file is a stray backslash before
# an unescaped pipe, which would render a four-cell row, so it fails here rather than in review.
SUMMARY_CELL = re.compile(r"(?:[^\\|]|\\\|)*")

#: Phase 9 is the backlog and sits outside the readiness sum; `v0.1.0` is phases 0 to 5.
BACKLOG_PHASE = 9
READINESS_MAX = 8
SUM_ROW = "| **Phases 0 to 8** | **Readiness total** | **{done}** | **{total}** | **{pct}** |"


def fail(message: str) -> NoReturn:
    raise SystemExit(f"roadmap_progress: {message}")


def read_text(path: Path) -> str:
    """Read a source of the generated regions.

    CRLF is refused rather than silently normalised: the generator writes `\n`, so a file that
    arrives with `\r\n` would show a whole-file diff on every regeneration and the derived blocks
    would never settle.
    """
    raw = path.read_bytes()
    if b"\r" in raw:
        fail(f"{path.name} has a carriage return; these files are stored with `\\n` line endings")
    return raw.decode("utf-8")


@dataclass(frozen=True, slots=True)
class Count:
    """One row of the table."""

    key: str
    name: str
    done: int
    total: int

    def row(self) -> str:
        cells = (self.key, self.name, self.done, self.total, _percent(self.done, self.total))
        return "| " + " | ".join(str(cell) for cell in cells) + " |"


def _percent(done: int, total: int) -> str:
    """A row that has nothing counted yet reads 0% rather than raising a ZeroDivisionError."""
    return f"{round(done / total * 100)}%" if total else "0%"


def _tally(mark: str) -> int:
    return 1 if mark == "x" else 0


def _title(name: str) -> str:
    """`Decisions and validation (blocks everything)` renders as `Decisions and validation`."""
    return name.split(" (")[0].strip()


def counts(text: str) -> tuple[list[Count], Count]:
    """The phase rows, the readiness total, and the gate row from the section 3 checklist."""
    titles: dict[int, str] = {}
    tally: dict[int, list[int]] = {}
    phase_done = phase_total = 0
    gates: list[int] = []
    for line in text.splitlines():
        heading = PHASE_RE.match(line)
        if heading:
            key = int(heading.group(1))
            titles[key] = _title(heading.group(2))
            tally[key] = [0, 0]
            continue
        task = TASK_RE.match(line.strip())
        if task and tally:
            bucket = tally[max(tally)]
            bucket[1] += 1
            bucket[0] += _tally(task.group(1))
            continue
        gate = GATE_RE.match(line.strip())
        if gate:
            gates.append(_tally(gate.group(1)))

    rows: list[Count] = []
    if not tally:
        fail("no `### Phase N:` heading to count tasks under")
    for key in sorted(tally):
        finished, all_tasks = tally[key]
        if all_tasks == 0:
            fail(f"Phase {key} has a heading and no task lines")
        label = f"{key} (backlog)" if key == BACKLOG_PHASE else str(key)
        rows.append(Count(key=label, name=titles[key], done=finished, total=all_tasks))
        if key <= READINESS_MAX:
            phase_done += finished
            phase_total += all_tasks

    gate_row = Count(
        key="Gates",
        name=f"G1 to G{len(gates)}" if gates else "Gates",
        done=sum(gates),
        total=len(gates),
    )
    rows.append(gate_row)
    return rows, Count(key="sum", name="sum", done=phase_done, total=phase_total)


def render(rows: list[Count], readiness: Count) -> str:
    """Phases in order, the backlog row where the document puts it, then the sum and the gates."""
    lines = list(HEADER)
    for row in rows:
        if row.key == "Gates":
            continue
        if row.key.startswith(f"{BACKLOG_PHASE} "):
            continue
        lines.append(row.row())
    lines.extend(row.row() for row in rows if row.key.startswith(f"{BACKLOG_PHASE} "))
    lines.append(
        SUM_ROW.format(
            done=readiness.done,
            total=readiness.total,
            pct=_percent(readiness.done, readiness.total),
        )
    )
    lines.extend(row.row() for row in rows if row.key == "Gates")
    return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class Change:
    """One `docs/changes/*.md` record: the row it renders as, and the moment it happened."""

    name: str
    stamp: datetime
    date_cell: str
    tasks: str
    summary: str

    def row(self) -> str:
        link = f"[details]({CHANGE_DIR}/{self.name})"
        return f"| {self.date_cell} | {self.summary} {link} | {self.tasks} |"


def _parse_date(value: str, source: str) -> tuple[datetime, str]:
    """`2026-10-30 15:52 UTC` and `2026-10-27 UTC`. The bare date renders without a time.

    A record with no time is a record from before rows carried one; keeping it bare means the
    table cannot claim a minute nobody recorded.
    """
    text = value.removesuffix(" UTC").strip()
    for fmt, timed in (("%Y-%m-%d %H:%M", True), ("%Y-%m-%d", False)):
        try:
            moment = datetime.strptime(text, fmt)
        except ValueError:
            continue
        return moment, text if timed else moment.strftime("%Y-%m-%d")
    fail(f"{source}: date {value!r} is not `YYYY-MM-DD HH:MM UTC` or `YYYY-MM-DD UTC`")


def read_change(path: Path) -> Change:
    """Validate one change file: its name, its front matter and the two cells it renders into."""
    matched = CHANGE_NAME_RE.match(path.name)
    if matched is None:
        fail(
            f"{path.name}: change files are named `YYYY-MM-DD-HHMM-<slug>.md` with a lowercase "
            "kebab-case slug"
        )
    if not path.is_file():  # pragma: no cover - the glob only returns real files
        fail(f"{path} does not exist")
    lines = read_text(path).splitlines()
    if not lines or lines[0].strip() != "---":
        fail(f"{path.name}: the file must open with a `---` front matter block")
    try:
        end_at = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        fail(f"{path.name}: the front matter block has no closing `---`")

    fields: dict[str, str] = {}
    for line in lines[1:end_at]:
        if not line.strip():
            continue
        field = FRONT_RE.match(line.strip())
        if field is None:
            fail(f"{path.name}: front matter line {line.strip()!r} is not `key: value`")
        key, value = field.group(1), field.group(2).strip()
        if key not in FRONT_KEYS:
            fail(f"{path.name}: unknown front matter key {key!r}; use {', '.join(FRONT_KEYS)}")
        if key in fields:
            fail(f"{path.name}: front matter key {key!r} appears twice")
        fields[key] = value
    missing = [key for key in FRONT_KEYS if key not in fields]
    if missing:
        fail(f"{path.name}: front matter is missing {', '.join(missing)}")

    stamp, date_cell = _parse_date(fields["date"], path.name)
    named = matched.group(1), matched.group(2)
    if named != (stamp.strftime("%Y-%m-%d"), stamp.strftime("%H%M")):
        fail(
            f"{path.name}: the name says {named[0]} {named[1][:2]}:{named[1][2:]} but the front "
            f"matter says {stamp.strftime('%Y-%m-%d')} {stamp.strftime('%H:%M')}"
        )
    now = datetime.now(UTC).replace(tzinfo=None, second=0, microsecond=0)
    if stamp > now:
        fail(
            f"{path.name}: date {fields['date']!r} is in the future; a record is written when the "
            "work lands"
        )
    summary = fields["summary"]
    if not summary:
        fail(f"{path.name}: summary is empty")
    if SUMMARY_CELL.fullmatch(summary) is None:
        fail(
            f"{path.name}: summary has a bare `|` or a stray `\\`; a pipe in the cell must be "
            "written `\\|`"
        )
    if len(summary) > SUMMARY_MAX:
        fail(f"{path.name}: summary is {len(summary)} characters, over the {SUMMARY_MAX} limit")
    tasks = fields["tasks"]
    if not tasks or "|" in tasks:
        fail(f"{path.name}: tasks must be a non-empty list without `|`")
    return Change(name=path.name, stamp=stamp, date_cell=date_cell, tasks=tasks, summary=summary)


def load_changes(root: Path) -> list[Change]:
    """Every change file under `docs/changes/`, newest first, ordered by name within a minute."""
    directory = root / CHANGE_DIR
    if not directory.is_dir():
        return []
    paths = sorted(p for p in directory.glob(f"*{CHANGE_SUFFIX}") if p.is_file())
    # The glob above is deliberately not recursive, so a nested file would satisfy the gate and
    # then be quietly left out of the changelog. Refuse it where it is visible.
    nested = sorted(
        p.relative_to(directory).as_posix()
        for p in directory.rglob(f"*{CHANGE_SUFFIX}")
        if p.is_file() and p.parent != directory
    )
    if nested:
        fail(
            f"change files sit directly in {CHANGE_DIR}/, not in a subdirectory: "
            + ", ".join(nested[:5])
        )
    for path in paths:
        if CHANGE_NAME_RE.match(path.name) is None:
            fail(
                f"{path.name}: change files are named `YYYY-MM-DD-HHMM-<slug>.md` with a "
                "lowercase kebab-case slug"
            )
    changes = [read_change(path) for path in paths]
    return sorted(changes, key=lambda change: (change.stamp, change.name), reverse=True)


def render_changelog(changes: list[Change]) -> str:
    return "\n".join([*CHANGELOG_HEADER, *(change.row() for change in changes)])


def replace_block(text: str, start: str, end: str, body: str) -> str:
    """Swap the region between two markers, refusing a document that does not have exactly one."""
    if text.count(start) != 1 or text.count(end) != 1:
        fail(f"expected exactly one {start} and one {end} marker")
    if text.index(start) > text.index(end):
        fail(f"{end} appears before {start}")
    head, _, rest = text.partition(start)
    _, _, tail = rest.partition(end)
    return f"{head}{start}\n{body}\n{end}{tail}"


def set_timestamp(text: str, stamp: datetime) -> str:
    """Rewrite `Last updated:` from the newest change, so the line cannot be edited by hand."""
    found = TIMESTAMP_RE.findall(text)
    if not found:
        fail("the document has no `Last updated:` line to set")
    if len(found) > 1:
        fail(f"the document has {len(found)} `Last updated:` lines; it has one, which is generated")
    moment = stamp.strftime("%Y-%m-%d %H:%M") if (stamp.hour or stamp.minute) else stamp.date()
    return TIMESTAMP_RE.sub(f"Last updated: {moment} UTC", text, count=1)


def build(text: str, root: Path) -> tuple[str, bool]:
    """The document as its sources say it should read, and whether the changelog region is live."""
    if START not in text or END not in text:
        fail(f"the file has no {START} ... {END} block")
    rows, readiness = counts(text)
    out = replace_block(text, START, END, render(rows, readiness))

    changes = load_changes(root)
    has_block = CHANGELOG_START in text or CHANGELOG_END in text
    if not changes and not has_block:
        return out, False
    if not changes:
        fail(f"the document has a CHANGELOG block but {root / CHANGE_DIR} holds no change files")
    if not has_block:
        fail(
            f"{len(changes)} change file(s) exist but the document has no "
            f"{CHANGELOG_START} ... {CHANGELOG_END} block"
        )
    out = replace_block(out, CHANGELOG_START, CHANGELOG_END, render_changelog(changes))
    return set_timestamp(out, changes[0].stamp), True


def _region(text: str, start: str, end: str) -> str:
    _, _, rest = text.partition(start)
    body, _, _ = rest.partition(end)
    return body


#: The derived blocks, in the order they appear in the document.
REGIONS = (("progress table", START, END), ("changelog", CHANGELOG_START, CHANGELOG_END))


def stale_regions(text: str, expected: str) -> list[str]:
    """Which derived regions disagree, so the failure names the region rather than the file."""
    found = [
        label
        for label, start, end in REGIONS
        if start in text
        and start in expected
        and _region(text, start, end) != _region(expected, start, end)
    ]
    stamp = TIMESTAMP_RE.search(text)
    want = TIMESTAMP_RE.search(expected)
    if stamp is not None and want is not None and stamp.group(0) != want.group(0):
        found.append("timestamp")
    return found


def _sentence_join(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def main(argv: list[str]) -> int:
    check = "--check" in argv
    given = [arg for arg in argv if arg != "--check"]
    path = Path(given[0]) if given else Path(__file__).resolve().parents[1] / "ROADMAP.md"
    text = read_text(path)
    expected, changelog = build(text, path.parent)
    if not check:
        if expected != text:
            path.write_text(expected, encoding="utf-8")
        return 0
    if expected == text:
        return 0
    labels = stale_regions(text, expected)
    if labels:
        print(f"roadmap_progress: stale {_sentence_join(labels)}")
    diff = difflib.unified_diff(
        text.splitlines(), expected.splitlines(), "committed", "derived", lineterm="", n=1
    )
    for line in list(diff)[:60]:
        print(line[:200])
    sources = "its task lines and docs/changes/" if changelog else "its task lines"
    print(
        f"roadmap_progress: {path} disagrees with {sources}; "
        "run scripts/roadmap_progress.py without --check",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
