"""Tests for Causal Reasoning strategy and strict guardrail boundaries."""

import pytest

from cognitia.abi.types import Observation
from cognitia.epistemic.types import (
    EpistemicStatus,
    Evidence,
    EvidenceDirection,
)
from cognitia.reasoning import (
    CausalHypothesis,
    CausalReasoner,
    ReasoningInput,
    ReasoningMode,
)


def test_causal_case_a_temporal_order_guardrail():
    """Case A: Temporal order (A BEFORE B) alone MUST NOT produce a causal conclusion."""
    obs1 = Observation(id="obs_a", payload={"event": "valve_opened", "timestamp": 100})
    obs2 = Observation(id="obs_b", payload={"event": "pressure_dropped", "timestamp": 200})

    reasoner = CausalReasoner()
    # No explicit causal graph provided
    inp = ReasoningInput(
        context_id="ctx_temporal",
        reasoning_mode=ReasoningMode.CAUSAL,
        premises=[obs1, obs2],
        metadata={"temporal_relation": "obs_a BEFORE obs_b"},
    )

    trace, result = reasoner.reason(inp)

    # Must be rejected / guardrail triggered
    assert len(result.candidate_hypotheses) == 0
    assert len(result.residuals) == 1
    assert result.residuals[0].factor_name == "causal_graph"
    assert "CANNOT be inferred from temporal succession" in result.residuals[0].description


def test_causal_case_b_correlation_guardrail():
    """Case B: Correlation (A CORRELATES_WITH B) alone MUST NOT produce a causal conclusion."""
    obs = Observation(id="obs_corr", payload={"rpm": 3000, "exhaust_temp": 650})

    reasoner = CausalReasoner()
    inp = ReasoningInput(
        context_id="ctx_corr",
        reasoning_mode=ReasoningMode.CAUSAL,
        premises=[obs],
        metadata={"cross_source_correlation": "rpm CORRELATES_WITH exhaust_temp (r=0.92)"},
    )

    trace, result = reasoner.reason(inp)

    assert len(result.candidate_hypotheses) == 0
    assert len(result.residuals) == 1
    assert "CANNOT be inferred" in result.residuals[0].description


def test_causal_case_c_explicit_graph_with_supporting_evidence():
    """Case C: Explicit causal graph + supporting evidence produces candidate causal hypothesis."""
    obs_cause = Observation(id="obs_wastegate", payload={"wastegate_duty_cycle": 85.0})
    obs_effect = Observation(id="obs_boost", payload={"boost_pressure_bar": 2.2})
    ev = Evidence(
        id="ev_boost_support",
        target_id="wastegate_duty_cycle",
        direction=EvidenceDirection.SUPPORT,
        confidence=1.0,
    )

    causal_edges = [
        ("wastegate_duty_cycle", "boost_pressure_bar", "turbine_exhaust_bypass_restriction")
    ]

    reasoner = CausalReasoner()
    inp = ReasoningInput(
        context_id="ctx_turbo",
        reasoning_mode=ReasoningMode.CAUSAL,
        premises=[obs_cause, obs_effect, ev],
        causal_graph=causal_edges,
    )

    trace, result = reasoner.reason(inp)

    assert trace.mode == ReasoningMode.CAUSAL
    assert isinstance(trace.conclusion, CausalHypothesis)
    hyp = trace.conclusion
    assert hyp.cause == "wastegate_duty_cycle"
    assert hyp.effect == "boost_pressure_bar"
    assert hyp.mechanism == "turbine_exhaust_bypass_restriction"
    assert hyp.status == EpistemicStatus.HYPOTHESIS
    assert "ev_boost_support" in hyp.supporting_evidence_ids
    assert len(result.candidate_hypotheses) == 1


def test_causal_contradictory_evidence_preserves_unresolved_status():
    """Verify that conflicting evidence preserves UNRESOLVED status without picking a winner."""
    obs_cause = Observation(id="obs_fuel", payload={"fuel_rail_pressure": 1800.0})
    ev_support = Evidence(
        id="ev_1",
        target_id="fuel_rail_pressure",
        direction=EvidenceDirection.SUPPORT,
    )
    ev_refute = Evidence(
        id="ev_2",
        target_id="fuel_rail_pressure",
        direction=EvidenceDirection.REFUTE,
    )

    causal_edges = [
        ("fuel_rail_pressure", "combustion_efficiency", "atomization_enhancement")
    ]

    reasoner = CausalReasoner()
    inp = ReasoningInput(
        context_id="ctx_combustion",
        reasoning_mode=ReasoningMode.CAUSAL,
        premises=[obs_cause, ev_support, ev_refute],
        causal_graph=causal_edges,
    )

    trace, result = reasoner.reason(inp)

    assert isinstance(trace.conclusion, CausalHypothesis)
    assert trace.conclusion.status == EpistemicStatus.UNRESOLVED
    assert len(result.contradictions_detected) >= 1
    assert "ev_1" in trace.conclusion.supporting_evidence_ids
    assert "ev_2" in trace.conclusion.contradictory_evidence_ids
