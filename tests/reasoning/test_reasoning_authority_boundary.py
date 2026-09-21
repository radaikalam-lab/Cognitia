"""Tests for Reasoning Authority Boundary enforcement."""

import dataclasses
import pytest

from cognitia.abi.types import Action, Observation
from cognitia.persistence.store import InMemoryPersistenceStore
from cognitia.reasoning import (
    DeterministicReasoningEngine,
    ReasoningInput,
    ReasoningMode,
)
from cognitia.rules.store import InMemoryRuleStore
from cognitia.rules.types import CognitiveRule, RuleStatus


def test_reasoning_cannot_mutate_source_artifacts_or_execute_actions():
    """Verify that reasoning cannot mutate inputs, stores, or dispatch actions."""
    rule_store = InMemoryRuleStore()
    rule = CognitiveRule(
        rule_id="r_auth",
        name="Auth Test Rule",
        predicate={"temp": {">": 100}},
        recommendation={"action": "DISPATCH_COOLANT_PUMP"},
    )
    rule_store.create_rule(rule)

    obs = Observation(id="obs_auth", payload={"temp": 110})

    engine = DeterministicReasoningEngine()
    inp = ReasoningInput(
        context_id="ctx_auth",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[obs],
        rules=rule_store.list_rules(status=RuleStatus.ACTIVE),
    )

    trace, result = engine.reason(inp)

    # Invariant: Observation is frozen and unaltered
    assert obs.payload["temp"] == 110
    with pytest.raises(dataclasses.FrozenInstanceError):
        obs.payload = {"temp": 90}  # type: ignore[misc]

    # Invariant: RuleStore is unaltered
    active_rules = rule_store.list_rules(status=RuleStatus.ACTIVE)
    assert len(active_rules) == 1
    assert active_rules[0].rule_id == "r_auth"

    # Invariant: Result is an advisory candidate conclusion, NOT an executed action
    assert "DISPATCH_COOLANT_PUMP" in trace.conclusion.derived_attributes_dict.values()
    assert not isinstance(trace.conclusion, Action)
