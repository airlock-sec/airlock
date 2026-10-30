#!/bin/sh
# Roadmap gate (tasks 1.9 and 1.15): a pull request that changes files must record the change.
#
# Three checks:
#   1. the diff must add or edit a record under `docs/changes/`, and must carry the regenerated
#      `ROADMAP.md` that record produces. `roadmap_progress.py --check` runs in the same job and
#      proves the regenerated file really is what the records say, so neither half can be faked;
#   2. the `Last updated` line must actually have moved, because it is now generated from the
#      newest record and a record dated in the past means nobody recorded this change when it
#      landed;
#   3. a pull request whose only file is `ROADMAP.md` is a planning edit and is always allowed,
#      which is the exception AGENTS.md section 1 states. Its timestamp is whatever the newest
#      record says, and check 1 of `roadmap_progress.py --check` is what keeps it honest.
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

if ! printf '%s\n' "$changed" | grep -q '^docs/changes/.*\.md$'; then
    echo "check_roadmap_touched: this change records nothing under docs/changes/."
    echo "AGENTS.md section 1: a task is not finished until ROADMAP.md is current, and the"
    echo "changelog there is generated from one file per change under docs/changes/."
    exit 1
fi

if ! printf '%s\n' "$changed" | grep -qx 'ROADMAP.md'; then
    echo "check_roadmap_touched: a change record was added but ROADMAP.md was not regenerated."
    echo "Run: python scripts/roadmap_progress.py"
    exit 1
fi

before=$(git show "${merge_base}:ROADMAP.md" | sed -n 's/^Last updated: //p' | head -n 1)
after=$(sed -n 's/^Last updated: //p' ROADMAP.md | head -n 1)
if [ -z "$after" ]; then
    echo "check_roadmap_touched: ROADMAP.md has no 'Last updated:' line to check" >&2
    exit 1
fi
if [ "$before" = "$after" ]; then
    echo "check_roadmap_touched: ROADMAP.md changed but its 'Last updated' line did not."
    echo "It still reads: Last updated: ${after}"
    echo "That line is generated from the newest docs/changes/ record, so date your record"
    echo "with the current UTC minute and regenerate the file."
    exit 1
fi

echo "check_roadmap_touched: ROADMAP.md updated, ${before} -> ${after}"
exit 0
