"""Cognitia Cognitive Memory and Consolidation Types.

Defines schemas for Memory Queries, structured Memory Context,
Candidate Learning Artifacts, and Consolidation Results.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from cognitia.abi.types import (
    Action,
    CognitiveObject,
    Decision,
    Observation,
    Outcome,
    SCHEMA_VERSION_V1,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.epistemic.types import (
    Claim,
    EpistemicNode,
    EpistemicStatus,
    Evidence,
    Hypothesis,
)
from cognitia.experience.record import ExperienceRecord
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.reasoning.types import ReasoningTrace


class CandidateType(str, enum.Enum):
    """Categorization of proposed cognitive adaptations."""

    PATTERN = "pattern"
    ASSOCIATION = "association"
    PREDICTION = "prediction"
    HYPOTHESIS = "hypothesis"
    RULE_CANDIDATE = "rule_candidate"
    MODEL_REVISION = "model_revision"
    REPRESENTATION_REVISION = "representation_revision"


class ConsolidationStatus(str, enum.Enum):
    """Status of candidate evaluation in the consolidation pipeline."""

    PENDING = "pending"
    SUPPORTED = "supported"
    REFUTED = "refuted"
    CONSOLIDATED = "consolidated"
    REJECTED = "rejected"


class OperatorLifecycleStatus(str, enum.Enum):
    """Formal lifecycle progression of a plasticity operator."""

    DECLARED = "declared"
    REGISTERED = "registered"
    VALIDATED = "validated"
    AVAILABLE = "available"
    ENABLED = "enabled"
    DISABLED = "disabled"
    SUSPENDED = "suspended"
    RETIRED = "retired"


@dataclass(frozen=True)
class MemoryQuery:
    """Domain-neutral query dimensions for selective memory retrieval."""

    agent_id: str | None = None
    environment_id: str | None = None
    episode_id: str | None = None
    source_application: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    object_types: list[str] | None = None
    epistemic_status: EpistemicStatus | None = None
    model_version: str | None = None
    limit: int | None = None
    metadata_filters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MemoryContext(CognitiveObject):
    """Structured context assembled from persisted history for cognitive processing."""

    query: MemoryQuery = field(default_factory=MemoryQuery)
    experiences: list[ExperienceRecord] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    hypotheses: list[Hypothesis] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    reasoning_traces: list[ReasoningTrace] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    outcomes: list[Outcome] = field(default_factory=list)
    epistemic_states: dict[str, EpistemicStatus] = field(default_factory=dict)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.COMPOSITE)
    )


@dataclass(frozen=True)
class CandidateLearningArtifact(CognitiveObject):
    """Proposal for cognitive adaptation produced by a Plasticity Operator."""

    candidate_type: CandidateType = CandidateType.PATTERN
    source_memory_ids: list[str] = field(default_factory=list)
    proposed_change: dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    confidence: float = 1.0
    provider: str = "plasticity_operator"
    model_version: str | None = None
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )


@dataclass(frozen=True)
class OperatorRecord(CognitiveObject):
    """Immutable record capturing identity, version, type, and lifecycle of a plasticity operator."""

    operator_id: str = ""
    operator_version: str = "1.0.0"
    operator_type: str = "pattern_discovery"
    is_deterministic: bool = True
    lifecycle_status: OperatorLifecycleStatus = OperatorLifecycleStatus.DECLARED
    registered_at: str = field(default_factory=current_utc_timestamp)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )


@dataclass(frozen=True)
class ConsolidationResult(CognitiveObject):
    """Result of evaluating and preparing a candidate artifact for model consolidation."""

    candidate_id: str = ""
    status: ConsolidationStatus = ConsolidationStatus.PENDING
    epistemic_justification: str = ""
    target_model_id: str = ""
    proposed_version: str = "1.0.0"
    calibration_checksum: str = ""
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )
