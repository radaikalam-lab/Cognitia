"""Cognitia Epistemic Service Interface and In-Memory Reference Implementation."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from cognitia.abi.types import Observation
from cognitia.epistemic.types import (
    Challenge,
    Claim,
    EpistemicNode,
    EpistemicStatus,
    EpistemicTransition,
    Evidence,
    EvidenceDirection,
    Hypothesis,
    Residual,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType


@runtime_checkable
class EpistemicService(Protocol):
    """Protocol defining the core operations of the domain-neutral Epistemic Service."""

    def record_observation(self, observation: Observation) -> EpistemicNode: ...
    def register_evidence(self, evidence: Evidence) -> EpistemicNode: ...
    def register_hypothesis(self, hypothesis: Hypothesis) -> EpistemicNode: ...
    def register_claim(self, claim: Claim) -> EpistemicNode: ...
    def issue_challenge(self, challenge: Challenge) -> EpistemicTransition: ...
    def record_residual(self, residual: Residual) -> EpistemicNode: ...
    def transition_state(
        self,
        node_id: str,
        new_status: EpistemicStatus,
        reason: str,
        provenance: ProvenanceRecord | None = None,
    ) -> EpistemicTransition: ...
    def get_node(self, node_id: str) -> EpistemicNode | None: ...
    def get_history(self, node_id: str) -> list[EpistemicTransition]: ...
    def list_nodes_by_status(self, status: EpistemicStatus) -> list[EpistemicNode]: ...


class InMemoryEpistemicService:
    """Deterministic, thread-safe, in-memory reference implementation of EpistemicService."""

    def __init__(self) -> None:
        self._nodes: dict[str, EpistemicNode] = {}
        self._evidence: dict[str, Evidence] = {}
        self._challenges: dict[str, Challenge] = {}

    def record_observation(self, observation: Observation) -> EpistemicNode:
        node = EpistemicNode(
            node_id=observation.id,
            entity_type="observation",
            status=EpistemicStatus.OBSERVED,
            confidence=1.0,
            content=observation,
        )
        self._nodes[node.node_id] = node
        return node

    def register_evidence(self, evidence: Evidence) -> EpistemicNode:
        self._evidence[evidence.id] = evidence
        node = EpistemicNode(
            node_id=evidence.id,
            entity_type="evidence",
            status=EpistemicStatus.SUPPORTED if evidence.direction == EvidenceDirection.SUPPORT else EpistemicStatus.REFUTED,
            confidence=evidence.confidence,
            content=evidence,
        )
        self._nodes[node.node_id] = node

        # Link to target if present
        if evidence.target_id and evidence.target_id in self._nodes:
            target_node = self._nodes[evidence.target_id]
            target_node.associated_evidence_ids.append(evidence.id)

        return node

    def register_hypothesis(self, hypothesis: Hypothesis) -> EpistemicNode:
        initial_status = hypothesis.initial_status
        node = EpistemicNode(
            node_id=hypothesis.id,
            entity_type="hypothesis",
            status=initial_status,
            confidence=0.5,
            content=hypothesis,
        )
        self._nodes[node.node_id] = node
        return node

    def register_claim(self, claim: Claim) -> EpistemicNode:
        node = EpistemicNode(
            node_id=claim.id,
            entity_type="claim",
            status=claim.status,
            confidence=claim.confidence,
            content=claim,
        )
        self._nodes[node.node_id] = node
        return node

    def issue_challenge(self, challenge: Challenge) -> EpistemicTransition:
        self._challenges[challenge.id] = challenge
        target_node = self._nodes.get(challenge.target_id)
        if not target_node:
            raise KeyError(f"Target node {challenge.target_id} not found in epistemic store")

        target_node.associated_challenge_ids.append(challenge.id)

        # Transition target to UNRESOLVED upon challenge unless already refuted
        new_status = EpistemicStatus.REFUTED if challenge.counter_evidence_ids else EpistemicStatus.UNRESOLVED
        return self.transition_state(
            node_id=target_node.node_id,
            new_status=new_status,
            reason=f"Challenge issued: {challenge.basis}",
            provenance=challenge.provenance,
        )

    def record_residual(self, residual: Residual) -> EpistemicNode:
        node = EpistemicNode(
            node_id=residual.id,
            entity_type="residual",
            status=EpistemicStatus.OBSERVED,
            confidence=1.0,
            content=residual,
        )
        self._nodes[node.node_id] = node
        return node

    def transition_state(
        self,
        node_id: str,
        new_status: EpistemicStatus,
        reason: str,
        provenance: ProvenanceRecord | None = None,
    ) -> EpistemicTransition:
        node = self._nodes.get(node_id)
        if not node:
            raise KeyError(f"Epistemic node {node_id} not found")

        prov = provenance or ProvenanceRecord(
            source_type=SourceType.DETERMINISTIC_RULE,
            producer_id="epistemic_service",
            parent_ids=[node_id],
        )

        transition = EpistemicTransition(
            node_id=node_id,
            from_status=node.status,
            to_status=new_status,
            reason=reason,
            provenance=prov,
        )
        node.status = new_status
        node.transitions.append(transition)
        return transition

    def get_node(self, node_id: str) -> EpistemicNode | None:
        return self._nodes.get(node_id)

    def get_history(self, node_id: str) -> list[EpistemicTransition]:
        node = self._nodes.get(node_id)
        return list(node.transitions) if node else []

    def list_nodes_by_status(self, status: EpistemicStatus) -> list[EpistemicNode]:
        return [node for node in self._nodes.values() if node.status == status]
