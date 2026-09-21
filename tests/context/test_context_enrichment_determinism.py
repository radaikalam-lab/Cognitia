"""Tests for Context Enrichment Determinism.

Validates that all enrichment operations produce identical, reproducible structures
given identical input observations and query parameters.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.runtime.local import LocalCognitiveRuntime


def test_context_enrichment_reproducibility() -> None:
    runtime = LocalCognitiveRuntime()

    obs_1 = Observation(
        source_id="device:a",
        payload={"flow": 10.0, "rpm": 1200},
        created_at="2026-09-21T10:00:00Z",
        metadata={"subject_id": "UNIT-1", "source_application": "scada"},
    )
    obs_2 = Observation(
        source_id="device:b",
        payload={"flow": 15.0, "rpm": 1400},
        created_at="2026-09-21T10:01:00Z",
        metadata={"subject_id": "UNIT-1", "source_application": "telemetry"},
    )

    runtime.persistence.save_object(obs_1)
    runtime.persistence.save_object(obs_2)

    ctx1 = runtime.assemble_context(obs_2)
    ctx2 = runtime.assemble_context(obs_2)

    # Verify identical enriched structures
    assert len(ctx1.entity_neighbourhood) == len(ctx2.entity_neighbourhood)
    assert len(ctx1.sequences) == len(ctx2.sequences)
    assert len(ctx1.aggregates) == len(ctx2.aggregates)
    assert len(ctx1.deviations) == len(ctx2.deviations)
    assert len(ctx1.correlations) == len(ctx2.correlations)

    for a1, a2 in zip(ctx1.aggregates, ctx2.aggregates):
        assert a1.metric == a2.metric
        assert a1.mean_value == a2.mean_value
        assert a1.std_dev == a2.std_dev
