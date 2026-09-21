"""Cognitia Epistemic Types.

Defines domain-neutral epistemic concepts, propositions, evidence structures,
and versioned state transitions.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any

from cognitia.abi.types import (
    CognitiveObject,
    Observation,
    Outcome,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType


class EpistemicStatus(str, enum.Enum):
    """Current evaluation and belief status of a cognitive proposition."""

    UNKNOWN = "unknown"
    OBSERVED = "observed"
    HYPOTHESIS = "hypothesis"
    TESTABLE = "testable"
    SUPPORTED = "supported"
    REFUTED = "refuted"
    UNRESOLVED = "unresolved"


class TransitionOutcome(str, enum.Enum):
    """Review and model lifecycle transition outcomes."""

    REVISION_PROPOSED = "revision_proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class EvidenceDirection(str, enum.Enum):
    """Directional support of evidence toward a target proposition."""

    SUPPORT = "support"
    REFUTE = "refute"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class Evidence(CognitiveObject):
    """Evidence evaluating a specific target proposition."""

    target_id: str = ""
    observation: Observation | None = None
    observation_ids: list[str] = field(default_factory=list)
    direction: EvidenceDirection = EvidenceDirection.SUPPORT
    confidence: float = 1.0
    weight: float = 1.0
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )



@dataclass(frozen=True)
class Hypothesis(CognitiveObject):
    """A testable proposition concerning domain behavior or latent dynamics."""

    statement: str = ""
    test_criteria: list[str] = field(default_factory=list)
    competing_hypothesis_ids: list[str] = field(default_factory=list)
    initial_status: EpistemicStatus = EpistemicStatus.HYPOTHESIS
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )


@dataclass(frozen=True)
class Claim(CognitiveObject):
    """An asserted belief or proposition with confidence score."""

    statement: str = ""
    confidence: float = 1.0
    status: EpistemicStatus = EpistemicStatus.SUPPORTED
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )


@dataclass(frozen=True)
class Challenge(CognitiveObject):
    """A formal challenge or falsification attempt against a target node."""

    target_id: str = ""
    basis: str = ""
    counter_evidence_ids: list[str] = field(default_factory=list)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )


@dataclass(frozen=True)
class Residual(CognitiveObject):
    """Unexplained variance or discrepancy between expectation and observation."""

    expected_outcome: Outcome = field(default_factory=Outcome)
    actual_outcome: Outcome = field(default_factory=Outcome)
    discrepancy_magnitude: float = 0.0
    discrepancy_details: dict[str, Any] = field(default_factory=dict)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )


@dataclass(frozen=True)
class EpistemicTransition:
    """An immutable, append-only record of an epistemic state transition."""

    transition_id: str = field(default_factory=generate_entity_id)
    node_id: str = ""
    from_status: EpistemicStatus = EpistemicStatus.UNKNOWN
    to_status: EpistemicStatus = EpistemicStatus.UNKNOWN
    reason: str = ""
    timestamp: str = field(default_factory=current_utc_timestamp)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE)
    )


@dataclass
class EpistemicNode:
    """Mutable graph container maintaining current status and immutable transition history."""

    node_id: str
    entity_type: str
    status: EpistemicStatus
    confidence: float
    content: CognitiveObject
    transitions: list[EpistemicTransition] = field(default_factory=list)
    associated_evidence_ids: list[str] = field(default_factory=list)
    associated_challenge_ids: list[str] = field(default_factory=list)
