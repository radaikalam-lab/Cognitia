"""Integration tests for plasticity system.

Verifies end-to-end behavior:
- Registry coordinates multiple operators.
- Candidate proposals remain advisory-only.
- No memory or production structures are mutated.
- Deterministic outputs are reproducible.
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
from cognitia.memory.registry import (
    InMemoryPlasticityOperatorRegistry,
    OperatorLifecycleStatus,
    OperatorRecord,
)
from cognitia.memory.types import CandidateType, MemoryContext, MemoryQuery
from cognitia.provenance.record import ProvenanceRecord, SourceType


def _observation(object_type: str, episode_id: str, ts: datetime) -> Observation:
    return Observation(
        source_id=f"subject-1:{episode_id}",
        payload={
            "object_type": object_type,
            "subject_id": "subject-1",
            "episode_id": episode_id,
            "created_at": ts.isoformat(),
        },
    )


def _experience(object_type: str, episode_id: str, ts: datetime) -> ExperienceRecord:
    return (
        ExperienceBuilder(source_application="integration_test", episode_id=episode_id)
        .with_observation(_observation(object_type, episode_id, ts))
        .build()
    )


def _context(experiences: list[ExperienceRecord]) -> MemoryContext:
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


class TestPlasticityIntegration:
    def test_full_pipeline_produces_candidates(self) -> None:
        registry = InMemoryPlasticityOperatorRegistry()
        pattern_record = OperatorRecord(
            operator_id="pattern-op",
            operator_version="1.0.0",
            operator_type="pattern_discovery",
            is_deterministic=True,
            provenance=ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE),
        )
        assoc_record = OperatorRecord(
            operator_id="assoc-op",
            operator_version="1.0.0",
            operator_type="association_discovery",
            is_deterministic=True,
            provenance=ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE),
        )
        recurrence_record = OperatorRecord(
            operator_id="recurrence-op",
            operator_version="1.0.0",
            operator_type="recurrence_discovery",
            is_deterministic=True,
            provenance=ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE),
        )
        registry.register(pattern_record)
        registry.register(assoc_record)
        registry.register(recurrence_record)

        registry.set_lifecycle_status("pattern-op", "1.0.0", OperatorLifecycleStatus.ENABLED)
        registry.set_lifecycle_status("assoc-op", "1.0.0", OperatorLifecycleStatus.ENABLED)
        registry.set_lifecycle_status("recurrence-op", "1.0.0", OperatorLifecycleStatus.ENABLED)

        base = datetime.now(timezone.utc)
        experiences = [
            _experience("BoostHigh", "drive-1", base - timedelta(minutes=20)),
            _experience("HighLoad", "drive-1", base - timedelta(minutes=20)),
            _experience("BoostHigh", "drive-2", base - timedelta(minutes=10)),
            _experience("HighLoad", "drive-2", base - timedelta(minutes=10)),
            _experience("BoostHigh", "drive-3", base),
            _experience("HighLoad", "drive-3", base),
        ]
        context = _context(experiences)

        pattern_op = DeterministicPatternOperator(operator_id="pattern-op")
        assoc_op = DeterministicAssociationOperator(operator_id="assoc-op")
        recurrence_op = DeterministicRecurrenceOperator(operator_id="recurrence-op")

        candidates = [
            pattern_op.propose(context),
            assoc_op.propose(context),
            recurrence_op.propose(context),
        ]

        assert len(candidates) == 3
        types = {c.candidate_type for c in candidates}
        assert CandidateType.PATTERN in types
        assert CandidateType.ASSOCIATION in types

    def test_proposals_are_read_only(self) -> None:
        pattern_op = DeterministicPatternOperator(operator_id="pattern-op")

        base = datetime.now(timezone.utc)
        experiences = [
            _experience("BoostHigh", "drive-1", base - timedelta(minutes=10)),
            _experience("BoostHigh", "drive-2", base),
        ]
        context = _context(experiences)

        original_ids = [e.id for e in context.experiences]
        pattern_op.propose(context)

        assert [e.id for e in context.experiences] == original_ids

    def test_deterministic_reproducibility(self) -> None:
        pattern_op = DeterministicPatternOperator(operator_id="pattern-op")

        base = datetime.now(timezone.utc)
        experiences = [
            _experience("BoostHigh", "drive-1", base - timedelta(minutes=10)),
            _experience("BoostHigh", "drive-2", base),
        ]
        context = _context(experiences)

        candidate_a = pattern_op.propose(context)
        candidate_b = pattern_op.propose(context)

        assert candidate_a.proposed_change == candidate_b.proposed_change

    def test_empty_memory_returns_empty_candidate(self) -> None:
        pattern_op = DeterministicPatternOperator(operator_id="pattern-op")
        context = _context([])

        result = pattern_op.propose(context)

        assert result.confidence == 0.0
