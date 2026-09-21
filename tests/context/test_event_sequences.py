"""Tests for Event Sequence Context Enrichment.

Validates chronological sequence detection, relative position tracking,
and delta logging without inferring causality.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.runtime.local import LocalCognitiveRuntime


def test_event_sequence_chronological_ordering() -> None:
    runtime = LocalCognitiveRuntime()

    obs_1 = Observation(source_id="step:1", payload={"step": "LOAD"}, created_at="2026-09-21T10:00:00Z")
    obs_2 = Observation(source_id="step:2", payload={"step": "PREHEAT"}, created_at="2026-09-21T10:00:10Z")
    obs_3 = Observation(source_id="step:3", payload={"step": "DISCHARGE"}, created_at="2026-09-21T10:00:20Z")
    obs_4 = Observation(source_id="step:4", payload={"step": "ANALYZE"}, created_at="2026-09-21T10:00:30Z")

    runtime.persistence.save_object(obs_1)
    runtime.persistence.save_object(obs_2)
    runtime.persistence.save_object(obs_3)
    runtime.persistence.save_object(obs_4)

    context = runtime.assemble_context(obs_3)

    assert len(context.sequences) == 1
    seq = context.sequences[0]
    assert seq.event_ids == (obs_1.id, obs_2.id, obs_3.id, obs_4.id)

    positions = seq.positions_dict
    assert positions[obs_1.id] == 1
    assert positions[obs_2.id] == 2
    assert positions[obs_3.id] == 3
    assert positions[obs_4.id] == 4

    deltas_dict = dict(seq.time_deltas)
    assert deltas_dict[obs_1.id] == -20.0
    assert deltas_dict[obs_2.id] == -10.0
    assert deltas_dict[obs_3.id] == 0.0
    assert deltas_dict[obs_4.id] == 10.0
