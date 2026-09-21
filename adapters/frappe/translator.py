"""Frappe Event Translator.

Translates Frappe ERP events into domain-neutral Cognitia Observations
while preserving document identity, timestamp, subject identity, payload, and provenance.
"""

from __future__ import annotations

from typing import Any

from cognitia.abi.types import Observation, current_utc_timestamp
from cognitia.provenance.record import ProvenanceRecord, SourceType

from adapters.frappe.events import FrappeEvent, FrappeEventType


class FrappeEventTranslator:
    """Translates incoming Frappe business events into canonical Cognitia Observations."""

    @staticmethod
    def translate(event: FrappeEvent) -> Observation:
        """Convert a FrappeEvent into an immutable Cognitia Observation with full provenance."""
        event_type_str = (
            event.event_type.value
            if isinstance(event.event_type, FrappeEventType)
            else str(event.event_type)
        )
        
        # Derive primary subject identifier if not explicitly provided
        subject_id = event.subject_id
        if not subject_id:
            subject_id = (
                event.payload.get("customer")
                or event.payload.get("supplier")
                or event.payload.get("item_code")
                or event.payload.get("patient")
                or event.payload.get("employee")
                or event.doc_name
            )

        timestamp = event.timestamp or current_utc_timestamp()

        # Build clean observation payload preserving all original data
        obs_payload: dict[str, Any] = {
            "event_type": event_type_str,
            "doc_type": event.doc_type,
            "doc_name": event.doc_name,
            "subject_id": subject_id,
            "user": event.user,
            "data": dict(event.payload),
        }

        # Build metadata for filtering and indexing
        metadata: dict[str, Any] = {
            "source_application": "frappe",
            "doc_type": event.doc_type,
            "doc_name": event.doc_name,
            "subject_id": subject_id,
            "event_type": event_type_str,
        }

        obs = Observation(
            source_id=f"frappe:{event.doc_type}:{event.doc_name}",
            payload=obs_payload,
            created_at=timestamp,
            metadata=metadata,
        )

        return obs
