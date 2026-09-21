"""Phase 5A: Embedded Attention Integration Tests."""

from __future__ import annotations

import pytest

from cognitia.runtime.local import LocalCognitiveRuntime
from cognitia.abi.types import Observation
from cognitia.attention.types import AttentionQuery

from tests.embedded.fixtures.host_adapter import SyntheticHostAdapter


class TestEmbeddedAttention:
    """Host application can perform attention over assembled context."""

    def test_attention_over_context(self, adapter: SyntheticHostAdapter) -> None:
        runtime = LocalCognitiveRuntime()
        for i in range(3):
            obs = adapter.create_order_submitted_observation(f"order_{i}", f"cust_{i}", float(i * 10))
            exp = adapter.create_experience_from_observation(obs).with_agent("host_app").build()
            runtime.persistence.save_object(exp)
        current_obs = adapter.create_order_submitted_observation("order_current", "cust_current", 500.0)
        context = runtime.assemble_context(current_obs)
        attention_result = runtime.focus_context(context)
        assert attention_result is not None
        assert hasattr(attention_result, "attention_items")
        assert hasattr(attention_result, "provenance")

    def test_recall_nequal_attention(self, adapter: SyntheticHostAdapter) -> None:
        runtime = LocalCognitiveRuntime()
        for i in range(3):
            obs = adapter.create_order_submitted_observation(f"order_{i}", f"cust_{i}", float(i * 10))
            exp = adapter.create_experience_from_observation(obs).with_agent("host_app").build()
            runtime.persistence.save_object(exp)
        current_obs = adapter.create_order_submitted_observation("order_current", "cust_current", 500.0)
        context = runtime.assemble_context(current_obs)
        attention_result = runtime.focus_context(context)
        from cognitia.recall.engine import InMemoryRecallEngine
        from cognitia.recall.types import RecallQuery, RecallObjectType
        recall_query = RecallQuery(object_types=(RecallObjectType.EXPERIENCE_RECORD,))
        recall_result = runtime.recall(recall_query)
        assert attention_result is not None
        assert recall_result is not None
        assert type(attention_result).__name__ != type(recall_result).__name__
