"""Tests for deterministic Analogical Reasoning strategy."""

import pytest

from cognitia.abi.types import Observation
from cognitia.reasoning import (
    AnalogicalMapping,
    AnalogicalReasoner,
    ReasoningInput,
    ReasoningMode,
)


def test_analogical_structural_mapping():
    """Verify structural correspondence mapping from source pattern to target context."""
    source_pattern = {
        "source_id": "acoustic_filter_profile_alpha",
        "elements": {
            "frequency_band": "domain_range",
            "amplitude_gain": "signal_magnitude",
            "damping_factor": "attenuation_rate",
        },
        "mapping_hints": {
            "frequency_band": "engine_rpm_band",
            "amplitude_gain": "boost_gain",
            "damping_factor": "exhaust_backpressure",
        },
        "basis": "signal_attenuation_topology",
    }

    target_obs = Observation(
        id="obs_vehicle",
        payload={
            "engine_rpm_band": "2000-4000",
            "boost_gain": 1.4,
            "exhaust_backpressure": 0.8,
        },
    )

    reasoner = AnalogicalReasoner()
    inp = ReasoningInput(
        context_id="ctx_vehicle",
        reasoning_mode=ReasoningMode.ANALOGY,
        premises=[target_obs],
        analogy_source=source_pattern,
    )

    trace, result = reasoner.reason(inp)

    assert trace.mode == ReasoningMode.ANALOGY
    assert isinstance(trace.conclusion, AnalogicalMapping)
    mapping = trace.conclusion
    assert mapping.source_structure_id == "acoustic_filter_profile_alpha"
    assert mapping.similarity_score == 1.0
    assert mapping.is_equivalent is False  # Invariant: Similarity != Equivalence
    assert len(mapping.correspondences) == 3
    assert len(mapping.known_limitations) >= 2
    assert "acoustic_filter_profile_alpha" in result.candidate_claims[0].statement


def test_analogical_partial_match_records_residual():
    """Verify unmapped source elements produce explicit residuals."""
    source_pattern = {
        "source_id": "three_stage_pipeline",
        "elements": {
            "stage_1": "init",
            "stage_2": "transform",
            "stage_3": "finalize",
        },
    }
    # Target only has stage_1 and stage_2
    target_obs = Observation(id="obs_partial", payload={"stage_1": "started", "stage_2": "processed"})

    reasoner = AnalogicalReasoner()
    inp = ReasoningInput(
        context_id="ctx_pipeline",
        reasoning_mode=ReasoningMode.ANALOGY,
        premises=[target_obs],
        analogy_source=source_pattern,
    )

    trace, result = reasoner.reason(inp)
    assert isinstance(trace.conclusion, AnalogicalMapping)
    assert len(trace.conclusion.correspondences) == 2
    assert trace.conclusion.similarity_score < 1.0
    assert len(trace.conclusion.residuals) == 1
    assert trace.conclusion.residuals[0].factor_name == "stage_3"
