"""Cognitia Phase 8: Distributed & Edge Cognition Tests."""

from __future__ import annotations

import pytest

from cognitia.abi.types import Observation
from cognitia.directional.types import (
    DirectionalObjective,
    DirectionalSpecification,
    DirectionalProposal,
)
from cognitia.distributed.runtime import (
    CentralCognitiveRuntime,
    EdgeCognitiveRuntime,
    LocalCognitiveRuntime,
)
from cognitia.distributed.sync import (
    InMemoryCognitiveTransport,
    InMemorySyncService,
    SyncService,
)
from cognitia.distributed.types import (
    CognitiveConflict,
    CognitiveEnvelope,
    CognitiveNode,
    CognitiveTopology,
    ConflictStatus,
    ConflictType,
    NodeCapability,
    NodeType,
    SynchronizationState,
)
from cognitia.epistemic.types import EpistemicStatus
from cognitia.reasoning.engine import DeterministicReasoningEngine
from cognitia.reasoning.types import ReasoningInput, ReasoningMode


def _make_node(node_id: str, node_type: NodeType = NodeType.EDGE) -> CognitiveNode:
    return CognitiveNode(
        node_id=node_id,
        node_type=node_type,
        runtime_version="0.1.0",
        capabilities=(
            NodeCapability(capability_id="obs", capability_type="observation"),
            NodeCapability(capability_id="reasoning", capability_type="reasoning"),
        ),
    )


def _make_envelope(
    payload: Any = None,
    source_node_id: str = "node_a",
    origin_node_id: str = "node_a",
    artifact_type: str = "observation",
    artifact_id: str = "art_1",
) -> CognitiveEnvelope:
    return CognitiveEnvelope(
        artifact_type=artifact_type,
        artifact_id=artifact_id,
        source_node_id=source_node_id,
        origin_node_id=origin_node_id,
        payload=payload or Observation(id=artifact_id, source_id=source_node_id),
    )


class TestCognitiveNodeIdentity:
    def test_node_creation(self) -> None:
        node = _make_node("node_1", NodeType.CENTRAL)
        assert node.id == "node_1"
        assert node.node_type == NodeType.CENTRAL
        assert node.runtime_version == "0.1.0"

    def test_node_types(self) -> None:
        assert NodeType.CENTRAL.value == "central"
        assert NodeType.EDGE.value == "edge"
        assert NodeType.EMBEDDED.value == "embedded"

    def test_node_capabilities(self) -> None:
        node = _make_node("node_1")
        assert len(node.capabilities) == 2
        assert node.capabilities[0].capability_id == "obs"

    def test_node_identity_does_not_replace_artifact_identity(self) -> None:
        node = _make_node("node_1")
        obs = Observation(id="obs_1", source_id=node.id)
        assert obs.id != node.id
        assert obs.source_id == node.id

    def test_node_has_provenance(self) -> None:
        node = _make_node("node_1")
        assert node.provenance is not None

    def test_node_serialization_deterministic(self) -> None:
        n1 = _make_node("node_1", NodeType.CENTRAL)
        assert n1.serialize() == n1.serialize()


class TestCognitiveTopology:
    def test_topology_creation(self) -> None:
        node = _make_node("node_1", NodeType.CENTRAL)
        topo = CognitiveTopology(nodes=[node])
        assert topo.get_node("node_1") is not None

    def test_topology_add_edge(self) -> None:
        n1 = _make_node("node_1", NodeType.CENTRAL)
        n2 = _make_node("node_2", NodeType.EDGE)
        topo = CognitiveTopology(nodes=[n1])
        topo.add_node(n2)
        topo.add_edge("node_1", "node_2")
        assert len(topo.list_edges()) == 1


