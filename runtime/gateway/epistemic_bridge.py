"""Epistemic Subsystem Bridge for Cognitia Runtime Gateway."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Ensure Cognitia core is in path
COGNITIA_SRC = Path(__file__).resolve().parent.parent.parent / "src"
if str(COGNITIA_SRC) not in sys.path:
    sys.path.insert(0, str(COGNITIA_SRC))

from cognitia.abi.types import Observation, SCHEMA_VERSION_V1, DeterministicSerializer
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.epistemic.service import InMemoryEpistemicService
from cognitia.directional.types import DirectionalSpecification, DirectionalProposal


class EpistemicBridge:
    """Bridges validated provider messages to Cognitia Epistemic Core."""

    def __init__(self, epistemic_service: InMemoryEpistemicService | None = None) -> None:
        self.epistemic_service = epistemic_service or InMemoryEpistemicService()
        self._provenance_store: dict[str, ProvenanceRecord] = {}
        self._ingested_count = 0

    def ingest_observation(
        self,
        obs_dict: dict[str, Any],
        provider_id: str,
        capability: str,
    ) -> dict[str, Any]:
        """Convert validated observation dictionary into canonical Observation & ProvenanceRecord

        and ingest into the Epistemic service.
        """
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
        self._ingested_count += 1

        return {
            "status": "ingested",
            "node_id": node.node_id,
            "entity_id": observation.id,
            "epistemic_status": node.status.value,
            "provenance_id": prov.id,
        }

    def ingest_directional_specification(
        self,
        spec_dict: dict[str, Any],
        provider_id: str,
    ) -> dict[str, Any]:
        """Ingest a Directional Specification and return an ADVISORY candidate proposal.

        CRITICAL: This proposal is strictly advisory and NEVER executed.
        """
        spec_id = spec_dict.get("id")
        objectives = spec_dict.get("objectives", [])
        constraints = spec_dict.get("constraints", [])
        success_criteria = spec_dict.get("success_criteria", [])

        # Invariant check: Directional specifications cannot mandate direct command execution
        proposal = {
            "proposal_id": f"prop-{spec_id}",
            "specification_id": spec_id,
            "provider_id": provider_id,
            "status": "advisory_candidate",
            "authority": "NONE",
            "evaluations": [
                {
                    "objective": obj.get("description", str(obj)),
                    "feasibility": "epistemic_advisory_only",
                }
                for obj in objectives
            ],
            "message": "Directional specification evaluated. Epistemic Novelty != Production Authority.",
        }
        return proposal

    def get_status_summary(self) -> dict[str, Any]:
        return {
            "epistemic_service": "InMemoryEpistemicService",
            "total_ingested_observations": self._ingested_count,
            "active_nodes_count": len(self.epistemic_service._nodes),
            "status": "available",
        }