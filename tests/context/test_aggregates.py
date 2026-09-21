"""Tests for Deterministic Aggregate Context Enrichment.

Validates descriptive statistical calculations (count, min, max, mean, median, range, std dev, deltas)
and confirms adherence to sample standard deviation (N-1) convention.
"""

import math
import statistics
import pytest

from cognitia.abi.types import Observation
from cognitia.runtime.local import LocalCognitiveRuntime


def test_deterministic_aggregates_computation() -> None:
    runtime = LocalCognitiveRuntime()

    # 4 prior observations: 10.0, 20.0, 30.0, 40.0
    values = [10.0, 20.0, 30.0, 40.0]
    for i, v in enumerate(values):
        obs = Observation(
            source_id="meter:power",
            payload={"current_amps": v},
            created_at=f"2026-09-21T10:0{i}:00Z",
        )
        runtime.persistence.save_object(obs)

    # Reference observation is the 5th one (value 50.0)
    ref_obs = Observation(
        source_id="meter:power",
        payload={"current_amps": 50.0},
        created_at="2026-09-21T10:04:00Z",
    )
    runtime.persistence.save_object(ref_obs)

    all_values = values + [50.0]
    context = runtime.assemble_context(ref_obs)

    agg = [a for a in context.aggregates if a.metric == "current_amps"][0]
    assert agg.count == 5
    assert agg.min_value == 10.0
    assert agg.max_value == 50.0
    assert agg.mean_value == 30.0
    assert agg.median_value == 30.0
    assert agg.range_value == 40.0
    assert math.isclose(agg.std_dev or 0.0, statistics.stdev(all_values), rel_tol=1e-5)
    assert agg.latest_value == 50.0
    assert agg.delta_from_previous == 10.0
    assert agg.delta_from_mean == 20.0
