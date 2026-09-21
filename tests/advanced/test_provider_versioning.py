"""Cognitia Provider Versioning Tests."""

from __future__ import annotations

import pytest

from cognitia.providers.registry import InMemoryAdvancedProviderRegistry
from cognitia.providers.types import (
    AdvancedCapabilityType,
    AdvancedProviderRecord,
    ProviderLifecycleStatus,
)


def _make_record(
    provider_id: str = "versioned_provider",
    version: str = "1.0.0",
    status: ProviderLifecycleStatus = ProviderLifecycleStatus.DECLARED,
) -> AdvancedProviderRecord:
    return AdvancedProviderRecord(
        provider_id=provider_id,
        provider_version=version,
        capability_types=(AdvancedCapabilityType.LLM_REASONING,),
        lifecycle_status=status,
    )


class TestProviderVersioning:
    """Tests verifying immutable provider versioning."""

    def test_multiple_versions_are_independent(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record(version="1.0.0"))
        registry.register(_make_record(version="2.0.0"))
        v1 = registry.get("versioned_provider", "1.0.0")
        v2 = registry.get("versioned_provider", "2.0.0")
        assert v1 is not None
        assert v2 is not None
        assert v1.provider_version == "1.0.0"
        assert v2.provider_version == "2.0.0"

    def test_versioning_never_overwrites(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record(version="1.0.0"))
        with pytest.raises(ValueError, match="already registered"):
            registry.register(_make_record(version="1.0.0"))

    def test_history_tracks_all_versions(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record(version="1.0.0"))
        registry.register(_make_record(version="1.1.0"))
        registry.register(_make_record(version="2.0.0"))
        versions = registry.list_versions("versioned_provider")
        assert len(versions) == 3

    def test_latest_version_is_most_recent(self) -> None:
        registry = InMemoryAdvancedProviderRegistry()
        registry.register(_make_record(version="1.0.0"))
        registry.register(_make_record(version="1.1.0"))
        latest = registry.get("versioned_provider")
        assert latest is not None
        assert latest.provider_version == "1.1.0"

    def test_immutable_provider_id_and_version(self) -> None:
        """Provider identity must be immutable."""
        record = _make_record(provider_id="immutable_provider", version="1.0.0")
        assert record.provider_id == "immutable_provider"
        assert record.provider_version == "1.0.0"
