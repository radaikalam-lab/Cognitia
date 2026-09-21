"""Tests for Automotive-like Synthetic Domain Context Enrichment.

Validates that Context Enrichment functions domain-neutrally on automotive-like telemetry:
- Vehicle V001 observed sequence: Acceleration -> Boost increase -> Fuel demand -> Temperature increase
- Observable state reconstruction before/after
- Historical baseline & aggregates (RPM, Boost, CoolantTemp, Speed)
- Cross-sensor correlation
- Contextual deviation indicators
- Seamless Attention consumption of enriched Context
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.attention.types import AttentionQuery
from cognitia.context.types import DeviationType
from cognitia.runtime.local import LocalCognitiveRuntime


def test_automotive_synthetic_context_enrichment() -> None:
    runtime = LocalCognitiveRuntime()

    # Telemetry stream representing Vehicle V001
    # Step 1: Idle cruise
    obs_1 = Observation(
        source_id="ecu:telemetry:v001",
        payload={
            "rpm": 1800.0,
            "boost_bar": 0.2,
            "coolant_temp_c": 88.0,
            "speed_kmh": 60.0,
            "operating_mode": "CRUISE",
        },
        created_at="2026-09-21T14:00:00Z",
        metadata={"subject_id": "VEHICLE-V001", "source_application": "ecu_telemetry"},
    )

    # Step 2: Acceleration demand initiated
    obs_2 = Observation(
        source_id="ecu:telemetry:v001",
        payload={
            "rpm": 2500.0,
            "boost_bar": 0.8,
            "coolant_temp_c": 89.0,
            "speed_kmh": 75.0,
            "operating_mode": "ACCEL",
            "accel_demand_pct": 80.0,
        },
        created_at="2026-09-21T14:00:02Z",
        metadata={"subject_id": "VEHICLE-V001", "source_application": "ecu_telemetry"},
    )

    # Step 3: Boost and fuel demand increase
    obs_3 = Observation(
        source_id="boost:sensor:v001",
        payload={
            "boost_bar": 1.6,
            "manifold_pressure_bar": 2.6,
        },
        created_at="2026-09-21T14:00:04Z",
        metadata={"subject_id": "VEHICLE-V001", "source_application": "boost_controller"},
    )

    # Step 4: High load temperature & speed
    obs_4 = Observation(
        source_id="ecu:telemetry:v001",
        payload={
            "rpm": 3800.0,
            "boost_bar": 1.7,
            "coolant_temp_c": 98.0,
            "speed_kmh": 110.0,
            "operating_mode": "HIGH_LOAD",
        },
        created_at="2026-09-21T14:00:08Z",
        metadata={"subject_id": "VEHICLE-V001", "source_application": "ecu_telemetry"},
    )

    runtime.persistence.save_object(obs_1)
    runtime.persistence.save_object(obs_2)
    runtime.persistence.save_object(obs_3)
    runtime.persistence.save_object(obs_4)

    # Assemble context around reference observation 4
    context = runtime.assemble_context(obs_4)

    # 1. Verify Event Sequence
    assert len(context.sequences) == 1
    seq = context.sequences[0]
    assert seq.event_ids == (obs_1.id, obs_2.id, obs_3.id, obs_4.id)

    # 2. Verify State Reconstruction
    state = context.state_reconstruction
    var_mode = state.get_variable("operating_mode")
    assert var_mode is not None
    assert var_mode.latest_value == "HIGH_LOAD"
    assert var_mode.previous_value == "ACCEL"
    assert var_mode.first_known_value == "CRUISE"

    # 3. Verify Deterministic Aggregates
    agg_rpm = [a for a in context.aggregates if a.metric == "rpm"][0]
    assert agg_rpm.count == 3  # obs_1, obs_2, obs_4
    assert agg_rpm.min_value == 1800.0
    assert agg_rpm.max_value == 3800.0
    assert agg_rpm.latest_value == 3800.0

    # 4. Verify Cross-Sensor Correlation (ecu_telemetry vs boost_controller)
    assert len(context.correlations) >= 1
    corr = [c for c in context.correlations if "boost_controller" in (c.source_a_app, c.source_b_app)][0]
    assert corr.time_delta_seconds >= 0.0

    # 5. Verify Contextual Deviations (coolant_temp_c latest 98.0 is above historical max 89.0)
    dev_temp = [d for d in context.deviations if d.metric == "coolant_temp_c"][0]
    assert dev_temp.deviation_type == DeviationType.ABOVE_HISTORICAL_RANGE
    assert dev_temp.magnitude == 9.0  # 98.0 - 89.0

    # 6. Verify Attention compatibility on enriched context
    attention = runtime.focus_context(
        context,
        AttentionQuery(task_type="anomaly_investigation", maximum_items=3),
    )
    assert len(attention.attention_items) >= 1
    assert obs_4.id in attention.selected_item_ids
