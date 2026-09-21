"""Cognitia Cognitive Recall Module.

Provides deterministic, offline, read-only cognitive recall over historical
experience and cognitive objects. Recall is provider-independent, snapshot-safe,
and explicitly NOT equivalent to attention, reasoning, learning, truth, or causality.

Phase 5 introduces the following abstractions:
- RecallQuery: query dimensions mirroring MemoryQuery but scoped to recall
- RecallCandidate: wrapper around a recalled cognitive object with scoring metadata
- RecallScore: deterministic composite score with normalized weights
- RecallResult: top-k recall output with provenance trace
- RecallTrace: immutable record of recall execution parameters and outcomes
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from cognitia.abi.types import CognitiveObject, generate_entity_id, current_utc_timestamp
from cognitia.context.types import RelevanceReason
from cognitia.epistemic.types import EpistemicStatus
from cognitia.provenance.record import ProvenanceRecord, SourceType


class RecallObjectType(str, enum.Enum):
    """Object categories eligible for cognitive recall."""

    EXPERIENCE_RECORD = "experience_record"
    OBSERVATION = "observation"
    EVIDENCE = "evidence"
    HYPOTHESIS = "hypothesis"
    CLAIM = "claim"
    REASONING_TRACE = "reasoning_trace"
    DECISION = "decision"
    OUTCOME = "outcome"
    COGNITIVE_OBJECT = "cognitive_object"


class ScoreComponentType(str, enum.Enum):
    """Deterministic component dimensions contributing to a RecallScore."""

    TEMPORAL_RECENCY = "temporal_recency"
    EPISODE_MATCH = "episode_match"
    AGENT_MATCH = "agent_match"
    ENVIRONMENT_MATCH = "environment_match"
    EPISTEMIC_STABILITY = "epistemic_stability"
    SOURCE_APPLICATION_MATCH = "source_application_match"
    METADATA_MATCH = "metadata_match"


@dataclass(frozen=True)
class ScoreComponent:
    """Single deterministic contribution to a RecallScore."""

    component_type: ScoreComponentType
    raw_value: float
    weight: float
    weighted_value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError("Score component weight must be between 0.0 and 1.0")
        if self.weighted_value < 0.0:
            raise ValueError("Score component weighted value must be non-negative")


@dataclass(frozen=True)
class RecallScore:
    """Deterministic composite score for a recalled cognitive object.

    INVARIANT: final_score is computed deterministically from weighted components
    and always lies in [0.0, 1.0].
    """

    final_score: float
    components: tuple[ScoreComponent, ...] = field(default_factory=tuple)
    max_possible_score: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.final_score <= float(self.max_possible_score):
            raise ValueError(
                f"RecallScore final_score {self.final_score} is outside valid range "
                f"[0.0, {self.max_possible_score}]"
            )
        if self.max_possible_score <= 0.0:
            raise ValueError("RecallScore max_possible_score must be positive")

    @property
    def normalized_score(self) -> float:
        """Score normalized to [0.0, 1.0]."""
        if self.max_possible_score == 0.0:
            return 0.0
        return self.final_score / self.max_possible_score


@dataclass(frozen=True)
class RecallQuery:
    """Domain-neutral query dimensions for cognitive recall.

    Mirrors MemoryQuery dimensions but is explicitly scoped to recall semantics
    and does not carry epistemic evaluation intent.
    """

    query_id: str = field(default_factory=generate_entity_id)
    agent_id: str | None = None
    environment_id: str | None = None
    episode_id: str | None = None
    source_application: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    object_types: tuple[RecallObjectType, ...] = field(default_factory=tuple)
    epistemic_statuses: tuple[EpistemicStatus, ...] = field(default_factory=tuple)
    model_version: str | None = None
    limit: int | None = None
    metadata_filters: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=current_utc_timestamp)


@dataclass(frozen=True)
class RecallCandidate:
    """Wrapper around a recalled cognitive object with recall scoring metadata.

    INVARIANT: candidate does not mutate the underlying cognitive object.
    """

    query: RecallQuery
    object: CognitiveObject
    score: RecallScore
    relevance_reason: RelevanceReason
    matched_filters: tuple[str, ...] = field(default_factory=tuple)
    rank: int | None = None

    def __post_init__(self) -> None:
        if self.rank is not None and self.rank < 1:
            raise ValueError("RecallCandidate rank must be positive when provided")


@dataclass(frozen=True)
class RecallResult:
    """Top-k recall output with deterministic ordering and provenance trace.

    INVARIANT: candidates are ordered by descending normalized score,
    with deterministic tie-breaking by object id.
    """

    query: RecallQuery
    candidates: tuple[RecallCandidate, ...] = field(default_factory=tuple)
    total_evaluated: int = 0
    total_matched: int = 0
    truncated: bool = False
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="recall_engine",
        )
    )
    trace_id: str | None = None

    def __post_init__(self) -> None:
        if self.truncated and self.limit and len(self.candidates) < self.limit:
            raise ValueError(
                "RecallResult truncated=True requires candidates length >= limit"
            )
        if self.total_matched > self.total_evaluated:
            raise ValueError(
                "RecallResult total_matched cannot exceed total_evaluated"
            )
        if self.limit and len(self.candidates) > self.limit:
            raise ValueError(
                "RecallResult candidates length exceeds query limit"
            )

    @property
    def limit(self) -> int | None:
        return self.query.limit

    @property
    def top_k(self) -> tuple[RecallCandidate, ...]:
        return self.candidates


@dataclass(frozen=True)
class RecallTrace:
    """Immutable record of recall execution parameters and outcomes.

    Used for audit, reproducibility, and provenance without exposing
    internal scoring implementation details.
    """

    trace_id: str = field(default_factory=generate_entity_id)
    query: RecallQuery | None = None
    engine_id: str = "default_recall_engine"
    total_evaluated: int = 0
    total_matched: int = 0
    returned_count: int = 0
    truncated: bool = False
    scoring_profile: str = "default"
    started_at: str = field(default_factory=current_utc_timestamp)
    completed_at: str = field(default_factory=current_utc_timestamp)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.total_matched > self.total_evaluated:
            raise ValueError(
                "RecallTrace total_matched cannot exceed total_evaluated"
            )
        if self.returned_count > self.total_matched:
            raise ValueError(
                "RecallTrace returned_count cannot exceed total_matched"
            )
        if self.truncated and self.returned_count > self.total_matched:
            raise ValueError(
                "RecallTrace truncated=True requires returned_count <= total_matched"
            )
        if self.completed_at < self.started_at:
            raise ValueError(
                "RecallTrace completed_at cannot be earlier than started_at"
            )
