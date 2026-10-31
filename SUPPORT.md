# Support

How to get help with Airlock, what to read before you ask, and the commands that decide whether a
pull request is reviewable.

## Where to ask

| Need | Go to |
|---|---|
| A question about using the scanner, or a false positive on a repository you scanned | [Open an issue](https://github.com/airlock-sec/airlock/issues/new/choose). The two templates ask for the mode, the commit and the rule id. |
| A way to make the scanner report clean when it should not | **Do not open an issue.** Follow [`SECURITY.md`](SECURITY.md) and file a private advisory. |
| A stalled or rejected application to work on an issue | Comment on the issue. The maintainer answers there. |
| Anything about the Drips Wave process itself | The Drips docs for [participating in a Wave](https://docs.drips.network/wave/maintainers/participating-in-a-wave/), then the Drips Discord. |

A chat channel is not set up yet, so the issue tracker is the only supported channel. This file is
the place that changes first if that ever does.

## Read before you open a pull request

1. [`AGENTS.md`](AGENTS.md) section 4: the hard rules. Several of them look like style and are
   security properties.
2. [`ARCHITECTURE_ESSENTIALS.md`](ARCHITECTURE_ESSENTIALS.md): the same rules in one screen, with
   the reason for each.
3. [`ROADMAP.md`](ROADMAP.md) section 4 and the task you picked up. If your task lists a dependency
   that is not done, say so in the issue rather than building around it.

The three rules that most often get a pull request closed here:

- **No new runtime dependencies.** Standard library only, with no exception. A proposed fix that
  adds a package is a conversation to have in the issue first, not something to land in a PR.
- **Nothing may be skipped silently.** Every file the scanner does not read produces a finding, and
  scanner-state findings cannot be suppressed. A change that makes a skip quieter is a regression
  even when the tests pass.
- **The change is recorded in the same pull request**, as one file under `docs/changes/` with a UTC
  date, and the `ROADMAP.md` that `scripts/roadmap_progress.py` regenerates from it. The `roadmap`
  check fails otherwise, and there are no exemptions, including for dependency bumps.

## Commands CI runs

Install the dev tools, then run all five. Python 3.11 is what CI uses. Locally, a direct
`pip install` into the system interpreter is refused with "externally-managed-environment" on a
current Debian or Ubuntu Python (PEP 668), so install through `uv` instead, which provisions its
own virtual environment and interpreter and never touches the system install:

```bash
uv run --group dev -- python3 -m pytest
uv run --group dev -- ruff check .
uv run --group dev -- ruff format --check .
uv run --group dev -- mypy src
uv run --group dev -- airlock scan --mode full .
```

`uv run --group dev` installs the package and the versions pinned in `pyproject.toml`'s `dev`
dependency group on first use. Without `uv`: `pipx install "ruff>=0.17.3"` and
`pipx install "mypy>=2.4.0"` for the standalone tools (`pipx ensurepath` once, so `~/.local/bin`
is on `PATH`), then a venv for the package and `pytest`, since `pytest` needs `airlock`
importable alongside it: `python3 -m venv .venv && .venv/bin/python3 -m pip install -e .
"pytest>=9.2.0"` (Debian and Ubuntu need the `python3-venv` apt package first), then
`source .venv/bin/activate` so `python3` and `airlock` come from that venv, and run the five
commands above without the `uv run --group dev --` prefix.

The self-scan must report no HIGH findings, and it is the installed console script rather than the
module path so that a wheel missing its rule data fails the build. The two roadmap gates run as a
separate job:

```bash
scripts/check_roadmap_touched.sh origin/main
python3 scripts/roadmap_progress.py --check
```

If a command does not exist on your branch, say so in the pull request instead of skipping it.

## Working on an issue from a Wave

- Ask to be assigned before starting, and wait for the assignment.
- One issue is one pull request. `Closes #<number>` goes in the pull request description, along
  with the task ids from `ROADMAP.md`.
- The acceptance criteria in the issue are the review checklist. If one of them is wrong, say so in
  the pull request rather than quietly dropping it.
- Resolve the work before the Wave ends. If a merge is blocked for a reason outside your control,
  say so on the issue so the maintainer can mark it resolved rather than cost you the points.

## Response times

Issues and pull requests are handled by one maintainer. Expect a first reply within a few days;
private security advisories state five business days in [`SECURITY.md`](SECURITY.md). Nothing here
is a support contract, and no version is released yet.
