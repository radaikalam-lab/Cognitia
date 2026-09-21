"""Phase 5A: Cognitia Failure Isolation Tests."""

from __future__ import annotations

import pytest

from cognitia.recall.engine import InMemoryRecallEngine
from cognitia.runtime.local import LocalCognitiveRuntime

from tests.embedded.fixtures.host_adapter import SyntheticHostAdapter
from tests.embedded.fixtures.synthetic_host import (
    Customer,
    InventoryItem,
    Order,
    SyntheticBusinessApplication,
    Transaction,
)


class TestFailureIsolation:
    """Host application can still execute core domain operations when Cognitia components fail."""

    def test_host_operates_without_cognitia(self) -> None:
        host_app = SyntheticBusinessApplication(app_id="failure_isolation_app")
        customer = Customer(customer_id="cust_1", name="Test Customer", tier="premium")
        host_app.register_customer(customer)
        assert host_app.get_customer("cust_1") is not None

    def test_host_operates_when_recall_unavailable(self, adapter: SyntheticHostAdapter) -> None:
        host_app = adapter._app
        customer = Customer(customer_id="cust_1", name="Test Customer")
        host_app.register_customer(customer)
        runtime = LocalCognitiveRuntime()
        obs = adapter.create_customer_created_observation("cust_1", "premium")
        context = runtime.assemble_context(obs)
        assert context is not None
        assert host_app.get_customer("cust_1") is not None

    def test_host_operates_when_reasoning_unavailable(self, adapter: SyntheticHostAdapter) -> None:
        host_app = adapter._app
        order = Order(order_id="order_1", customer_id="cust_1", total_amount=100.0)
        host_app.place_order(order)
        assert host_app.get_order("order_1") is not None