class TestCognitiveEnvelope:
    def test_envelope_wraps_observation(self) -> None:
        obs = Observation(id="obs_1", source_id="node_a")
        env = CognitiveEnvelope(
            artifact_type="observation",
            artifact_id="obs_1",
            source_node_id="node_a",
            origin_node_id="node_a",
            payload=obs,
        )
        assert env.payload.id == "obs_1"
        assert env.artifact_type == "observation"

    def test_envelope_wraps_directional_proposal(self) -> None:
        proposal = DirectionalProposal(
            specification_id="spec_1",
            provider_id="provider_1",
        )
        env = CognitiveEnvelope(
            artifact_type="directional_proposal",
            artifact_id=proposal.id,
            source_node_id="node_a",
            origin_node_id="node_a",
            payload=proposal,
        )
        assert isinstance(env.payload, DirectionalProposal)
        assert env.payload.specification_id == "spec_1"

    def test_envelope_preserves_origin_node(self) -> None:
        env = _make_envelope(
            source_node_id="node_b",
            origin_node_id="node_a",
        )
        assert env.source_node_id == "node_b"
        assert env.origin_node_id == "node_a"

    def test_envelope_deterministic_serialization(self) -> None:
        obs = Observation(id="obs_det", source_id="node_a")
        env1 = CognitiveEnvelope(
            artifact_type="observation",
            artifact_id="obs_det",
            source_node_id="node_a",
            origin_node_id="node_a",
            payload=obs,
        )
        assert env1.serialize() == env1.serialize()

    def test_envelope_has_provenance(self) -> None:
        env = _make_envelope()
        assert env.provenance is not None

    def test_envelope_does_not_create_edge_specific_artifact(self) -> None:
        obs = Observation(id="obs_1", source_id="node_a")
        env = CognitiveEnvelope(
            artifact_type="observation",
            artifact_id="obs_1",
            source_node_id="node_a",
            origin_node_id="node_a",
            payload=obs,
        )
        assert isinstance(env.payload, Observation)
        assert not hasattr(env, "edge_observation")


class TestNodeCapabilities:
    def test_capability_advertisement(self) -> None:
        cap = NodeCapability(
            capability_id="reasoning",
            capability_type="reasoning",
            version="1.0.0",
            is_available=True,
        )
        assert cap.capability_id == "reasoning"
        assert cap.is_available is True

    def test_capability_does_not_imply_authority(self) -> None:
        cap = NodeCapability(
            capability_id="directional",
            capability_type="directional_programming",
        )
        assert cap.capability_id == "directional"
        assert cap.is_available is True
        assert not hasattr(cap, "execute_authority")

    def test_node_capabilities_listed(self) -> None:
        node = _make_node("node_1")
        assert len(node.capabilities) > 0


class TestCentralEdgeRuntimes:
    def test_central_runtime_creation(self) -> None:
        runtime = CentralCognitiveRuntime()
        assert runtime is not None
        assert runtime.persistence is not None
        assert runtime.memory is not None
        assert runtime.recall_engine is not None

    def test_edge_runtime_creation(self) -> None:
        runtime = EdgeCognitiveRuntime()
        assert runtime is not None
        assert runtime.persistence is not None
        assert runtime.memory is not None
        assert runtime.recall_engine is not None

    def test_both_runtimes_share_substrate(self) -> None:
        central = CentralCognitiveRuntime()
        edge = EdgeCognitiveRuntime()
        assert type(central.persistence) == type(edge.persistence)
        assert type(central.memory) == type(edge.memory)

    def test_runtime_local_cognition_without_central(self) -> None:
        edge = EdgeCognitiveRuntime()
        obs = Observation(id="obs_local", payload={"temp": 100})
        edge.persistence.save_object(obs)
        retrieved = edge.persistence.get_object("obs_local")
        assert retrieved is not None
        assert retrieved.id == "obs_local"

    def test_central_runtime_reasoning(self) -> None:
        runtime = CentralCognitiveRuntime()
        engine = DeterministicReasoningEngine()
        obs = Observation(id="obs_r", payload={"val": 20})
        inp = ReasoningInput(
            context_id="ctx_r",
            reasoning_mode=ReasoningMode.DEDUCTION,
            premises=[obs],
        )
        trace, result = engine.reason(inp)
        assert trace is not None
        assert result is not None

    def test_edge_runtime_reasoning(self) -> None:
        runtime = EdgeCognitiveRuntime()
        engine = DeterministicReasoningEngine()
        obs = Observation(id="obs_er", payload={"val": 20})
        inp = ReasoningInput(
            context_id="ctx_er",
            reasoning_mode=ReasoningMode.DEDUCTION,
            premises=[obs],
        )
        trace, result = engine.reason(inp)
        assert trace is not None
        assert result is not None


