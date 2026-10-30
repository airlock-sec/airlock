"""The two roadmap gates (tasks 1.9 and 1.15).

A gate that silently passes is worse than no gate, so both scripts are run here the way a
workflow runs them: as a subprocess, with their real arguments, against a temporary file or a
temporary repository, asserting on exit codes. The first tests are the ones that matter most: they
run the generator over this repository's own `ROADMAP.md` and its own `docs/changes/` records, so
the committed changelog cannot drift from the records it is built from or lose a row.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PROGRESS = REPO_ROOT / "scripts" / "roadmap_progress.py"
TOUCHED = REPO_ROOT / "scripts" / "check_roadmap_touched.sh"

HEAD = "# ROADMAP\n\nLast updated: 2026-10-28 10:00 UTC\n"
STALE = (
    "<!-- PROGRESS:START -->\n"
    "| Phase | Name | Done | Total | Progress |\n"
    "|---|---|---|---|---|\n"
    "| OLD | STALE | 9 | 9 | 99% |\n"
    "<!-- PROGRESS:END -->\n"
)
FIXTURE = f"""{HEAD}
## 2. Progress

{STALE}
## 3. Readiness gates

- [x] **G1** One gate met.
- [ ] **G2** One gate open.

## 5. Phases and tasks

### Phase 0: Example work (blocks nothing)

- [x] **0.1** First.
- [ ] **0.2** Second.

### Phase 1: Later work

- [ ] **1.1** Only task.

### Phase 9: Backlog (not counted toward readiness)

