"""Tests for FJH Experience Formation."""

from __future__ import annotations

import pytest

from cognitia.abi.types import Observation
from adapters.fjh.events import FJHEvent, FJHStage
from adapters.fjh.experience import FJHExperienceBuilder, FJHLifecycleType
from adapters.fjh.translator import FJHEventTranslator


class TestFJHExperienceFormation:
    """Validate FJH experience aggregation from sequences of observations."""

    def _make_observation(self, experiment_id: str, stage: FJHStage) -> Observation:
        event = FJHEvent(
            stage=stage,
            experiment_id=experiment_id,
            payload={"dummy": True},
            precursor_id="GRAPHITE-001",
            chamber_id="CHAMBER-ALPHA",
        )
        return FJHEventTranslator.translate(event)

    def test_single_shot_lifecycle_experience(self) -> None:
        experiment_id = "FJH-EXP-2026-001"
        observations = [
            self._make_observation(experiment_id, FJHStage.REQUESTED),
            self._make_observation(experiment_id, FJHStage.VALIDATED),
            self._make_observation(experiment_id, FJHStage.EXECUTED),
            self._make_observation(experiment_id, FJHStage.MEASURED),
            self._make_observation(experiment_id, FJHStage.DERIVED),
            self._make_observation(experiment_id, FJHStage.INTERPRETED),
        ]

        experience = FJHExperienceBuilder.build_lifecycle_experience(
            lifecycle_id=experiment_id,
            lifecycle_type=FJHLifecycleType.SINGLE_SHOT,
            observations=observations,
            environment_id="fjh_lab",
            agent_id="fjh_operator",
        )

        assert experience.source_application == "fjh"
        assert experience.episode_id == experiment_id
        assert experience.environment_id == "fjh_lab"
        assert experience.agent_id == "fjh_operator"
        assert experience.metadata["lifecycle_type"] == "FJHSingleShot"
        assert experience.metadata["observation_count"] == 6
        assert experience.metadata["experiment_ids"] == [experiment_id]
        assert experience.metadata["precursor_ids"] == ["GRAPHITE-001"]
        assert experience.metadata["chamber_ids"] == ["CHAMBER-ALPHA"]

    def test_parameter_sweep_lifecycle(self) -> None:
        experiment_id = "FJH-EXP-2026-002"
        observations = [self._make_observation(experiment_id, FJHStage.REQUESTED)]

        experience = FJHExperienceBuilder.build_lifecycle_experience(
            lifecycle_id=experiment_id,
            lifecycle_type=FJHLifecycleType.PARAMETER_SWEEP,
            observations=observations,
            additional_context={"sweep_parameter": "voltage_V", "values": [80, 100, 120]},
        )

        assert experience.metadata["lifecycle_type"] == "FJHParameterSweep"
        assert experience.metadata["sweep_parameter"] == "voltage_V"
        assert experience.metadata["values"] == [80, 100, 120]

    def test_multiple_experiment_ids_aggregated(self) -> None:
        observations = [
            self._make_observation("FJH-EXP-A", FJHStage.REQUESTED),
            self._make_observation("FJH-EXP-B", FJHStage.REQUESTED),
        ]

        experience = FJHExperienceBuilder.build_lifecycle_experience(
            lifecycle_id="COMPARISON-001",
            lifecycle_type=FJHLifecycleType.PRECURSOR_COMPARISON,
            observations=observations,
        )

        assert experience.metadata["experiment_ids"] == ["FJH-EXP-A", "FJH-EXP-B"]

    def test_provenance_links_all_observations(self) -> None:
        observations = [
            self._make_observation("FJH-EXP-2026-001", FJHStage.REQUESTED),
            self._make_observation("FJH-EXP-2026-001", FJHStage.EXECUTED),
        ]

        experience = FJHExperienceBuilder.build_lifecycle_experience(
            lifecycle_id="FJH-EXP-2026-001",
            lifecycle_type=FJHLifecycleType.SINGLE_SHOT,
            observations=observations,
        )

        assert experience.provenance.source_type.value == "sensor"
        assert experience.provenance.producer_id == "fjh_adapter:experience_builder"
        assert set(experience.provenance.parent_ids) == {obs.id for obs in observations}

    def test_empty_observations_list(self) -> None:
        experience = FJHExperienceBuilder.build_lifecycle_experience(
            lifecycle_id="FJH-EXP-2026-001",
            lifecycle_type=FJHLifecycleType.SINGLE_SHOT,
            observations=[],
        )

        assert experience.observation.source_id == "unknown"
        assert experience.metadata["observation_count"] == 0
        assert experience.metadata["observation_ids"] == []

    def test_string_lifecycle_type_accepted(self) -> None:
        observations = [self._make_observation("FJH-EXP-2026-001", FJHStage.REQUESTED)]
        experience = FJHExperienceBuilder.build_lifecycle_experience(
            lifecycle_id="FJH-EXP-2026-001",
            lifecycle_type="CustomFJHLifecycle",
            observations=observations,
        )
        assert experience.metadata["lifecycle_type"] == "CustomFJHLifecycle"