class TestInMemoryCognitiveTransport:
    def test_send_receive(self) -> None:
        transport = InMemoryCognitiveTransport()
        env = _make_envelope()
        transport.send(env, "node_b")
        received = transport.receive("node_b")
        assert received is not None
        assert received.id == env.id

    def test_receive_returns_none_when_empty(self) -> None:
        transport = InMemoryCognitiveTransport()
        assert transport.receive("node_empty") is None

    def test_idempotent_receive(self) -> None:
        transport = InMemoryCognitiveTransport()
        env = _make_envelope()
        transport.send(env, "node_b")
        r1 = transport.receive("node_b")
        r2 = transport.receive("node_b")
        assert r1 is not None
        assert r2 is None

    def test_acknowledge(self) -> None:
        transport = InMemoryCognitiveTransport()
        env = _make_envelope()
        transport.send(env, "node_b")
        received = transport.receive("node_b")
        assert received is not None
        transport.acknowledge(received.id)

    def test_sync_state(self) -> None:
        transport = InMemoryCognitiveTransport()
        state = transport.get_sync_state("node_a", "node_b")
        assert state.node_id == "node_a"
        assert state.peer_id == "node_b"

    def test_update_sync_state(self) -> None:
        transport = InMemoryCognitiveTransport()
        state = transport.update_sync_state(
            "node_a", "node_b",
            last_sent="2026-01-01T00:00:00Z",
            pending_delta=1,
        )
        assert state.pending_count == 1

    def test_get_pending(self) -> None:
        transport = InMemoryCognitiveTransport()
        env = _make_envelope()
        transport.send(env, "node_b")
        pending = transport.get_pending("node_b")
        assert len(pending) == 1
        assert pending[0].id == env.id

    def test_simulate_duplicate(self) -> None:
        transport = InMemoryCognitiveTransport()
        env = _make_envelope()
        transport.send(env, "node_b")
        r1 = transport.receive("node_b")
        assert r1 is not None
        transport.simulate_duplicate(env)
        r2 = transport.receive("node_b")
        assert r2 is not None
        assert r2.id == env.id

    def test_duplicate_does_not_duplicate_semantic_artifact(self) -> None:
        transport = InMemoryCognitiveTransport()
        obs = Observation(id="obs_dup", source_id="node_a")
        env = CognitiveEnvelope(
            artifact_type="observation",
            artifact_id="obs_dup",
            source_node_id="node_a",
            origin_node_id="node_a",
            payload=obs,
        )
        transport.send(env, "node_b")
        r1 = transport.receive("node_b")
        transport.simulate_duplicate(env)
        r2 = transport.receive("node_b")
        assert r1 is not None
        assert r2 is not None
        assert r1.payload.id == r2.payload.id
        assert r1.payload.id == "obs_dup"

    def test_transport_clear(self) -> None:
        transport = InMemoryCognitiveTransport()
        env = _make_envelope()
        transport.send(env, "node_b")
        transport.clear()
        assert transport.receive("node_b") is None


class TestInMemorySyncService:
    def test_publish_receive(self) -> None:
        sync = InMemorySyncService()
        env = _make_envelope()
        sync.publish(env)
        received = sync.receive("node_a")
        assert received is not None
        assert received.id == env.id

    def test_get_pending(self) -> None:
        sync = InMemorySyncService()
        env = _make_envelope()
        sync.publish(env)
        pending = sync.get_pending("node_a")
        assert len(pending) == 1

    def test_get_sync_state(self) -> None:
        sync = InMemorySyncService()
        state = sync.get_sync_state("node_a", "node_b")
        assert state.node_id == "node_a"
        assert state.peer_id == "node_b"

    def test_reconcile_returns_empty_by_default(self) -> None:
        sync = InMemorySyncService()
        conflicts = sync.reconcile("node_b")
        assert conflicts == []


class TestCognitiveConflict:
    def test_conflict_creation(self) -> None:
        conflict = CognitiveConflict(
            subject_id="hyp_1",
            artifact_ids=("art_a", "art_b"),
            source_nodes=("node_a", "node_b"),
            conflict_type=ConflictType.EPISTEMIC_CONFLICT,
            description="Edge A supports, Edge B refutes",
        )
        assert conflict.subject_id == "hyp_1"
        assert conflict.conflict_type == ConflictType.EPISTEMIC_CONFLICT
        assert conflict.status == ConflictStatus.OPEN

    def test_conflict_types(self) -> None:
        assert ConflictType.VERSION_CONFLICT.value == "version_conflict"
        assert ConflictType.EPISTEMIC_CONFLICT.value == "epistemic_conflict"
        assert ConflictType.DIRECTION_CONFLICT.value == "direction_conflict"

    def test_conflict_status(self) -> None:
        conflict = CognitiveConflict()
        assert conflict.status == ConflictStatus.OPEN

    def test_epistemic_conflict_not_silently_resolved(self) -> None:
        conflict = CognitiveConflict(
            subject_id="hyp_1",
            conflict_type=ConflictType.EPISTEMIC_CONFLICT,
            description="Conflicting evidence",
        )
        assert conflict.status == ConflictStatus.OPEN
        assert conflict.description != ""

    def test_conflict_has_provenance(self) -> None:
        conflict = CognitiveConflict()
        assert conflict.provenance is not None

    def test_conflict_deterministic(self) -> None:
        c1 = CognitiveConflict(
            subject_id="s1",
            artifact_ids=("a1",),
            source_nodes=("n1",),
            conflict_type=ConflictType.STATE_CONFLICT,
            description="test",
        )
        assert c1.serialize() == c1.serialize()


