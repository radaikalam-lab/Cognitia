"""Tests for Context Compression Enrichment.

Validates that ContextCompression computes deterministic structural summaries
without duplicating Attention or performing task-dependent item prioritization.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.runtime.local import LocalCognitiveRuntime


def test_context_compression_summary() -> None:
    runtime = LocalCognitiveRuntime()

    obs_1 = Observation(
        source_id="app1:sensor",
        payload={"v": 10},
        created_at="2026-09-21T10:00:00Z",
        metadata={"subject_id": "SUB-1", "source_application": "app1"},
    )
    obs_2 = Observation(
        source_id="app2:sensor",
        payload={"v": 20},
        created_at="2026-09-21T10:05:00Z",
        metadata={"subject_id": "SUB-2", "source_application": "app2"},
    )

    runtime.persistence.save_object(obs_1)
    runtime.persistence.save_object(obs_2)

    context = runtime.assemble_context(obs_2)

    assert context.compression is not None
    comp = context.compression
    assert comp.observation_count == 2
    assert comp.timespan_seconds == 300.0
    assert comp.subject_count == 2
    assert comp.source_count == 2
    assert not hasattr(comp, "selected_items")
    assert not hasattr(comp, "ranked_items")
