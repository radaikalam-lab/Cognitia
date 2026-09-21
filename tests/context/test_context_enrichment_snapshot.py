"""Tests for Context Enrichment Snapshot Immutability.

Validates that enriched Context snapshots remain frozen and unaffected by subsequent persistence operations.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.runtime.local import LocalCognitiveRuntime


def test_context_enrichment_snapshot_isolation() -> None:
    runtime = LocalCognitiveRuntime()

    obs_1 = Observation(
        source_id="sensor:1",
        payload={"level": 50.0},
        created_at="2026-09-21T10:00:00Z",
    )
    runtime.persistence.save_object(obs_1)

    ctx1 = runtime.assemble_context(obs_1)
    initial_agg_count = len(ctx1.aggregates)
    initial_seq_count = len(ctx1.sequences)

    # Mutate persistence at T2
    obs_2 = Observation(
        source_id="sensor:1",
        payload={"level": 90.0},
        created_at="2026-09-21T10:10:00Z",
    )
    runtime.persistence.save_object(obs_2)

    # Re-verify ctx1 is completely unchanged
    assert len(ctx1.aggregates) == initial_agg_count
    assert len(ctx1.sequences) == initial_seq_count

    # Assemble new context ctx2 at T2
    ctx2 = runtime.assemble_context(obs_2)
    assert len(ctx2.sequences) == 1
    assert len(ctx2.aggregates) == 1
    assert ctx2.aggregates[0].count == 2
