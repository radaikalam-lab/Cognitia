"""Tests for Contextual Deviation Enrichment.

Validates detection of contextual deviations against historical baselines
(ABOVE_HISTORICAL_RANGE, BELOW_HISTORICAL_RANGE, RAPID_CHANGE) without asserting faults or diagnosis.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.context.types import DeviationType
from cognitia.runtime.local import LocalCognitiveRuntime


def test_contextual_deviation_above_range() -> None:
    runtime = LocalCognitiveRuntime()

    # Historical observations: 65, 70, 75
    for i, temp in enumerate([65.0, 70.0, 75.0]):
        runtime.persistence.save_object(
            Observation(
                source_id="temp:sensor",
                payload={"temperature_c": temp},
                created_at=f"2026-09-21T10:0{i}:00Z",
            )
        )

    # Reference observation: 90.0 (above historical max 75.0 by 15.0)
    current_obs = Observation(
        source_id="temp:sensor",
        payload={"temperature_c": 90.0},
        created_at="2026-09-21T10:05:00Z",
    )
    runtime.persistence.save_object(current_obs)

    context = runtime.assemble_context(current_obs)

    assert len(context.deviations) >= 1
    dev = [d for d in context.deviations if d.metric == "temperature_c"][0]
    assert dev.deviation_type == DeviationType.ABOVE_HISTORICAL_RANGE
    assert dev.current_value == 90.0
    assert dev.baseline_reference == (65.0, 75.0)
    assert dev.magnitude == 15.0
