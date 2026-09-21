"""Cognitia Provider Availability and Activation Tests."""

from __future__ import annotations

import pytest

from cognitia.providers.gateway import InMemoryProviderGateway, ProviderExecutionError
from cognitia.providers.registry import InMemoryAdvancedProviderRegistry
from cognitia.providers.scaffolds.llm import MockLLMProvider
from cognitia.providers.types import (
    AdvancedCapabilityType,
    AdvancedProviderRecord,
    ProviderLifecycleStatus,
    ReasoningRequest,
    ResourceRequirements,
)
from cognitia.reasoning.types import ReasoningInput, ReasoningMode


def _make_snapshot() -> ReasoningInput:
    return ReasoningInput(
        context_id="snap_availability",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[],
    )


def _make_request() -> ReasoningRequest:
    return ReasoningRequest(
        input_snapshot_id="snap_availability",
        requested_capability=AdvancedCapabilityType.LLM_REASONING,
    )


class TestProviderAvailability:
    """Provider must be AVAILABLE (resources satisfied) before ENABLED."""

    def test_resource_requirement_network_unavailable_blocks(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="network_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.ENABLED,
                resources=ResourceRequirements(requires_network=True),
            )
        )
        gateway = InMemoryProviderGateway(
            provider_registry=registry,
            available_resources={"network": False},
        )
        provider = MockLLMProvider(provider_id="network_provider")
        with pytest.raises(ProviderExecutionError):
            gateway.execute(provider, _make_request(), _make_snapshot())

    def test_resource_requirement_network_available_allows(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="network_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.ENABLED,
                resources=ResourceRequirements(requires_network=True),
            )
        )
        gateway = InMemoryProviderGateway(
            provider_registry=registry,
            available_resources={"network": True},
        )
        provider = MockLLMProvider(provider_id="network_provider")
        artifact = gateway.execute(provider, _make_request(), _make_snapshot())
        assert artifact is not None

    def test_resource_requirement_gpu_unavailable_blocks(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="gpu_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.TINYML_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.ENABLED,
                resources=ResourceRequirements(requires_gpu=True),
            )
        )
        gateway = InMemoryProviderGateway(
            provider_registry=registry,
            available_resources={"gpu": False},
        )
        provider = MockLLMProvider(provider_id="gpu_provider")
        with pytest.raises(ProviderExecutionError):
            gateway.execute(provider, _make_request(), _make_snapshot())

    def test_no_resource_requirements_passes(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="no_resources_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.ENABLED,
                resources=ResourceRequirements(),
            )
        )
        gateway = InMemoryProviderGateway(
            provider_registry=registry,
            available_resources={},
        )
        provider = MockLLMProvider(provider_id="no_resources_provider")
        artifact = gateway.execute(provider, _make_request(), _make_snapshot())
        assert artifact is not None

    def test_authorize_returns_check_results(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="auth_test",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.ENABLED,
            )
        )
        gateway = InMemoryProviderGateway(provider_registry=registry)
        authorized, checks = gateway.authorize(
            "auth_test", "1.0.0", _make_request(), _make_snapshot()
        )
        assert authorized is True
        assert all(c.passed for c in checks)

    def test_authorize_failure_returns_failed_checks(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        gateway = InMemoryProviderGateway(provider_registry=registry)
        authorized, checks = gateway.authorize(
            "unknown", "1.0.0", _make_request(), _make_snapshot()
        )
        assert authorized is False
        assert not all(c.passed for c in checks)


class TestProviderActivation:
    """Normal activation path: REGISTERED -> VALIDATED -> AVAILABLE -> ENABLED."""

    def test_activation_path(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="activation_test",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.REGISTERED,
            )
        )
        assert not registry.is_enabled("activation_test", "1.0.0")
        registry.set_lifecycle_status(
            "activation_test", "1.0.0", ProviderLifecycleStatus.VALIDATED
        )
        assert not registry.is_enabled("activation_test", "1.0.0")
        registry.set_lifecycle_status(
            "activation_test", "1.0.0", ProviderLifecycleStatus.AVAILABLE
        )
        assert not registry.is_enabled("activation_test", "1.0.0")
        registry.set_lifecycle_status(
            "activation_test", "1.0.0", ProviderLifecycleStatus.ENABLED
        )
        assert registry.is_enabled("activation_test", "1.0.0") is True

    def test_direct_enable_from_registered(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="direct_enable",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.REGISTERED,
            )
        )
        registry.set_lifecycle_status(
            "direct_enable", "1.0.0", ProviderLifecycleStatus.ENABLED
        )
        assert registry.is_enabled("direct_enable", "1.0.0") is True

    def test_disabling_after_enabling(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="toggle_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.ENABLED,
            )
        )
        assert registry.is_enabled("toggle_provider", "1.0.0") is True
        registry.set_lifecycle_status(
            "toggle_provider", "1.0.0", ProviderLifecycleStatus.DISABLED
        )
        assert registry.is_enabled("toggle_provider", "1.0.0") is False
