"""Phase 5A: Embedded Recall Integration Tests."""

from __future__ import annotations

import pytest

from cognitia.runtime.local import LocalCognitiveRuntime
from cognitia.recall.engine import InMemoryRecallEngine
from cognitia.recall.types import RecallObjectType, RecallQuery

from tests.embedded.fixtures.host_adapter import SyntheticHostAdapter
from tests.embedded.fixtures.synthetic_host import SyntheticBusinessApplication


@pytest.fixture
def host_app() -> SyntheticBusinessApplication:
    return SyntheticBusinessApplication(app_id="recall_test_app")


@pytest.fixture
def adapter(host_app: SyntheticBusinessApplication) -> SyntheticHostAdapter:
    return SyntheticHostAdapter(host_app, app_id="recall_test_app")


@pytest.fixture
def populated_runtime(adapter: SyntheticHostAdapter) -> LocalCognitiveRuntime:
    runtime = LocalCognitiveRuntime()
    for i in range(5):
        obs = adapter.create_order_submitted_observation(f"order_{i}", f"cust_{i}", float(i * 10))
        exp = (
            adapter.create_experience_from_observation(obs)
            .with_agent("host_app")
            .build()
        )
        runtime.persistence.save_object(exp)
    return runtime


class TestEmbeddedRecall:
    """Host application can retrieve historical memory through embedded Cognitia Recall."""

    def test_recall_returns_historical_experiences(self, populated_runtime: LocalCognitiveRuntime, adapter: SyntheticHostAdapter) -> None:
        query = RecallQuery(object_types=(RecallObjectType.EXPERIENCE_RECORD,))
        result = populated_runtime.recall(query)
        assert result.total_evaluated >= 5

    def test_recall_with_episode_filter(self, populated_runtime: LocalCognitiveRuntime, adapter: SyntheticHostAdapter) -> None:
        obs = adapter.create_order_submitted_observation("order_target", "cust_target", 999.0)
        exp = adapter.create_experience_from_observation(obs).with_agent("host_app").build()
        populated_runtime.persistence.save_object(exp)
        query = RecallQuery(
            object_types=(RecallObjectType.EXPERIENCE_RECORD,),
            episode_id="recall_test_app:OrderSubmitted",
        )
        result = populated_runtime.recall(query)
        assert result.total_matched >= 1

    def test_recall_with_trace(self, populated_runtime: LocalCognitiveRuntime) -> None:
        query = RecallQuery(object_types=(RecallObjectType.EXPERIENCE_RECORD,))
        result, trace = populated_runtime.recall_with_trace(query)
        assert trace.total_evaluated == result.total_evaluated
        assert trace.total_matched == result.total_matched
