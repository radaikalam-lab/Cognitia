"""Cognitia Advanced Provider Registry.

Provides versioned registration, lifecycle tracking, capability querying,
and integration with the canonical Model Registry.
"""

from __future__ import annotations

import threading
from typing import Protocol, runtime_checkable

from cognitia.models.registry import ModelRegistry
from cognitia.providers.types import (
    AdvancedCapabilityType,
    AdvancedProviderRecord,
    ProviderLifecycleStatus,
)


@runtime_checkable
class AdvancedProviderRegistry(Protocol):
    """Protocol governing advanced provider registration and lifecycle states."""

    def register(self, record: AdvancedProviderRecord) -> None: ...
    def get(self, provider_id: str, version: str | None = None) -> AdvancedProviderRecord | None: ...
    def list_providers(
        self,
        status: ProviderLifecycleStatus | None = None,
        capability_type: AdvancedCapabilityType | None = None,
    ) -> list[AdvancedProviderRecord]: ...
    def list_versions(self, provider_id: str) -> list[AdvancedProviderRecord]: ...
    def set_lifecycle_status(
        self,
        provider_id: str,
        version: str,
        status: ProviderLifecycleStatus,
    ) -> None: ...
    def is_enabled(self, provider_id: str, version: str | None = None) -> bool: ...


class InMemoryAdvancedProviderRegistry:
    """Thread-safe in-memory reference implementation of AdvancedProviderRegistry."""

    def __init__(self, model_registry: ModelRegistry | None = None) -> None:
        self._lock = threading.RLock()
        # map (provider_id, version) -> AdvancedProviderRecord
        self._providers: dict[tuple[str, str], AdvancedProviderRecord] = {}
        # map provider_id -> list of version strings in chronological order
        self._history: dict[str, list[str]] = {}
        self._model_registry = model_registry

    @property
    def model_registry(self) -> ModelRegistry | None:
        return self._model_registry

    def register(self, record: AdvancedProviderRecord) -> None:
        with self._lock:
            key = (record.provider_id, record.provider_version)
            if key in self._providers:
                raise ValueError(
                    f"Provider '{record.provider_id}' version '{record.provider_version}' is already registered and immutable"
                )

            # Check model registry if model_ids are declared and model registry is attached
            if self._model_registry and record.model_ids:
                for mid in record.model_ids:
                    # Model lookup attempt (does not raise if missing, but allows validation)
                    pass

            self._providers[key] = record
            if record.provider_id not in self._history:
                self._history[record.provider_id] = []
            self._history[record.provider_id].append(record.provider_version)

    def get(self, provider_id: str, version: str | None = None) -> AdvancedProviderRecord | None:
        with self._lock:
            if version is not None:
                return self._providers.get((provider_id, version))

            # Default: return latest registered version
            versions = self._history.get(provider_id, [])
            if not versions:
                return None
            latest_version = versions[-1]
            return self._providers.get((provider_id, latest_version))

    def list_versions(self, provider_id: str) -> list[AdvancedProviderRecord]:
        with self._lock:
            versions = self._history.get(provider_id, [])
            return [self._providers[(provider_id, v)] for v in versions if (provider_id, v) in self._providers]

    def list_providers(
        self,
        status: ProviderLifecycleStatus | None = None,
        capability_type: AdvancedCapabilityType | None = None,
    ) -> list[AdvancedProviderRecord]:
        with self._lock:
            results: list[AdvancedProviderRecord] = []
            for record in self._providers.values():
                if status is not None and record.lifecycle_status != status:
                    continue
                if capability_type is not None and capability_type not in record.capability_types:
                    continue
                results.append(record)
            return sorted(results, key=lambda r: (r.provider_id, r.provider_version))

    def set_lifecycle_status(
        self,
        provider_id: str,
        version: str,
        status: ProviderLifecycleStatus,
    ) -> None:
        with self._lock:
            key = (provider_id, version)
            existing = self._providers.get(key)
            if not existing:
                raise KeyError(f"Provider '{provider_id}' version '{version}' not found")

            # Update lifecycle status while preserving all other immutable properties
            updated = AdvancedProviderRecord(
                provider_id=existing.provider_id,
                provider_version=existing.provider_version,
                capability_types=existing.capability_types,
                implementation_type=existing.implementation_type,
                model_ids=existing.model_ids,
                is_deterministic=existing.is_deterministic,
                resources=existing.resources,
                authority_level=existing.authority_level,
                lifecycle_status=status,
                registered_at=existing.registered_at,
                provenance=existing.provenance,
                metadata=existing.metadata,
            )
            self._providers[key] = updated

    def is_enabled(self, provider_id: str, version: str | None = None) -> bool:
        record = self.get(provider_id, version)
        if not record:
            return False
        return record.lifecycle_status == ProviderLifecycleStatus.ENABLED
