"""Synthetic host-to-Cognitia adapter.

Translates between SyntheticBusinessApplication domain events and
Cognitia canonical concepts (Observation, Action, Decision).

The adapter owns translation only. It does not own domain state.
"""

from __future__ import annotations

from typing import Any

from cognitia.abi.types import Action, Observation
from cognitia.experience.record import ExperienceBuilder


class SyntheticHostAdapter:
    """Minimal adapter translating synthetic host events to Cognitia concepts."""

    def __init__(self, app: SyntheticBusinessApplication, app_id: str = "synthetic_business_app") -> None:
        self._app = app
        self._app_id = app_id

    def create_observation(self, event_name: str, payload: dict[str, Any]) -> Observation:
        """Translate a host application event into a Cognitia Observation."""
        return Observation(
            source_id=f"{self._app_id}:{event_name}",
            payload=payload,
        )

    def create_order_submitted_observation(self, order_id: str, customer_id: str, total_amount: float) -> Observation:
        return self.create_observation(
            event_name="OrderSubmitted",
            payload={
                "order_id": order_id,
                "customer_id": customer_id,
                "total_amount": total_amount,
            },
        )

    def create_inventory_low_observation(self, item_id: str, quantity: int, threshold: int) -> Observation:
        return self.create_observation(
            event_name="InventoryLow",
            payload={
                "item_id": item_id,
                "quantity": quantity,
                "threshold": threshold,
            },
        )

    def create_customer_created_observation(self, customer_id: str, tier: str) -> Observation:
        return self.create_observation(
            event_name="CustomerCreated",
            payload={
                "customer_id": customer_id,
                "tier": tier,
            },
        )

    def create_experience_from_observation(
        self,
        observation: Observation,
        action: Action | None = None,
    ) -> ExperienceBuilder:
        """Wrap a translated observation in an ExperienceBuilder for persistence."""
        return (
            ExperienceBuilder(
                source_application=self._app_id,
                episode_id=observation.source_id,
            )
            .with_observation(observation)
            .with_action(action or Action())
        )
