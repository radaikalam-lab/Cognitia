"""Phase 5A: Embedded Application Integration Validation.

Tests proving Cognitia can be embedded directly inside a host application
without requiring a separate Cognitia service, network, or external dependencies.
"""

from __future__ import annotations

import pytest

from cognitia.abi.types import Action, Decision, Observation
from cognitia.attention.engine import DeterministicAttentionEngine
from cognitia.attention.types import AttentionQuery
from cognitia.capabilities.base import DeterministicMockDecisionProvider
from cognitia.context.engine import DeterministicContextAssembler
from cognitia.context.types import ContextQuery
from cognitia.experience.record import ExperienceBuilder
from cognitia.memory.store import InMemoryMemoryStore
from cognitia.persistence.store import InMemoryPersistenceStore
from cognitia.providers.gateway import InMemoryProviderGateway
from cognitia.providers.registry import InMemoryAdvancedProviderRegistry
from cognitia.recall.engine import InMemoryRecallEngine
from cognitia.reasoning.engine import DeterministicReasoningEngine
from cognitia.runtime.local import LocalCognitiveRuntime
from cognitia.service.facade import InMemoryExperienceService

from tests.embedded.fixtures.host_adapter import SyntheticHostAdapter
from tests.embedded.fixtures.synthetic_host import (
    Customer,
    InventoryItem,
    Order,
    SyntheticBusinessApplication,
    Transaction,
)


@pytest.fixture
def host_app() -> SyntheticBusinessApplication:
    return SyntheticBusinessApplication(app_id="test_synthetic_app")


@pytest.fixture
def adapter(host_app: SyntheticBusinessApplication) -> SyntheticHostAdapter:
    return SyntheticHostAdapter(host_app, app_id="test_synthetic_app")


@pytest.fixture
def runtime() -> LocalCognitiveRuntime:
    return LocalCognitiveRuntime()


class TestEmbeddedRuntimeInstantiation:
    """Cognitia can be instantiated inside a normal host application process."""

    def test_embedded_runtime_no_service_required(self, runtime: LocalCognitiveRuntime) -> None:
        assert runtime is not None
        assert runtime.persistence is not None
        assert runtime.memory is not None
        assert runtime.recall_engine is not None
        assert runtime.context_assembler is not None
        assert runtime.attention_engine is not None
        assert runtime.reasoning_engine is not None

    def test_runtime_is_normal_python_object(self, runtime: LocalCognitiveRuntime) -> None:
        assert hasattr(runtime, "recall")
        assert hasattr(runtime, "assemble_context")
        assert hasattr(runtime, "focus_context")
        assert hasattr(runtime, "reason")


class TestHostAdapterBoundary:
    """Adapter translates host events to Cognitia observations."""

    def test_host_event_becomes_observation(self, adapter: SyntheticHostAdapter) -> None:
        observation = adapter.create_order_submitted_observation(
            order_id="order_1",
            customer_id="cust_1",
            total_amount=100.0,
        )
        assert observation.source_id.endswith("OrderSubmitted")
        assert observation.payload["order_id"] == "order_1"

    def test_adapter_does_not_mutate_host_state(self, host_app: SyntheticBusinessApplication, adapter: SyntheticHostAdapter) -> None:
        initial_order_count = len(host_app.orders)
        observation = adapter.create_order_submitted_observation(
            order_id="order_new",
            customer_id="cust_1",
            total_amount=50.0,
        )
        assert len(host_app.orders) == initial_order_count
        assert "order_new" not in host_app.orders


class TestEmbeddedPersistence:
    """Host application can persist observations through embedded Cognitia."""

    def test_persist_observation_via_runtime(self, runtime: LocalCognitiveRuntime, adapter: SyntheticHostAdapter) -> None:
        observation = adapter.create_customer_created_observation("cust_1", "premium")
        experience = (
            adapter.create_experience_from_observation(observation)
            .with_agent("host_app")
            .build()
        )
        runtime.persistence.save_object(experience)
        assert len(runtime.persistence.list_all_objects()) == 1

    def test_persist_multiple_observations(self, runtime: LocalCognitiveRuntime, adapter: SyntheticHostAdapter) -> None:
        for i in range(3):
            observation = adapter.create_order_submitted_observation(f"order_{i}", f"cust_{i}", float(i * 10))
            experience = (
                adapter.create_experience_from_observation(observation)
                .with_agent("host_app")
                .build()
            )
            runtime.persistence.save_object(experience)
        assert len(runtime.persistence.list_all_objects()) == 3