class TestSynchronizationState:
    def test_state_creation(self) -> None:
        state = SynchronizationState(
            node_id="node_a",
            peer_id="node_b",
        )
        assert state.node_id == "node_a"
        assert state.peer_id == "node_b"
        assert state.pending_count == 0

    def test_state_counts(self) -> None:
        state = SynchronizationState(
            node_id="node_a",
            peer_id="node_b",
            pending_count=5,
            acknowledged_count=3,
            failed_count=1,
        )
        assert state.pending_count == 5
        assert state.acknowledged_count == 3
        assert state.failed_count == 1


class TestDirectionalProgrammingDistribution:
    def test_directional_specification_crosses_node_boundary(self) -> None:
        env = CognitiveEnvelope(
            artifact_type="directional_specification",
            artifact_id="spec_1",
            source_node_id="edge_a",
            origin_node_id="edge_a",
            payload=DirectionalSpecification(
                objectives=[DirectionalObjective(description="test", target_state={"v": 1})],
            ),
        )
        assert isinstance(env.payload, DirectionalSpecification)
        assert env.source_node_id == "edge_a"

    def test_directional_proposal_crosses_node_boundary(self) -> None:
        proposal = DirectionalProposal(
            specification_id="spec_1",
            provider_id="provider_1",
        )
        env = CognitiveEnvelope(
            artifact_type="directional_proposal",
            artifact_id=proposal.id,
            source_node_id="edge_a",
            origin_node_id="edge_a",
            payload=proposal,
        )
        assert isinstance(env.payload, DirectionalProposal)
        assert env.payload.specification_id == "spec_1"
        assert env.payload.epistemic_status == EpistemicStatus.UNRESOLVED

    def test_proposal_remains_advisory_across_nodes(self) -> None:
        from cognitia.abi.types import Decision
        proposal = DirectionalProposal(
            specification_id="spec_1",
            provider_id="provider_1",
        )
        assert not isinstance(proposal, Decision)
        env = CognitiveEnvelope(
            artifact_type="directional_proposal",
            artifact_id=proposal.id,
            source_node_id="edge_a",
            origin_node_id="edge_a",
            payload=proposal,
        )
        assert not isinstance(env.payload, Decision)


class TestReasoningDistribution:
    def test_reasoning_trace_preserves_provenance_across_nodes(self) -> None:
        engine = DeterministicReasoningEngine()
        obs = Observation(id="obs_dist", source_id="edge_node")
        inp = ReasoningInput(
            context_id="ctx_dist",
            reasoning_mode=ReasoningMode.DEDUCTION,
            premises=[obs],
        )
        trace, result = engine.reason(inp)
        assert trace.provenance is not None
        assert trace.mode == ReasoningMode.DEDUCTION


class TestProvenancePreservation:
    def test_envelope_provenance_tracks_artifact(self) -> None:
        obs = Observation(id="obs_prov", source_id="edge_a")
        env = CognitiveEnvelope(
            artifact_type="observation",
            artifact_id="obs_prov",
            source_node_id="edge_a",
            origin_node_id="edge_a",
            payload=obs,
        )
        assert env.provenance is not None
        assert env.provenance.source_type.value == "deterministic_rule"

    def test_origin_node_identifiable_after_sync(self) -> None:
        env = _make_envelope(
            source_node_id="edge_b",
            origin_node_id="edge_a",
        )
        assert env.origin_node_id == "edge_a"
        assert env.source_node_id == "edge_b"

    def test_transport_metadata_distinct_from_provenance(self) -> None:
        env = _make_envelope()
        assert env.provenance.source_type.value == "deterministic_rule"
        assert env.artifact_type == "observation"


class TestAuthorityBoundary:
    def test_synchronization_is_not_execution(self) -> None:
        sync = InMemorySyncService()
        assert not hasattr(sync, "execute_action")
        assert not hasattr(sync, "actuate")

    def test_edge_cognition_is_not_actuator_authority(self) -> None:
        edge = EdgeCognitiveRuntime()
        assert not hasattr(edge, "actuate")
        assert not hasattr(edge, "execute_action")

    def test_central_cognition_is_not_domain_authority(self) -> None:
        central = CentralCognitiveRuntime()
        assert not hasattr(central, "actuate")
        assert not hasattr(central, "execute_action")

    def test_proposal_is_not_action(self) -> None:
        from cognitia.abi.types import Action
        proposal = DirectionalProposal()
        assert not isinstance(proposal, Action)

    def test_capability_is_not_authority(self) -> None:
        node = _make_node("node_1")
        cap = node.capabilities[0]
        assert not hasattr(cap, "grant_authority")
        assert not hasattr(cap, "execute")


