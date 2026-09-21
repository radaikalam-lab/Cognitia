"""Phase 5A: Embedded Context Integration Tests."""

from __future__ import annotations

import pytest

from cognitia.abi.types import Observation
from cognitia.runtime.local import LocalCognitiveRuntime
from cognitia.context.engine import DeterministicContextAssembler
from cognitia.context.types import ContextQuery

from tests.embedded.fixtures.host_adapter import SyntheticHostAdapter
from tests.embedded.fixtures.synthetic_host import SyntheticBusinessApplication


@pytest.fixture
def host_app() -> SyntheticBusinessApplication:
    return SyntheticBusinessApplication(app_id="context_test_app")


@pytest.fixture
def adapter(host_app: SyntheticBusinessApplication) -> SyntheticHostAdapter:
    return SyntheticHostAdapter(host_app, app_id="context_test_app")


class TestEmbeddedContext:
    """Host application can assemble cognitive context from current observation and recalled memory."""

    def test_context_assembles_with_current_observation(self, adapter: SyntheticHostAdapter) -> None:
        runtime = LocalCognitiveRuntime()
        observation = adapter.create_order_submitted_observation("order_1", "cust_1", 100.0)
        context = runtime.assemble_context(observation)
        assert context is not None

    def test_context_includes_recalled_memory(self, adapter: SyntheticHostAdapter) -> None:
        runtime = LocalCognitiveRuntime()
        for i in range(3):
            obs = adapter.create_order_submitted_observation(f"order_{i}", f"cust_{i}", float(i * 10))
            exp = adapter.create_experience_from_observation(obs).with_agent("host_app").build()
            runtime.persistence.save_object(exp)
        current_obs = adapter.create_order_submitted_observation("order_current", "cust_current", 500.0)
        context = runtime.assemble_context(current_obs)
        assert len(context.related_experience_ids) >= 3
