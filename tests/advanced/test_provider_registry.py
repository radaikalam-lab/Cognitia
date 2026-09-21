"""Cognitia Advanced Provider Registry Tests."""

from __future__ import annotations

import pytest

from cognitia.capabilities.base import CapabilityType
from cognitia.models.registry import InMemoryModelRegistry, ModelRecord, ModelStatus
from cognitia.providers.registry import InMemoryAdvancedProviderRegistry
from cognitia.providers.types import (
    AdvancedCapabilityType,
    AdvancedProviderRecord,
    ProviderLifecycleStatus,
    ResourceRequirements,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType


def _make_record(
    provider_id: str = "test_provider",
    version: str = "1.0.0",
    capabilities: tuple[AdvancedCapabilityType, ...] | None = None,
    status: ProviderLifecycleStatus = ProviderLifecycleStatus.DECLARED,
    model_ids: tuple[str, ...] = (),
) -> AdvancedProviderRecord:
    return AdvancedProviderRecord(
        provider_id=provider_id,
        provider_version=version,
        capability_types=capabilities or (AdvancedCapabilityType.LLM_REASONING,),
        lifecycle_status=status,
        model_ids=model_ids,
    )


class TestAdvancedProviderRegistry:
    """Tests for InMemoryAdvancedProviderRegistry."""

    def test_register_and_get(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        record = _make_record()
        registry.register(record)
        retrieved = registry.get("test_provider", "1.0.0")
        assert retrieved is not None
        assert retrieved.provider_id == "test_provider"
        assert retrieved.provider_version == "1.0.0"
        assert retrieved.lifecycle_status == ProviderLifecycleStatus.DECLARED

    def test_register_duplicate_raises(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        record = _make_record()
        registry.register(record)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(record)

    def test_get_latest_version_when_no_version_specified(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record(version="1.0.0"))
        registry.register(_make_record(version="2.0.0"))
        latest = registry.get("test_provider")
        assert latest is not None
        assert latest.provider_version == "2.0.0"

    def test_get_returns_none_for_unknown_provider(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        assert registry.get("nonexistent") is None
        assert registry.get("nonexistent", "1.0.0") is None

    def test_list_providers_empty(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        assert registry.list_providers() == []

    def test_list_providers_filters_by_status(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            _make_record(provider_id="p1", status=ProviderLifecycleStatus.ENABLED)
        )
        registry.register(
            _make_record(
                provider_id="p2",
                status=ProviderLifecycleStatus.DISABLED,
            )
        )
        enabled = registry.list_providers(status=ProviderLifecycleStatus.ENABLED)
        assert len(enabled) == 1
        assert enabled[0].provider_id == "p1"

    def test_list_providers_filters_by_capability(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            _make_record(
                capabilities=(AdvancedCapabilityType.LLM_REASONING,),
            )
        )
        registry.register(
            _make_record(
                provider_id="p2",
                capabilities=(AdvancedCapabilityType.VECTOR_RETRIEVAL,),
            )
        )
        llm = registry.list_providers(
            capability_type=AdvancedCapabilityType.LLM_REASONING
        )
        assert len(llm) == 1
        assert llm[0].provider_id == "test_provider"

    def test_list_versions(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record(version="1.0.0"))
        registry.register(_make_record(version="2.0.0"))
        versions = registry.list_versions("test_provider")
        assert len(versions) == 2
        assert {v.provider_version for v in versions} == {"1.0.0", "2.0.0"}

    def test_set_lifecycle_status(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record())
        registry.set_lifecycle_status(
            "test_provider", "1.0.0", ProviderLifecycleStatus.ENABLED
        )
        record = registry.get("test_provider", "1.0.0")
        assert record is not None
        assert record.lifecycle_status == ProviderLifecycleStatus.ENABLED

    def test_set_lifecycle_status_unknown_raises(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        with pytest.raises(KeyError):
            registry.set_lifecycle_status(
                "nonexistent", "1.0.0", ProviderLifecycleStatus.ENABLED
            )

    def test_is_enabled_true(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            _make_record(status=ProviderLifecycleStatus.ENABLED)
        )
        assert registry.is_enabled("test_provider", "1.0.0") is True

    def test_is_enabled_false_for_disabled(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(
            _make_record(status=ProviderLifecycleStatus.DISABLED)
        )
        assert registry.is_enabled("test_provider", "1.0.0") is False

    def test_is_enabled_false_for_unknown(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        assert registry.is_enabled("unknown") is False

    def test_model_registry_integration(self) -> None:
        model_registry = InMemoryModelRegistry()
        registry = InMemoryAdvancedProviderRegistry(
            model_registry=model_registry
        )
        model = ModelRecord(
            model_id="test_model",
            model_version="1.0.0",
            provider="mock_provider",
            capability_type=CapabilityType.DECISION,
            status=ModelStatus.ACTIVE,
        )
        model_registry.register(model)
        record = _make_record(model_ids=("test_model",))
        registry.register(record)
        assert registry.get("test_provider", "1.0.0") is not None

    def test_immutable_versioning_multiple_versions(self) -> None:
        """Historical versions must remain addressable."""
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record(version="1.0.0"))
        registry.register(_make_record(version="2.0.0"))
        v1 = registry.get("test_provider", "1.0.0")
        v2 = registry.get("test_provider", "2.0.0")
        assert v1 is not None
        assert v2 is not None
        assert v1.provider_version == "1.0.0"
        assert v2.provider_version == "2.0.0"
