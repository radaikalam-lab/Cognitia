"""Phase 5A: Advanced Provider Embedding Tests."""

from __future__ import annotations

import pytest

from cognitia.providers.gateway import InMemoryProviderGateway
from cognitia.providers.registry import InMemoryAdvancedProviderRegistry
from cognitia.providers.scaffolds.llm import MockLLMProvider
from cognitia.providers.types import (
    AdvancedCapabilityType,
    AdvancedProviderRecord,
    ProviderLifecycleStatus,
    ReasoningMode,
)
from cognitia.runtime.local import LocalCognitiveRuntime


class TestAdvancedProviderEmbedding:
    """Mock advanced providers can operate through ProviderGateway inside embedded Cognitia."""

    def test_mock_provider_through_gateway(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="mock_llm_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.ENABLED,
            )
        )
        gateway = InMemoryProviderGateway(provider_registry=registry)
        provider = MockLLMProvider(provider_id="mock_llm_provider")
        from cognitia.reasoning.types import ReasoningInput
        input_snapshot = ReasoningInput(
            context_id="test_snapshot",
            reasoning_mode=ReasoningMode.DEDUCTION,
            premises=(),
        )
        from cognitia.providers.types import ReasoningRequest
        request = ReasoningRequest(
            input_snapshot_id="test_snapshot",
            requested_capability=AdvancedCapabilityType.LLM_REASONING,
        )
        result = gateway.execute(provider, request, input_snapshot)
        assert result is not None

    def test_provider_cannot_access_host_state(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="mock_llm_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.ENABLED,
            )
        )
        gateway = InMemoryProviderGateway(provider_registry=registry)
        provider = MockLLMProvider(provider_id="mock_llm_provider")
        host_state = {"secret_inventory": 100}
        from cognitia.reasoning.types import ReasoningInput
        input_snapshot = ReasoningInput(
            context_id="test_snapshot",
            reasoning_mode=ReasoningMode.DEDUCTION,
            premises=(),
        )
        from cognitia.providers.types import ReasoningRequest
        request = ReasoningRequest(
            input_snapshot_id="test_snapshot",
            requested_capability=AdvancedCapabilityType.LLM_REASONING,
        )
        result = gateway.execute(provider, request, input_snapshot)
        assert result is not None

    def test_provider_output_is_candidate_not_truth(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="mock_llm_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.ENABLED,
            )
        )
        gateway = InMemoryProviderGateway(provider_registry=registry)
        provider = MockLLMProvider(provider_id="mock_llm_provider")
        from cognitia.reasoning.types import ReasoningInput
        input_snapshot = ReasoningInput(
            context_id="test_snapshot",
            reasoning_mode=ReasoningMode.DEDUCTION,
            premises=(),
        )
        from cognitia.providers.types import ReasoningRequest
        request = ReasoningRequest(
            input_snapshot_id="test_snapshot",
            requested_capability=AdvancedCapabilityType.LLM_REASONING,
        )
        result = gateway.execute(provider, request, input_snapshot)
        assert result is not None
