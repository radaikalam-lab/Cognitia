"""Synthetic domain-neutral host application for embedded Cognitia integration tests.

This module represents a generic host application that owns its domain state
and delegates cognitive processing to an embedded Cognitia runtime.

The host application is domain-neutral. It uses generic entities:
- Customer
- Order
- InventoryItem
- Transaction

Cognitia is used only as an advisory cognitive layer.
Cognitia never directly mutates host domain state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Customer:
    """Synthetic host customer entity."""

    customer_id: str
    name: str
    tier: str = "standard"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Order:
    """Synthetic host order entity."""

    order_id: str
    customer_id: str
    items: list[str] = field(default_factory=list)
    total_amount: float = 0.0
    status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InventoryItem:
    """Synthetic host inventory entity."""

    item_id: str
    quantity: int = 0
    reorder_threshold: int = 10
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Transaction:
    """Synthetic host transaction entity."""

    transaction_id: str
    amount: float = 0.0
    currency: str = "USD"
    status: str = "pending"
    metadata: dict[str, Any] = field(default_factory=dict)


class SyntheticBusinessApplication:
    """Minimal synthetic host application demonstrating embedded Cognitia usage.

    The host application:
    - Owns domain state (customers, orders, inventory, transactions)
    - Translates domain events into Cognitia Observations
    - Receives Cognitia advisories and decides whether to act
    - Never allows Cognitia to directly mutate domain state
    """

    def __init__(self, app_id: str = "synthetic_business_app") -> None:
        self.app_id = app_id
        self._customers: dict[str, Customer] = {}
        self._orders: dict[str, Order] = {}
        self._inventory: dict[str, InventoryItem] = {}
        self._transactions: dict[str, Transaction] = {}

    # --- Domain state mutation (host authority) ---

    def register_customer(self, customer: Customer) -> None:
        self._customers[customer.customer_id] = customer

    def place_order(self, order: Order) -> None:
        self._orders[order.order_id] = order

    def update_inventory(self, item: InventoryItem) -> None:
        self._inventory[item.item_id] = item

    def record_transaction(self, transaction: Transaction) -> None:
        self._transactions[transaction.transaction_id] = transaction

    # --- Domain state queries ---

    def get_customer(self, customer_id: str) -> Customer | None:
        return self._customers.get(customer_id)

    def get_order(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    def get_inventory(self, item_id: str) -> InventoryItem | None:
        return self._inventory.get(item_id)

    def get_transaction(self, transaction_id: str) -> Transaction | None:
        return self._transactions.get(transaction_id)

    @property
    def customers(self) -> dict[str, Customer]:
        return dict(self._customers)

    @property
    def orders(self) -> dict[str, Order]:
        return dict(self._orders)

    @property
    def inventory(self) -> dict[str, InventoryItem]:
        return dict(self._inventory)

    @property
    def transactions(self) -> dict[str, Transaction]:
        return dict(self._transactions)

    # --- Advisory boundary ---

    def receive_advisory(self, advisory: Any) -> None:
        """Host application receives a Cognitia advisory.

        The host may inspect the advisory and decide whether to act.
        Cognitia does not automatically mutate host state.
        """
        if hasattr(advisory, "confidence") and advisory.confidence < 0.5:
            return
        # In a real application, the host would decide whether to act.
        # Here we simply acknowledge receipt without mutating state.
