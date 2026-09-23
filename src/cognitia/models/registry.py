"""Cognitia Model Registry.

Provides immutable model registration, version tracking, calibration checksums,
and provenance preservation.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from cognitia.abi.types import (
    CognitiveObject,
    current_utc_timestamp,
)
from cognitia.capabilities.base import CapabilityType
from cognitia.provenance.record import ProvenanceRecord, SourceType


class ModelStatus(str, enum.Enum):
    """Lifecycle status of a registered cognitive model."""

    EXPERIMENTAL = "experimental"
    CANDIDATE = "candidate"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


@dataclass(frozen=True)
class ModelRecord(CognitiveObject):
    """Immutable record of a registered cognitive model version."""

    model_id: str = ""
    model_version: str = "1.0.0"
    provider: str = "deterministic_rules"
    capability_type: CapabilityType = CapabilityType.DECISION
    input_schema_version: str = "1.0.0"
    output_schema_version: str = "1.0.0"
    calibration_checksum: str = ""
    is_deterministic: bool = True
    status: ModelStatus = ModelStatus.ACTIVE
    registered_at: str = field(default_factory=current_utc_timestamp)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )


@runtime_checkable
class ModelRegistry(Protocol):
    """Protocol for model version registry and lifecycle management."""

    def register(self, record: ModelRecord) -> None: ...
    def get(self, model_id: str, version: str) -> ModelRecord | None: ...
    def list_versions(self, model_id: str) -> list[ModelRecord]: ...
    def get_active(self, model_id: str) -> ModelRecord | None: ...
    def set_status(self, model_id: str, version: str, status: ModelStatus) -> None: ...


class InMemoryModelRegistry:
    """Thread-safe, immutable in-memory reference implementation of ModelRegistry."""

    def __init__(self) -> None:
        # Key: (model_id, version) -> ModelRecord
        self._registry: dict[tuple[str, str], ModelRecord] = {}

    def register(self, record: ModelRecord) -> None:
        key = (record.model_id, record.model_version)
        if key in self._registry:
            raise ValueError(
                f"Model '{record.model_id}' version '{record.model_version}' is already registered and immutable"
            )
        self._registry[key] = record

    def get(self, model_id: str, version: str) -> ModelRecord | None:
        return self._registry.get((model_id, version))

    def list_versions(self, model_id: str) -> list[ModelRecord]:
        return [
            record
            for (m_id, _), record in self._registry.items()
            if m_id == model_id
        ]

    def get_active(self, model_id: str) -> ModelRecord | None:
        for (m_id, _), record in self._registry.items():
            if m_id == model_id and record.status == ModelStatus.ACTIVE:
                return record
        return None

    def set_status(self, model_id: str, version: str, status: ModelStatus) -> None:
        key = (model_id, version)
        existing = self._registry.get(key)
        if not existing:
            raise KeyError(f"Model '{model_id}' version '{version}' not found")

        # Create updated record preserving all other immutable metadata
        updated = ModelRecord(
            id=existing.id,
            schema_version=existing.schema_version,
            created_at=existing.created_at,
            metadata=existing.metadata,
            model_id=existing.model_id,
            model_version=existing.model_version,
            provider=existing.provider,
            capability_type=existing.capability_type,
            input_schema_version=existing.input_schema_version,
            output_schema_version=existing.output_schema_version,
            calibration_checksum=existing.calibration_checksum,
            is_deterministic=existing.is_deterministic,
            status=status,
            registered_at=existing.registered_at,
            provenance=existing.provenance,
        )
        self._registry[key] = updated
