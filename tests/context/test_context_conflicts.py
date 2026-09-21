"""Tests for Context Conflict Preservation Enrichment.

Validates that observational conflicts occurring at identical timestamps/subjects
are preserved in ContextConflict structures without silent overwrites or premature resolution.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.runtime.local import LocalCognitiveRuntime


def test_context_conflict_preservation() -> None:
    runtime = LocalCognitiveRuntime()

    # Two conflicting observations at the exact same timestamp for the same subject
    obs_1 = Observation(
        source_id="sensor:north:channel_a",
        payload={"temperature": 70.0},
        created_at="2026-09-21T10:00:00Z",
        metadata={"subject_id": "CHAMBER-1"},
    )
    obs_2 = Observation(
        source_id="sensor:north:channel_b",
        payload={"temperature": 90.0},
        created_at="2026-09-21T10:00:00Z",
        metadata={"subject_id": "CHAMBER-1"},
    )

    runtime.persistence.save_object(obs_1)
    runtime.persistence.save_object(obs_2)

    context = runtime.assemble_context(obs_1)

    assert len(context.conflicts) == 1
    conflict = context.conflicts[0]
    assert conflict.conflict_type == "concurrent_value_divergence"
    assert obs_1.id in conflict.object_ids
    assert obs_2.id in conflict.object_ids
