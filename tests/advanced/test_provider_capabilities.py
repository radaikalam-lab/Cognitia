"""Cognitia Provider Capability Tests."""

from __future__ import annotations

import pytest

from cognitia.providers.scaffolds.causal import (
    CausalInferenceProvider,
    MockCausalProvider,
)
from cognitia.providers.scaffolds.evolution import (
    MockStrategyEvolutionProvider,
    ReasoningStrategyEvolutionProvider,
)
from cognitia.providers.scaffolds.hypothesis import (
    HypothesisGenerationProvider,
    MockHypothesisProvider,
)
from cognitia.providers.scaffolds.llm import LLMReasoningProvider, MockLLMProvider
from cognitia.providers.scaffolds.rl import MockRLProvider, ReinforcementLearningProvider
from cognitia.providers.scaffolds.semantic_graph import (
    MockSemanticGraphProvider,
    SemanticGraphProvider,
)
from cognitia.providers.scaffolds.similarity import MockSimilarityProvider, SimilarityProvider
from cognitia.providers.scaffolds.tinyml import MockTinyMLProvider, TinyMLReasoningProvider
from cognitia.providers.types import AdvancedCapabilityType


class TestAdvancedCapabilityType:
    """Tests verifying all capability types exist."""

    def test_all_capability_types_exist(self) -> None:
        expected = {
            "LLM_REASONING",
            "TINYML_REASONING",
            "HYPOTHESIS_GENERATION",
            "CAUSAL_INFERENCE",
            "SEMANTIC_GRAPH",
            "VECTOR_RETRIEVAL",
            "REINFORCEMENT_LEARNING",
            "SELF_MODIFYING_REASONING",
            "DIRECTIONAL_PROGRAMMING",
        }
        actual = {c.name for c in AdvancedCapabilityType}
        assert actual == expected

    def test_capability_values_are_strings(self) -> None:
        for cap in AdvancedCapabilityType:
            assert isinstance(cap.value, str)
            assert len(cap.value) > 0


class TestLLMProviderCapability:
    def test_mock_llm_provider_capabilities(self) -> None:
        provider = MockLLMProvider()
        assert AdvancedCapabilityType.LLM_REASONING in provider.capabilities()

    def test_llm_provider_implements_protocol(self) -> None:
        provider = MockLLMProvider()
        assert isinstance(provider, LLMReasoningProvider)


class TestTinyMLProviderCapability:
    def test_mock_tinyml_provider_capabilities(self) -> None:
        provider = MockTinyMLProvider()
        assert AdvancedCapabilityType.TINYML_REASONING in provider.capabilities()

    def test_tinyml_provider_implements_protocol(self) -> None:
        provider = MockTinyMLProvider()
        assert isinstance(provider, TinyMLReasoningProvider)


class TestHypothesisProviderCapability:
    def test_mock_hypothesis_provider_capabilities(self) -> None:
        provider = MockHypothesisProvider()
        assert AdvancedCapabilityType.HYPOTHESIS_GENERATION in provider.capabilities()

    def test_hypothesis_provider_implements_protocol(self) -> None:
        provider = MockHypothesisProvider()
        assert isinstance(provider, HypothesisGenerationProvider)


class TestCausalProviderCapability:
    def test_mock_causal_provider_capabilities(self) -> None:
        provider = MockCausalProvider()
        assert AdvancedCapabilityType.CAUSAL_INFERENCE in provider.capabilities()

    def test_causal_provider_implements_protocol(self) -> None:
        provider = MockCausalProvider()
        assert isinstance(provider, CausalInferenceProvider)


class TestSemanticGraphProviderCapability:
    def test_mock_semantic_graph_provider_capabilities(self) -> None:
        provider = MockSemanticGraphProvider()
        assert AdvancedCapabilityType.SEMANTIC_GRAPH in provider.capabilities()

    def test_semantic_graph_provider_implements_protocol(self) -> None:
        provider = MockSemanticGraphProvider()
        assert isinstance(provider, SemanticGraphProvider)


class TestSimilarityProviderCapability:
    def test_mock_similarity_provider_capabilities(self) -> None:
        provider = MockSimilarityProvider()
        assert AdvancedCapabilityType.VECTOR_RETRIEVAL in provider.capabilities()

    def test_similarity_provider_implements_protocol(self) -> None:
        provider = MockSimilarityProvider()
        assert isinstance(provider, SimilarityProvider)


class TestRLProviderCapability:
    def test_mock_rl_provider_capabilities(self) -> None:
        provider = MockRLProvider()
        assert AdvancedCapabilityType.REINFORCEMENT_LEARNING in provider.capabilities()

    def test_rl_provider_implements_protocol(self) -> None:
        provider = MockRLProvider()
        assert isinstance(provider, ReinforcementLearningProvider)


class TestStrategyEvolutionProviderCapability:
    def test_mock_strategy_evolution_provider_capabilities(self) -> None:
        provider = MockStrategyEvolutionProvider()
        assert AdvancedCapabilityType.SELF_MODIFYING_REASONING in provider.capabilities()

    def test_strategy_evolution_provider_implements_protocol(self) -> None:
        provider = MockStrategyEvolutionProvider()
        assert isinstance(provider, ReasoningStrategyEvolutionProvider)
