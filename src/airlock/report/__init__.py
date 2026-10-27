"""Reporters. Each one imports only from `model` (project_structure.md 3).

Output order is severity descending, then path, line and rule id, so HIGH always leads a
runbook even when a reporter truncates. Evidence is attacker-controlled text and is never
rendered as raw markdown.
"""
