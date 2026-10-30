#!/bin/sh
# Roadmap gate (tasks 1.9 and 1.15): a pull request that changes files must record the change.
#
# Three checks:
#   1. the diff must ADD a record directly under `docs/changes/`, and must carry the regenerated
#      `ROADMAP.md` that record produces. `roadmap_progress.py --check` runs in the same job and
#      proves the regenerated file really is what the records say, so neither half can be faked;
#   2. no record that exists on the base may disappear. History is append-only, because a record
#      is the source of the changelog and deleting one rewrites what the project says happened.
#      It is also the only guard against a pull request that deletes `docs/changes/` together with
#      the CHANGELOG block, which is the one state the generator's table-only fallback accepts;
#   3. a pull request whose only file is `ROADMAP.md` is a planning edit and is always allowed,
#      which is the exception AGENTS.md section 1 states.
#
# `Last updated` is not compared here. It is generated from the newest record, so
# `roadmap_progress.py --check` is what proves that line, and a shell string comparison would
# instead reject a backfill record for work that landed before the newest one.
#
# Usage: scripts/check_roadmap_touched.sh <base-ref>
# In a workflow the base ref is origin/$GITHUB_BASE_REF. A branch with no commits ahead of its
# base passes: there is no change to describe.

set -eu

base="${1:-}"
if [ -z "$base" ] && [ -n "${GITHUB_BASE_REF:-}" ]; then
    base="origin/${GITHUB_BASE_REF}"
fi
if [ -z "$base" ]; then
    echo "check_roadmap_touched: no base ref; pass one or set GITHUB_BASE_REF" >&2
    exit 1
fi

if ! git rev-parse --verify --quiet "${base}^{commit}" >/dev/null; then
    echo "check_roadmap_touched: ${base} is not a commit here; fetch the base branch" >&2
    exit 1
fi

merge_base=$(git merge-base "${base}" HEAD) || {
    echo "check_roadmap_touched: cannot find a merge base with ${base}" >&2
    exit 1
}

changed=$(git diff --name-only "${merge_base}" HEAD)
if [ -z "$changed" ]; then
    echo "check_roadmap_touched: nothing changed, so there is nothing to record"
    exit 0
fi

# The planning-edit exception: this file alone, nothing else.
if [ "$(printf '%s\n' "$changed" | grep -cv '^ROADMAP\.md$')" -eq 0 ]; then
    echo "check_roadmap_touched: ROADMAP.md only, so this is a planning edit and is allowed"
    exit 0
fi

# --no-renames so a rename reports as a removal here; a record path is a changelog link.
removed=$(git diff --no-renames --name-only --diff-filter=D "${merge_base}" HEAD -- docs/changes)
if [ -n "$removed" ]; then
    echo "check_roadmap_touched: these records are on the base and are gone here:"
    printf '%s\n' "$removed" | sed 's/^/    /'
    echo "docs/changes/ is append-only: a record is the source of the changelog, and work that"
    echo "has landed stays described. If a record is wrong, add one that corrects it."
    exit 1
fi

added=$(git diff --no-renames --name-only --diff-filter=A "${merge_base}" HEAD -- docs/changes)
# The generator globs docs/changes/*.md without recursing, so a nested file would pass this gate
# and then be left out of the changelog; the flat name shape is checked here as well as there.
if ! printf '%s\n' "$added" | grep -Eq '^docs/changes/[^/]*\.md$'; then
    echo "check_roadmap_touched: this change adds no record directly under docs/changes/."
    echo "AGENTS.md section 1: a task is not finished until ROADMAP.md is current, and the"
    echo "changelog there is generated from one flat file per change under docs/changes/,"
    echo "named YYYY-MM-DD-HHMM-<slug>.md."
    exit 1
fi

if ! printf '%s\n' "$changed" | grep -qx 'ROADMAP.md'; then
    echo "check_roadmap_touched: a change record was added but ROADMAP.md was not regenerated."
    echo "Run: python scripts/roadmap_progress.py"
    exit 1
fi

count=$(printf '%s\n' "$added" | grep -Ecx '^docs/changes/[^/]*\.md$')
echo "check_roadmap_touched: ${count} record(s) added under docs/changes/, ROADMAP.md regenerated"
exit 0
