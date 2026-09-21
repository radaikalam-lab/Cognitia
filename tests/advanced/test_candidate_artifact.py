"""Cognitia CandidateReasoningArtifact Tests."""

from __future__ import annotations

import pytest

from cognitia.epistemic.types import EpistemicStatus
from cognitia.providers.scaffolds.causal import MockCausalProvider
from cognitia.providers.scaffolds.evolution import MockStrategyEvolutionProvider
from cognitia.providers.scaffolds.hypothesis import MockHypothesisProvider
from cognitia.providers.scaffolds.llm import MockLLMProvider
from cognitia.providers.scaffolds.rl import MockRLProvider
from cognitia.providers.scaffolds.semantic_graph import MockSemanticGraphProvider
from cognitia.providers.scaffolds.similarity import MockSimilarityProvider
from cognitia.providers.scaffolds.tinyml import MockTinyMLProvider
from cognitia.providers.types import (
    AdvancedCapabilityType,
    CandidateReasoningArtifact,
    ProposalLifecycleStatus,
    ReasoningRequest,
)
from cognitia.reasoning.types import ReasoningInput, ReasoningMode


def _make_snapshot() -> ReasoningInput:
    return ReasoningInput(
        context_id="snap_001",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[],
    )


def _make_request() -> ReasoningRequest:
    return ReasoningRequest(
        input_snapshot_id="snap_001",
        requested_capability=AdvancedCapabilityType.LLM_REASONING,
    )


class TestCandidateReasoningArtifact:
    """Tests verifying the CandidateReasoningArtifact envelope."""

    def test_new_artifact_starts_unresolved(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert artifact.epistemic_status == EpistemicStatus.UNRESOLVED

    def test_new_artifact_starts_proposed(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert artifact.proposal_status == ProposalLifecycleStatus.PROPOSED

    def test_artifact_has_provider_id(self) -> None:
        provider = MockLLMProvider(provider_id="custom_provider")
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert artifact.provider_id == "custom_provider"

    def test_artifact_has_provider_version(self) -> None:
        provider = MockLLMProvider(provider_version="2.0.0")
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert artifact.provider_version == "2.0.0"

    def test_artifact_has_input_snapshot_id(self) -> None:
        artifact = MockLLMProvider().reason(_make_request(), _make_snapshot())
        assert artifact.input_snapshot_id == "snap_001"

    def test_artifact_payload_is_mapping(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        payload = artifact.payload_dict
        assert isinstance(payload, dict)
        assert len(payload) > 0

    def test_artifact_has_provenance(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert artifact.provenance is not None
        assert artifact.provenance.producer_id is not None

    def test_artifact_id_equals_artifact_id_field(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert artifact.id == artifact.artifact_id

    def test_llm_artifact_type(self) -> None:
        provider = MockLLMProvider()
        artifact = provider.reason(_make_request(), _make_snapshot())
        assert artifact.artifact_type == "llm_reasoning_candidate"

    def test_tinyml_artifact_type(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="snap_001",
            requested_capability=AdvancedCapabilityType.TINYML_REASONING,
        )
        provider = MockTinyMLProvider()
        artifact = provider.infer(request, _make_snapshot())
        assert artifact.artifact_type == "tinyml_inference_candidate"

    def test_hypothesis_artifact_type(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="snap_001",
            requested_capability=AdvancedCapabilityType.HYPOTHESIS_GENERATION,
        )
        provider = MockHypothesisProvider()
        artifact = provider.generate_hypotheses(request, _make_snapshot())
        assert artifact.artifact_type == "candidate_hypothesis_artifact"

    def test_causal_artifact_type(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="snap_001",
            requested_capability=AdvancedCapabilityType.CAUSAL_INFERENCE,
        )
        provider = MockCausalProvider()
        artifact = provider.discover_causal_structure(request, _make_snapshot())
        assert artifact.artifact_type == "candidate_causal_structure"

    def test_semantic_graph_artifact_type(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="snap_001",
            requested_capability=AdvancedCapabilityType.SEMANTIC_GRAPH,
        )
        provider = MockSemanticGraphProvider()
        artifact = provider.query_graph(request, _make_snapshot())
        assert artifact.artifact_type == "semantic_graph_candidate"

    def test_similarity_artifact_type(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="snap_001",
            requested_capability=AdvancedCapabilityType.VECTOR_RETRIEVAL,
        )
        provider = MockSimilarityProvider()
        artifact = provider.find_similar(request, _make_snapshot())
        assert artifact.artifact_type == "vector_similarity_candidate"

    def test_rl_artifact_type(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="snap_001",
            requested_capability=AdvancedCapabilityType.REINFORCEMENT_LEARNING,
        )
        provider = MockRLProvider()
        artifact = provider.evaluate_policy(request, _make_snapshot())
        assert artifact.artifact_type == "rl_policy_candidate_proposal"

    def test_strategy_evolution_artifact_type(self) -> None:
        request = ReasoningRequest(
            input_snapshot_id="snap_001",
            requested_capability=AdvancedCapabilityType.SELF_MODIFYING_REASONING,
        )
        provider = MockStrategyEvolutionProvider()
        artifact = provider.propose_strategy_revision(request, _make_snapshot())
        assert artifact.artifact_type == "candidate_strategy_revision"

    def test_all_artifacts_start_unresolved(self) -> None:
        from cognitia.providers.scaffolds.causal import MockCausalProvider
        from cognitia.providers.scaffolds.evolution import MockStrategyEvolutionProvider
        from cognitia.providers.scaffolds.hypothesis import MockHypothesisProvider
        from cognitia.providers.scaffolds.rl import MockRLProvider
        from cognitia.providers.scaffolds.semantic_graph import MockSemanticGraphProvider
        from cognitia.providers.scaffolds.similarity import MockSimilarityProvider
        from cognitia.providers.scaffolds.tinyml import MockTinyMLProvider

        snapshot = _make_snapshot()
        for provider in [
            MockLLMProvider(),
            MockTinyMLProvider(),
            MockHypothesisProvider(),
            MockCausalProvider(),
            MockSemanticGraphProvider(),
            MockSimilarityProvider(),
            MockRLProvider(),
            MockStrategyEvolutionProvider(),
        ]:
            request = ReasoningRequest(
                input_snapshot_id="snap_001",
                requested_capability=provider.capabilities()[0],
            )
            if hasattr(provider, "reason"):
                artifact = provider.reason(request, snapshot)
            elif hasattr(provider, "infer"):
                artifact = provider.infer(request, snapshot)
            elif hasattr(provider, "generate_hypotheses"):
                artifact = provider.generate_hypotheses(request, snapshot)
            elif hasattr(provider, "discover_causal_structure"):
                artifact = provider.discover_causal_structure(request, snapshot)
            elif hasattr(provider, "query_graph"):
                artifact = provider.query_graph(request, snapshot)
            elif hasattr(provider, "find_similar"):
                artifact = provider.find_similar(request, snapshot)
            elif hasattr(provider, "evaluate_policy"):
                artifact = provider.evaluate_policy(request, snapshot)
            elif hasattr(provider, "propose_strategy_revision"):
                artifact = provider.propose_strategy_revision(request, snapshot)
            else:
                raise AssertionError(f"No method found on {provider.provider_id}")
            assert artifact.epistemic_status == EpistemicStatus.UNRESOLVED, (
                f"{provider.provider_id} did not produce UNRESOLVED artifact"
            )
