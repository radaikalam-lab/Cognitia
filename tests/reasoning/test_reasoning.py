"""Tests for Reasoning capabilities, modes, and immutable traces."""

import dataclasses
import pytest

from cognitia.abi.types import CognitiveObject
from cognitia.reasoning.capability import DeterministicMockReasoner
from cognitia.reasoning.types import ReasoningMode, ReasoningTrace


def test_reasoning_capability_modes():
    """Verify reasoning capability execution across supported modes."""
    reasoner = DeterministicMockReasoner()
    premises = [
        CognitiveObject(metadata={"premise": "All valve seals wear over time"}),
        CognitiveObject(metadata={"premise": "Valve 4 has operated for 10,000 cycles"}),
    ]

    for mode in [
        ReasoningMode.DEDUCTION,
        ReasoningMode.ABDUCTION,
        ReasoningMode.ANALOGY,
        ReasoningMode.COUNTERFACTUAL,
        ReasoningMode.CAUSAL,
    ]:
        trace = reasoner.reason(mode=mode, premises=premises)

        assert isinstance(trace, ReasoningTrace)
        assert trace.mode == mode
        assert len(trace.steps) == 2
        assert trace.confidence == 1.0
        assert trace.provider == "deterministic_rules"
        assert trace.provenance.is_deterministic is True


def test_reasoning_trace_immutability():
    """Verify that reasoning traces are immutable audit artifacts."""
    reasoner = DeterministicMockReasoner()
    trace = reasoner.reason(mode=ReasoningMode.DEDUCTION, premises=[CognitiveObject()])

    with pytest.raises(dataclasses.FrozenInstanceError):
        trace.confidence = 0.5  # type: ignore[misc]
