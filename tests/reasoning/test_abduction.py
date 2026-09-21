"""Tests for deterministic Abductive Reasoning strategy."""

import pytest

from cognitia.abi.types import Observation
from cognitia.epistemic.types import EpistemicStatus, Hypothesis
from cognitia.reasoning import (
    AbductiveHypotheses,
    AbductiveReasoner,
    ReasoningInput,
    ReasoningMode,
)
from cognitia.rules.types import CognitiveRule


def test_abductive_candidate_generation():
    """Verify generation of competing candidate hypotheses for observed symptoms."""
    # Rules representing candidate diagnostic explanations
    rule1 = CognitiveRule(
        rule_id="diag_high_load",
        name="High Thermal Load",
        scope="diagnostic",
        predicate={"coolant_temp": 115.0, "rpm": 4500},
        recommendation={"hypothesis": "High Thermal Engine Load", "test_criteria": "Verify torque output"},
    )
    rule2 = CognitiveRule(
        rule_id="diag_coolant_leak",
        name="Coolant Leak",
        scope="diagnostic",
        predicate={"coolant_temp": 115.0, "coolant_level": "LOW"},
        recommendation={"hypothesis": "Coolant System Leakage", "test_criteria": "Inspect pressure reservoir"},
    )
    rule3 = CognitiveRule(
        rule_id="diag_sensor_fault",
        name="Sensor Anomaly",
        scope="diagnostic",
        predicate={"coolant_temp": 115.0},
        recommendation={"hypothesis": "Thermal Sensor Measurement Glitch", "test_criteria": "Compare redundant sensor"},
    )

    # Observed facts: coolant_temp = 115.0, rpm = 4500
    obs = Observation(id="obs_engine", payload={"coolant_temp": 115.0, "rpm": 4500})

    reasoner = AbductiveReasoner()
    inp = ReasoningInput(
        context_id="ctx_diag",
        reasoning_mode=ReasoningMode.ABDUCTION,
        premises=[obs],
        rules=[rule1, rule2, rule3],
    )

    trace, result = reasoner.reason(inp)

    assert trace.mode == ReasoningMode.ABDUCTION
    assert isinstance(trace.conclusion, AbductiveHypotheses)
    assert len(trace.conclusion.candidate_hypotheses) == 3

    # First ranked should be High Thermal Engine Load (2 symptoms matched: coolant_temp + rpm)
    top_hyp = trace.conclusion.candidate_hypotheses[0]
    assert "High Thermal Engine Load" in top_hyp.statement
    assert top_hyp.initial_status == EpistemicStatus.HYPOTHESIS

    # Check competing hypotheses linkage
    assert len(top_hyp.competing_hypothesis_ids) == 2
    for other_hyp in trace.conclusion.candidate_hypotheses[1:]:
        assert other_hyp.id in top_hyp.competing_hypothesis_ids


def test_abductive_unexplained_symptom_residual():
    """Verify that an observation with no matching explanatory rule produces a residual."""
    obs = Observation(id="obs_unseen", payload={"strange_vibration_hz": 999.0})
    reasoner = AbductiveReasoner()
    inp = ReasoningInput(
        context_id="ctx_mystery",
        reasoning_mode=ReasoningMode.ABDUCTION,
        premises=[obs],
        rules=[],
    )

    trace, result = reasoner.reason(inp)
    assert isinstance(trace.conclusion, AbductiveHypotheses)
    assert len(trace.conclusion.candidate_hypotheses) == 0
    assert len(trace.conclusion.residuals) == 1
    assert trace.conclusion.residuals[0].residual_type == "unmodeled_dynamic"
