"""Cognitia TinyML Reasoning Provider Contract Tests."""

from __future__ import annotations

import pytest

from cognitia.providers.scaffolds.tinyml import TinyMLReasoningProvider, MockTinyMLProvider
from cognitia.providers.types import (
    AdvancedCapabilityType,
    ReasoningRequest,
)
from cognitia.reasoning.types import ReasoningInput, ReasoningMode


def _make_snapshot() -> ReasoningInput:
    return ReasoningInput(
        context_id="tinyml_snap",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[],
    )


class TestTinyMLProviderContract:
    def test_mock_implements_protocol(self) -> None:
        provider = MockTinyMLProvider()
        assert isinstance(provider, TinyMLReasoningProvider)

    def test_provider_id_attribute(self) -> None:
        provider = MockTinyMLProvider(provider_id="tinyml_edge")
        assert provider.provider_id == "tinyml_edge"

    def test_calibration_checksum_attribute(self) -> None:
        provider = MockTinyMLProvider(calibration_checksum="deadbeef")
        assert provider.calibration_checksum == "deadbeef"

    def test_capabilities_returns_tinyml_reasoning(self) -> None:
        provider = MockTinyMLProvider()
        assert AdvancedCapabilityType.TINYML_REASONING in provider.capabilities()

    def test_infer_returns_candidate_artifact(self) -> None:
        from cognitia.providers.types import CandidateReasoningArtifact
        request = ReasoningRequest(
            input_snapshot_id="tinyml_snap",
            requested_capability=AdvancedCapabilityType.TINYML_REASONING,
        )
        provider = MockTinyMLProvider()
        result = provider.infer(request, _make_snapshot())
        assert isinstance(result, CandidateReasoningArtifact)

    def test_output_is_unresolved(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="tinyml_snap",
            requested_capability=AdvancedCapabilityType.TINYML_REASONING,
        )
        provider = MockTinyMLProvider()
        artifact = provider.infer(request, _make_snapshot())
        assert artifact.epistemic_status.name == "UNRESOLVED"

    def test_output_is_not_domain_state_mutation(self) -> None:
        """TinyML output is a candidate inference, not a domain state mutation."""
        request = ReasoningRequest(
            input_snapshot_id="tinyml_snap",
            requested_capability=AdvancedCapabilityType.TINYML_REASONING,
        )
        provider = MockTinyMLProvider()
        artifact = provider.infer(request, _make_snapshot())
        assert artifact.artifact_type == "tinyml_inference_candidate"

    def test_payload_contains_expected_keys(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="tinyml_snap",
            requested_capability=AdvancedCapabilityType.TINYML_REASONING,
        )
        provider = MockTinyMLProvider()
        artifact = provider.infer(request, _make_snapshot())
        payload = artifact.payload_dict
        assert "classification_label" in payload
        assert "anomaly_score" in payload
        assert "calibration_checksum" in payload
