"""The fixture coverage gate (task 2.12, `PRD.md` FR-13, `ARCHITECTURE.md` 12).

Every shipped rule must name a builder, that builder must carry a positive and a negative case,
the positive must fire the rule and the negative must not. The gate runs the shipped rule data
through the engine pass and the whole detector registry, so a rule wired to nothing, a pattern that
stopped matching and a positive case that quietly became a copy of its negative all fail here.

A fixture that crashed a detector would otherwise pass by accident, so every run also asserts that
no `detector-error` came back.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from tests.fixtures import (
    Case,
    Fixture,
    builders,
    fired,
    fixture_gap,
    orphaned_builders,
    shipped_rules,
)

from airlock.model import Rule, RuleTests

RUNNER_ERROR = "detector-error"

RULES: tuple[Rule, ...] = shipped_rules()
RULE_IDS = [rule.id for rule in RULES]


def rule_for(rule_id: str) -> Rule:
    return next(rule for rule in RULES if rule.id == rule_id)


def case_for(rule: Rule, kind: str) -> Case:
    builder = builders()[getattr(rule.tests, kind)]
    case = getattr(builder(), kind)
    assert case is not None, f"{rule.id} has no {kind} case"
    return case


def hits_for(rule_id: str, kind: str) -> set[str]:
    rule = rule_for(rule_id)
    hits = fired(case_for(rule, kind))
    assert RUNNER_ERROR not in hits, f"{rule.id}'s {kind} fixture crashed a detector"
    return hits


class TestTheGate:
    def test_every_shipped_rule_has_both_fixture_halves(self) -> None:
        assert fixture_gap(RULES, builders()) == []

    def test_no_builder_is_orphaned(self) -> None:
        # A builder nobody names is a rule that was renamed or dropped without the fixture moving.
        assert orphaned_builders(RULES, builders()) == []

    def test_the_gate_bites_on_a_rule_with_no_builder(self) -> None:
        rule = replace(rule_for("cfg-dynamic-code"), tests=RuleTests("cfg_gone", "cfg_gone"))
        assert fixture_gap([rule], builders()) == [
            "cfg-dynamic-code: no positive fixture builder named cfg_gone",
            "cfg-dynamic-code: no negative fixture builder named cfg_gone",
        ]

    def test_the_gate_bites_on_a_builder_that_lost_one_half(self) -> None:
        rule = rule_for("cfg-dynamic-code")
        half = Fixture(positive=case_for(rule, "positive"), negative=None)
        known = {**builders(), rule.tests.positive: lambda: half}
        assert fixture_gap([rule], known) == [
            "cfg-dynamic-code: builder cfg_dynamic_code declares no negative case"
        ]


class TestFixturesFire:
    @pytest.mark.parametrize("rule_id", RULE_IDS)
    def test_the_positive_fixture_fires_its_rule(self, rule_id: str) -> None:
        assert rule_id in hits_for(rule_id, "positive")

    @pytest.mark.parametrize("rule_id", RULE_IDS)
    def test_the_negative_fixture_does_not(self, rule_id: str) -> None:
        assert rule_id not in hits_for(rule_id, "negative")
