"""Tests for Reasoning Contract conformance and canonical schemas."""

import dataclasses
import pytest

from cognitia.abi.types import CognitiveObject, DeterministicSerializer, Observation
from cognitia.reasoning import (
    DeterministicReasoningEngine,
    EngineReasoningCapability,
    ReasoningCapability,
    ReasoningInput,
    ReasoningMode,
    ReasoningResult,
    ReasoningStep,
    ReasoningTrace,
)


def test_reasoning_trace_contract_conformance():
    """Verify ReasoningTrace matches schema defined in contracts/reasoning-contract.md."""
    step1 = ReasoningStep(
        step_number=1,
        inference_rule="modus_ponens",
        input_references=["obs_1"],
        intermediate_claim="Condition met",
        confidence=1.0,
    )
    premise = Observation(id="obs_1", source_id="sensor_1", payload={"temp": 95.0})
    conclusion = CognitiveObject(metadata={"state": "OVERHEAT"})

    trace = ReasoningTrace(
        mode=ReasoningMode.DEDUCTION,
        premises=[premise],
        steps=[step1],
        conclusion=conclusion,
        confidence=1.0,
        provider="deterministic_deductive_reasoner",
    )

    assert trace.mode == ReasoningMode.DEDUCTION
    assert len(trace.premises) == 1
    assert len(trace.steps) == 1
    assert trace.steps[0].step_number == 1
    assert trace.steps[0].inference_rule == "modus_ponens"
    assert trace.conclusion == conclusion
    assert trace.confidence == 1.0
    assert trace.provider == "deterministic_deductive_reasoner"
    assert trace.provenance is not None

    # Check serialization
    serialized = trace.serialize()
    deserialized = DeterministicSerializer.deserialize(serialized)
    assert deserialized["mode"] == "deduction"
    assert deserialized["confidence"] == 1.0


def test_reasoning_trace_and_input_immutability():
    """Verify that ReasoningTrace and ReasoningInput enforce deep immutability."""
    trace = ReasoningTrace()
    with pytest.raises(dataclasses.FrozenInstanceError):
        trace.confidence = 0.5  # type: ignore[misc]

    inp = ReasoningInput(context_id="ctx_1", reasoning_mode=ReasoningMode.DEDUCTION)
    with pytest.raises(dataclasses.FrozenInstanceError):
        inp.context_id = "ctx_2"  # type: ignore[misc]


def test_all_five_modes_supported_in_engine_capability():
    """Verify EngineReasoningCapability supports all 5 canonical modes."""
    cap = EngineReasoningCapability()
    assert isinstance(cap, ReasoningCapability)
    assert cap.supported_modes == {
        ReasoningMode.DEDUCTION,
        ReasoningMode.ABDUCTION,
        ReasoningMode.ANALOGY,
        ReasoningMode.COUNTERFACTUAL,
        ReasoningMode.CAUSAL,
    }
