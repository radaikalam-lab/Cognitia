"""Cognitia Semantic Knowledge Graph Provider Scaffold.

Defines provider-neutral semantic graph interfaces, node/edge models, and deterministic mock.
MANDATORY INVARIANT: Graph edges explicitly distinguish OBSERVED_RELATION from HYPOTHESIZED_RELATION.
A graph edge is not an established ground-truth fact without epistemic validation.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, runtime_checkable

from cognitia.abi.types import CognitiveObject, SCHEMA_VERSION_V1, current_utc_timestamp, generate_entity_id
from cognitia.epistemic.types import EpistemicStatus
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.providers.types import (
    AdvancedCapabilityType,
    CandidateReasoningArtifact,
    ProposalLifecycleStatus,
    ReasoningRequest,
)
from cognitia.reasoning.types import ReasoningInput


class RelationEpistemicType(str, enum.Enum):
    """Categorization of epistemic certainty for a semantic graph edge."""

    OBSERVED_RELATION = "observed_relation"
    HYPOTHESIZED_RELATION = "hypothesized_relation"
    INFERRED_RELATION = "inferred_relation"


@dataclass(frozen=True)
class GraphNode(CognitiveObject):
    """A semantic entity node in a knowledge graph."""

    node_id: str = ""
    entity_type: str = "concept"
    label: str = ""
    properties: tuple[tuple[str, Any], ...] = ()


@dataclass(frozen=True)
class GraphEdge(CognitiveObject):
    """A directed semantic relationship between two nodes."""

    edge_id: str = ""
    source_node_id: str = ""
    target_node_id: str = ""
    predicate: str = "relates_to"
    relation_type: RelationEpistemicType = RelationEpistemicType.OBSERVED_RELATION
    confidence: float = 1.0
    epistemic_status: EpistemicStatus = EpistemicStatus.OBSERVED
    properties: tuple[tuple[str, Any], ...] = ()


@runtime_checkable
class SemanticGraphProvider(Protocol):
    """Protocol for semantic knowledge graph providers."""

    provider_id: str
    provider_version: str

    def capabilities(self) -> tuple[AdvancedCapabilityType, ...]: ...

    def query_graph(
        self,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact: ...


class MockSemanticGraphProvider:
    """Deterministic in-memory reference mock for SemanticGraphProvider."""

    def __init__(
        self,
        provider_id: str = "mock_semantic_graph_provider",
        provider_version: str = "1.0.0",
    ) -> None:
        self.provider_id = provider_id
        self.provider_version = provider_version

    def capabilities(self) -> tuple[AdvancedCapabilityType, ...]:
        return (AdvancedCapabilityType.SEMANTIC_GRAPH,)

    def query_graph(
        self,
        request: ReasoningRequest,
        input_snapshot: ReasoningInput,
    ) -> CandidateReasoningArtifact:
        nodes = [
            {"node_id": "concept_A", "label": "PressureManifold", "type": "component"},
            {"node_id": "concept_B", "label": "CombustionChamber", "type": "subsystem"},
        ]
        edges = [
            {
                "source": "concept_A",
                "target": "concept_B",
                "predicate": "feeds_into",
                "relation_type": RelationEpistemicType.HYPOTHESIZED_RELATION.value,
            }
        ]

        payload = {
            "graph_nodes": nodes,
            "graph_edges": edges,
            "edge_epistemic_type": RelationEpistemicType.HYPOTHESIZED_RELATION.value,
        }

        prov = ProvenanceRecord(
            source_type=SourceType.REASONING_ENGINE,
            producer_id=f"{self.provider_id}:{self.provider_version}",
            parent_ids=[input_snapshot.provenance.id, request.request_id],
            is_deterministic=True,
        )

        return CandidateReasoningArtifact(
            provider_id=self.provider_id,
            provider_version=self.provider_version,
            input_snapshot_id=input_snapshot.context_id,
            artifact_type="semantic_graph_candidate",
            payload=payload,
            assumptions=("Graph edges represent candidate semantic relationships, not verified physical axioms.",),
            epistemic_status=EpistemicStatus.UNRESOLVED,
            proposal_status=ProposalLifecycleStatus.PROPOSED,
            provenance=prov,
        )
