"""Tests for FJH Advisory Presentation and Authority Boundary Enforcement."""

from __future__ import annotations

import copy

import pytest

from cognitia.runtime.local import LocalCognitiveRuntime
from adapters.fjh.advisory import FJHAdvisory
from adapters.fjh.client import FJHCognitiaAdapter
from adapters.fjh.events import FJHEvent, FJHStage


class TestFJHAdvisoryBoundary:
    """Validate FJH advisory generation and strict non-authority boundary."""

    def test_advisory_generation_and_non_authority(self) -> None:
        runtime = LocalCognitiveRuntime()
        adapter = FJHCognitiaAdapter(runtime=runtime)

        # Human creates an FJH safety cognitive rule
        adapter.ingest_event(
            FJHEvent(
                stage=FJHStage.REQUESTED,
                experiment_id="FJH-EXP-2026-001",
                payload={
                    "voltage_V": 120.0,
                    "capacitance_uF": 1000.0,
                    "precursor_type": "graphite",
                    "sample_mass_g": 0.05,
                },
            )
        )

        # Simulated FJH experiment request
        fjh_request = {
            "voltage_V": 120.0,
            "capacitance_uF": 1000.0,
            "precursor_type": "graphite",
            "sample_mass_g": 0.05,
        }
        original_copy = copy.deepcopy(fjh_request)

        advisory = adapter.get_advisory(
            experiment_id="FJH-EXP-2026-001",
            stage="FJH_REQUESTED",
            payload=fjh_request,
        )

        assert isinstance(advisory, FJHAdvisory)
        assert advisory.is_authoritative is False
        assert advisory.experiment_id == "FJH-EXP-2026-001"
        assert advisory.stage == "FJH_REQUESTED"

        # AUTHORITY BOUNDARY VERIFICATION:
        # Cognitia MUST NOT have modified fjh_request
        assert fjh_request == original_copy
        assert fjh_request["voltage_V"] == 120.0
        assert fjh_request["sample_mass_g"] == pytest.approx(0.05)

    def test_advisory_contains_decision(self) -> None:
        runtime = LocalCognitiveRuntime()
        adapter = FJHCognitiaAdapter(runtime=runtime)

        adapter.ingest_event(
            FJHEvent(
                stage=FJHStage.MEASURED,
                experiment_id="FJH-EXP-2026-001",
                payload={"voltage_waveform": [0.0, 120.0, 0.0]},
            )
        )

        advisory = adapter.get_advisory(
            experiment_id="FJH-EXP-2026-001",
            stage="FJH_MEASURED",
            payload={"observation_note": "peak_temp_reached"},
        )

        assert advisory.decision is not None
        assert advisory.confidence == pytest.approx(1.0)
        assert advisory.epistemic_status == "SUPPORTED"

    def test_advisory_is_never_authoritative(self) -> None:
        runtime = LocalCognitiveRuntime()
        adapter = FJHCognitiaAdapter(runtime=runtime)

        for stage in FJHStage:
            advisory = adapter.get_advisory(
                experiment_id="FJH-EXP-2026-001",
                stage=stage.value,
                payload={},
            )
            assert advisory.is_authoritative is False

    def test_to_dict_serialization(self) -> None:
        advisory = FJHAdvisory(
            experiment_id="FJH-EXP-2026-001",
            stage="FJH_EXECUTED",
            historical_context_summary="2 prior runs",
            similar_experiments_count=2,
            recommendation="consider_argon_atmosphere",
            confidence=0.95,
            is_authoritative=False,
            metadata={"operator_id": "op_1"},
        )

        d = advisory.to_dict()
        assert d["experiment_id"] == "FJH-EXP-2026-001"
        assert d["stage"] == "FJH_EXECUTED"
        assert d["is_authoritative"] is False
        assert d["confidence"] == pytest.approx(0.95)
        assert d["metadata"]["operator_id"] == "op_1"
        assert d["decision_id"] is None
