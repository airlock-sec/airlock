---
date: 2026-10-28 12:19 UTC
tasks: 1.5, 1.9, G2, G10
summary: The first pull-request run on GitHub found a real defect in the CI skeleton.
---

The first pull-request run on GitHub found a real defect in the CI skeleton. Actions is
now enabled and has run: the merge of #15 put `ci.yml` on `main`, the push triggered it,
and every step passed there (`475 passed`, ruff clean, format clean on 45 files, mypy
clean on 24 files, self-scan 0 HIGH over 77 files, 19 seconds). The first `pull_request`
run then failed the suite with `check_roadmap_touched: origin/main is not a commit
here`, which is not a code problem but a checkout problem: an `actions/checkout` default
on a pull request is a detached merge ref with no base branch, and
`test_this_branch_passes_the_gate_it_is_adding` runs the gate against that base. So
`ci.yml` now asks for `fetch-depth: 0`, with the reason in the comment above it, and the
test resolves `origin/main` then `main` and reports which assumption about the checkout
went unmet instead of failing with git's own message about a ref it was never going to
have. `roadmap-check.yml` needed no change: it already fetched the history, and on probe
PR #17 it failed for exactly the right reason (`this change touches files but not
ROADMAP.md`), which is the failing half of 1.9's Done when. Verified locally before
pushing: the 10 gate tests, `ruff check`, `ruff format --check`, both workflow files
parse as YAML, and the resolver exercised in a throwaway clone with no remote. Verified
on GitHub: this PR's own run, which is the passing half of 1.9 and the reason 1.5 and
1.9 move off `[~]` in the commit after this row
