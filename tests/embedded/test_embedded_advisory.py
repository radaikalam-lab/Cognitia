"""Phase 5A: Embedded Advisory Boundary Tests."""

from __future__ import annotations

import pytest

from cognitia.runtime.local import LocalCognitiveRuntime
from cognitia.abi.types import Decision, Observation
from cognitia.reasoning.types import ReasoningInput, ReasoningMode

from tests.embedded.fixtures.host_adapter import SyntheticHostAdapter
from tests.embedded.fixtures.synthetic_host import (
    Customer,
    InventoryItem,
    Order,
    SyntheticBusinessApplication,
)


class TestEmbeddedAdvisory:
    """Cognitia returns advisories to host application without mutating domain state."""

    def test_cognitia_does_not_mutate_host_state(self, adapter: SyntheticHostAdapter) -> None:
        host_app = adapter._app
        initial_inventory = {item_id: item.quantity for item_id, item in host_app.inventory.items()}
        runtime = LocalCognitiveRuntime()
        obs = adapter.create_inventory_low_observation("item_1", 5, 10)
        context = runtime.assemble_context(obs)
        runtime.focus_context(context)
        for item_id, item in host_app.inventory.items():
            assert item.quantity == initial_inventory.get(item_id, item.quantity)

    def test_host_receives_advisory_and_decides(self, adapter: SyntheticHostAdapter) -> None:
        host_app = adapter._app
        runtime = LocalCognitiveRuntime()
        obs = adapter.create_order_submitted_observation("order_1", "cust_1", 100.0)
        context = runtime.assemble_context(obs)
        attention_result = runtime.focus_context(context)
        reasoning_input = ReasoningInput(
            reasoning_mode=ReasoningMode.DEDUCTION,
            premises=(),
            attention_result_id=attention_result.id,
        )
        _, result = runtime.reason(reasoning_input)
        assert result.candidate_conclusions is not None
        host_app.receive_advisory(result.candidate_conclusions)
        assert "order_1" not in host_app.orders
