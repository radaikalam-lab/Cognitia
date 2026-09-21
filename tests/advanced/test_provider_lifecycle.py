"""Cognitia Provider Lifecycle Tests."""

from __future__ import annotations

import pytest

from cognitia.providers.registry import InMemoryAdvancedProviderRegistry
from cognitia.providers.types import (
    AdvancedCapabilityType,
    AdvancedProviderRecord,
    ProviderLifecycleStatus,
)


def _make_record(
    provider_id: str = "lifecycle_provider",
    version: str = "1.0.0",
    status: ProviderLifecycleStatus = ProviderLifecycleStatus.DECLARED,
) -> AdvancedProviderRecord:
    return AdvancedProviderRecord(
        provider_id=provider_id,
        provider_version=version,
        capability_types=(AdvancedCapabilityType.LLM_REASONING,),
        lifecycle_status=status,
    )


class TestProviderLifecycle:
    """Tests verifying lifecycle status transitions and semantics."""

    def test_default_status_is_declared(self) -> None:
        record = _make_record()
        assert record.lifecycle_status == ProviderLifecycleStatus.DECLARED

    def test_all_lifecycle_states_exist(self) -> None:
        expected = {
            "DECLARED",
            "REGISTERED",
            "VALIDATED",
            "AVAILABLE",
            "ENABLED",
            "DISABLED",
            "SUSPENDED",
            "RETIRED",
        }
        actual = {s.name for s in ProviderLifecycleStatus}
        assert actual == expected

    def test_registered_is_distinct_from_enabled(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record(status=ProviderLifecycleStatus.REGISTERED))
        assert registry.is_enabled("lifecycle_provider", "1.0.0") is False

    def test_validated_is_distinct_from_enabled(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record(status=ProviderLifecycleStatus.VALIDATED))
        assert registry.is_enabled("lifecycle_provider", "1.0.0") is False

    def test_available_is_distinct_from_enabled(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record(status=ProviderLifecycleStatus.AVAILABLE))
        assert registry.is_enabled("lifecycle_provider", "1.0.0") is False

    def test_available_plus_disabled_is_not_enabled(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record(status=ProviderLifecycleStatus.DISABLED))
        assert registry.is_enabled("lifecycle_provider", "1.0.0") is False

    def test_enabled_means_executable(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record(status=ProviderLifecycleStatus.ENABLED))
        assert registry.is_enabled("lifecycle_provider", "1.0.0") is True

    def test_disabled_blocks_execution(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record(status=ProviderLifecycleStatus.DISABLED))
        assert registry.is_enabled("lifecycle_provider", "1.0.0") is False

    def test_suspended_blocks_execution(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record(status=ProviderLifecycleStatus.SUSPENDED))
        assert registry.is_enabled("lifecycle_provider", "1.0.0") is False

    def test_retired_blocks_execution(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record(status=ProviderLifecycleStatus.RETIRED))
        assert registry.is_enabled("lifecycle_provider", "1.0.0") is False

    def test_lifecycle_transition_declared_to_enabled(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record(status=ProviderLifecycleStatus.DECLARED))
        registry.set_lifecycle_status(
            "lifecycle_provider", "1.0.0", ProviderLifecycleStatus.ENABLED
        )
        assert registry.is_enabled("lifecycle_provider", "1.0.0") is True

    def test_lifecycle_transition_enabled_to_disabled(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record(status=ProviderLifecycleStatus.ENABLED))
        registry.set_lifecycle_status(
            "lifecycle_provider", "1.0.0", ProviderLifecycleStatus.DISABLED
        )
        assert registry.is_enabled("lifecycle_provider", "1.0.0") is False

    def test_all_providers_default_to_non_enabled(self) -> None:
        """Every provider must default to DECLARED or DISABLED."""
        for status in ProviderLifecycleStatus:
            registry = InMemoryAdvancedProviderRegistry()
            record = _make_record(status=status)
            registry.register(record)
            if status == ProviderLifecycleStatus.ENABLED:
                assert registry.is_enabled("lifecycle_provider", "1.0.0") is True
            else:
                assert registry.is_enabled("lifecycle_provider", "1.0.0") is False
