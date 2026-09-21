"""Synthetic domain plasticity tests.

Domains:
- ERP (Enterprise Resource Planning)
- Automotive
- Acoustics
- Scientific

Each domain exercises the plasticity operators with domain-specific
experience structures while preserving the same operator contracts.

Operators remain read-only and advisory-only across all domains.
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
        ExperienceBuilder(source_application="synthetic_domain", episode_id=episode_id)
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


class TestERPDomain:
    def test_pattern_operator_detects_recurring_invoice_event(self) -> None:
        base = datetime.now(timezone.utc)
        experiences = [
            _experience("InvoiceCreated", "ep-1", base - timedelta(days=30)),
            _experience("InvoiceCreated", "ep-2", base - timedelta(days=15)),
            _experience("InvoiceCreated", "ep-3", base),
            _experience("PaymentReceived", "ep-3", base),
        ]
        context = _context(experiences)

        operator = DeterministicPatternOperator()
        result = operator.propose(context)

        assert result.candidate_type is CandidateType.PATTERN
        assert result.proposed_change["event_type"] == "InvoiceCreated"
        assert result.proposed_change["recurrence_count"] == 3

    def test_association_operator_detects_invoice_payment_cooccurrence(self) -> None:
        base = datetime.now(timezone.utc)
        experiences = [
            _experience("InvoiceCreated", "ep-1", base),
            _experience("PaymentReceived", "ep-1", base),
            _experience("InvoiceCreated", "ep-2", base + timedelta(days=1)),
            _experience("PaymentReceived", "ep-2", base + timedelta(days=1)),
        ]
        context = _context(experiences)

        operator = DeterministicAssociationOperator()
        result = operator.propose(context)

        assert result.candidate_type is CandidateType.ASSOCIATION
        association = result.proposed_change["association_pair"]
        assert "InvoiceCreated" in association
        assert "PaymentReceived" in association
        assert result.proposed_change["cooccurrence_count"] >= 1


class TestAutomotiveDomain:
    def test_pattern_operator_detects_recurring_boost_event(self) -> None:
        base = datetime.now(timezone.utc)
        experiences = [
            _experience("BoostHigh", "drive-1", base - timedelta(minutes=10)),
            _experience("BoostHigh", "drive-2", base - timedelta(minutes=5)),
            _experience("BoostHigh", "drive-3", base),
            _experience("LowFlow", "drive-3", base),
        ]
        context = _context(experiences)

        operator = DeterministicPatternOperator()
        result = operator.propose(context)

        assert result.candidate_type is CandidateType.PATTERN
        assert result.proposed_change["event_type"] == "BoostHigh"
        assert result.proposed_change["recurrence_count"] == 3

    def test_recurrence_operator_detects_temporal_boost_pattern(self) -> None:
        base = datetime.now(timezone.utc)
        experiences = [
            _experience("BoostHigh", "drive-1", base - timedelta(minutes=20)),
            _experience("BoostHigh", "drive-2", base - timedelta(minutes=10)),
            _experience("BoostHigh", "drive-3", base),
        ]
        context = _context(experiences)

        operator = DeterministicRecurrenceOperator()
        result = operator.propose(context)

        assert result.candidate_type is CandidateType.PATTERN
        assert result.proposed_change["occurrence_count"] == 3
        assert result.proposed_change["median_interval_seconds"] is not None


class TestAcousticsDomain:
    def test_pattern_operator_detects_recurring_noise_event(self) -> None:
        base = datetime.now(timezone.utc)
        experiences = [
            _experience("NoiseDetected", "session-1", base - timedelta(seconds=30)),
            _experience("NoiseDetected", "session-2", base - timedelta(seconds=15)),
            _experience("NoiseDetected", "session-3", base),
            _experience("SilenceDetected", "session-3", base),
        ]
        context = _context(experiences)

        operator = DeterministicPatternOperator()
        result = operator.propose(context)

        assert result.candidate_type is CandidateType.PATTERN
        assert result.proposed_change["event_type"] == "NoiseDetected"
        assert result.proposed_change["recurrence_count"] == 3

    def test_association_operator_detects_noise_silence_cooccurrence(self) -> None:
        base = datetime.now(timezone.utc)
        experiences = [
            _experience("NoiseDetected", "session-1", base),
            _experience("SilenceDetected", "session-1", base),
            _experience("NoiseDetected", "session-2", base + timedelta(seconds=10)),
            _experience("SilenceDetected", "session-2", base + timedelta(seconds=10)),
        ]
        context = _context(experiences)

        operator = DeterministicAssociationOperator()
        result = operator.propose(context)

        assert result.candidate_type is CandidateType.ASSOCIATION
        association = result.proposed_change["association_pair"]
        assert "NoiseDetected" in association
        assert "SilenceDetected" in association
        assert result.proposed_change["cooccurrence_count"] >= 1


class TestScientificDomain:
    def test_pattern_operator_detects_recurring_measurement(self) -> None:
        base = datetime.now(timezone.utc)
        experiences = [
            _experience("MeasurementTaken", "experiment-1", base - timedelta(hours=2)),
            _experience("MeasurementTaken", "experiment-2", base - timedelta(hours=1)),
            _experience("MeasurementTaken", "experiment-3", base),
            _experience("CalibrationPerformed", "experiment-3", base),
        ]
        context = _context(experiences)

        operator = DeterministicPatternOperator()
        result = operator.propose(context)

        assert result.candidate_type is CandidateType.PATTERN
        assert result.proposed_change["event_type"] == "MeasurementTaken"
        assert result.proposed_change["recurrence_count"] == 3

    def test_recurrence_operator_detects_measurement_interval(self) -> None:
        base = datetime.now(timezone.utc)
        experiences = [
            _experience("MeasurementTaken", "experiment-1", base - timedelta(hours=2)),
            _experience("MeasurementTaken", "experiment-2", base - timedelta(hours=1)),
            _experience("MeasurementTaken", "experiment-3", base),
        ]
        context = _context(experiences)

        operator = DeterministicRecurrenceOperator()
        result = operator.propose(context)

        assert result.candidate_type is CandidateType.PATTERN
        assert result.proposed_change["occurrence_count"] == 3
        assert result.proposed_change["median_interval_seconds"] is not None
