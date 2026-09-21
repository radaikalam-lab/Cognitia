"""Tests for Memory Layer Retrieval of Frappe ERP Historical Experiences."""

import pytest

from cognitia.memory.types import MemoryQuery
from cognitia.runtime.local import LocalCognitiveRuntime
from adapters.frappe.client import FrappeCognitiaAdapter
from adapters.frappe.events import FrappeEvent, FrappeEventType
from adapters.frappe.experience import ERPLifecycleType


def test_erp_memory_retrieval_by_subject() -> None:
    runtime = LocalCognitiveRuntime()
    adapter = FrappeCognitiaAdapter(runtime=runtime)

    # Ingest historical events for Customer CUST-100
    obs1 = adapter.ingest_event(
        FrappeEvent(
            event_type=FrappeEventType.SALES_ORDER_SUBMITTED,
            doc_type="Sales Order",
            doc_name="SO-100",
            payload={"customer": "CUST-100", "total": 5000.0},
        )
    )
    obs2 = adapter.ingest_event(
        FrappeEvent(
            event_type=FrappeEventType.DELIVERY_NOTE_SUBMITTED,
            doc_type="Delivery Note",
            doc_name="DN-100",
            payload={"customer": "CUST-100", "status": "completed"},
        )
    )
    # Form experience for CUST-100
    adapter.record_lifecycle_experience(
        lifecycle_id="CYCLE-100",
        lifecycle_type=ERPLifecycleType.SALES_ORDER_LIFECYCLE,
        observations=[obs1, obs2],
    )

    # Ingest historical events for Customer CUST-200
    obs3 = adapter.ingest_event(
        FrappeEvent(
            event_type=FrappeEventType.SALES_ORDER_SUBMITTED,
            doc_type="Sales Order",
            doc_name="SO-200",
            payload={"customer": "CUST-200", "total": 8000.0},
        )
    )
    adapter.record_lifecycle_experience(
        lifecycle_id="CYCLE-200",
        lifecycle_type=ERPLifecycleType.SALES_ORDER_LIFECYCLE,
        observations=[obs3],
    )

    # Memory Query: retrieve all Frappe experiences
    query_all = MemoryQuery(
        source_application="frappe",
        object_types=["ExperienceRecord"],
    )
    items_all = runtime.memory.retrieve(query_all)
    assert len(items_all) == 2

    # Memory Query: retrieve observations filtered by episode/doc_name
    query_episode = MemoryQuery(
        source_application="frappe",
        episode_id="SO-100",
    )
    items_episode = runtime.memory.retrieve(query_episode)
    assert len(items_episode) == 1
    assert items_episode[0].source_id == "frappe:Sales Order:SO-100"
