"""Cognitia Persistence Event Models and Query Types.

Defines immutable cognitive events, standard event types, and query criteria
for the Cognitia Event Journal and Object Store.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from cognitia.abi.types import (
    CognitiveObject,
    SCHEMA_VERSION_V1,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType


class CognitiveEventType(str, enum.Enum):
    """Standard event types representing meaningful cognitive occurrences."""

    OBSERVATION_RECORDED = "ObservationRecorded"
    EVIDENCE_REGISTERED = "EvidenceRegistered"
    EXPERIENCE_RECORDED = "ExperienceRecorded"
    HYPOTHESIS_REGISTERED = "HypothesisRegistered"
    CLAIM_REGISTERED = "ClaimRegistered"
    CHALLENGE_ISSUED = "ChallengeIssued"
    RESIDUAL_RECORDED = "ResidualRecorded"
    EPISTEMIC_TRANSITION_RECORDED = "EpistemicTransitionRecorded"
    REASONING_STARTED = "ReasoningStarted"
    REASONING_COMPLETED = "ReasoningCompleted"
    DECISION_PROPOSED = "DecisionProposed"
    ACTION_RECORDED = "ActionRecorded"
    OUTCOME_RECORDED = "OutcomeRecorded"
    MODEL_REGISTERED = "ModelRegistered"
    MODEL_STATUS_CHANGED = "ModelStatusChanged"
    CAPABILITY_REGISTERED = "CapabilityRegistered"


@dataclass(frozen=True)
class CognitiveEvent(CognitiveObject):
    """Immutable event recording a discrete cognitive occurrence or state change."""

    event_type: str = "cognitive_event"
    source_type: SourceType = SourceType.DETERMINISTIC_RULE
    source_id: str = "cognitia_core"
    subject_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )


@dataclass(frozen=True)
class EventQuery:
    """Query parameters for filtering cognitive events in the Event Journal."""

    event_type: str | None = None
    subject_id: str | None = None
    source_id: str | None = None
    source_type: SourceType | None = None
    start_time: str | None = None
    end_time: str | None = None
    schema_version: str | None = None
    limit: int | None = None


@dataclass(frozen=True)
class ObjectQuery:
    """Query parameters for filtering cognitive artifacts in the Object Store."""

    entity_type: str | None = None
    schema_version: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    limit: int | None = None
