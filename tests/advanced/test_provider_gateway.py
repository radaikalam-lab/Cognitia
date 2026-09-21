"""Cognitia Provider Gateway Tests."""

from __future__ import annotations

import pytest

from cognitia.providers.gateway import (
    GatewayCheckResult,
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
    ResourceRequirements,
)
from cognitia.reasoning.types import ReasoningInput, ReasoningMode


def _make_snapshot() -> ReasoningInput:
    return ReasoningInput(
        context_id="snap_gateway",
        reasoning_mode=ReasoningMode.DEDUCTION,
        premises=[],
    )


def _make_request(capability: AdvancedCapabilityType = AdvancedCapabilityType.LLM_REASONING) -> ReasoningRequest:
    return ReasoningRequest(
        input_snapshot_id="snap_gateway",
        requested_capability=capability,
    )


class TestProviderGateway:
    """Tests for the ProviderGateway authorization and execution."""

    def _make_registry_with_enabled(self) -> tuple[InMemoryAdvancedProviderRegistry, MockLLMProvider]:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="gateway_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.ENABLED,
            )
        )
        provider = MockLLMProvider(provider_id="gateway_provider")
        return registry, provider

    def test_execute_returns_artifact(self) -> None:
        registry, provider = self._make_registry_with_enabled()
        gateway = InMemoryProviderGateway(provider_registry=registry)
        artifact = gateway.execute(provider, _make_request(), _make_snapshot())
        assert artifact is not None
        assert artifact.provider_id == "gateway_provider"

    def test_execute_rejects_unsupported_capability(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="limited_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.TINYML_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.ENABLED,
            )
        )
        gateway = InMemoryProviderGateway(provider_registry=registry)
        provider = MockLLMProvider(provider_id="limited_provider")
        with pytest.raises(ProviderExecutionError):
            gateway.execute(
                provider,
                _make_request(AdvancedCapabilityType.LLM_REASONING),
                _make_snapshot(),
            )

    def test_execute_rejects_snapshot_id_mismatch(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="snap_mismatch_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.ENABLED,
            )
        )
        gateway = InMemoryProviderGateway(provider_registry=registry)
        provider = MockLLMProvider(provider_id="snap_mismatch_provider")
        bad_request = ReasoningRequest(
            input_snapshot_id="nonexistent_snap",
            requested_capability=AdvancedCapabilityType.LLM_REASONING,
        )
        with pytest.raises(ProviderExecutionError):
            gateway.execute(provider, bad_request, _make_snapshot())

    def test_authorize_returns_all_checks(self) -> None:
        registry, _ = self._make_registry_with_enabled()
        gateway = InMemoryProviderGateway(provider_registry=registry)
        authorized, checks = gateway.authorize(
            "gateway_provider", "1.0.0", _make_request(), _make_snapshot()
        )
        assert authorized is True
        check_names = [c.check_name for c in checks]
        assert "provider_exists" in check_names
        assert "lifecycle_enabled" in check_names
        assert "capability_supported" in check_names
        assert "resources_satisfied" in check_names
        assert "input_snapshot_valid" in check_names

    def test_authorize_false_for_missing_provider(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        gateway = InMemoryProviderGateway(provider_registry=registry)
        authorized, checks = gateway.authorize(
            "missing", "1.0.0", _make_request(), _make_snapshot()
        )
        assert authorized is False
        assert not checks[0].passed
        assert checks[0].check_name == "provider_exists"

    def test_gateway_does_not_perform_epistemic_evaluation(self) -> None:
        """Gateway execution returns CandidateReasoningArtifact without calling EpistemicService."""
        registry, provider = self._make_registry_with_enabled()
        gateway = InMemoryProviderGateway(provider_registry=registry)
        artifact = gateway.execute(provider, _make_request(), _make_snapshot())
        assert artifact.epistemic_status.name == "UNRESOLVED"

    def test_gateway_respects_resource_requirements(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            AdvancedProviderRecord(
                provider_id="resource_provider",
                provider_version="1.0.0",
                capability_types=(AdvancedCapabilityType.LLM_REASONING,),
                lifecycle_status=ProviderLifecycleStatus.ENABLED,
                resources=ResourceRequirements(requires_filesystem=True),
            )
        )
        gateway = InMemoryProviderGateway(
            provider_registry=registry,
            available_resources={"filesystem": False},
        )
        provider = MockLLMProvider(provider_id="resource_provider")
        with pytest.raises(ProviderExecutionError):
            gateway.execute(provider, _make_request(), _make_snapshot())

    def test_check_result_repr(self) -> None:
        result = GatewayCheckResult(check_name="test", passed=True, detail="ok")
        assert "PASS" in repr(result)
        result_fail = GatewayCheckResult(check_name="test", passed=False, detail="fail")
        assert "FAIL" in repr(result_fail)
