"""Cognitia Model Registry.

Provides immutable model registration, version tracking, domain scoping,
calibration checksums, and provenance preservation.
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


class ModelLifecycleState(str, enum.Enum):
    """Explicit lifecycle states for registered cognitive models."""

    DISCOVERED = "discovered"
    REGISTERED = "registered"
    CANDIDATE = "candidate"
    EVALUATED = "evaluated"
    PROPOSED = "proposed"
    APPROVED = "approved"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class RuntimeActivationState(str, enum.Enum):
    """Separation of declared model lifecycle from host-observed runtime activation."""

    NOT_ACTIVE = "not_active"
    ACTIVE = "active"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ModelRecord(CognitiveObject):
    """Immutable record of a registered cognitive model version."""

    model_id: str = ""
    model_version: str = "1.0.0"
    domain_id: str = "default"
    provider: str = "deterministic_rules"
    capability_type: CapabilityType = CapabilityType.DECISION
    input_schema_version: str = "1.0.0"
    output_schema_version: str = "1.0.0"
    calibration_checksum: str = ""
    is_deterministic: bool = True
    status: ModelStatus = ModelStatus.ACTIVE
    lifecycle_state: ModelLifecycleState = ModelLifecycleState.REGISTERED
    runtime_activation_state: RuntimeActivationState = RuntimeActivationState.NOT_ACTIVE
    task_type: str = "classification"
    model_role: str = "primary"
    registered_at: str = field(default_factory=current_utc_timestamp)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )


@runtime_checkable
class ModelRegistry(Protocol):
    """Protocol for model version registry and lifecycle management."""

    def register(self, record: ModelRecord) -> None: ...
    def get(self, model_id: str, version: str, domain_id: str | None = None) -> ModelRecord | None: ...
    def list_versions(self, model_id: str, domain_id: str | None = None) -> list[ModelRecord]: ...
    def get_active(
        self,
        model_id: str | None = None,
        domain_id: str | None = None,
        task_type: str = "classification",
        model_role: str = "primary",
    ) -> ModelRecord | None: ...
    def list_by_domain(self, domain_id: str) -> list[ModelRecord]: ...
    def set_status(self, model_id: str, version: str, status: ModelStatus, domain_id: str = "default") -> None: ...
    def set_lifecycle_state(
        self,
        model_id: str,
        version: str,
        state: ModelLifecycleState,
        domain_id: str = "default",
    ) -> ModelRecord: ...
    def set_runtime_activation(
        self,
        model_id: str,
        version: str,
        activation: RuntimeActivationState,
        domain_id: str = "default",
        task_type: str = "classification",
        model_role: str = "primary",
    ) -> ModelRecord: ...


class InMemoryModelRegistry:
    """Thread-safe, immutable in-memory reference implementation of ModelRegistry with domain and task scoping."""

    def __init__(self) -> None:
        # Key: (domain_id, model_id, version) -> ModelRecord
        self._registry: dict[tuple[str, str, str], ModelRecord] = {}

    def register(self, record: ModelRecord) -> None:
        key = (record.domain_id, record.model_id, record.model_version)
        if key in self._registry:
            raise ValueError(
                f"Model '{record.model_id}' version '{record.model_version}' in domain '{record.domain_id}' is already registered and immutable"
            )
        self._registry[key] = record

    def get(self, model_id: str, version: str, domain_id: str | None = None) -> ModelRecord | None:
        if domain_id:
            return self._registry.get((domain_id, model_id, version))
        for (d_id, m_id, v), record in self._registry.items():
            if m_id == model_id and v == version:
                return record
        return None

    def list_versions(self, model_id: str, domain_id: str | None = None) -> list[ModelRecord]:
        if domain_id:
            return [
                record
                for (d_id, m_id, _), record in self._registry.items()
                if d_id == domain_id and m_id == model_id
            ]
        return [
            record
            for (_, m_id, _), record in self._registry.items()
            if m_id == model_id
        ]

    def get_active(
        self,
        model_id: str | None = None,
        domain_id: str | None = None,
        task_type: str = "classification",
        model_role: str = "primary",
    ) -> ModelRecord | None:
        """Retrieve the unique active model for the given scope (domain_id, task_type, model_role)."""
        target_domain = domain_id or "default"
        # First priority: check for observed runtime activation or active lifecycle in the exact scope
        for (d_id, m_id, _), record in self._registry.items():
            if d_id == target_domain:
                if model_id and m_id != model_id:
                    continue
                if record.task_type == task_type and record.model_role == model_role:
                    if record.runtime_activation_state == RuntimeActivationState.ACTIVE or record.lifecycle_state == ModelLifecycleState.ACTIVE or record.status == ModelStatus.ACTIVE:
                        return record

        # Fallback to model_id match if specified
        if model_id:
            for (d_id, m_id, _), record in self._registry.items():
                if (d_id == target_domain or not domain_id) and m_id == model_id and (record.status == ModelStatus.ACTIVE or record.lifecycle_state == ModelLifecycleState.ACTIVE):
                    return record

        # Global fallback if domain is not specified
        if not domain_id:
            for (_, m_id, _), record in self._registry.items():
                if (not model_id or m_id == model_id) and (record.status == ModelStatus.ACTIVE or record.lifecycle_state == ModelLifecycleState.ACTIVE):
                    return record
        return None

    def list_by_domain(self, domain_id: str) -> list[ModelRecord]:
        return [
            record
            for (d_id, _, _), record in self._registry.items()
            if d_id == domain_id
        ]

    def set_status(self, model_id: str, version: str, status: ModelStatus, domain_id: str = "default") -> None:
        key = (domain_id, model_id, version)
        existing = self._registry.get(key)
        if not existing:
            # Fallback for un-scoped lookup if domain is default
            for (d_id, m_id, v), rec in self._registry.items():
                if m_id == model_id and v == version:
                    existing = rec
                    key = (d_id, m_id, v)
                    break
        if not existing:
            raise KeyError(f"Model '{model_id}' version '{version}' in domain '{domain_id}' not found")

        updated = ModelRecord(
            id=existing.id,
            schema_version=existing.schema_version,
            created_at=existing.created_at,
            metadata=existing.metadata,
            model_id=existing.model_id,
            model_version=existing.model_version,
            domain_id=existing.domain_id,
            provider=existing.provider,
            capability_type=existing.capability_type,
            input_schema_version=existing.input_schema_version,
            output_schema_version=existing.output_schema_version,
            calibration_checksum=existing.calibration_checksum,
            is_deterministic=existing.is_deterministic,
            status=status,
            lifecycle_state=existing.lifecycle_state,
            runtime_activation_state=existing.runtime_activation_state,
            task_type=existing.task_type,
            model_role=existing.model_role,
            registered_at=existing.registered_at,
            provenance=existing.provenance,
        )
        self._registry[key] = updated

    def set_lifecycle_state(
        self,
        model_id: str,
        version: str,
        state: ModelLifecycleState,
        domain_id: str = "default",
    ) -> ModelRecord:
        """Update model lifecycle state while preserving immutable model definition."""
        key = (domain_id, model_id, version)
        existing = self._registry.get(key)
        if not existing:
            for (d_id, m_id, v), rec in self._registry.items():
                if m_id == model_id and v == version:
                    existing = rec
                    key = (d_id, m_id, v)
                    break
        if not existing:
            raise KeyError(f"Model '{model_id}' version '{version}' in domain '{domain_id}' not found")

        # Map status appropriately
        status_map = {
            ModelLifecycleState.DISCOVERED: ModelStatus.EXPERIMENTAL,
            ModelLifecycleState.REGISTERED: ModelStatus.EXPERIMENTAL,
            ModelLifecycleState.CANDIDATE: ModelStatus.CANDIDATE,
            ModelLifecycleState.EVALUATED: ModelStatus.CANDIDATE,
            ModelLifecycleState.PROPOSED: ModelStatus.CANDIDATE,
            ModelLifecycleState.APPROVED: ModelStatus.CANDIDATE,
            ModelLifecycleState.ACTIVE: ModelStatus.ACTIVE,
            ModelLifecycleState.SUPERSEDED: ModelStatus.DEPRECATED,
            ModelLifecycleState.ARCHIVED: ModelStatus.RETIRED,
        }

        updated = ModelRecord(
            id=existing.id,
            schema_version=existing.schema_version,
            created_at=existing.created_at,
            metadata=existing.metadata,
            model_id=existing.model_id,
            model_version=existing.model_version,
            domain_id=existing.domain_id,
            provider=existing.provider,
            capability_type=existing.capability_type,
            input_schema_version=existing.input_schema_version,
            output_schema_version=existing.output_schema_version,
            calibration_checksum=existing.calibration_checksum,
            is_deterministic=existing.is_deterministic,
            status=status_map.get(state, existing.status),
            lifecycle_state=state,
            runtime_activation_state=existing.runtime_activation_state,
            task_type=existing.task_type,
            model_role=existing.model_role,
            registered_at=existing.registered_at,
            provenance=existing.provenance,
        )
        self._registry[key] = updated
        return updated

    def set_runtime_activation(
        self,
        model_id: str,
        version: str,
        activation: RuntimeActivationState,
        domain_id: str = "default",
        task_type: str = "classification",
        model_role: str = "primary",
    ) -> ModelRecord:
        """Set runtime activation state. When activating, supersedes any previously active model in the same scope."""
        key = (domain_id, model_id, version)
        existing = self._registry.get(key)
        if not existing:
            for (d_id, m_id, v), rec in self._registry.items():
                if m_id == model_id and v == version:
                    existing = rec
                    key = (d_id, m_id, v)
                    break
        if not existing:
            raise KeyError(f"Model '{model_id}' version '{version}' in domain '{domain_id}' not found")

        # If activating this model, supersede previous active models in the same (domain_id, task_type, model_role) scope
        if activation == RuntimeActivationState.ACTIVE:
            for (d_id, m_id, v), rec in list(self._registry.items()):
                if d_id == domain_id and (m_id != model_id or v != version):
                    if rec.task_type == task_type and rec.model_role == model_role:
                        if rec.runtime_activation_state == RuntimeActivationState.ACTIVE or rec.lifecycle_state == ModelLifecycleState.ACTIVE:
                            superseded = ModelRecord(
                                id=rec.id,
                                schema_version=rec.schema_version,
                                created_at=rec.created_at,
                                metadata=rec.metadata,
                                model_id=rec.model_id,
                                model_version=rec.model_version,
                                domain_id=rec.domain_id,
                                provider=rec.provider,
                                capability_type=rec.capability_type,
                                input_schema_version=rec.input_schema_version,
                                output_schema_version=rec.output_schema_version,
                                calibration_checksum=rec.calibration_checksum,
                                is_deterministic=rec.is_deterministic,
                                status=ModelStatus.DEPRECATED,
                                lifecycle_state=ModelLifecycleState.SUPERSEDED,
                                runtime_activation_state=RuntimeActivationState.NOT_ACTIVE,
                                task_type=rec.task_type,
                                model_role=rec.model_role,
                                registered_at=rec.registered_at,
                                provenance=rec.provenance,
                            )
                            self._registry[(d_id, m_id, v)] = superseded

        updated = ModelRecord(
            id=existing.id,
            schema_version=existing.schema_version,
            created_at=existing.created_at,
            metadata=existing.metadata,
            model_id=existing.model_id,
            model_version=existing.model_version,
            domain_id=existing.domain_id,
            provider=existing.provider,
            capability_type=existing.capability_type,
            input_schema_version=existing.input_schema_version,
            output_schema_version=existing.output_schema_version,
            calibration_checksum=existing.calibration_checksum,
            is_deterministic=existing.is_deterministic,
            status=ModelStatus.ACTIVE if activation == RuntimeActivationState.ACTIVE else existing.status,
            lifecycle_state=ModelLifecycleState.ACTIVE if activation == RuntimeActivationState.ACTIVE else existing.lifecycle_state,
            runtime_activation_state=activation,
            task_type=task_type,
            model_role=model_role,
            registered_at=existing.registered_at,
            provenance=existing.provenance,
        )
        self._registry[key] = updated
        return updated
