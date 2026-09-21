"""Cognitia Persistence Store Interface and In-Memory Reference Implementation."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cognitia.abi.types import CognitiveObject, DeterministicSerializer
from cognitia.persistence.events import (
    CognitiveEvent,
    EventQuery,
    ObjectQuery,
)


@runtime_checkable
class PersistenceStore(Protocol):
    """Protocol for provider-agnostic cognitive persistence backends."""

    def append_event(self, event: CognitiveEvent) -> None:
        """Append an immutable event to the journal."""
        ...

    def get_event(self, event_id: str) -> CognitiveEvent | None:
        """Retrieve an event by ID."""
        ...

    def query_events(self, query: EventQuery) -> list[CognitiveEvent]:
        """Query events matching filter criteria."""
        ...

    def get_timeline(self, subject_id: str | None = None) -> list[CognitiveEvent]:
        """Retrieve an ordered sequence of events representing the cognitive timeline."""
        ...

    def save_object(self, obj: CognitiveObject) -> None:
        """Persist a canonical cognitive object."""
        ...

    def get_object(self, object_id: str) -> CognitiveObject | None:
        """Retrieve a canonical cognitive object by ID."""
        ...

    def query_objects(self, query: ObjectQuery) -> list[CognitiveObject]:
        """Query objects matching filter criteria."""
        ...

    def list_all_objects(self) -> list[CognitiveObject]:
        """List all persisted objects."""
        ...


class InMemoryPersistenceStore:
    """Thread-safe, deterministic in-memory reference implementation of PersistenceStore."""

    def __init__(self) -> None:
        self._events: list[CognitiveEvent] = []
        self._events_by_id: dict[str, CognitiveEvent] = {}
        self._objects: dict[str, CognitiveObject] = {}

    def append_event(self, event: CognitiveEvent) -> None:
        """Append an immutable event. Rejects duplicate event IDs and invalid schemas."""
        if not event.id:
            raise ValueError("CognitiveEvent must possess a non-empty entity ID")
        if not event.schema_version:
            raise ValueError("CognitiveEvent must declare a valid schema_version")
        if event.id in self._events_by_id:
            raise ValueError(f"Event with ID '{event.id}' already exists and is immutable")

        # Validate that payload can be deterministically serialized
        DeterministicSerializer.serialize(event)

        self._events.append(event)
        self._events_by_id[event.id] = event

    def get_event(self, event_id: str) -> CognitiveEvent | None:
        return self._events_by_id.get(event_id)

    def query_events(self, query: EventQuery) -> list[CognitiveEvent]:
        results = []
        for event in self._events:
            if query.event_type and event.event_type != query.event_type:
                continue
            if query.subject_id and event.subject_id != query.subject_id:
                continue
            if query.source_id and event.source_id != query.source_id:
                continue
            if query.source_type and event.source_type != query.source_type:
                continue
            if query.schema_version and event.schema_version != query.schema_version:
                continue
            if query.start_time and event.created_at < query.start_time:
                continue
            if query.end_time and event.created_at > query.end_time:
                continue
            results.append(event)
            if query.limit and len(results) >= query.limit:
                break
        return results

    def get_timeline(self, subject_id: str | None = None) -> list[CognitiveEvent]:
        """Return events in insertion/temporal order, optionally filtered by subject."""
        if subject_id is None:
            return list(self._events)
        return [e for e in self._events if e.subject_id == subject_id]

    def save_object(self, obj: CognitiveObject) -> None:
        """Save a canonical cognitive object. Rejects missing IDs or invalid schemas."""
        if not obj.id:
            raise ValueError("CognitiveObject must possess a non-empty entity ID")
        if not obj.schema_version:
            raise ValueError("CognitiveObject must declare a valid schema_version")

        # Validate deterministic serialization integrity
        DeterministicSerializer.serialize(obj)
        self._objects[obj.id] = obj

    def get_object(self, object_id: str) -> CognitiveObject | None:
        return self._objects.get(object_id)

    def query_objects(self, query: ObjectQuery) -> list[CognitiveObject]:
        results = []
        for obj in self._objects.values():
            if query.entity_type:
                obj_type = getattr(obj, "entity_type", type(obj).__name__.lower())
                if obj_type != query.entity_type.lower():
                    continue
            if query.schema_version and obj.schema_version != query.schema_version:
                continue
            if query.start_time and obj.created_at < query.start_time:
                continue
            if query.end_time and obj.created_at > query.end_time:
                continue
            results.append(obj)
            if query.limit and len(results) >= query.limit:
                break
        return results

    def list_all_objects(self) -> list[CognitiveObject]:
        return list(self._objects.values())
