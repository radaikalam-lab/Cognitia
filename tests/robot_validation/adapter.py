"""Cognitia Robotics Dataset Validation Adapter.

Isolated under tests/robotics/. Translates external robotics episode records
into canonical Cognitia structures without introducing robot control authority.

This adapter is NOT part of Cognitia core. It lives in the test environment
and must not be imported from src/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cognitia.abi.types import (
    Action,
    CognitiveObject,
    Observation,
    Outcome,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.experience.record import ExperienceRecord
from cognitia.provenance.record import ProvenanceRecord, SourceType


@dataclass(frozen=True)
class RobotEpisodeRecord:
    """Simplified representation of a robotics dataset episode.

    Mirrors fields documented for ExylosAi/pick_and_place_sample without
    depending on LeRobot, PyTorch, or Hugging Face datasets in Cognitia core.
    """

    episode_id: str
    frame_index: int
    timestamp: str
    robot_state_9d: tuple[float, ...]
    action_9d: tuple[float, ...]
    camera_count: int = 5
    phase: str = "unknown"
    success: bool | None = None
    failure_reason: str | None = None
    correction: str | None = None
    derived_metrics: dict[str, Any] = field(default_factory=dict)
    task: str = "pick_and_place"
    source: str = "ExylosAi/pick_and_place_sample"
    source_node: str = "external_robotics_dataset"


class RobotDatasetAdapter:
    """Translates robot dataset records into canonical Cognitia artifacts.

    INVARIANTS:
    1. Dataset actions are NOT Cognitia Actions. They are contextual metadata.
    2. Dataset success flags are evidence, not truth.
    3. Robot authority never leaks into Cognitia.
    4. All generated artifacts carry dataset-sourced provenance.
    """

    def __init__(self, source_name: str = "ExylosAi/pick_and_place_sample") -> None:
        self._source_name = source_name

    def to_observation(self, record: RobotEpisodeRecord) -> Observation:
        """Translate a robot dataset record into a canonical Observation."""
        payload: dict[str, Any] = {
            "subject_id": record.episode_id,
            "frame_index": record.frame_index,
            "robot_state_9d": list(record.robot_state_9d),
            "action_9d": list(record.action_9d),
            "camera_count": record.camera_count,
            "phase": record.phase,
            "task": record.task,
            "source": record.source,
            "source_node": record.source_node,
            "derived_metrics": record.derived_metrics,
        }
        if record.success is not None:
            payload["reported_success"] = record.success
        if record.failure_reason:
            payload["failure_reason"] = record.failure_reason
        if record.correction:
            payload["correction"] = record.correction

        return Observation(
            source_id=record.source_node,
            payload=payload,
            metadata={
                "dataset": self._source_name,
                "episode_id": record.episode_id,
                "frame_index": record.frame_index,
                "timestamp": record.timestamp,
                "phase": record.phase,
                "task": record.task,
            },
        )

    def to_experience(self, observation: Observation, episode_id: str) -> ExperienceRecord:
        """Translate an observation into an ExperienceRecord for the loop."""
        prov = ProvenanceRecord(
            source_type=SourceType.SENSOR,
            producer_id="robot_dataset_adapter",
            parent_ids=[observation.id],
            is_deterministic=True,
        )
        return ExperienceRecord(
            source_application="robotics_validation",
            source_node="robot_dataset_adapter",
            agent_id="robot_dataset_agent",
            environment_id="simulated_robot_env",
            episode_id=episode_id,
            observation=observation,
            action=Action(
                name="dataset_recorded_action",
                parameters={
                    "action_9d": observation.payload.get("action_9d", []),
                    "phase": observation.payload.get("phase", "unknown"),
                },
                target_node=observation.source_id,
            ),
            expected_outcome=None,
            actual_outcome=None,
            provenance=prov,
        )

    def to_outcome(self, observation: Observation) -> Outcome | None:
        """Translate observed success/failure metadata into an Outcome, if determinable."""
        success = observation.payload.get("reported_success")
        if success is None:
            return None
        metrics: dict[str, float] = {}
        if "derived_metrics" in observation.payload and isinstance(
            observation.payload["derived_metrics"], dict
        ):
            for key, value in observation.payload["derived_metrics"].items():
                if isinstance(value, (int, float)):
                    metrics[key] = float(value)
        return Outcome(
            status="success" if success else "failure",
            metrics=metrics,
            resulting_observation=None,
        )
