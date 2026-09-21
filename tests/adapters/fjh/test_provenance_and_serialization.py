"""Tests for FJH Provenance Chain Integrity and Deterministic Serialization."""

from __future__ import annotations

import json

import pytest

from cognitia.abi.types import DeterministicSerializer
from cognitia.provenance.record import ProvenanceRecord, SourceType, compute_checksum
from cognitia.persistence.events import CognitiveEventType, EventQuery
from cognitia.runtime.local import LocalCognitiveRuntime
from adapters.fjh.advisory import FJHAdvisory
from adapters.fjh.events import FJHEvent, FJHStage
from adapters.fjh.translator import FJHEventTranslator
from adapters.fjh.client import FJHCognitiaAdapter


class TestFJHProvenanceAndSerialization:
    """Validate provenance and deterministic serialization for FJH adapter."""

    def test_observation_serialization_is_deterministic(self) -> None:
        event = FJHEvent(
            stage=FJHStage.EXECUTED,
            experiment_id="FJH-EXP-2026-001",
            payload={"discharge_energy_J": 7200.0},
            precursor_id="GRAPHITE-001",
            chamber_id="CHAMBER-ALPHA",
            timestamp="2026-09-21T10:00:00Z",
        )
        obs = FJHEventTranslator.translate(event)

        serialized = obs.serialize()
        assert isinstance(serialized, str)

        # Re-serialize and confirm byte-for-byte equality
        assert serialized == DeterministicSerializer.serialize(obs)

        # Deserialize and verify key fields
        deserialized = json.loads(serialized)
        assert deserialized["source_id"] == "fjh:FJH-EXP-2026-001:FJH_EXECUTED"
        assert deserialized["payload"]["experiment_id"] == "FJH-EXP-2026-001"

    def test_advisory_serialization_is_deterministic(self) -> None:
        advisory = FJHAdvisory(
            experiment_id="FJH-EXP-2026-001",
            stage="FJH_INTERPRETED",
            historical_context_summary="5 prior runs",
            recommendation="increase_capacitance_to_1500uF",
            confidence=0.88,
            is_authoritative=False,
        )
        serialized = advisory.serialize()
        assert isinstance(serialized, str)

        deserialized = json.loads(serialized)
        assert deserialized["experiment_id"] == "FJH-EXP-2026-001"
        assert deserialized["is_authoritative"] is False

    def test_ingested_event_creates_provenance_chain(self) -> None:
        runtime = LocalCognitiveRuntime()
        adapter = FJHCognitiaAdapter(runtime=runtime)

        obs = adapter.ingest_event(
            FJHEvent(
                stage=FJHStage.REQUESTED,
                experiment_id="FJH-EXP-2026-001",
                payload={"voltage_V": 120.0},
            )
        )

        # Verify observation has identity
        assert obs.id is not None
        assert len(obs.id) > 0

        # Verify event journal entry
        events = runtime.persistence.query_events(
            EventQuery(source_id=obs.id)
        )
        assert len(events) == 1
        cog_event = events[0]
        assert cog_event.event_type == CognitiveEventType.OBSERVATION_RECORDED.value
        assert cog_event.source_id == obs.id

    def test_provenance_record_checksum(self) -> None:
        prov = ProvenanceRecord(
            source_type=SourceType.SENSOR,
            producer_id="fjh_adapter",
            parent_ids=["parent-1", "parent-2"],
            is_deterministic=True,
        )

        checksum = compute_checksum(prov)
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 hex length

        # Deterministic: same object produces same checksum
        assert compute_checksum(prov) == checksum

    def test_deterministic_serialization_sorted_keys(self) -> None:
        event = FJHEvent(
            stage=FJHStage.DERIVED,
            experiment_id="FJH-EXP-2026-001",
            payload={"z_key": 1, "a_key": 2, "m_key": 3},
        )
        obs = FJHEventTranslator.translate(event)
        serialized = obs.serialize()

        # Parse and verify keys are sorted
        deserialized = json.loads(serialized)
        payload_keys = list(deserialized["payload"]["data"].keys())
        assert payload_keys == sorted(payload_keys)
