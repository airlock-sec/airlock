"""Step-summary reporter: Markdown to `$GITHUB_STEP_SUMMARY`. Task 2.9.

Counts, skipped-file counts and every HIGH finding. Evidence is rendered only inside fenced
code blocks, with the fence made longer than any backtick run in the evidence and the block
truncated to a fixed length, so a payload cannot break out of the fence or flood the
summary (ARCHITECTURE.md 6.6).
"""
