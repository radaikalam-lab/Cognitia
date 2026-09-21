"""Tests for deterministic plasticity operators.

Covers:
- DeterministicPatternOperator
- DeterministicAssociationOperator
- DeterministicRecurrenceOperator

Contract requirements:
- Operators are read-only.
- Operators do not mutate memory, models, rules, or production structures.
- Candidate artifacts remain advisory-only proposals.
- Confidence is bounded in [0.0, 1.0].
- Provenance is deterministic and complete.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from cognitia.abi.types import Observation
from cognitia.experience.record import ExperienceBuilder, ExperienceRecord
from cognitia.memory.operators import (
    DeterministicAssociationOperator,
    DeterministicPatternOperator,
    DeterministicRecurrenceOperator,
)
from cognitia.memory.types import CandidateType, MemoryContext, MemoryQuery
from cognitia.provenance.record import ProvenanceRecord, SourceType


def _make_observation(
    object_type: str,
    subject_id: str = "subject-1",
    episode_id: str = "episode-1",
    created_at: str | None = None,
) -> Observation:
    return Observation(
        source_id=f"{subject_id}:{episode_id}",
        payload={
            "object_type": object_type,
            "subject_id": subject_id,
            "episode_id": episode_id,
            "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        },
    )


def _make_experience(
    object_type: str,
    episode_id: str = "episode-1",
    source_application: str = "test_app",
    created_at: str | None = None,
) -> ExperienceRecord:
    return (
        ExperienceBuilder(
            source_application=source_application,
            episode_id=episode_id,
        )
        .with_observation(
            _make_observation(
                object_type=object_type,
                episode_id=episode_id,
                created_at=created_at,
            )
        )
        .build()
    )


def _build_context(experiences: list[ExperienceRecord]) -> MemoryContext:
    return MemoryContext(
        id=str(uuid.uuid4()),
        query=MemoryQuery(),
        experiences=experiences,
        observations=[],
        evidence=[],
        hypotheses=[],
        claims=[],
        reasoning_traces=[],
        decisions=[],
        outcomes=[],
        epistemic_states={},
        provenance=ProvenanceRecord(source_type=SourceType.COMPOSITE),
    )


class TestDeterministicPatternOperator:
    def test_no_experiences_returns_empty_pattern(self) -> None:
        operator = DeterministicPatternOperator()
        context = _build_context([])
        result = operator.propose(context)

        assert result.candidate_type is CandidateType.PATTERN
        assert result.confidence == 0.0
        assert result.provider == "deterministic_pattern_operator"
        assert result.proposed_change["recurrence_count"] == 0

    def test_detects_recurring_event_subject_pair(self) -> None:
        experiences = [
            _make_experience("BoostHigh", episode_id="ep-1"),
            _make_experience("BoostHigh", episode_id="ep-2"),
            _make_experience("LowFlow", episode_id="ep-3"),
        ]
        context = _build_context(experiences)

        operator = DeterministicPatternOperator()
        result = operator.propose(context)

        assert result.candidate_type is CandidateType.PATTERN
        assert result.confidence > 0.0
        assert result.proposed_change["event_type"] == "BoostHigh"
        assert result.proposed_change["subject_id"] == "subject-1"
        assert result.proposed_change["recurrence_count"] == 2

    def test_no_recurring_pattern_returns_zero_confidence(self) -> None:
        experiences = [
            _make_experience("BoostHigh", episode_id="ep-1"),
            _make_experience("LowFlow", episode_id="ep-2"),
            _make_experience("HighLoad", episode_id="ep-3"),
        ]
        context = _build_context(experiences)

        operator = DeterministicPatternOperator()
        result = operator.propose(context)

        assert result.confidence == 0.0

    def test_provenance_is_deterministic(self) -> None:
        experiences = [
            _make_experience("BoostHigh", episode_id="ep-1"),
            _make_experience("BoostHigh", episode_id="ep-2"),
        ]
        context = _build_context(experiences)

        operator = DeterministicPatternOperator()
        result = operator.propose(context)

        assert isinstance(result.provenance, ProvenanceRecord)
        assert result.provenance.source_type is SourceType.DETERMINISTIC_RULE
        assert result.provenance.is_deterministic is True
        assert result.provenance.producer_id == "deterministic_pattern_operator:1.0.0"


class TestDeterministicAssociationOperator:
    def test_no_experiences_returns_empty_association(self) -> None:
        operator = DeterministicAssociationOperator()
        context = _build_context([])
        result = operator.propose(context)

        assert result.candidate_type is CandidateType.ASSOCIATION
        assert result.confidence == 0.0
        assert result.provider == "deterministic_association_operator"

    def test_detects_cooccurrence(self) -> None:
        experiences = [
            _make_experience("BoostHigh", episode_id="ep-1"),
            _make_experience("HighLoad", episode_id="ep-1"),
            _make_experience("BoostHigh", episode_id="ep-2"),
            _make_experience("HighLoad", episode_id="ep-2"),
        ]
        context = _build_context(experiences)

        operator = DeterministicAssociationOperator()
        result = operator.propose(context)

        assert result.candidate_type is CandidateType.ASSOCIATION
        assert result.confidence > 0.0
        association = result.proposed_change["association_pair"]
        assert "BoostHigh" in association
        assert "HighLoad" in association
        assert result.proposed_change["cooccurrence_count"] >= 1

    def test_no_causation_claimed(self) -> None:
        experiences = [
            _make_experience("BoostHigh", episode_id="ep-1"),
            _make_experience("HighLoad", episode_id="ep-1"),
        ]
        context = _build_context(experiences)

        operator = DeterministicAssociationOperator()
        result = operator.propose(context)

        assert "causes" not in result.rationale.lower()
        assert "co-occurs" in result.rationale.lower()


class TestDeterministicRecurrenceOperator:
    def test_no_experiences_returns_empty_recurrence(self) -> None:
        operator = DeterministicRecurrenceOperator()
        context = _build_context([])
        result = operator.propose(context)

        assert result.candidate_type is CandidateType.PATTERN
        assert result.confidence == 0.0
        assert result.provider == "deterministic_recurrence_operator"

    def test_detects_temporal_recurrence(self) -> None:
        base = datetime.now(timezone.utc)
        experiences = [
            _make_experience(
                "BoostHigh",
                episode_id="ep-1",
                created_at=(base - timedelta(minutes=10)).isoformat(),
            ),
            _make_experience(
                "BoostHigh",
                episode_id="ep-2",
                created_at=(base - timedelta(minutes=5)).isoformat(),
            ),
            _make_experience(
                "BoostHigh",
                episode_id="ep-3",
                created_at=base.isoformat(),
            ),
        ]
        context = _build_context(experiences)

        operator = DeterministicRecurrenceOperator()
        result = operator.propose(context)

        assert result.candidate_type is CandidateType.PATTERN
        assert result.confidence > 0.0
        assert result.proposed_change["occurrence_count"] == 3
        assert result.proposed_change["median_interval_seconds"] is not None

    def test_provenance_is_deterministic(self) -> None:
        experiences = [
            _make_experience("BoostHigh", episode_id="ep-1"),
            _make_experience("BoostHigh", episode_id="ep-2"),
        ]
        context = _build_context(experiences)

        operator = DeterministicRecurrenceOperator()
        result = operator.propose(context)

        assert isinstance(result.provenance, ProvenanceRecord)
        assert result.provenance.source_type is SourceType.DETERMINISTIC_RULE
        assert result.provenance.is_deterministic is True
        assert result.provenance.producer_id == "deterministic_recurrence_operator:1.0.0"
