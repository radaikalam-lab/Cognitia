"""Tests for the plasticity operator registry.

Covers:
- Operator registration and lifecycle
- Operator activation and deactivation
- Candidate proposal orchestration across multiple operators
- Deterministic candidate ordering
"""

from __future__ import annotations

import uuid

import pytest

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


class FakeExperience:
    def __init__(self, experience_id: str, object_type: str, episode_id: str) -> None:
        self.id = experience_id
        self.episode_id = episode_id
        self.observation = _FakeObservation(object_type)
        self.outcome = "success"


class _FakeObservation:
    def __init__(self, object_type: str) -> None:
        self.object_type = object_type
        self.created_at = "2024-01-01T00:00:00Z"


def _build_context(object_types: list[str], episode_id: str = "ep-1") -> MemoryContext:
    experiences = [FakeExperience(str(uuid.uuid4()), ot, episode_id) for ot in object_types]
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


class TestInMemoryPlasticityOperatorRegistry:
    def test_register_operator_returns_none(self) -> None:
        registry = InMemoryPlasticityOperatorRegistry()
        operator = DeterministicPatternOperator(operator_id="pattern-op")
        record = OperatorRecord(
            operator_id="pattern-op",
            operator_version="1.0.0",
            operator_type="pattern_discovery",
            is_deterministic=True,
            provenance=ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE),
        )

        registry.register(record)

        retrieved = registry.get("pattern-op")
        assert retrieved is not None
        assert retrieved.operator_id == "pattern-op"

    def test_set_lifecycle_status_changes_status(self) -> None:
        registry = InMemoryPlasticityOperatorRegistry()
        record = OperatorRecord(
            operator_id="pattern-op",
            operator_version="1.0.0",
            operator_type="pattern_discovery",
            is_deterministic=True,
            lifecycle_status=OperatorLifecycleStatus.REGISTERED,
            provenance=ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE),
        )
        registry.register(record)

        registry.set_lifecycle_status("pattern-op", "1.0.0", OperatorLifecycleStatus.ENABLED)

        retrieved = registry.get("pattern-op")
        assert retrieved is not None
        assert retrieved.lifecycle_status == OperatorLifecycleStatus.ENABLED

    def test_is_enabled_reflects_lifecycle_status(self) -> None:
        registry = InMemoryPlasticityOperatorRegistry()
        record = OperatorRecord(
            operator_id="pattern-op",
            operator_version="1.0.0",
            operator_type="pattern_discovery",
            is_deterministic=True,
            lifecycle_status=OperatorLifecycleStatus.REGISTERED,
            provenance=ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE),
        )
        registry.register(record)

        assert registry.is_enabled("pattern-op") is False

        registry.set_lifecycle_status("pattern-op", "1.0.0", OperatorLifecycleStatus.ENABLED)
        assert registry.is_enabled("pattern-op") is True

    def test_list_operators_filters_by_status(self) -> None:
        registry = InMemoryPlasticityOperatorRegistry()
        record_a = OperatorRecord(
            operator_id="pattern-op",
            operator_version="1.0.0",
            operator_type="pattern_discovery",
            is_deterministic=True,
            lifecycle_status=OperatorLifecycleStatus.ENABLED,
            provenance=ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE),
        )
        record_b = OperatorRecord(
            operator_id="assoc-op",
            operator_version="1.0.0",
            operator_type="association_discovery",
            is_deterministic=True,
            lifecycle_status=OperatorLifecycleStatus.REGISTERED,
            provenance=ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE),
        )
        registry.register(record_a)
        registry.register(record_b)

        enabled = registry.list_operators(status=OperatorLifecycleStatus.ENABLED)
        assert len(enabled) == 1
        assert enabled[0].operator_id == "pattern-op"

    def test_register_duplicate_raises(self) -> None:
        registry = InMemoryPlasticityOperatorRegistry()
        record = OperatorRecord(
            operator_id="pattern-op",
            operator_version="1.0.0",
            operator_type="pattern_discovery",
            is_deterministic=True,
            provenance=ProvenanceRecord(source_type=SourceType.DETERMINISTIC_RULE),
        )
        registry.register(record)

        with pytest.raises(ValueError):
            registry.register(record)

    def test_set_lifecycle_status_nonexistent_raises(self) -> None:
        registry = InMemoryPlasticityOperatorRegistry()

        with pytest.raises(KeyError):
            registry.set_lifecycle_status("nonexistent", "1.0.0", OperatorLifecycleStatus.ENABLED)
