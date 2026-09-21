"""Tests for deterministic Deductive Reasoning strategy."""

import pytest

from cognitia.abi.types import Observation
from cognitia.reasoning import (
    DeductiveConclusion,
    DeductiveReasoner,
    ReasoningInput,
    ReasoningMode,
    ReasoningResidual,
)
from cognitia.rules.types import CognitiveRule, RuleStatus


def test_deduction_full_match():
    """Verify deductive derivation when all premise conditions match rule predicate."""
    rule = CognitiveRule(
        rule_id="rule_high_power",
        name="High Power Mode",
        predicate={"rpm": {">": 3000}, "boost_pressure": {"within": [1.5, 2.5]}},
        recommendation={"operating_mode": "HIGH_PERFORMANCE", "enrichment": "BOOST_ACTIVE"},
        confidence=1.0,
    )
    obs = Observation(id="obs_telemetry", payload={"rpm": 3200, "boost_pressure": 2.0})

    reasoner = DeductiveReasoner()
    inp = ReasoningInput(
        context_id="ctx_auto",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[obs],
        rules=[rule],
    )

    trace, result = reasoner.reason(inp)

    assert trace.mode == ReasoningMode.DEDUCTION
    assert isinstance(trace.conclusion, DeductiveConclusion)
    assert trace.conclusion.derived_attributes_dict["operating_mode"] == "HIGH_PERFORMANCE"
    assert "rule_high_power" in trace.conclusion.matched_rule_ids
    assert len(trace.conclusion.satisfied_conditions) == 2
    assert len(trace.conclusion.unsatisfied_conditions) == 0
    assert len(trace.conclusion.residuals) == 0
    assert len(trace.steps) == 2
    assert len(result.candidate_claims) == 1


def test_deduction_missing_premise_produces_residual():
    """Verify that a missing required premise is recorded as an explicit residual and does not match."""
    rule = CognitiveRule(
        rule_id="rule_thermal_check",
        name="Thermal Check",
        predicate={"coolant_temp": {">": 105.0}, "coolant_flow": {"<": 20.0}},
        recommendation={"cooling_state": "CRITICAL_FLOW_DEFICIT"},
    )
    # Only coolant_temp provided; coolant_flow is missing
    obs = Observation(id="obs_temp", payload={"coolant_temp": 110.0})

    reasoner = DeductiveReasoner()
    inp = ReasoningInput(
        context_id="ctx_auto",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[obs],
        rules=[rule],
    )

    trace, result = reasoner.reason(inp)

    assert isinstance(trace.conclusion, DeductiveConclusion)
    assert "rule_thermal_check" not in trace.conclusion.matched_rule_ids
    assert len(trace.conclusion.unsatisfied_conditions) == 1
    assert len(trace.conclusion.residuals) == 1
    residual = trace.conclusion.residuals[0]
    assert isinstance(residual, ReasoningResidual)
    assert residual.factor_name == "coolant_flow"
    assert residual.residual_type == "missing_observation"
    assert trace.conclusion.derived_attributes == ()
