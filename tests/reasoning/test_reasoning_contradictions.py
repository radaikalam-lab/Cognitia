"""Tests for Contradiction Preservation in reasoning."""

import pytest

from cognitia.abi.types import Observation
from cognitia.epistemic.types import EpistemicStatus, Evidence, EvidenceDirection
from cognitia.reasoning import (
    CausalHypothesis,
    DeterministicReasoningEngine,
    ReasoningInput,
    ReasoningMode,
)


def test_contradictory_evidence_preservation_no_majority_vote():
    """Verify that multiple supporting and one refuting evidence do NOT resolve by majority vote."""
    ev_sup_1 = Evidence(id="ev_s1", target_id="boost_valve", direction=EvidenceDirection.SUPPORT)
    ev_sup_2 = Evidence(id="ev_s2", target_id="boost_valve", direction=EvidenceDirection.SUPPORT)
    ev_ref = Evidence(id="ev_r1", target_id="boost_valve", direction=EvidenceDirection.REFUTE)

    engine = DeterministicReasoningEngine()
    inp = ReasoningInput(
        context_id="ctx_contra",
        reasoning_mode=ReasoningMode.CAUSAL,
        premises=[ev_sup_1, ev_sup_2, ev_ref],
        causal_graph=[("boost_valve", "manifold_pressure", "pneumatic_actuation")],
    )

    trace, result = engine.reason(inp)

    assert isinstance(trace.conclusion, CausalHypothesis)
    # Despite 2 SUPPORT vs 1 REFUTE, status must NOT be forced to SUPPORTED
    assert trace.conclusion.status == EpistemicStatus.UNRESOLVED
    assert len(result.contradictions_detected) >= 1
    assert "ev_s1" in trace.conclusion.supporting_evidence_ids
    assert "ev_s2" in trace.conclusion.supporting_evidence_ids
    assert "ev_r1" in trace.conclusion.contradictory_evidence_ids
