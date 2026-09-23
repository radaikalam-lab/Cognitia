"""Cognitia Runtime - Epistemic Bridge with Durable File Persistence.

Connects the Runtime HTTP Gateway to the Epistemic Subsystem and File Persistence Provider.
Ensures durable journal logging before memory updates and complete recovery on startup.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from cognitia.abi.types import (
    Observation,
    SCHEMA_VERSION_V1,
)
from cognitia.directional.types import DirectionalProposal
from cognitia.providers.types import ProposalLifecycleStatus
from cognitia.epistemic.service import InMemoryEpistemicService
from cognitia.epistemic.types import (
    EpistemicNode,
    EpistemicStatus,
    Evidence,
    EvidenceDirection,
)
from cognitia.provenance.record import (
    ProvenanceRecord,
    SourceType,
)

from ..persistence.persistence_contract import (
    PersistenceError,
    PersistenceProvider,
    PersistenceStatus,
    PersistenceWriteError,
)
from ..persistence.persistence_models import JournalRecord, SnapshotData

logger = logging.getLogger("cognitia.runtime.epistemic_bridge")

MAX_EPISTEMIC_NODES = 50000


class EpistemicCapacityExceededError(Exception):
    """Raised when the in-memory epistemic store reaches capacity."""
    pass


class EpistemicBridge:
    """Bridge coordinating validation, durable persistence, and in-memory epistemic state."""

    def __init__(
        self,
        epistemic_service: InMemoryEpistemicService | None = None,
        persistence_service: PersistenceProvider | None = None,
    ) -> None:
        self.epistemic_service = epistemic_service or InMemoryEpistemicService()
        self.persistence_service = persistence_service
        self._provenance_store: dict[str, ProvenanceRecord] = {}
        self._proposals_store: dict[str, DirectionalProposal] = {}
        self._lock = threading.RLock()
        self._ingested_observations_count = 0
        self._ingested_evidence_count = 0
        self._ingested_proposals_count = 0

        # Perform recovery if persistence provider is supplied
        if self.persistence_service is not None:
            self._initialize_and_recover()

    def _initialize_and_recover(self) -> None:
        """Execute persistence recovery and restore working state."""
        with self._lock:
            if not self.persistence_service:
                return

            snapshot, records_to_replay = self.persistence_service.initialize_and_recover()

            # 1. Restore Snapshot state if available
            if snapshot:
                self._import_snapshot_state(snapshot)

            # 2. Replay journal records after snapshot
            for record in records_to_replay:
                self._apply_journal_record_to_memory(record)

            logger.info(
                f"EpistemicBridge state ready: {len(self.epistemic_service._nodes)} active nodes, "
                f"{len(self._provenance_store)} provenance records, "
                f"{self._ingested_observations_count} observations, "
                f"{self._ingested_evidence_count} evidence"
            )

    def _apply_journal_record_to_memory(self, record: JournalRecord) -> None:
        """Replay a single journal record into working memory without re-persisting."""
        payload = record.payload
        rec_type = record.record_type

        # Restore Provenance if present
        prov_dict = payload.get("provenance")
        if prov_dict and isinstance(prov_dict, dict):
            prov = ProvenanceRecord(
                id=prov_dict.get("id"),
                schema_version=prov_dict.get("schema_version", SCHEMA_VERSION_V1),
                created_at=prov_dict.get("created_at"),
                producer_id=prov_dict.get("producer_id", "recovered"),
                capability_id=prov_dict.get("capability_id", "recovered"),
                source_type=SourceType(prov_dict.get("source_type", SourceType.SENSOR.value)),
                parent_ids=prov_dict.get("parent_ids", []),
                metadata=prov_dict.get("metadata", {}),
            )
            self._provenance_store[prov.id] = prov

        if rec_type == "observation":
            obs_dict = payload.get("observation", {})
            observation = Observation(
                id=obs_dict["id"],
                schema_version=obs_dict.get("schema_version", SCHEMA_VERSION_V1),
                created_at=obs_dict.get("created_at"),
                source_id=obs_dict.get("source_id", "recovered"),
                metadata=obs_dict.get("metadata", {}),
                payload=obs_dict.get("payload", {}),
            )
            self.epistemic_service.record_observation(observation)
            self._ingested_observations_count += 1

        elif rec_type == "evidence":
            ev_dict = payload.get("evidence", {})
            direction_str = ev_dict.get("direction", "SUPPORT").upper()
            direction = (
                EvidenceDirection.SUPPORT
                if direction_str == "SUPPORT"
                else (
                    EvidenceDirection.REFUTE
                    if direction_str == "REFUTE"
                    else EvidenceDirection.NEUTRAL
                )
            )
            prov_rec = self._provenance_store.get(ev_dict.get("provenance_id", ""))
            evidence = Evidence(
                id=ev_dict["id"],
                schema_version=ev_dict.get("schema_version", SCHEMA_VERSION_V1),
                created_at=ev_dict.get("created_at"),
                target_id=ev_dict["target_id"],
                direction=direction,
                confidence=float(ev_dict.get("confidence", 1.0)),
                weight=float(ev_dict.get("weight", 1.0)),
                provenance=prov_rec,
                observation_ids=ev_dict.get("observation_ids", []),
                metadata=ev_dict.get("metadata", {}),
            )
            self.epistemic_service.register_evidence(evidence)
            self._ingested_evidence_count += 1

        elif rec_type == "directional_specification":
            prop_dict = payload.get("proposal", {})
            if prop_dict:
                prov_rec = self._provenance_store.get(prop_dict.get("provenance_id", ""))
                proposal = DirectionalProposal(
                    specification_id=prop_dict.get("specification_id", ""),
                    provider_id=prop_dict.get("provider_id", ""),
                    provider_version=prop_dict.get("provider_version", "1.0.0"),
                    proposed_actions=(),
                    residuals=(),
                    confidence=float(prop_dict.get("confidence", 0.85)),
                    proposal_status=ProposalLifecycleStatus(prop_dict.get("proposal_status", "PROPOSED")),
                    epistemic_status=EpistemicStatus(prop_dict.get("epistemic_status", "UNRESOLVED")),
                    provenance=prov_rec,
                    metadata=prop_dict.get("metadata", {}),
                )
                if prop_dict.get("id"):
                    object.__setattr__(proposal, "id", prop_dict["id"])
                self._proposals_store[proposal.id] = proposal
                self._ingested_proposals_count += 1

    def _import_snapshot_state(self, snapshot: SnapshotData) -> None:
        """Import working state from snapshot data."""
        state = snapshot.state

        for p in state.get("provenance", []):
            prov = ProvenanceRecord(
                id=p.get("id"),
                schema_version=p.get("schema_version", SCHEMA_VERSION_V1),
                created_at=p.get("created_at"),
                producer_id=p.get("producer_id", ""),
                capability_id=p.get("capability_id", ""),
                source_type=SourceType(p.get("source_type", SourceType.SENSOR.value)),
                parent_ids=p.get("parent_ids", []),
                metadata=p.get("metadata", {}),
            )
            self._provenance_store[prov.id] = prov

        for obs_dict in state.get("observations", []):
            obs = Observation(
                id=obs_dict["id"],
                schema_version=obs_dict.get("schema_version", SCHEMA_VERSION_V1),
                created_at=obs_dict.get("created_at"),
                source_id=obs_dict.get("source_id", ""),
                metadata=obs_dict.get("metadata", {}),
                payload=obs_dict.get("payload", {}),
            )
            self.epistemic_service.record_observation(obs)
            self._ingested_observations_count += 1

        for ev_dict in state.get("evidence", []):
            direction_str = ev_dict.get("direction", "SUPPORT").upper()
            direction = (
                EvidenceDirection.SUPPORT
                if direction_str == "SUPPORT"
                else (
                    EvidenceDirection.REFUTE
                    if direction_str == "REFUTE"
                    else EvidenceDirection.NEUTRAL
                )
            )
            prov_rec = self._provenance_store.get(ev_dict.get("provenance_id", ""))
            ev = Evidence(
                id=ev_dict["id"],
                schema_version=ev_dict.get("schema_version", SCHEMA_VERSION_V1),
                created_at=ev_dict.get("created_at"),
                target_id=ev_dict["target_id"],
                direction=direction,
                confidence=float(ev_dict.get("confidence", 1.0)),
                weight=float(ev_dict.get("weight", 1.0)),
                provenance=prov_rec,
                observation_ids=ev_dict.get("observation_ids", []),
                metadata=ev_dict.get("metadata", {}),
            )
            self.epistemic_service.register_evidence(ev)
            self._ingested_evidence_count += 1

        for prop_dict in state.get("proposals", []):
            prov_rec = self._provenance_store.get(prop_dict.get("provenance_id", ""))
            prop = DirectionalProposal(
                specification_id=prop_dict.get("specification_id", ""),
                provider_id=prop_dict.get("provider_id", ""),
                provider_version=prop_dict.get("provider_version", "1.0.0"),
                proposed_actions=(),
                residuals=(),
                confidence=float(prop_dict.get("confidence", 0.85)),
                proposal_status=ProposalLifecycleStatus(prop_dict.get("proposal_status", "PROPOSED")),
                epistemic_status=EpistemicStatus(prop_dict.get("epistemic_status", "UNRESOLVED")),
                provenance=prov_rec,
                metadata=prop_dict.get("metadata", {}),
            )
            if prop_dict.get("id"):
                object.__setattr__(prop, "id", prop_dict["id"])
            self._proposals_store[prop.id] = prop
            self._ingested_proposals_count += 1

    def export_state_dict(self) -> dict[str, Any]:
        """Export a full canonical working state representation for snapshotting."""
        with self._lock:
            obs_list = []
            ev_list = []
            for node in self.epistemic_service._nodes.values():
                if node.entity_type == "observation" and isinstance(node.content, Observation):
                    obs_list.append({
                        "id": node.content.id,
                        "schema_version": node.content.schema_version,
                        "created_at": node.content.created_at,
                        "source_id": node.content.source_id,
                        "metadata": node.content.metadata,
                        "payload": node.content.payload,
                    })
                elif node.entity_type == "evidence" and isinstance(node.content, Evidence):
                    ev_list.append({
                        "id": node.content.id,
                        "schema_version": node.content.schema_version,
                        "created_at": node.content.created_at,
                        "target_id": node.content.target_id,
                        "direction": node.content.direction.name,
                        "confidence": node.content.confidence,
                        "weight": node.content.weight,
                        "provenance_id": node.content.provenance.id if node.content.provenance else None,
                        "observation_ids": node.content.observation_ids,
                        "metadata": node.content.metadata,
                    })

            prov_list = []
            for p in self._provenance_store.values():
                prov_list.append({
                    "id": p.id,
                    "schema_version": p.schema_version,
                    "created_at": p.created_at,
                    "producer_id": p.producer_id,
                    "capability_id": p.capability_id,
                    "source_type": p.source_type.value,
                    "parent_ids": list(p.parent_ids),
                    "metadata": p.metadata,
                })

            prop_list = []
            for prop in self._proposals_store.values():
                prop_list.append({
                    "id": prop.id,
                    "specification_id": prop.specification_id,
                    "provider_id": prop.provider_id,
                    "provider_version": prop.provider_version,
                    "confidence": prop.confidence,
                    "proposal_status": prop.proposal_status.value,
                    "epistemic_status": prop.epistemic_status.value,
                    "provenance_id": prop.provenance.id if prop.provenance else None,
                    "metadata": prop.metadata,
                })

            return {
                "observations": obs_list,
                "evidence": ev_list,
                "provenance": prov_list,
                "proposals": prop_list,
                "total_nodes": len(self.epistemic_service._nodes),
            }

    def ingest_observation(
        self,
        obs_dict: dict[str, Any],
        provider_id: str,
        capability: str,
    ) -> dict[str, Any]:
        """Convert validated observation dictionary, persist to journal, and ingest into memory."""
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

            # 4. PERSISTENCE FIRST: Write to durable journal before memory update
            if self.persistence_service is not None:
                prov_export = {
                    "id": prov.id,
                    "schema_version": prov.schema_version,
                    "created_at": prov.created_at,
                    "producer_id": prov.producer_id,
                    "capability_id": prov.capability_id,
                    "source_type": prov.source_type.value,
                    "parent_ids": list(prov.parent_ids),
                    "metadata": prov.metadata,
                }
                obs_export = {
                    "id": observation.id,
                    "schema_version": observation.schema_version,
                    "created_at": observation.created_at,
                    "source_id": observation.source_id,
                    "metadata": observation.metadata,
                    "payload": observation.payload,
                }
                # Throws PersistenceWriteError if disk write fails - memory will not be modified
                self.persistence_service.append_record(
                    record_type="observation",
                    record_id=observation.id,
                    payload={"observation": obs_export, "provenance": prov_export},
                )

            # 5. Record in In-Memory Epistemic Store
            self._provenance_store[prov.id] = prov
            node = self.epistemic_service.record_observation(observation)
            self._ingested_observations_count += 1

            # 6. Check automatic snapshot threshold
            if self.persistence_service and hasattr(self.persistence_service, "should_take_snapshot"):
                if self.persistence_service.should_take_snapshot():
                    try:
                        self.persistence_service.create_snapshot(self.export_state_dict())
                    except Exception as e:
                        logger.warning(f"Automatic snapshot failed: {e}")

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
        """Convert validated evidence dictionary, persist to journal, and register in memory."""
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

            # PERSISTENCE FIRST
            if self.persistence_service is not None:
                prov_export = {
                    "id": prov.id,
                    "schema_version": prov.schema_version,
                    "created_at": prov.created_at,
                    "producer_id": prov.producer_id,
                    "capability_id": prov.capability_id,
                    "source_type": prov.source_type.value,
                    "parent_ids": list(prov.parent_ids),
                    "metadata": prov.metadata,
                }
                ev_export = {
                    "id": evidence.id,
                    "schema_version": evidence.schema_version,
                    "created_at": evidence.created_at,
                    "target_id": evidence.target_id,
                    "direction": evidence.direction.name,
                    "confidence": evidence.confidence,
                    "weight": evidence.weight,
                    "provenance_id": prov.id,
                    "observation_ids": evidence.observation_ids,
                    "metadata": evidence.metadata,
                }
                self.persistence_service.append_record(
                    record_type="evidence",
                    record_id=evidence.id,
                    payload={"evidence": ev_export, "provenance": prov_export},
                )

            self._provenance_store[prov.id] = prov
            node = self.epistemic_service.register_evidence(evidence)
            self._ingested_evidence_count += 1

            if self.persistence_service and hasattr(self.persistence_service, "should_take_snapshot"):
                if self.persistence_service.should_take_snapshot():
                    try:
                        self.persistence_service.create_snapshot(self.export_state_dict())
                    except Exception as e:
                        logger.warning(f"Automatic snapshot failed: {e}")

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
        """Ingest Directional Specification, persist proposal record, and return proposal."""
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

            # PERSISTENCE FIRST
            if self.persistence_service is not None:
                prov_export = {
                    "id": prov.id,
                    "schema_version": prov.schema_version,
                    "created_at": prov.created_at,
                    "producer_id": prov.producer_id,
                    "capability_id": prov.capability_id,
                    "source_type": prov.source_type.value,
                    "parent_ids": list(prov.parent_ids),
                    "metadata": prov.metadata,
                }
                prop_export = {
                    "id": proposal.id,
                    "specification_id": proposal.specification_id,
                    "provider_id": proposal.provider_id,
                    "provider_version": proposal.provider_version,
                    "confidence": proposal.confidence,
                    "proposal_status": proposal.proposal_status.value,
                    "epistemic_status": proposal.epistemic_status.value,
                    "provenance_id": prov.id,
                    "metadata": proposal.metadata,
                }
                self.persistence_service.append_record(
                    record_type="directional_specification",
                    record_id=spec_id,
                    payload={
                        "specification": spec_dict,
                        "proposal": prop_export,
                        "provenance": prov_export,
                    },
                )

            self._provenance_store[prov.id] = prov
            self._proposals_store[proposal.id] = proposal
            self._ingested_proposals_count += 1

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
            pers_health = (
                self.persistence_service.get_health()
                if self.persistence_service
                else {"enabled": False, "status": "disabled"}
            )
            return {
                "epistemic_service": "InMemoryEpistemicService",
                "total_ingested_observations": self._ingested_observations_count,
                "total_ingested_evidence": self._ingested_evidence_count,
                "active_nodes_count": len(self.epistemic_service._nodes),
                "max_node_capacity": MAX_EPISTEMIC_NODES,
                "persistence": pers_health,
                "status": "available",
            }

    def close(self) -> None:
        with self._lock:
            if self.persistence_service:
                self.persistence_service.close()
