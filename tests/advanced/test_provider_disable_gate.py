"""Cognitia Provider Disable Gate Tests.

Verifies that disabled providers cannot execute.
"""

from __future__ import annotations

import pytest

from cognitia.providers.gateway import (
    InMemoryProviderGateway,
    ProviderExecutionError,
)
from cognitia.providers.registry import InMemoryAdvancedProviderRegistry
from cognitia.providers.scaffolds.llm import MockLLMProvider
from cognitia.providers.types import (
    AdvancedCapabilityType,
    AdvancedProviderRecord,
    ProviderLifecycleStatus,
    ReasoningRequest,
)
from cognitia.reasoning.types import ReasoningInput, ReasoningMode


def _make_snapshot() -> ReasoningInput:
    return ReasoningInput(
        context_id="snap_disable_gate",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[],
    )


def _make_request() -> ReasoningRequest:
    return ReasoningRequest(
        input_snapshot_id="snap_disable_gate",
        requested_capability=AdvancedCapabilityType.LLM_REASONING,
    )


class TestProviderDisableGate:
    """Disabled providers must not execute."""

    def test_disabled_provider_rejected(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="disabled_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.DISABLED,
            )
        )
        gateway = InMemoryProviderGateway(provider_registry=registry)
        provider = MockLLMProvider(provider_id="disabled_provider")
        with pytest.raises(ProviderExecutionError):
            gateway.execute(provider, _make_request(), _make_snapshot())

    def test_enabled_provider_accepted(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="enabled_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.ENABLED,
            )
        )
        gateway = InMemoryProviderGateway(provider_registry=registry)
        provider = MockLLMProvider(provider_id="enabled_provider")
        artifact = gateway.execute(provider, _make_request(), _make_snapshot())
        assert artifact is not None
        assert artifact.provider_id == "enabled_provider"

    def test_suspended_provider_rejected(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="suspended_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.SUSPENDED,
            )
        )
        gateway = InMemoryProviderGateway(provider_registry=registry)
        provider = MockLLMProvider(provider_id="suspended_provider")
        with pytest.raises(ProviderExecutionError):
            gateway.execute(provider, _make_request(), _make_snapshot())

    def test_retired_provider_rejected(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="retired_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.RETIRED,
            )
        )
        gateway = InMemoryProviderGateway(provider_registry=registry)
        provider = MockLLMProvider(provider_id="retired_provider")
        with pytest.raises(ProviderExecutionError):
            gateway.execute(provider, _make_request(), _make_snapshot())

    def test_registered_but_not_enabled_rejected(self) -> None:
        """AVAILABLE + DISABLED must not execute."""
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="available_disabled_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.AVAILABLE,
            )
        )
        gateway = InMemoryProviderGateway(provider_registry=registry)
        provider = MockLLMProvider(provider_id="available_disabled_provider")
        with pytest.raises(ProviderExecutionError):
            gateway.execute(provider, _make_request(), _make_snapshot())

    def test_unregistered_provider_rejected(self) -> None:
        gateway = InMemoryProviderGateway(
            provider_registry=InMemoryAdvancedProviderRegistry()
        )
        provider = MockLLMProvider(provider_id="unknown_provider")
        with pytest.raises(ProviderExecutionError):
            gateway.execute(provider, _make_request(), _make_snapshot())

    def test_error_contains_provider_id_and_version(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        gateway = InMemoryProviderGateway(provider_registry=registry)
        provider = MockLLMProvider(provider_id="test_err", provider_version="9.9.9")
        with pytest.raises(ProviderExecutionError) as exc_info:
            gateway.execute(provider, _make_request(), _make_snapshot())
        assert "test_err" in str(exc_info.value)
        assert "9.9.9" in str(exc_info.value)
