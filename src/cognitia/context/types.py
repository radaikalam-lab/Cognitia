"""Cognitia Cognitive Context Data Types and Schemas.

Defines domain-neutral structures for assembled cognitive contexts,
temporal relationships, entity neighbourhoods, state reconstructions, event sequences,
recurrence patterns, deterministic aggregates, contextual deviations, cross-source correlations,
provenance neighbourhoods, epistemic tensions, conflicts, and context compression.
All context structures use deeply immutable primitives (tuples and frozen dataclasses).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Mapping

from cognitia.abi.types import (
    CognitiveObject,
    SCHEMA_VERSION_V1,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.epistemic.types import EpistemicStatus
from cognitia.provenance.record import ProvenanceRecord, SourceType


class RelevanceReason(str, enum.Enum):
    """Enumeration of why an item was selected into Cognitive Context."""

    REFERENCE_OBSERVATION = "reference_observation"
    SUBJECT_MATCH = "subject_match"
    EPISODE_MATCH = "episode_match"
    TEMPORAL_MATCH = "temporal_match"
    RULE_MATCH = "rule_match"
    MEMORY_MATCH = "memory_match"
    EXPLICIT_QUERY = "explicit_query"
    SOURCE_MATCH = "source_match"


# --- 1. Temporal Neighbourhood Types ---

class TemporalRelationType(str, enum.Enum):
    """Enumeration of temporal relations relative to a reference observation."""

    BEFORE = "before"
    AFTER = "after"
    WITHIN_WINDOW = "within_window"
    SAME_TIME_BUCKET = "same_time_bucket"
    CONCURRENT = "concurrent"


@dataclass(frozen=True)
class TemporalRelation:
    """Explicit deterministic temporal relationship between entities."""

    entity_id: str
    relation_type: TemporalRelationType
    delta_seconds: float
    timestamp: str


@dataclass(frozen=True)
class TemporalContext:
    """Temporal neighborhood information surrounding a reference observation.
    
    INVARIANT: Temporal proximity alone does NOT imply causal relationship.
    """

    reference_timestamp: str
    window_seconds_before: float | None = None
    window_seconds_after: float | None = None
    preceding_observation_ids: tuple[str, ...] = ()
    succeeding_observation_ids: tuple[str, ...] = ()
    time_deltas: tuple[tuple[str, float], ...] = ()  # immutable sequence of (entity_id, delta_seconds)
    relations: tuple[TemporalRelation, ...] = ()

    @property
    def deltas_dict(self) -> dict[str, float]:
        """Convenience dictionary mapping entity_id to time delta in seconds."""
        return dict(self.time_deltas)


# --- 2. Entity Neighbourhood Types ---

class EntityRelationType(str, enum.Enum):
    """Structural correlation between entities in context."""

    SAME_SUBJECT = "same_subject"
    SAME_EPISODE = "same_episode"
    SAME_SOURCE = "same_source"
    SHARED_PARENT = "shared_parent"
    SHARED_PROVENANCE = "shared_provenance"
    EXPLICIT_RELATIONSHIP = "explicit_relationship"


@dataclass(frozen=True)
class EntityRelation:
    """Provider-neutral structural relationship between entities."""

    entity_id: str
    target_id: str
    relation_type: EntityRelationType
    provenance_id: str | None = None
    metadata: tuple[tuple[str, Any], ...] = ()

    @property
    def metadata_dict(self) -> dict[str, Any]:
        return dict(self.metadata)


# --- 3. State Reconstruction Types ---

@dataclass(frozen=True)
class StateVariable:
    """Reconstructed observable state variable value based strictly on recorded observations."""

    name: str
    latest_value: Any
    previous_value: Any = None
    first_known_value: Any = None
    observed_at: str | None = None
    validity_interval_seconds: float | None = None
    is_unknown: bool = False
    is_conflicted: bool = False


@dataclass(frozen=True)
class StateReconstruction:
    """Reconstructed observable system/environment state surrounding an observation."""

    variables: tuple[StateVariable, ...] = ()
    reconstructed_at: str = ""

    @property
    def variables_dict(self) -> dict[str, Any]:
        """Convenience dictionary mapping variable names to latest known values."""
        return {v.name: v.latest_value for v in self.variables}

    def get_variable(self, name: str) -> StateVariable | None:
        for v in self.variables:
            if v.name == name:
                return v
        return None


# --- 4. Event Sequence Context Types ---

@dataclass(frozen=True)
class SequenceContext:
    """Structural chronological event sequence surrounding an observation."""

    sequence_id: str
    event_ids: tuple[str, ...]
    relative_positions: tuple[tuple[str, int], ...]
    timestamps: tuple[tuple[str, str], ...]
    time_deltas: tuple[tuple[str, float], ...]
    provenance_id: str | None = None

    @property
    def positions_dict(self) -> dict[str, int]:
        return dict(self.relative_positions)


# --- 5. Recurrence Context Types ---

@dataclass(frozen=True)
class RecurrenceContext:
    """Descriptive recurrence patterns over observed historical occurrences."""

    subject_id: str | None
    event_pattern: str
    occurrence_count: int
    window_seconds: float
    intervals_seconds: tuple[float, ...] = ()
    median_interval_seconds: float | None = None
    latest_interval_seconds: float | None = None


# --- 6. Deterministic Aggregate Context Types ---

@dataclass(frozen=True)
class AggregateContext:
    """Descriptive statistical aggregates calculated deterministically over historical metrics."""

    metric: str
    count: int
    min_value: float | None = None
    max_value: float | None = None
    mean_value: float | None = None
    median_value: float | None = None
    range_value: float | None = None
    std_dev: float | None = None
    latest_value: float | None = None
    delta_from_previous: float | None = None
    delta_from_mean: float | None = None


# --- 7. Contextual Deviation Types ---

class DeviationType(str, enum.Enum):
    """Descriptive deviation categorization without diagnostic claims."""

    ABOVE_HISTORICAL_RANGE = "above_historical_range"
    BELOW_HISTORICAL_RANGE = "below_historical_range"
    ABOVE_BASELINE = "above_baseline"
    BELOW_BASELINE = "below_baseline"
    RAPID_CHANGE = "rapid_change"
    UNUSUAL_INTERVAL = "unusual_interval"


@dataclass(frozen=True)
class ContextDeviation:
    """Descriptive contextual deviation indicator relative to historical baseline."""

    metric: str
    current_value: float
    baseline_reference: Any  # scalar float or tuple[float, float]
    deviation_type: DeviationType
    magnitude: float
    provenance_id: str | None = None
    metadata: tuple[tuple[str, Any], ...] = ()

    @property
    def metadata_dict(self) -> dict[str, Any]:
        return dict(self.metadata)


# --- 8. Cross-Source Correlation Types ---

class CorrelationReason(str, enum.Enum):
    """Explicit deterministic reason for cross-source correlation."""

    TEMPORAL_PROXIMITY = "temporal_proximity"
    SHARED_SUBJECT = "shared_subject"
    SHARED_EPISODE = "shared_episode"
    SHARED_SOURCE = "shared_source"
    SHARED_PROVENANCE = "shared_provenance"
    EXPLICIT_RELATIONSHIP = "explicit_relationship"


@dataclass(frozen=True)
class CrossSourceCorrelation:
    """Temporal and structural correlation across multi-source observations."""

    source_a_id: str
    source_b_id: str
    source_a_app: str
    source_b_app: str
    correlation_reason: CorrelationReason
    time_delta_seconds: float
    metadata: tuple[tuple[str, Any], ...] = ()

    @property
    def metadata_dict(self) -> dict[str, Any]:
        return dict(self.metadata)


# --- 9. Provenance Neighbourhood Types ---

@dataclass(frozen=True)
class ProvenanceNeighbourhood:
    """Extended provenance lineage neighbourhood surrounding the current context."""

    root_entity_id: str
    derived_from_ids: tuple[str, ...] = ()
    produced_by_ids: tuple[str, ...] = ()
    transformed_by_ids: tuple[str, ...] = ()
    measured_by_ids: tuple[str, ...] = ()
    validated_by_ids: tuple[str, ...] = ()
    referenced_by_ids: tuple[str, ...] = ()


# --- 10. Epistemic Tension & Conflict Mapping Types ---

@dataclass(frozen=True)
class EpistemicTension:
    """Preserved multi-directional evidence mapping for a cognitive proposition."""

    proposition_id: str
    supporting_evidence_ids: tuple[str, ...] = ()
    refuting_evidence_ids: tuple[str, ...] = ()
    neutral_evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContextConflict:
    """Preserved observational conflict without silent overwrite or premature resolution."""

    object_ids: tuple[str, ...]
    conflict_type: str
    description: str = ""
    timestamp: str = ""
    provenance_id: str | None = None


# --- 11. Context Compression Types ---

@dataclass(frozen=True)
class ContextCompression:
    """Deterministic structural summary of an assembled CognitiveContext."""

    observation_count: int = 0
    timespan_seconds: float = 0.0
    subject_count: int = 0
    source_count: int = 0
    supported_epistemic_count: int = 0
    unresolved_epistemic_count: int = 0
    refuted_epistemic_count: int = 0
    sequence_count: int = 0
    deviation_count: int = 0
    conflict_count: int = 0


# --- Context Item & Query ---

@dataclass(frozen=True)
class ContextItem:
    """Auditable wrapper explaining why a specific entity was included in the context."""

    item_id: str
    item_type: str
    relevance_reason: RelevanceReason
    relevance_score: float = 1.0  # Defined strictly as deterministic context ranking tier
    epistemic_status: EpistemicStatus | None = None
    provenance_id: str | None = None


@dataclass(frozen=True)
class ContextQuery:
    """Specification for assembling a Cognitive Context around an observation."""

    temporal_window_seconds_before: float | None = 3600.0  # default 1 hour before
    temporal_window_seconds_after: float | None = 60.0    # default 1 min after
    include_memory: bool = True
    include_rules: bool = True
    include_epistemics: bool = True
    explicit_subject_id: str | None = None
    scope: str | None = None
    max_related_observations: int = 50
    max_related_experiences: int = 20
    # Phase 3A enrichment switches (default True for rich situational assembly)
    include_state_reconstruction: bool = True
    include_sequences: bool = True
    include_recurrence: bool = True
    include_aggregates: bool = True
    include_deviations: bool = True
    include_correlations: bool = True
    include_provenance_neighbourhood: bool = True
    include_epistemic_tensions: bool = True
    include_conflicts: bool = True
    include_compression: bool = True


@dataclass(frozen=True)
class CognitiveContext(CognitiveObject):
    """Assembled situational cognitive context surrounding a reference observation.
    
    INVARIANTS:
    1. Context is an assembly of relevant references and descriptive structures, NOT a second object store.
    2. Context snapshots are deeply immutable once assembled.
    3. Context does NOT represent truth, conclusion, decision, causality, or action.
    """

    reference_observation_id: str = ""
    reference_subject_id: str | None = None
    temporal_context: TemporalContext = field(
        default_factory=lambda: TemporalContext(reference_timestamp=current_utc_timestamp())
    )
    related_observation_ids: tuple[str, ...] = ()
    related_experience_ids: tuple[str, ...] = ()
    active_rule_ids: tuple[str, ...] = ()
    epistemic_context: tuple[tuple[str, EpistemicStatus], ...] = ()
    context_items: tuple[ContextItem, ...] = ()
    # Phase 3A Enriched Structures
    entity_neighbourhood: tuple[EntityRelation, ...] = ()
    state_reconstruction: StateReconstruction = field(default_factory=StateReconstruction)
    sequences: tuple[SequenceContext, ...] = ()
    recurrence: tuple[RecurrenceContext, ...] = ()
    aggregates: tuple[AggregateContext, ...] = ()
    deviations: tuple[ContextDeviation, ...] = ()
    correlations: tuple[CrossSourceCorrelation, ...] = ()
    provenance_neighbourhood: tuple[ProvenanceNeighbourhood, ...] = ()
    epistemic_tensions: tuple[EpistemicTension, ...] = ()
    conflicts: tuple[ContextConflict, ...] = ()
    compression: ContextCompression | None = None
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.COMPOSITE,
            producer_id="context_assembly_engine",
            is_deterministic=True,
        )
    )

    @property
    def epistemic_map(self) -> dict[str, EpistemicStatus]:
        """Convenience dictionary mapping entity_id to EpistemicStatus."""
        return dict(self.epistemic_context)
