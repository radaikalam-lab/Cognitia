"""Cognitia LLM Reasoning Provider Contract Tests."""

from __future__ import annotations

from cognitia.providers.scaffolds.llm import LLMReasoningProvider, MockLLMProvider
from cognitia.providers.types import (
    AdvancedCapabilityType,
    ReasoningRequest,
)
from cognitia.reasoning.types import ReasoningInput, ReasoningMode


def _make_snapshot() -> ReasoningInput:
    return ReasoningInput(
        context_id="llm_snap",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[],
    )


def _make_request() -> ReasoningRequest:
    return ReasoningRequest(
        input_snapshot_id="llm_snap",
        requested_capability=AdvancedCapabilityType.LLM_REASONING,
    )


class TestLLMProviderContract:
    def test_mock_implements_protocol(self) -> None:
        provider = MockLLMProvider()
        assert isinstance(provider, LLMReasoningProvider)

    def test_provider_id_attribute(self) -> None:
        provider = MockLLMProvider(provider_id="llm_alpha")
        assert provider.provider_id == "llm_alpha"

    def test_provider_version_attribute(self) -> None:
        provider = MockLLMProvider(provider_version="3.0.0")
        assert provider.provider_version == "3.0.0"

    def test_model_id_attribute(self) -> None:
        provider = MockLLMProvider(model_id="gpt_synthetic")
        assert provider.model_id == "gpt_synthetic"

    def test_model_version_attribute(self) -> None:
        provider = MockLLMProvider(model_version="2.0.0")
        assert provider.model_version == "2.0.0"

    def test_capabilities_returns_llm_reasoning(self) -> None:
        provider = MockLLMProvider()
        assert AdvancedCapabilityType.LLM_REASONING in provider.capabilities()

    def test_reason_returns_candidate_artifact(self) -> None:
        from cognitia.providers.types import CandidateReasoningArtifact
        provider = MockLLMProvider()
        result = provider.reason(_make_request(), _make_snapshot())
        assert isinstance(result, CandidateReasoningArtifact)

    def test_output_is_not_truth(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert artifact.epistemic_status.name == "UNRESOLVED"
        assert artifact.proposal_status.name == "PROPOSED"

    def test_output_is_not_decision(self) -> None:
        from cognitia.abi.types import Decision
        provider = MockLLMProvider()
        result = provider.reason(_make_request(), _make_snapshot())
        assert not isinstance(result, Decision)

    def test_output_is_not_authority(self) -> None:
        from cognitia.abi.types import Decision
        provider = MockLLMProvider()
        result = provider.reason(_make_request(), _make_snapshot())
        assert not isinstance(result, Decision)
        assert result.artifact_type != "decision"

    def test_deterministic_output(self) -> None:
        provider = MockLLMProvider()
        request = _make_request()
        snapshot = _make_snapshot()
        a1 = provider.reason(request, snapshot)
        a2 = provider.reason(request, snapshot)
        assert a1.payload_dict == a2.payload_dict
        assert a1.provider_id == a2.provider_id
        assert a1.provider_version == a2.provider_version
        assert a1.input_snapshot_id == a2.input_snapshot_id

    def test_payload_contains_expected_keys(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        payload = artifact.payload_dict
        assert "candidate_narrative" in payload
        assert "generated_hypotheses" in payload
