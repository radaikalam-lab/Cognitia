"""Cognitia Advanced Reasoning Provider Types and Data Schemas.

Defines canonical vocabulary for advanced capability classes, provider lifecycle states,
immutable provider records, resource requirement declarations, reasoning requests,
and strongly typed CandidateReasoningArtifact envelopes.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from cognitia.abi.types import (
    CognitiveObject,
    SCHEMA_VERSION_V1,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.epistemic.types import EpistemicStatus
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.reasoning.types import ReasoningMode, ReasoningResidual


class AdvancedCapabilityType(str, enum.Enum):
    """Canonical capability classes supported by the Advanced Provider Layer."""

    LLM_REASONING = "llm_reasoning"
    TINYML_REASONING = "tinyml_reasoning"
    HYPOTHESIS_GENERATION = "hypothesis_generation"
    CAUSAL_INFERENCE = "causal_inference"
    SEMANTIC_GRAPH = "semantic_graph"
    VECTOR_RETRIEVAL = "vector_retrieval"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    SELF_MODIFYING_REASONING = "self_modifying_reasoning"
    DIRECTIONAL_PROGRAMMING = "directional_programming"


class ProviderLifecycleStatus(str, enum.Enum):
    """Formal lifecycle progression of an advanced provider."""

    DECLARED = "declared"
    REGISTERED = "registered"
    VALIDATED = "validated"
    AVAILABLE = "available"
    ENABLED = "enabled"
    DISABLED = "disabled"
    SUSPENDED = "suspended"
    RETIRED = "retired"


class ProposalLifecycleStatus(str, enum.Enum):
    """Governance lifecycle for candidate structures and policies produced by providers."""

    PROPOSED = "proposed"
    VALIDATED = "validated"
    APPROVED = "approved"
    ACTIVATABLE = "activatable"
    ACTIVATED = "activated"
    REJECTED = "rejected"
    RETIRED = "retired"


@dataclass(frozen=True)
class ResourceRequirements:
    """Explicit declaration of computational and environment dependencies."""

    requires_network: bool = False
    requires_gpu: bool = False
    requires_external_runtime: bool = False
    requires_filesystem: bool = False
    memory_bytes_limit: int | None = None
    sandbox_type: str = "standard_in_process"


@dataclass(frozen=True)
class AdvancedProviderRecord(CognitiveObject):
    """Immutable record capturing identity, version, capabilities, and lifecycle of a provider."""

    provider_id: str = ""
    provider_version: str = "1.0.0"
    capability_types: tuple[AdvancedCapabilityType, ...] = ()
    implementation_type: str = "mock"
    model_ids: tuple[str, ...] = ()
    is_deterministic: bool = True
    resources: ResourceRequirements = field(default_factory=ResourceRequirements)
    authority_level: str = "advisory_only"
    lifecycle_status: ProviderLifecycleStatus = ProviderLifecycleStatus.DECLARED
    registered_at: str = field(default_factory=current_utc_timestamp)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )

    def __init__(
        self,
        provider_id: str,
        provider_version: str = "1.0.0",
        capability_types: Sequence[AdvancedCapabilityType] = (),
        implementation_type: str = "mock",
        model_ids: Sequence[str] = (),
        is_deterministic: bool = True,
        resources: ResourceRequirements | None = None,
        authority_level: str = "advisory_only",
        lifecycle_status: ProviderLifecycleStatus = ProviderLifecycleStatus.DECLARED,
        registered_at: str | None = None,
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
    ) -> None:
        object.__setattr__(self, "id", f"provider:{provider_id}:{provider_version}")
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", registered_at or current_utc_timestamp())
        object.__setattr__(self, "provider_id", str(provider_id))
        object.__setattr__(self, "provider_version", str(provider_version))
        object.__setattr__(self, "capability_types", tuple(capability_types))
        object.__setattr__(self, "implementation_type", str(implementation_type))
        object.__setattr__(self, "model_ids", tuple(model_ids))
        object.__setattr__(self, "is_deterministic", bool(is_deterministic))
        object.__setattr__(self, "resources", resources or ResourceRequirements())
        object.__setattr__(self, "authority_level", str(authority_level))
        object.__setattr__(self, "lifecycle_status", lifecycle_status)
        object.__setattr__(self, "registered_at", registered_at or current_utc_timestamp())

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id=f"provider_registry:{provider_id}:{provider_version}",
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)

        if metadata is None:
            meta_dict: dict[str, Any] = {}
        elif isinstance(metadata, Mapping):
            meta_dict = dict(metadata)
        else:
            meta_dict = dict(metadata)
        object.__setattr__(self, "metadata", meta_dict)


@dataclass(frozen=True)
class ReasoningRequest:
    """Minimal immutable request envelope for invoking an advanced reasoning provider."""

    request_id: str = field(default_factory=generate_entity_id)
    input_snapshot_id: str = ""
    reasoning_mode: ReasoningMode = ReasoningMode.DEDUCTION
    requested_capability: AdvancedCapabilityType = AdvancedCapabilityType.LLM_REASONING
    configuration: tuple[tuple[str, Any], ...] = ()
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.REASONING_ENGINE)
    )

    def __init__(
        self,
        input_snapshot_id: str,
        reasoning_mode: ReasoningMode = ReasoningMode.DEDUCTION,
        requested_capability: AdvancedCapabilityType = AdvancedCapabilityType.LLM_REASONING,
        configuration: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
        provenance: ProvenanceRecord | None = None,
    ) -> None:
        object.__setattr__(self, "request_id", generate_entity_id())
        object.__setattr__(self, "input_snapshot_id", str(input_snapshot_id))
        object.__setattr__(self, "reasoning_mode", reasoning_mode)
        object.__setattr__(self, "requested_capability", requested_capability)

        if configuration is None:
            config_tuple: tuple[tuple[str, Any], ...] = ()
        elif isinstance(configuration, Mapping):
            config_tuple = tuple(configuration.items())
        else:
            config_tuple = tuple(configuration)
        object.__setattr__(self, "configuration", config_tuple)

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE,
            producer_id="reasoning_request_builder",
            parent_ids=[input_snapshot_id],
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)

    @property
    def configuration_dict(self) -> dict[str, Any]:
        return dict(self.configuration)


@dataclass(frozen=True)
class CandidateReasoningArtifact(CognitiveObject):
    """Strongly typed universal envelope for outputs emitted by advanced providers.
    
    INVARIANTS:
    1. Newly emitted candidate artifacts MUST start with epistemic_status = UNRESOLVED.
    2. Candidate artifacts are advisory proposals; they never represent physical truth or authority.
    3. Changing a candidate into an active structure requires explicit epistemic evaluation and governance approval.
    """

    artifact_id: str = field(default_factory=generate_entity_id)
    artifact_type: str = "candidate_reasoning_artifact"
    provider_id: str = ""
    provider_version: str = "1.0.0"
    model_id: str | None = None
    model_version: str | None = None
    input_snapshot_id: str = ""
    payload: tuple[tuple[str, Any], ...] = ()
    assumptions: tuple[str, ...] = ()
    residuals: tuple[ReasoningResidual, ...] = ()
    epistemic_status: EpistemicStatus = EpistemicStatus.UNRESOLVED  # Invariant 10
    proposal_status: ProposalLifecycleStatus = ProposalLifecycleStatus.PROPOSED
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.REASONING_ENGINE)
    )

    def __init__(
        self,
        provider_id: str,
        input_snapshot_id: str,
        artifact_id: str | None = None,
        artifact_type: str = "candidate_reasoning_artifact",
        provider_version: str = "1.0.0",
        model_id: str | None = None,
        model_version: str | None = None,
        payload: Mapping[str, Any] | Sequence[tuple[str, Any]] | None = None,
        assumptions: Sequence[str] = (),
        residuals: Sequence[ReasoningResidual] = (),
        epistemic_status: EpistemicStatus = EpistemicStatus.UNRESOLVED,
        proposal_status: ProposalLifecycleStatus = ProposalLifecycleStatus.PROPOSED,
        provenance: ProvenanceRecord | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        art_id = artifact_id or generate_entity_id()
        object.__setattr__(self, "id", art_id)
        object.__setattr__(self, "artifact_id", art_id)
        object.__setattr__(self, "schema_version", SCHEMA_VERSION_V1)
        object.__setattr__(self, "created_at", current_utc_timestamp())
        object.__setattr__(self, "artifact_type", str(artifact_type))
        object.__setattr__(self, "provider_id", str(provider_id))
        object.__setattr__(self, "provider_version", str(provider_version))
        object.__setattr__(self, "model_id", str(model_id) if model_id else None)
        object.__setattr__(self, "model_version", str(model_version) if model_version else None)
        object.__setattr__(self, "input_snapshot_id", str(input_snapshot_id))

        if payload is None:
            payload_tuple: tuple[tuple[str, Any], ...] = ()
        elif isinstance(payload, Mapping):
            payload_tuple = tuple(payload.items())
        else:
            payload_tuple = tuple(payload)
        object.__setattr__(self, "payload", payload_tuple)
        object.__setattr__(self, "assumptions", tuple(assumptions))
        object.__setattr__(self, "residuals", tuple(residuals))
        object.__setattr__(self, "epistemic_status", epistemic_status)
        object.__setattr__(self, "proposal_status", proposal_status)

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE,
            producer_id=f"provider:{provider_id}:{provider_version}",
            parent_ids=[input_snapshot_id],
            is_deterministic=True,
        )
        object.__setattr__(self, "provenance", prov)
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @property
    def payload_dict(self) -> dict[str, Any]:
        return dict(self.payload)
