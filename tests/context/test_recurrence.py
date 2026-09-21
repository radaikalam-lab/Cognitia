"""Tests for Recurrence Context Enrichment.

Validates recurrence count, observation interval calculations, and median/latest interval metrics.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.runtime.local import LocalCognitiveRuntime


def test_recurrence_calculation() -> None:
    runtime = LocalCognitiveRuntime()

    # 4 recurring events spaced at 10s, 20s, 30s intervals
    obs_1 = Observation(source_id="app:job", payload={"job": "SYNC"}, created_at="2026-09-21T10:00:00Z")
    obs_2 = Observation(source_id="app:job", payload={"job": "SYNC"}, created_at="2026-09-21T10:00:10Z")
    obs_3 = Observation(source_id="app:job", payload={"job": "SYNC"}, created_at="2026-09-21T10:00:30Z")
    obs_4 = Observation(source_id="app:job", payload={"job": "SYNC"}, created_at="2026-09-21T10:01:00Z")

    runtime.persistence.save_object(obs_1)
    runtime.persistence.save_object(obs_2)
    runtime.persistence.save_object(obs_3)
    runtime.persistence.save_object(obs_4)

    context = runtime.assemble_context(obs_4)

    assert len(context.recurrence) == 1
    rec = context.recurrence[0]
    assert rec.occurrence_count == 4
    assert rec.intervals_seconds == (10.0, 20.0, 30.0)
    assert rec.median_interval_seconds == 20.0
    assert rec.latest_interval_seconds == 30.0
    assert rec.window_seconds == 60.0
