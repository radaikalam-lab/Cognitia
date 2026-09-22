"""Cognitia Synchronization Abstraction and In-Memory Cognitive Transport.

Provides transport-neutral synchronization semantics and a deterministic
in-memory reference transport for testing.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cognitia.distributed.types import (
    CognitiveConflict,
    CognitiveEnvelope,
    ConflictStatus,
    SynchronizationState,
)


@runtime_checkable
class SyncService(Protocol):
    """Transport-neutral synchronization abstraction."""

    def publish(self, envelope: CognitiveEnvelope) -> None:
        """Publish an envelope for delivery to peers."""
        ...

    def receive(self, node_id: str) -> CognitiveEnvelope | None:
        """Receive the next pending envelope for a node."""
        ...

    def acknowledge(self, envelope_id: str) -> None:
        """Acknowledge receipt of an envelope."""
        ...

    def get_sync_state(
        self,
        source_node_id: str,
        target_node_id: str,
    ) -> SynchronizationState:
        """Return synchronization state between two nodes."""
        ...

    def reconcile(self, peer_id: str) -> list[CognitiveConflict]:
        """Reconcile state with a peer and return detected conflicts."""
        ...

    def get_pending(self, node_id: str) -> list[CognitiveEnvelope]:
        """Return all pending envelopes for a node."""
        ...


class InMemoryCognitiveTransport:
    """Deterministic in-memory cognitive transport for tests.

    Simulates send, receive, duplication, delay, failure, and reconnection
    without network dependencies.
    """

    def __init__(self) -> None:
        self._queues: dict[str, list[CognitiveEnvelope]] = {}
        self._received: set[str] = set()
        self._acknowledged: set[str] = set()
        self._states: dict[tuple[str, str], SynchronizationState] = {}
        self._targets: dict[str, str] = {}

    def _ensure_queue(self, node_id: str) -> list[CognitiveEnvelope]:
        if node_id not in self._queues:
            self._queues[node_id] = []
        return self._queues[node_id]

    def send(
        self,
        envelope: CognitiveEnvelope,
        target_node_id: str,
    ) -> None:
        """Send an envelope to a target node's queue."""
        self._targets[envelope.id] = target_node_id
        self._ensure_queue(target_node_id).append(envelope)

    def receive(self, node_id: str) -> CognitiveEnvelope | None:
        """Receive the next pending envelope for a node, idempotently."""
        queue = self._ensure_queue(node_id)
        while queue:
            envelope = queue.pop(0)
            if envelope.id not in self._received:
                self._received.add(envelope.id)
                return envelope
        return None

    def acknowledge(self, envelope_id: str) -> None:
        """Acknowledge receipt of an envelope."""
        self._acknowledged.add(envelope_id)

    def get_sync_state(
        self,
        source_node_id: str,
        target_node_id: str,
    ) -> SynchronizationState:
        key = (source_node_id, target_node_id)
        if key not in self._states:
            self._states[key] = SynchronizationState(
                node_id=source_node_id,
                peer_id=target_node_id,
            )
        return self._states[key]

    def update_sync_state(
        self,
        source_node_id: str,
        target_node_id: str,
        last_sent: str | None = None,
        last_received: str | None = None,
        pending_delta: int = 0,
        acknowledged_delta: int = 0,
        failed_delta: int = 0,
    ) -> SynchronizationState:
        key = (source_node_id, target_node_id)
        state = self.get_sync_state(source_node_id, target_node_id)
        updated = SynchronizationState(
            node_id=source_node_id,
            peer_id=target_node_id,
            last_sent=last_sent or state.last_sent,
            last_received=last_received or state.last_received,
            pending_count=state.pending_count + pending_delta,
            acknowledged_count=state.acknowledged_count + acknowledged_delta,
            failed_count=state.failed_count + failed_delta,
            provenance=state.provenance,
            metadata=state.metadata,
        )
        self._states[key] = updated
        return updated

    def reconcile(self, peer_id: str) -> list[CognitiveConflict]:
        """Reconcile state with a peer. Returns empty list by default."""
        return []

    def get_pending(self, node_id: str) -> list[CognitiveEnvelope]:
        """Return all pending (unreceived) envelopes for a node."""
        queue = self._ensure_queue(node_id)
        return [e for e in queue if e.id not in self._received]

    def simulate_duplicate(self, envelope: CognitiveEnvelope) -> None:
        """Simulate duplicate delivery by re-queueing an already-received envelope."""
        self._received.discard(envelope.id)
        target = self._targets.get(envelope.id, envelope.source_node_id)
        self._ensure_queue(target).append(envelope)

    def clear(self) -> None:
        """Reset transport state."""
        self._queues.clear()
        self._received.clear()
        self._acknowledged.clear()
        self._states.clear()
        self._targets.clear()


class InMemorySyncService:
    """In-memory reference implementation of SyncService using InMemoryCognitiveTransport."""

    def __init__(self, transport: InMemoryCognitiveTransport | None = None) -> None:
        self._transport = transport or InMemoryCognitiveTransport()

    @property
    def transport(self) -> InMemoryCognitiveTransport:
        return self._transport

    def publish(self, envelope: CognitiveEnvelope) -> None:
        self._transport.send(envelope, envelope.source_node_id)

    def receive(self, node_id: str) -> CognitiveEnvelope | None:
        return self._transport.receive(node_id)

    def acknowledge(self, envelope_id: str) -> None:
        self._transport.acknowledge(envelope_id)

    def get_sync_state(
        self,
        source_node_id: str,
        target_node_id: str,
    ) -> SynchronizationState:
        return self._transport.get_sync_state(source_node_id, target_node_id)

    def reconcile(self, peer_id: str) -> list[CognitiveConflict]:
        return self._transport.reconcile(peer_id)

    def get_pending(self, node_id: str) -> list[CognitiveEnvelope]:
        return self._transport.get_pending(node_id)
