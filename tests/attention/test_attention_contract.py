"""Tests for Cognitia Cognitive Attention Contract Invariants and Schema.

Validates that Attention types adhere to immutability, reference non-duplication,
and contract specifications.
"""

import dataclasses
import pytest

from cognitia.abi.types import Observation
from cognitia.attention.engine import DeterministicAttentionEngine
from cognitia.attention.types import (
    AttentionItem,
    AttentionQuery,
    AttentionReason,
    AttentionResult,
)
from cognitia.context.types import CognitiveContext, ContextItem, RelevanceReason
from cognitia.epistemic.types import EpistemicStatus


def test_attention_query_immutability() -> None:
    query = AttentionQuery(
        task_id="task_001",
        task_type="anomaly_investigation",
        focus_subject_ids=["SUB-1", "SUB-2"],
        requested_item_types=["Observation", "CognitiveRule"],
        maximum_items=3,
        minimum_score=0.2,
        target_epistemic_statuses=[EpistemicStatus.REFUTED],
        scope="erp.finance",
        parameters={"priority": "high"},
    )

    assert query.task_id == "task_001"
    assert query.task_type == "anomaly_investigation"
    assert query.focus_subject_ids == ("SUB-1", "SUB-2")
    assert query.requested_item_types == ("Observation", "CognitiveRule")
    assert query.maximum_items == 3
    assert query.minimum_score == 0.2
    assert query.target_epistemic_statuses == (EpistemicStatus.REFUTED,)
    assert query.scope == "erp.finance"
    assert query.parameters_dict == {"priority": "high"}

    with pytest.raises(dataclasses.FrozenInstanceError):
        query.task_id = "mutated_task"  # type: ignore


def test_attention_item_immutability() -> None:
    item = AttentionItem(
        item_id="obs_123",
        rank=1,
        attention_score=0.85,
        source_context_item_id="obs_123",
        selection_reasons=[AttentionReason.TASK_MATCH, AttentionReason.SUBJECT_MATCH],
        epistemic_status=EpistemicStatus.OBSERVED,
        metadata={"weight": 1.0},
    )

    assert item.item_id == "obs_123"
    assert item.rank == 1
    assert item.attention_score == 0.85
    assert item.selection_reasons == (AttentionReason.TASK_MATCH, AttentionReason.SUBJECT_MATCH)
    assert item.metadata_dict == {"weight": 1.0}

    with pytest.raises(dataclasses.FrozenInstanceError):
        item.rank = 2  # type: ignore


def test_attention_result_immutability() -> None:
    item = AttentionItem(
        item_id="obs_1",
        rank=1,
        attention_score=0.9,
        source_context_item_id="obs_1",
        selection_reasons=[AttentionReason.REFERENCE_ITEM],
    )
    result = AttentionResult(
        reference_observation_id="obs_1",
        context_id="ctx_001",
        task_id="task_001",
        task_type="general_focus",
        selected_item_ids=("obs_1",),
        attention_items=(item,),
        budget_limit=5,
    )

    assert result.context_id == "ctx_001"
    assert result.selected_item_ids == ("obs_1",)
    assert result.get_item("obs_1") == item
    assert result.get_item("non_existent") is None

    with pytest.raises(dataclasses.FrozenInstanceError):
        result.task_id = "mutated"  # type: ignore


def test_attention_does_not_duplicate_context() -> None:
    """Attention references context item IDs rather than duplicating objects."""
    obs = Observation(
        source_id="app:sensor:1",
        payload={"sensor_value": 42.0, "heavy_data": [1] * 1000},
    )
    ctx_item = ContextItem(
        item_id=obs.id,
        item_type="Observation",
        relevance_reason=RelevanceReason.REFERENCE_OBSERVATION,
        relevance_score=1.0,
    )
    ctx = CognitiveContext(
        reference_observation_id=obs.id,
        context_items=(ctx_item,),
    )

    engine = DeterministicAttentionEngine()
    result = engine.focus(ctx, AttentionQuery(maximum_items=1))

    assert len(result.attention_items) == 1
    att_item = result.attention_items[0]
    assert att_item.item_id == obs.id
    assert att_item.source_context_item_id == obs.id
    # Attention does not store payload
    assert not hasattr(att_item, "payload")
