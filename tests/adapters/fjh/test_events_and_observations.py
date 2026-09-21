"""Tests for FJH Event Translation and Observation Mapping."""

from __future__ import annotations

import pytest

from cognitia.abi.types import Observation
from adapters.fjh.events import FJHEvent, FJHStage
from adapters.fjh.translator import FJHEventTranslator


class TestFJHEventTranslation:
    """Validate FJH event-to-Observation translation across all lifecycle stages."""

    @pytest.mark.parametrize("stage", list(FJHStage))
    def test_translation_preserves_stage_and_experiment_id(self, stage: FJHStage) -> None:
        event = FJHEvent(
            stage=stage,
            experiment_id="FJH-EXP-2026-001",
            payload={"voltage_V": 120.0, "capacitance_uF": 1000.0},
            precursor_id="GRAPHITE-001",
            chamber_id="CHAMBER-ALPHA",
            operator_id="operator_1",
            timestamp="2026-09-21T10:00:00Z",
        )

        obs = FJHEventTranslator.translate(event)

        assert isinstance(obs, Observation)
        assert obs.created_at == "2026-09-21T10:00:00Z"
        assert obs.payload["stage"] == stage.value
        assert obs.payload["experiment_id"] == "FJH-EXP-2026-001"
        assert obs.payload["precursor_id"] == "GRAPHITE-001"
        assert obs.payload["chamber_id"] == "CHAMBER-ALPHA"
        assert obs.payload["operator_id"] == "operator_1"
        assert obs.payload["data"]["voltage_V"] == 120.0
        assert obs.metadata["stage"] == stage.value
        assert obs.metadata["experiment_id"] == "FJH-EXP-2026-001"
        assert obs.metadata["source_application"] == "fjh"

    def test_requested_stage_translation(self) -> None:
        event = FJHEvent(
            stage=FJHStage.REQUESTED,
            experiment_id="FJH-EXP-2026-001",
            payload={
                "voltage_V": 120.0,
                "capacitance_uF": 1000.0,
                "precursor_type": "graphite",
                "sample_mass_g": 0.05,
            },
            precursor_id="GRAPHITE-001",
            chamber_id="CHAMBER-ALPHA",
        )

        obs = FJHEventTranslator.translate(event)
        assert obs.source_id == "fjh:FJH-EXP-2026-001:FJH_REQUESTED"
        assert obs.payload["stage"] == "FJH_REQUESTED"
        assert obs.payload["data"]["precursor_type"] == "graphite"
        assert obs.metadata["precursor_id"] == "GRAPHITE-001"

    def test_validated_stage_translation(self) -> None:
        event = FJHEvent(
            stage=FJHStage.VALIDATED,
            experiment_id="FJH-EXP-2026-001",
            payload={"validation_status": "passed", "safety_checks": ["interlock", "pressure"]},
            precursor_id="GRAPHITE-001",
            chamber_id="CHAMBER-ALPHA",
        )

        obs = FJHEventTranslator.translate(event)
        assert obs.source_id == "fjh:FJH-EXP-2026-001:FJH_VALIDATED"
        assert obs.payload["data"]["validation_status"] == "passed"

    def test_executed_stage_translation(self) -> None:
        event = FJHEvent(
            stage=FJHStage.EXECUTED,
            experiment_id="FJH-EXP-2026-001",
            payload={"discharge_energy_J": 7200.0, "peak_current_A": 850.0},
            precursor_id="GRAPHITE-001",
            chamber_id="CHAMBER-ALPHA",
        )

        obs = FJHEventTranslator.translate(event)
        assert obs.source_id == "fjh:FJH-EXP-2026-001:FJH_EXECUTED"
        assert obs.payload["data"]["discharge_energy_J"] == 7200.0

    def test_measured_stage_translation(self) -> None:
        event = FJHEvent(
            stage=FJHStage.MEASURED,
            experiment_id="FJH-EXP-2026-001",
            payload={
                "voltage_waveform": [0.0, 110.0, 120.0, 0.0],
                "current_waveform": [0.0, 700.0, 850.0, 0.0],
                "temperature_estimate_K": 2800.0,
            },
            precursor_id="GRAPHITE-001",
            chamber_id="CHAMBER-ALPHA",
        )

        obs = FJHEventTranslator.translate(event)
        assert obs.source_id == "fjh:FJH-EXP-2026-001:FJH_MEASURED"
        assert obs.payload["data"]["temperature_estimate_K"] == 2800.0

    def test_derived_stage_translation(self) -> None:
        event = FJHEvent(
            stage=FJHStage.DERIVED,
            experiment_id="FJH-EXP-2026-001",
            payload={
                "resistivity_ohm_cm": 0.00035,
                "heating_rate_K_per_s": 5.6e6,
                "cooling_rate_K_per_s": 1.2e6,
            },
            precursor_id="GRAPHITE-001",
            chamber_id="CHAMBER-ALPHA",
        )

        obs = FJHEventTranslator.translate(event)
        assert obs.source_id == "fjh:FJH-EXP-2026-001:FJH_DERIVED"
        assert obs.payload["data"]["resistivity_ohm_cm"] == pytest.approx(0.00035)

    def test_interpreted_stage_translation(self) -> None:
        event = FJHEvent(
            stage=FJHStage.INTERPRETED,
            experiment_id="FJH-EXP-2026-001",
            payload={
                "quality_assessment": "high_quality_graphene",
                "comparison_baseline": "EXP-2025-089",
                "hypothesis": "fast_cooling_promotes_few_layer",
            },
            precursor_id="GRAPHITE-001",
            chamber_id="CHAMBER-ALPHA",
        )

        obs = FJHEventTranslator.translate(event)
        assert obs.source_id == "fjh:FJH-EXP-2026-001:FJH_INTERPRETED"
        assert obs.payload["data"]["quality_assessment"] == "high_quality_graphene"

    def test_metadata_indexing_fields(self) -> None:
        event = FJHEvent(
            stage=FJHStage.MEASURED,
            experiment_id="FJH-EXP-2026-001",
            payload={"voltage_waveform": [0.0, 120.0, 0.0]},
            precursor_id="GRAPHITE-001",
            chamber_id="CHAMBER-ALPHA",
            metadata={"custom_tag": "repeat_run_3"},
        )

        obs = FJHEventTranslator.translate(event)
        assert obs.metadata["source_application"] == "fjh"
        assert obs.metadata["stage"] == "FJH_MEASURED"
        assert obs.metadata["experiment_id"] == "FJH-EXP-2026-001"
        assert obs.metadata["precursor_id"] == "GRAPHITE-001"
        assert obs.metadata["chamber_id"] == "CHAMBER-ALPHA"
        assert obs.metadata["custom_tag"] == "repeat_run_3"

    def test_auto_timestamp_when_missing(self) -> None:
        event = FJHEvent(
            stage=FJHStage.REQUESTED,
            experiment_id="FJH-EXP-2026-001",
            payload={},
        )
        obs = FJHEventTranslator.translate(event)
        assert obs.created_at is not None
        assert len(obs.created_at) > 0

    def test_string_stage_accepted(self) -> None:
        event = FJHEvent(
            stage="FJH_EXECUTED",
            experiment_id="FJH-EXP-2026-001",
            payload={},
        )
        obs = FJHEventTranslator.translate(event)
        assert obs.payload["stage"] == "FJH_EXECUTED"
        assert obs.metadata["stage"] == "FJH_EXECUTED"
