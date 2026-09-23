"""Epistemic Subsystem Bridge for Cognitia Standalone Runtime."""

from __future__ import annotations

import sys
import threading
import uuid
from pathlib import Path
from typing import Any

# Ensure Cognitia core is in path
COGNITIA_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(COGNITIA_SRC) not in sys.path:
    sys.path.insert(0, str(COGNITIA_SRC))

from cognitia.abi.types import Observation, SCHEMA_VERSION_V1, DeterministicSerializer
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.epistemic.service import InMemoryEpistemicService, Evidence, EvidenceDirection
from cognitia.directional.types import (
    DirectionalSpecification,
    DirectionalProposal,
    ProposalLifecycleStatus,
    EpistemicStatus,
)

MAX_EPISTEMIC_NODES = 50000


class EpistemicCapacityExceededError(RuntimeError):
    """Raised when the epistemic node capacity ceiling is reached."""


class EpistemicBridge:
    """Bridges validated provider messages to Cognitia Epistemic Core."""

    def __init__(self, epistemic_service: InMemoryEpistemicService | None = None) -> None:
        self.epistemic_service = epistemic_service or InMemoryEpistemicService()
        self._provenance_store: dict[str, ProvenanceRecord] = {}
        self._lock = threading.Lock()
        self._ingested_observations_count = 0
        self._ingested_evidence_count = 0

    def ingest_observation(
        self,
        obs_dict: dict[str, Any],
        provider_id: str,
        capability: str,
    ) -> dict[str, Any]:
        """Convert validated observation dictionary into canonical Observation & ProvenanceRecord

        and ingest into the Epistemic service.
        """
        with self._lock:
            if len(self.epistemic_service._nodes) >= MAX_EPISTEMIC_NODES:
                raise EpistemicCapacityExceededError(
                    f"Epistemic capacity reached maximum limit ({MAX_EPISTEMIC_NODES} nodes)"
                )

            # 1. Build canonical ProvenanceRecord
            prov_dict = obs_dict.get("provenance") or obs_dict.get("metadata", {}).get("provenance")
            if prov_dict and isinstance(prov_dict, dict):
                prov = ProvenanceRecord(
                    producer_id=prov_dict.get("producer_id", provider_id),
                    capability_id=prov_dict.get("capability_id", capability),
                    source_type=SourceType.SENSOR,
                    created_at=obs_dict.get("created_at"),
                    metadata=prov_dict.get("metadata", {}),
                )
            else:
                prov = ProvenanceRecord(
                    producer_id=provider_id,
                    capability_id=capability,
                    source_type=SourceType.SENSOR,
                    created_at=obs_dict.get("created_at"),
                    metadata={
                        "capability": capability,
                        "provider_id": provider_id,
                    },
                )
            self._provenance_store[prov.id] = prov

            # 2. Attach provenance reference to Observation metadata
            obs_metadata = dict(obs_dict.get("metadata", {}))
            obs_metadata["provenance_id"] = prov.id
            obs_metadata["provenance_producer"] = prov.producer_id
            obs_metadata["provenance_capability"] = prov.capability_id

            # 3. Build canonical Observation
            observation = Observation(
                id=obs_dict["id"],
                schema_version=obs_dict.get("schema_version", SCHEMA_VERSION_V1),
                created_at=obs_dict["created_at"],
                source_id=obs_dict.get("source_id", provider_id),
                metadata=obs_metadata,
                payload=obs_dict.get("payload", {}),
            )

            # 4. Record in Epistemic Service
            node = self.epistemic_service.record_observation(observation)
            self._ingested_observations_count += 1

            return {
                "status": "ingested",
                "entity_type": "observation",
                "node_id": node.node_id,
                "entity_id": observation.id,
                "epistemic_status": node.status.value,
                "provenance_id": prov.id,
            }

    def ingest_evidence(
        self,
        evidence_dict: dict[str, Any],
        provider_id: str,
        capability: str,
    ) -> dict[str, Any]:
        """Convert validated evidence dictionary into canonical Evidence & ProvenanceRecord

        and register with Epistemic service.
        """
        with self._lock:
            if len(self.epistemic_service._nodes) >= MAX_EPISTEMIC_NODES:
                raise EpistemicCapacityExceededError(
                    f"Epistemic capacity reached maximum limit ({MAX_EPISTEMIC_NODES} nodes)"
                )

            prov = ProvenanceRecord(
                producer_id=provider_id,
                capability_id=capability,
                source_type=SourceType.SENSOR,
                created_at=evidence_dict.get("created_at"),
                metadata={"capability": capability, "provider_id": provider_id},
            )
            self._provenance_store[prov.id] = prov

            direction_str = evidence_dict.get("direction", "SUPPORT").upper()
            direction = (
                EvidenceDirection.SUPPORT
                if direction_str == "SUPPORT"
                else (
                    EvidenceDirection.REFUTE
                    if direction_str == "REFUTE"
                    else EvidenceDirection.NEUTRAL
                )
            )

            evidence = Evidence(
                id=evidence_dict["id"],
                schema_version=evidence_dict.get("schema_version", SCHEMA_VERSION_V1),
                created_at=evidence_dict["created_at"],
                target_id=evidence_dict["target_id"],
                direction=direction,
                confidence=float(evidence_dict.get("confidence", 1.0)),
                weight=float(evidence_dict.get("weight", 1.0)),
                provenance=prov,
                observation_ids=evidence_dict.get("observation_ids", []),
                metadata=evidence_dict.get("metadata", {}),
            )

            node = self.epistemic_service.register_evidence(evidence)
            self._ingested_evidence_count += 1

            return {
                "status": "ingested",
                "entity_type": "evidence",
                "node_id": node.node_id,
                "entity_id": evidence.id,
                "target_id": evidence.target_id,
                "epistemic_status": node.status.value,
                "provenance_id": prov.id,
            }

    def ingest_directional_specification(
        self,
        spec_dict: dict[str, Any],
        provider_id: str,
    ) -> dict[str, Any]:
        """Ingest a Directional Specification and emit a canonical DirectionalProposal.

        CRITICAL: Proposals are strictly advisory candidates and NEVER executed.
        """
        with self._lock:
            spec_id = spec_dict["id"]

            prov = ProvenanceRecord(
                producer_id="cognitia.runtime.directional",
                capability_id="propose.directional",
                source_type=SourceType.REASONING_ENGINE,
                metadata={"specification_id": spec_id, "provider_id": provider_id},
            )

            proposal = DirectionalProposal(
                specification_id=spec_id,
                provider_id=provider_id,
                provider_version="1.0.0",
                proposed_actions=(),
                residuals=(),
                confidence=0.85,
                proposal_status=ProposalLifecycleStatus.PROPOSED,
                epistemic_status=EpistemicStatus.UNRESOLVED,
                provenance=prov,
                metadata={"advisory_only": True, "authority": "NONE"},
            )

            return {
                "proposal_id": proposal.id,
                "specification_id": proposal.specification_id,
                "provider_id": proposal.provider_id,
                "proposal_status": proposal.proposal_status.value,
                "epistemic_status": proposal.epistemic_status.value,
                "confidence": proposal.confidence,
                "authority": "NONE",
                "message": "Directional proposal emitted. Epistemic Novelty != Production Authority.",
                "provenance_id": prov.id,
            }

    def get_status_summary(self) -> dict[str, Any]:
        with self._lock:
            return {
                "epistemic_service": "InMemoryEpistemicService",
                "total_ingested_observations": self._ingested_observations_count,
                "total_ingested_evidence": self._ingested_evidence_count,
                "active_nodes_count": len(self.epistemic_service._nodes),
                "max_node_capacity": MAX_EPISTEMIC_NODES,
                "status": "available",
            }