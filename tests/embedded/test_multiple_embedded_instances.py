"""Phase 5A: Multiple Embedded Instances Tests."""

from __future__ import annotations

import pytest

from cognitia.runtime.local import LocalCognitiveRuntime
from cognitia.recall.engine import InMemoryRecallEngine
from cognitia.recall.types import RecallQuery, RecallObjectType

from tests.embedded.fixtures.host_adapter import SyntheticHostAdapter
from tests.embedded.fixtures.synthetic_host import SyntheticBusinessApplication


class TestMultipleEmbeddedInstances:
    """Multiple host applications can coexist with isolated Cognitia runtimes."""

    def test_multiple_runtimes_isolated(self) -> None:
        app_a = SyntheticBusinessApplication(app_id="app_a")
        app_b = SyntheticBusinessApplication(app_id="app_b")
        adapter_a = SyntheticHostAdapter(app_a, app_id="app_a")
        adapter_b = SyntheticHostAdapter(app_b, app_id="app_b")
        runtime_a = LocalCognitiveRuntime()
        runtime_b = LocalCognitiveRuntime()
        obs_a = adapter_a.create_order_submitted_observation("order_a", "cust_a", 100.0)
        obs_b = adapter_b.create_order_submitted_observation("order_b", "cust_b", 200.0)
        exp_a = adapter_a.create_experience_from_observation(obs_a).with_agent("app_a").build()
        exp_b = adapter_b.create_experience_from_observation(obs_b).with_agent("app_b").build()
        runtime_a.persistence.save_object(exp_a)
        runtime_b.persistence.save_object(exp_b)
        assert len(runtime_a.persistence.list_all_objects()) == 1
        assert len(runtime_b.persistence.list_all_objects()) == 1

    def test_shared_runtime_optional(self) -> None:
        app_a = SyntheticBusinessApplication(app_id="app_a")
        app_b = SyntheticBusinessApplication(app_id="app_b")
        adapter_a = SyntheticHostAdapter(app_a, app_id="app_a")
        adapter_b = SyntheticHostAdapter(app_b, app_id="app_b")
        shared_runtime = LocalCognitiveRuntime()
        obs_a = adapter_a.create_order_submitted_observation("order_a", "cust_a", 100.0)
        obs_b = adapter_b.create_order_submitted_observation("order_b", "cust_b", 200.0)
        exp_a = adapter_a.create_experience_from_observation(obs_a).with_agent("app_a").build()
        exp_b = adapter_b.create_experience_from_observation(obs_b).with_agent("app_b").build()
        shared_runtime.persistence.save_object(exp_a)
        shared_runtime.persistence.save_object(exp_b)
        assert len(shared_runtime.persistence.list_all_objects()) == 2