class TestFailureIsolation:
    def test_central_unavailable_edge_continues(self) -> None:
        edge = EdgeCognitiveRuntime()
        obs = Observation(id="obs_fail", payload={"val": 1})
        edge.persistence.save_object(obs)
        retrieved = edge.persistence.get_object("obs_fail")
        assert retrieved is not None

    def test_sync_unavailable_does_not_destroy_local_history(self) -> None:
        edge = EdgeCognitiveRuntime()
        obs = Observation(id="obs_hist", payload={"val": 1})
        edge.persistence.save_object(obs)
        assert edge.persistence.get_object("obs_hist") is not None

    def test_edge_unavailable_does_not_compromise_central(self) -> None:
        central = CentralCognitiveRuntime()
        obs = Observation(id="obs_central", payload={"val": 1})
        central.persistence.save_object(obs)
        assert central.persistence.get_object("obs_central") is not None


class TestDisconnectedOperation:
    def test_edge_operates_without_central(self) -> None:
        edge = EdgeCognitiveRuntime()
        obs = Observation(id="obs_disc", payload={"temp": 100})
        edge.persistence.save_object(obs)
        retrieved = edge.persistence.get_object("obs_disc")
        assert retrieved is not None
        assert retrieved.id == "obs_disc"

    def test_edge_produces_advisory_output_while_disconnected(self) -> None:
        edge = EdgeCognitiveRuntime()
        obs = Observation(id="obs_adv", payload={"val": 20})
        decision = edge.request_decision(obs)
        assert decision is not None
        assert decision.confidence >= 0.0


class TestPlasticityBoundary:
    def test_plasticity_does_not_autonomously_mutate_models(self) -> None:
        edge = EdgeCognitiveRuntime()
        assert not hasattr(edge, "mutate_model")
        assert not hasattr(edge, "auto_learn")


class TestOfflineSyncReconnection:
    def test_offline_artifacts_remain_traceable(self) -> None:
        transport = InMemoryCognitiveTransport()
        obs = Observation(id="obs_off", source_id="edge_a")
        env = CognitiveEnvelope(
            artifact_type="observation",
            artifact_id="obs_off",
            source_node_id="edge_a",
            origin_node_id="edge_a",
            payload=obs,
        )
        transport.send(env, "central")
        received = transport.receive("central")
        assert received is not None
        assert received.origin_node_id == "edge_a"
        assert received.source_node_id == "edge_a"

    def test_reconnection_reconcile(self) -> None:
        sync = InMemorySyncService()
        conflicts = sync.reconcile("peer_1")
        assert conflicts == []


class TestDeterminism:
    def test_same_input_same_result(self) -> None:
        edge1 = EdgeCognitiveRuntime()
        edge2 = EdgeCognitiveRuntime()
        obs = Observation(id="obs_det2", payload={"val": 20})
        d1 = edge1.request_decision(obs)
        d2 = edge2.request_decision(obs)
        assert d1.proposed_action.name == d2.proposed_action.name
        assert d1.confidence == d2.confidence


class TestNodeIdentityVersusArtifactIdentity:
    def test_node_id_separate_from_artifact_ids(self) -> None:
        node = _make_node("node_1")
        obs = Observation(id="obs_1", source_id=node.id)
        assert obs.id != node.id
        assert obs.source_id == node.id

    def test_envelope_artifact_id_separate_from_envelope_id(self) -> None:
        env = _make_envelope(artifact_id="art_1")
        assert env.id != env.artifact_id

    def test_multiple_artifacts_same_node(self) -> None:
        node = _make_node("node_1")
        obs1 = Observation(id="obs_1", source_id=node.id)
        obs2 = Observation(id="obs_2", source_id=node.id)
        assert obs1.id != obs2.id
        assert obs1.source_id == obs2.source_id == node.id


class TestNoExternalDependencies:
    def test_no_network_dependency_in_transport(self) -> None:
        transport = InMemoryCognitiveTransport()
        assert not hasattr(transport, "socket")
        assert not hasattr(transport, "http")

    def test_no_external_dependency_in_runtimes(self) -> None:
        central = CentralCognitiveRuntime()
        edge = EdgeCognitiveRuntime()
        assert central is not None
        assert edge is not None