- [ ] **9.1** Someday.
"""

#: The table this fixture's task lines render, so a changelog failure cannot hide behind a stale
#: progress table.
CURRENT = (
    "<!-- PROGRESS:START -->\n"
    "| Phase | Name | Done | Total | Progress |\n"
    "|---|---|---|---|---|\n"
    "| 0 | Example work | 1 | 2 | 50% |\n"
    "| 1 | Later work | 0 | 1 | 0% |\n"
    "| 9 (backlog) | Backlog | 0 | 1 | 0% |\n"
    "| **Phases 0 to 8** | **Readiness total** | **1** | **3** | **33%** |\n"
    "| Gates | G1 to G2 | 1 | 2 | 50% |\n"
    "<!-- PROGRESS:END -->\n"
)


def run(program: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run([program, *args], capture_output=True, text=True, check=False, cwd=cwd)


def base_ref(root: Path) -> str:
    """The first name that resolves to a commit in this checkout, or an empty string.

    The remote-tracking name is the one a workflow run has after fetching the history; the bare
    one covers a clone whose remote is not called `origin`. Returning "" instead of raising lets
    the caller state which assumption about the checkout was not met.
    """
    for ref in ("origin/main", "main"):
        if run("git", "rev-parse", "--verify", "--quiet", ref, cwd=root).returncode == 0:
            return ref
    return ""


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
            *args,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


@pytest.fixture
def branch_repo(tmp_path: Path) -> Path:
    """A repository with a `main` commit and an empty branch on top of it."""
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "--initial-branch=main")
    (root / "README.md").write_text("base\n", encoding="utf-8")
    (root / "ROADMAP.md").write_text(HEAD, encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "base")
    git(root, "checkout", "-q", "-b", "task")
    return root


#: A record's whole front matter, for the cases that need an unusual set of keys.
VALID_FRONT = "date: 2026-11-01 09:00 UTC\ntasks: 1.15\nsummary: Done."


def add_record(
    root: Path,
    name: str,
    *,
    date: str = "2026-11-01 09:00",
    tasks: str = "1.15",
    summary: str = "A change worth recording.",
    body: str = "The record says what was verified.",
    front: str | None = None,
) -> Path:
    """One `docs/changes/` record with a valid name unless the case is about the name."""
    directory = root / "docs" / "changes"
    directory.mkdir(parents=True, exist_ok=True)
    block = front if front is not None else f"date: {date} UTC\ntasks: {tasks}\nsummary: {summary}"
    path = directory / name
    path.write_text(f"---\n{block}\n---\n\n{body}\n", encoding="utf-8")
    return path


def roadmap_text(records: str = "") -> str:
    """The temporary roadmap the generator is pointed at, with both derived blocks present.

    The progress table is already the one the fixture's tasks render, so a failure here is about
    the changelog or the timestamp and the message can be asserted exactly.
    """
    return (
        f"{FIXTURE.replace(STALE, CURRENT)}\n## 9. Changelog\n\n"
        "<!-- CHANGELOG:START -->\n"
        "| Date (UTC) | Change | Tasks |\n"
        "|---|---|---|\n"
        f"{records}"
        "<!-- CHANGELOG:END -->\n"
    )


ROW_RE = re.compile(r"^\| \d{4}-\d{2}-\d{2} ")


def changelog_rows(text: str) -> list[str]:
    """The rendered changelog rows, in the order the document shows them."""
    block = text.split("<!-- CHANGELOG:START -->", 1)[1].split("<!-- CHANGELOG:END -->", 1)[0]
    return [line for line in block.splitlines() if ROW_RE.match(line)]


def _sortable(date_cell: str) -> str:
    """`2026-10-27` sorts at midnight, the way the generator reads a bare date."""
    return date_cell if len(date_cell) > 10 else f"{date_cell} 00:00"


class TestProgressTable:
    def test_the_committed_roadmap_is_current(self) -> None:
        result = run("python3", str(PROGRESS), "--check", cwd=REPO_ROOT)
        assert result.returncode == 0, result.stdout + result.stderr

    def test_render_counts_each_phase_and_sums_the_readiness_phases(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(FIXTURE, encoding="utf-8")
        result = run("python3", str(PROGRESS), str(roadmap))
        assert result.returncode == 0, result.stdout + result.stderr
        table = roadmap.read_text(encoding="utf-8")
        assert "| 0 | Example work | 1 | 2 | 50% |" in table
        assert "| 1 | Later work | 0 | 1 | 0% |" in table
        assert "| 9 (backlog) | Backlog | 0 | 1 | 0% |" in table
        assert "| **Phases 0 to 8** | **Readiness total** | **1** | **3** | **33%** |" in table
        assert "| Gates | G1 to G2 | 1 | 2 | 50% |" in table
        assert "STALE" not in table

    def test_a_stale_table_fails_the_check_and_prints_the_table_that_is_right(
        self, tmp_path: Path
    ) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        stale = FIXTURE.replace("| OLD | STALE |", "| 0 | Example work |")
        roadmap.write_text(stale, encoding="utf-8")
        result = run("python3", str(PROGRESS), "--check", str(roadmap))
        assert result.returncode == 1
        assert "| 0 | Example work | 1 | 2 | 50% |" in result.stdout

    def test_a_progress_block_with_no_markers_is_an_error(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(HEAD + "\n## 5. Phases\n\n- [ ] **0.1** Orphan.\n", encoding="utf-8")
        result = run("python3", str(PROGRESS), str(roadmap))
        assert result.returncode == 1
        assert "PROGRESS:START" in result.stderr

    def test_a_phase_with_no_tasks_is_an_error(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(FIXTURE.replace("- [ ] **1.1** Only task.\n", ""), encoding="utf-8")
        result = run("python3", str(PROGRESS), str(roadmap))
        assert result.returncode == 1
        assert "Phase 1" in result.stderr


class TestRoadmapTouched:
    def test_a_change_that_records_nothing_fails(self, branch_repo: Path) -> None:
        (branch_repo / "src.py").write_text("x = 1\n", encoding="utf-8")
        git(branch_repo, "add", "-A")
        git(branch_repo, "commit", "-q", "-m", "code only")
        result = run("sh", str(TOUCHED), "main", cwd=branch_repo)
        assert result.returncode == 1
        assert "docs/changes" in result.stdout

    def test_code_plus_a_record_and_a_regenerated_roadmap_passes(self, branch_repo: Path) -> None:
        (branch_repo / "src.py").write_text("x = 1\n", encoding="utf-8")
        add_record(branch_repo, "2026-11-01-0900-one-change.md")
        (branch_repo / "ROADMAP.md").write_text(
            HEAD.replace("10:00 UTC", "2026-11-01 09:00 UTC"), encoding="utf-8"
        )
        git(branch_repo, "add", "-A")
        git(branch_repo, "commit", "-q", "-m", "code, record and roadmap")
        assert run("sh", str(TOUCHED), "main", cwd=branch_repo).returncode == 0

    def test_a_record_without_a_regenerated_roadmap_fails(self, branch_repo: Path) -> None:
        (branch_repo / "src.py").write_text("x = 1\n", encoding="utf-8")
        add_record(branch_repo, "2026-11-01-0900-one-change.md")
        git(branch_repo, "add", "-A")
        git(branch_repo, "commit", "-q", "-m", "a record nobody regenerated the file from")
        result = run("sh", str(TOUCHED), "main", cwd=branch_repo)
        assert result.returncode == 1
        assert "regenerated" in result.stdout

    def test_code_and_a_timestamp_but_no_record_fails(self, branch_repo: Path) -> None:
        """The gate is stronger than it was: touching ROADMAP.md no longer counts as recording."""
        (branch_repo / "src.py").write_text("x = 1\n", encoding="utf-8")
        (branch_repo / "ROADMAP.md").write_text(
            HEAD.replace("10:00 UTC", "2026-11-01 09:00 UTC"), encoding="utf-8"
        )
        git(branch_repo, "add", "-A")
        git(branch_repo, "commit", "-q", "-m", "roadmap edited by hand")
        result = run("sh", str(TOUCHED), "main", cwd=branch_repo)
        assert result.returncode == 1
        assert "docs/changes" in result.stdout

    def test_a_roadmap_only_diff_is_a_planning_edit(self, branch_repo: Path) -> None:
        (branch_repo / "ROADMAP.md").write_text(HEAD + "\nA note.\n", encoding="utf-8")
        git(branch_repo, "add", "-A")
        git(branch_repo, "commit", "-q", "-m", "planning edit")
        result = run("sh", str(TOUCHED), "main", cwd=branch_repo)
        assert result.returncode == 0
        assert "planning edit" in result.stdout

    def test_a_record_that_did_not_move_the_timestamp_fails(self, branch_repo: Path) -> None:
        (branch_repo / "src.py").write_text("x = 1\n", encoding="utf-8")
        add_record(branch_repo, "2026-10-01-0900-an-old-change.md", date="2026-10-01 09:00")
        (branch_repo / "ROADMAP.md").write_text(HEAD + "\n| stale |\n", encoding="utf-8")
        git(branch_repo, "add", "-A")
        git(branch_repo, "commit", "-q", "-m", "a record dated in the past")
        result = run("sh", str(TOUCHED), "main", cwd=branch_repo)
        assert result.returncode == 1
        assert "Last updated" in result.stdout

    def test_a_branch_with_no_commits_ahead_is_not_a_failure(self, branch_repo: Path) -> None:
        assert run("sh", str(TOUCHED), "main", cwd=branch_repo).returncode == 0

    def test_this_branch_passes_the_gate_it_is_adding(self) -> None:
        """If the gate cannot be satisfied by the work that adds it, it is the wrong gate."""
        ref = base_ref(REPO_ROOT)
        assert ref, (
            "neither origin/main nor main resolves in this checkout, so the gate has no base to "
            "compare against; ci.yml asks for fetch-depth: 0 for exactly this test"
        )
        result = run("sh", str(TOUCHED), ref, cwd=REPO_ROOT)
        assert result.returncode == 0, result.stdout + result.stderr


class TestChangelogGeneration:
    """The changelog is generated from `docs/changes/`, one file per change (task 1.15)."""

    def test_a_record_renders_a_row_and_moves_the_timestamp(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(roadmap_text(), encoding="utf-8")
        add_record(
            tmp_path,
            "2026-11-01-0900-one-change.md",
            summary="One change lands.",
            tasks="1.15, FR-20",
        )
        assert run("python3", str(PROGRESS), str(roadmap)).returncode == 0
        text = roadmap.read_text(encoding="utf-8")
        link = "[details](docs/changes/2026-11-01-0900-one-change.md)"
        assert f"| 2026-11-01 09:00 | One change lands. {link} | 1.15, FR-20 |" in text
        assert "Last updated: 2026-11-01 09:00 UTC" in text
        assert run("python3", str(PROGRESS), "--check", str(roadmap)).returncode == 0

    def test_the_newest_record_is_the_first_row(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(roadmap_text(), encoding="utf-8")
        add_record(tmp_path, "2026-11-01-0900-later.md", date="2026-11-01 09:00")
        add_record(tmp_path, "2026-10-30-1552-earlier.md", date="2026-10-30 15:52")
        add_record(tmp_path, "2026-10-27-0000-oldest.md", date="2026-10-27")
        assert run("python3", str(PROGRESS), str(roadmap)).returncode == 0
        rows = changelog_rows(roadmap.read_text(encoding="utf-8"))
        assert [row.split("|")[1].strip() for row in rows] == [
            "2026-11-01 09:00",
            "2026-10-30 15:52",
            "2026-10-27",
        ]
        assert "Last updated: 2026-11-01 09:00 UTC" in roadmap.read_text(encoding="utf-8")

    def test_a_record_missing_from_the_block_fails_the_check(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        add_record(tmp_path, "2026-11-01-0900-one-change.md")
        roadmap.write_text(roadmap_text(), encoding="utf-8")
        result = run("python3", str(PROGRESS), "--check", str(roadmap))
        assert result.returncode == 1
        assert "roadmap_progress: stale changelog and timestamp" in result.stdout
        assert "progress table" not in result.stdout

    def test_a_hand_edited_row_fails_the_check(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        add_record(tmp_path, "2026-11-01-0900-one-change.md")
        roadmap.write_text(
            roadmap_text(
                "| 2026-11-01 09:00 | Something nobody wrote down. | 9.9 |\n",
            ),
            encoding="utf-8",
        )
        result = run("python3", str(PROGRESS), "--check", str(roadmap))
        assert result.returncode == 1
        assert "Something nobody wrote down" in result.stdout

    def test_a_block_with_no_records_is_an_error(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(roadmap_text(), encoding="utf-8")
        result = run("python3", str(PROGRESS), str(roadmap))
        assert result.returncode == 1
        assert "no change files" in result.stderr

    def test_records_with_no_block_are_an_error(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(FIXTURE, encoding="utf-8")
        add_record(tmp_path, "2026-11-01-0900-one-change.md")
        result = run("python3", str(PROGRESS), str(roadmap))
        assert result.returncode == 1
        assert "CHANGELOG:START" in result.stderr

    def test_a_half_marked_block_is_an_error(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(
            roadmap_text().replace("<!-- CHANGELOG:END -->", "<!-- wrong -->"), encoding="utf-8"
        )
        add_record(tmp_path, "2026-11-01-0900-one-change.md")
        result = run("python3", str(PROGRESS), str(roadmap))
        assert result.returncode == 1
        assert "exactly one" in result.stderr

    @pytest.mark.parametrize(
        "name,front,expect",
        [
            ("notes.md", VALID_FRONT, "are named"),
            ("2026-11-01-9am-one-change.md", VALID_FRONT, "are named"),
            ("2026-11-01-0900-One-Change.md", VALID_FRONT, "are named"),
            (
                "2026-11-01-0900-one-change.md",
                "date: 2026-11-01 08:00 UTC\ntasks: 1.15\nsummary: Done.",
                "the name says",
            ),
            (
                "2026-11-01-0900-one-change.md",
                "date: 2026-13-45 09:00 UTC\ntasks: 1.15\nsummary: Done.",
                "is not",
            ),
            (
                "2026-11-01-0900-one-change.md",
                "date: 2026-11-01\ntasks: 1.15\nsummary: Done.",
                "the name says",
            ),
            ("2026-11-01-0900-one-change.md", "tasks: 1.15\nsummary: Done.", "missing date"),
            ("2026-11-01-0900-one-change.md", "date: 2026-11-01\ntasks: 1.15", "missing summary"),
            (
                "2026-11-01-0900-one-change.md",
                "date: 2026-11-01 09:00 UTC\ntasks: 1.15\nsummary:",
                "summary is empty",
            ),
            (
                "2026-11-01-0900-one-change.md",
                "date: 2026-11-01 09:00 UTC\ntasks:\nsummary: Done.",
                "non-empty list",
            ),
            (
                "2026-11-01-0900-one-change.md",
                f"{VALID_FRONT}\nowner: nobody",
                "unknown front matter key",
            ),
            (
                "2026-11-01-0900-one-change.md",
                "date: 2026-11-01 09:00 UTC\ntasks: 1.15\ntasks: 1.16\nsummary: Done.",
                "appears twice",
            ),
            (
                "2026-11-01-0900-one-change.md",
                "date 2026-11-01\ntasks: 1.15\nsummary: Done.",
                "is not `key: value`",
            ),
            (
                "2026-11-01-0900-one-change.md",
                "date: 2026-11-01 09:00 UTC\ntasks: 1.15\nsummary: a row | that breaks",
                "unescaped",
            ),
            (
                "2026-11-01-0900-one-change.md",
                f"date: 2026-11-01 09:00 UTC\ntasks: 1.15\nsummary: {'long ' * 60}",
                "over the 240 limit",
            ),
        ],
    )
    def test_an_invalid_record_is_refused(
        self, tmp_path: Path, name: str, front: str, expect: str
    ) -> None:
        """A bad record fails the build rather than rendering a bad row or a wrong timestamp."""
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(roadmap_text(), encoding="utf-8")
        add_record(tmp_path, name, front=front)
        result = run("python3", str(PROGRESS), str(roadmap))
        assert result.returncode == 1
        assert expect in result.stderr

    def test_an_escaped_pipe_renders_as_the_cell_written(self, tmp_path: Path) -> None:
        roadmap = tmp_path / "ROADMAP.md"
        roadmap.write_text(roadmap_text(), encoding="utf-8")
        add_record(tmp_path, "2026-11-01-0900-one-change.md", summary="collector \\| rules")
        assert run("python3", str(PROGRESS), str(roadmap)).returncode == 0
        assert "| 2026-11-01 09:00 | collector \\| rules" in roadmap.read_text(encoding="utf-8")

    def test_every_committed_record_renders_exactly_one_row(self) -> None:
        text = (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        rows = changelog_rows(text)
        records = sorted(p.name for p in (REPO_ROOT / "docs" / "changes").glob("*.md"))
        linked = [row.rsplit("](docs/changes/", 1)[1].split(")", 1)[0] for row in rows]
        assert len(records) > 1
        assert sorted(linked) == records
        assert len(linked) == len(set(linked))

    def test_the_committed_records_are_named_and_ordered(self) -> None:
        """Records may share a minute; the name breaks the tie, so the order stays deterministic."""
        names = sorted(p.name for p in (REPO_ROOT / "docs" / "changes").glob("*.md"))
        assert len(set(names)) == len(names)
        for name in names:
            assert re.match(
                r"^\d{4}-\d{2}-\d{2}-\d{4}-[a-z0-9][a-z0-9-]{1,58}[a-z0-9]\.md$", name
            ), name
        rows = changelog_rows((REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8"))
        links = [row.rsplit("](docs/changes/", 1)[1].split(")", 1)[0] for row in rows]
        assert links == sorted(names, reverse=True)
        stamps = [row.split("|")[1].strip() for row in rows]
        assert stamps == sorted(stamps, key=_sortable, reverse=True)
