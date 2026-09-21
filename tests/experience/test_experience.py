"""Tests for domain-neutral Experience records and builder utilities."""

from cognitia.abi.types import Action, Observation, Outcome
from cognitia.experience.record import ExperienceBuilder, ExperienceRecord


def test_experience_builder_creation():
    """Verify fluent building of domain-neutral experience records."""
    obs = Observation(source_id="camera_0", payload={"luminance": 0.85})
    act = Action(name="increase_gain", parameters={"factor": 1.2})
    expected = Outcome(status="expected_target_reached", metrics={"target_accuracy": 0.9})
    actual = Outcome(status="target_reached", metrics={"target_accuracy": 0.92})

    exp = (
        ExperienceBuilder(source_application="robotics_swarm", episode_id="ep_104")
        .with_node("node_7")
        .with_agent("swarm_drone_12")
        .with_environment("arena_alpha")
        .with_observation(obs)
        .with_action(act)
        .with_expected_outcome(expected)
        .with_actual_outcome(actual)
        .with_model_version("2.1.0")
        .with_metadata("temperature_c", 24.5)
        .build()
    )

    assert isinstance(exp, ExperienceRecord)
    assert exp.source_application == "robotics_swarm"
    assert exp.source_node == "node_7"
    assert exp.agent_id == "swarm_drone_12"
    assert exp.episode_id == "ep_104"
    assert exp.environment_id == "arena_alpha"
    assert exp.observation.payload["luminance"] == 0.85
    assert exp.actual_outcome is not None
    assert exp.actual_outcome.metrics["target_accuracy"] == 0.92
    assert exp.metadata["temperature_c"] == 24.5
