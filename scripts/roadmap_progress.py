#!/usr/bin/env python3
"""Recompute the `ROADMAP.md` progress table from the task lines (task 1.9).

The table is derived data, and this repository has already been wrong about it twice: six rows
were ticked on branches that had not reached the default branch, and three bootstrap rows stayed
unticked after the files they describe merged. A table written by hand drifts from the checklist
it summarizes, so the checklist is the source and this script renders the table.

Usage:
    scripts/roadmap_progress.py [--check] [path-to-ROADMAP.md]

With `--check` nothing is written: the script exits 1 when the committed table disagrees with the
tasks, and prints the table that would be right. Without it the block between the PROGRESS
markers is replaced.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

START = "<!-- PROGRESS:START -->"
END = "<!-- PROGRESS:END -->"
HEADER = ["| Phase | Name | Done | Total | Progress |", "|---|---|---|---|---|"]

# `[~]` counts as unfinished: a half-landed task is not a done task.
TASK_RE = re.compile(r"^- \[([ x~])\] \*\*(\d+\.\d+)\*\*")
GATE_RE = re.compile(r"^- \[([ x~])\] \*\*(G\d+)\*\*")
PHASE_RE = re.compile(r"^### Phase (\d+): (.+)$")

#: Phase 9 is the backlog and sits outside the readiness sum; `v0.1.0` is phases 0 to 5.
BACKLOG_PHASE = 9
READINESS_MAX = 8
SUM_ROW = "| **Phases 0 to 8** | **Readiness total** | **{done}** | **{total}** | **{pct}** |"


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
    return f"{round(done / total * 100)}%"


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
        raise SystemExit("roadmap_progress: no `### Phase N:` heading to count tasks under")
    for key in sorted(tally):
        finished, all_tasks = tally[key]
        if all_tasks == 0:
            raise SystemExit(f"roadmap_progress: Phase {key} has a heading and no task lines")
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


def replace_block(text: str, body: str) -> str:
    head, _, rest = text.partition(START)
    _, end, tail = rest.partition(END)
    return f"{head}{START}\n{body}\n{end}{tail}"


def main(argv: list[str]) -> int:
    check = "--check" in argv
    given = [arg for arg in argv if arg != "--check"]
    path = Path(given[0]) if given else Path(__file__).resolve().parents[1] / "ROADMAP.md"
    text = path.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit(f"roadmap_progress: the file has no {START} ... {END} block")
    rows, readiness = counts(text)
    body = render(rows, readiness)
    if not check:
        path.write_text(replace_block(text, body), encoding="utf-8")
        return 0
    if replace_block(text, body) == text:
        return 0
    print(body)
    print(
        f"roadmap_progress: {path} disagrees with its own task lines; "
        "run scripts/roadmap_progress.py without --check",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
