"""Cognitia Hypothesis Generation Provider Contract Tests."""

from __future__ import annotations

import pytest

from cognitia.providers.scaffolds.hypothesis import (
    HypothesisGenerationProvider,
    MockHypothesisProvider,
)
from cognitia.providers.types import (
    AdvancedCapabilityType,
    ReasoningRequest,
)
from cognitia.reasoning.types import ReasoningInput, ReasoningMode


def _make_snapshot() -> ReasoningInput:
    return ReasoningInput(
        context_id="hypothesis_snap",
        reasoning_mode=ReasoningMode.ABDUCTION,
        premises=[],
    )


class TestHypothesisProviderContract:
    def test_mock_implements_protocol(self) -> None:
        provider = MockHypothesisProvider()
        assert isinstance(provider, HypothesisGenerationProvider)

    def test_capabilities_returns_hypothesis_generation(self) -> None:
        provider = MockHypothesisProvider()
        assert AdvancedCapabilityType.HYPOTHESIS_GENERATION in provider.capabilities()

    def test_generate_hypotheses_returns_candidate_artifact(self) -> None:
        from cognitia.providers.types import CandidateReasoningArtifact
        request = ReasoningRequest(
            input_snapshot_id="hypothesis_snap",
            requested_capability=AdvancedCapabilityType.HYPOTHESIS_GENERATION,
        )
        provider = MockHypothesisProvider()
        result = provider.generate_hypotheses(request, _make_snapshot())
        assert isinstance(result, CandidateReasoningArtifact)

    def test_generated_hypothesis_is_not_accepted(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="hypothesis_snap",
            requested_capability=AdvancedCapabilityType.HYPOTHESIS_GENERATION,
        )
        provider = MockHypothesisProvider()
        artifact = provider.generate_hypotheses(request, _make_snapshot())
        assert artifact.epistemic_status.name == "UNRESOLVED"
        assert artifact.epistemic_status.name != "SUPPORTED"

    def test_payload_contains_expected_keys(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="hypothesis_snap",
            requested_capability=AdvancedCapabilityType.HYPOTHESIS_GENERATION,
        )
        provider = MockHypothesisProvider()
        artifact = provider.generate_hypotheses(request, _make_snapshot())
        payload = artifact.payload_dict
        assert "generation_basis" in payload
        assert "candidate_propositions" in payload
        assert "assumptions" in payload
        assert "unknowns" in payload
