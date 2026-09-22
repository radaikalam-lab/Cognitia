"""Deterministic robotics dataset fixtures for Cognitia validation.

Mirrors the documented structure of ExylosAi/pick_and_place_sample:
- 50 episodes, 21,412 frames
- Franka Panda 7-DoF arm + parallel gripper
- 9D robot state, 9D action
- 5 synchronized RGB cameras
- phase annotations
- success/failure flags
- failure reasons
- correction information
- derived metrics
"""

from __future__ import annotations

from tests.robot_validation.adapter import RobotEpisodeRecord


def _state(base: float, noise: float = 0.0) -> tuple[float, ...]:
    return tuple(round(base + i * 0.1 + noise, 4) for i in range(9))


def _action(base: float, noise: float = 0.0) -> tuple[float, ...]:
    return tuple(round(base + i * 0.05 + noise, 4) for i in range(9))


def _metrics(**kwargs: float) -> dict[str, float]:
    return kwargs


# Scenario A — Successful episode
SUCCESSFUL_EPISODE: list[RobotEpisodeRecord] = [
    RobotEpisodeRecord(
        episode_id="robot_success_ep_001",
        frame_index=0,
        timestamp="2026-01-01T00:00:00.000000+00:00",
        robot_state_9d=_state(0.0),
        action_9d=_action(0.0),
        phase="approach",
        success=None,
        failure_reason=None,
        correction=None,
        derived_metrics=_metrics(approach_distance=0.95),
        task="pick_and_place",
    ),
    RobotEpisodeRecord(
        episode_id="robot_success_ep_001",
        frame_index=1,
        timestamp="2026-01-01T00:00:01.000000+00:00",
        robot_state_9d=_state(0.1),
        action_9d=_action(0.1),
        phase="grasp",
        success=None,
        failure_reason=None,
        correction=None,
        derived_metrics=_metrics(grasp_force=0.88),
        task="pick_and_place",
    ),
    RobotEpisodeRecord(
        episode_id="robot_success_ep_001",
        frame_index=2,
        timestamp="2026-01-01T00:00:02.000000+00:00",
        robot_state_9d=_state(0.2),
        action_9d=_action(0.2),
        phase="lift",
        success=None,
        failure_reason=None,
        correction=None,
        derived_metrics=_metrics(lift_height=0.92),
        task="pick_and_place",
    ),
    RobotEpisodeRecord(
        episode_id="robot_success_ep_001",
        frame_index=3,
        timestamp="2026-01-01T00:00:03.000000+00:00",
        robot_state_9d=_state(0.3),
        action_9d=_action(0.3),
        phase="place",
        success=True,
        failure_reason=None,
        correction=None,
        derived_metrics=_metrics(placement_accuracy=0.97),
        task="pick_and_place",
    ),
]


# Scenario B — Failed episode
FAILED_EPISODE: list[RobotEpisodeRecord] = [
    RobotEpisodeRecord(
        episode_id="robot_failure_ep_002",
        frame_index=0,
        timestamp="2026-01-01T00:01:00.000000+00:00",
        robot_state_9d=_state(1.0),
        action_9d=_action(1.0),
        phase="approach",
        success=None,
        failure_reason=None,
        correction=None,
        derived_metrics=_metrics(approach_distance=0.82),
        task="pick_and_place",
    ),
    RobotEpisodeRecord(
        episode_id="robot_failure_ep_002",
        frame_index=1,
        timestamp="2026-01-01T00:01:01.000000+00:00",
        robot_state_9d=_state(1.1, noise=0.05),
        action_9d=_action(1.1, noise=0.05),
        phase="grasp",
        success=None,
        failure_reason=None,
        correction="reposition_gripper",
        derived_metrics=_metrics(grasp_force=0.45),
        task="pick_and_place",
    ),
    RobotEpisodeRecord(
        episode_id="robot_failure_ep_002",
        frame_index=2,
        timestamp="2026-01-01T00:01:02.000000+00:00",
        robot_state_9d=_state(1.2, noise=0.1),
        action_9d=_action(1.2, noise=0.1),
        phase="lift",
        success=False,
        failure_reason="object_slipped_during_lift",
        correction="retry_grasp",
        derived_metrics=_metrics(lift_height=0.30),
        task="pick_and_place",
    ),
]


# Scenario C — Ambiguous / insufficient evidence
AMBIGUOUS_EPISODE: list[RobotEpisodeRecord] = [
    RobotEpisodeRecord(
        episode_id="robot_ambiguous_ep_003",
        frame_index=0,
        timestamp="2026-01-01T00:02:00.000000+00:00",
        robot_state_9d=_state(2.0),
        action_9d=_action(2.0),
        phase="approach",
        success=None,
        failure_reason=None,
        correction=None,
        derived_metrics=_metrics(approach_distance=0.60),
        task="pick_and_place",
    ),
    RobotEpisodeRecord(
        episode_id="robot_ambiguous_ep_003",
        frame_index=1,
        timestamp="2026-01-01T00:02:01.000000+00:00",
        robot_state_9d=_state(2.1),
        action_9d=_action(2.1),
        phase="grasp",
        success=None,
        failure_reason=None,
        correction=None,
        derived_metrics={},
        task="pick_and_place",
    ),
]


def get_scenario(name: str) -> list[RobotEpisodeRecord]:
    mapping = {
        "success": SUCCESSFUL_EPISODE,
        "failure": FAILED_EPISODE,
        "ambiguous": AMBIGUOUS_EPISODE,
    }
    return mapping[name]
