"""Phase 5A: Domain Authority Tests."""

from __future__ import annotations

import pytest

from cognitia.runtime.local import LocalCognitiveRuntime
from tests.embedded.fixtures.host_adapter import SyntheticHostAdapter
from tests.embedded.fixtures.synthetic_host import (
    Customer,
    InventoryItem,
    Order,
    SyntheticBusinessApplication,
)


class TestDomainAuthority:
    """Host application remains the authority over its domain state."""

    def test_host_inventory_unchanged_after_cognition(self, adapter: SyntheticHostAdapter) -> None:
        host_app = adapter._app
        item = InventoryItem(item_id="item_1", quantity=100, reorder_threshold=10)
        host_app.update_inventory(item)
        runtime = LocalCognitiveRuntime()
        obs = adapter.create_inventory_low_observation("item_1", 5, 10)
        context = runtime.assemble_context(obs)
        runtime.focus_context(context)
        assert host_app.get_inventory("item_1").quantity == 100

    def test_host_order_unchanged_without_explicit_mutation(self, adapter: SyntheticHostAdapter) -> None:
        host_app = adapter._app
        order = Order(order_id="order_1", customer_id="cust_1", total_amount=100.0, status="pending")
        host_app.place_order(order)
        runtime = LocalCognitiveRuntime()
        obs = adapter.create_order_submitted_observation("order_1", "cust_1", 100.0)
        context = runtime.assemble_context(obs)
        runtime.focus_context(context)
        retrieved = host_app.get_order("order_1")
        assert retrieved is not None
        assert retrieved.status == "pending"
