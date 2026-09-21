"""Tests for Observable State Reconstruction Enrichment.

Validates deterministic state variable reconstruction, latest/previous/first value tracking,
explicit unknown state handling, and preservation of conflicting states.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.context.enrichers.state import StateReconstructionEnricher
from cognitia.runtime.local import LocalCognitiveRuntime


def test_state_reconstruction_progression() -> None:
    runtime = LocalCognitiveRuntime()

    obs_1 = Observation(
        source_id="controller:valves",
        payload={"valve_main": "CLOSED", "pressure_bar": 1.0},
        created_at="2026-09-21T10:00:00Z",
    )
    obs_2 = Observation(
        source_id="controller:valves",
        payload={"valve_main": "OPEN", "pressure_bar": 3.5},
        created_at="2026-09-21T10:00:10Z",
    )
    obs_ref = Observation(
        source_id="controller:valves",
        payload={"pressure_bar": 4.8},
        created_at="2026-09-21T10:00:30Z",
    )

    runtime.persistence.save_object(obs_1)
    runtime.persistence.save_object(obs_2)
    runtime.persistence.save_object(obs_ref)

    context = runtime.assemble_context(obs_ref)
    recon = context.state_reconstruction

    var_pressure = recon.get_variable("pressure_bar")
    assert var_pressure is not None
    assert var_pressure.latest_value == 4.8
    assert var_pressure.previous_value == 3.5
    assert var_pressure.first_known_value == 1.0
    assert var_pressure.is_unknown is False
    assert var_pressure.is_conflicted is False

    var_valve = recon.get_variable("valve_main")
    assert var_valve is not None
    assert var_valve.latest_value == "OPEN"
    assert var_valve.previous_value == "CLOSED"
    assert var_valve.first_known_value == "CLOSED"


def test_state_reconstruction_unknown_and_conflict() -> None:
    enricher = StateReconstructionEnricher()

    obs_a = Observation(
        source_id="sensor:alpha",
        payload={"target_temp": 50.0},
        created_at="2026-09-21T12:00:00Z",
    )
    obs_b_conflict = Observation(
        source_id="sensor:beta",
        payload={"target_temp": 75.0},
        created_at="2026-09-21T12:00:00Z",  # Exact same timestamp with differing value
    )

    recon = enricher.reconstruct_state(
        reference_observation=obs_a,
        chronological_observations=[obs_a, obs_b_conflict],
        known_variable_names={"target_temp", "unobserved_sensor_rpm"},
    )

    var_temp = recon.get_variable("target_temp")
    assert var_temp is not None
    assert var_temp.is_conflicted is True

    var_unknown = recon.get_variable("unobserved_sensor_rpm")
    assert var_unknown is not None
    assert var_unknown.is_unknown is True
    assert var_unknown.latest_value == "UNKNOWN"
