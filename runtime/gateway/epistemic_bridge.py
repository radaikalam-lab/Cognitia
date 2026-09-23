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
from cognitia.learning.contract import (
    AdaptiveLearningResult,
    CandidateStatus,
    DriftReport,
    FeedbackRecord,
    KnowledgeType,
    LearningCurvePoint,
    LearningDomain,
    LearningEvent,
    LearningTransferProposal,
    LearningUpdate,
    ModelCandidate,
    ModelComparisonRecord,
    ModelEvaluation,
    ModelPromotionProposal,
    OutcomeRecord,
    PromotionDecisionRecord,
    TaskType,
    TransferCompatibilityResult,
    TransferCompatibilityStatus,
    TransferDecisionRecord,
    TransferType,
)
from cognitia.learning.laya_provider import LayaProvider
from cognitia.learning.representation import RepresentationAdapter
from cognitia.learning.service import AdaptiveLearningService
from cognitia.models.registry import ModelRecord, ModelStatus


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
        self.adaptive_learning = AdaptiveLearningService(
            persistence_service=self.persistence_service
        )

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
        elif rec_type == "model_registered":
            m_rec = ModelRecord(
                model_id=payload.get("model_id", ""),
                model_version=payload.get("model_version", "1.0.0"),
                domain_id=payload.get("domain_id", "default"),
                provider=payload.get("provider", "laya"),
                status=ModelStatus(payload.get("status", "active")),
                is_deterministic=payload.get("is_deterministic", True),
                calibration_checksum=payload.get("calibration_checksum", ""),
            )
            try:
                self.adaptive_learning.register_model(m_rec)
            except Exception:
                pass

        elif rec_type == "adaptive_learning_result":
            res = AdaptiveLearningResult(
                id=payload.get("id", ""),
                domain_id=payload.get("domain_id", "default"),
                model_id=payload.get("model_id", ""),
                model_version=payload.get("model_version", "1.0.0"),
                provider_id=payload.get("provider_id", "laya"),
                task=TaskType(payload.get("task", "classification")),
                output=payload.get("output", {}),
                confidence=float(payload.get("confidence", 0.0)),
                is_deterministic=payload.get("is_deterministic", True),
                input_reference=payload.get("input_reference", ""),
                representation_version=payload.get("representation_version", "1.0.0"),
                epistemic_status=payload.get("epistemic_status", "UNRESOLVED"),
                authority="NONE",
            )
            self.adaptive_learning._learning_history.append(res)

        elif rec_type == "learning_curve_point":
            pt = LearningCurvePoint(
                id=payload.get("id", ""),
                domain_id=payload.get("domain_id", "default"),
                model_id=payload.get("model_id", ""),
                model_version=payload.get("model_version", "1.0.0"),
                provider_id=payload.get("provider_id", "laya"),
                step_or_epoch=int(payload.get("step_or_epoch", 0)),
                sample_count=int(payload.get("sample_count", 0)),
                metrics=payload.get("metrics", {}),
            )
            self.adaptive_learning._learning_curves.append(pt)

        elif rec_type == "model_comparison":
            comp = ModelComparisonRecord(
                id=payload.get("id", ""),
                task=TaskType(payload.get("task", "classification")),
                dataset_id=payload.get("dataset_id", ""),
                candidate_models=payload.get("candidate_models", []),
                metrics_by_model=payload.get("metrics_by_model", {}),
                advisory_summary=payload.get("advisory_summary", ""),
                authority="NONE",
            )
            self.adaptive_learning._comparisons.append(comp)

        elif rec_type == "drift_report":
            report = DriftReport(
                id=payload.get("id", ""),
                domain_id=payload.get("domain_id", "default"),
                model_id=payload.get("model_id", ""),
                drift_type=payload.get("drift_type", "prediction_drift"),
                metric_name=payload.get("metric_name", ""),
                baseline_value=float(payload.get("baseline_value", 0.0)),
                current_value=float(payload.get("current_value", 0.0)),
                drift_magnitude=float(payload.get("drift_magnitude", 0.0)),
                drift_detected=bool(payload.get("drift_detected", False)),
                recommendation=payload.get("recommendation", ""),
                authority="NONE",
            )
            self.adaptive_learning._drift_reports.append(report)

        elif rec_type == "outcome_record":
            outcome = OutcomeRecord(
                id=payload.get("id", ""),
                domain_id=payload.get("domain_id", "default"),
                source_id=payload.get("source_id", ""),
                target_prediction_id=payload.get("target_prediction_id", ""),
                observation_id=payload.get("observation_id", ""),
                actual_values=payload.get("actual_values", {}),
                is_ground_truth=payload.get("is_ground_truth", True),
                authority="NONE",
                metadata=payload.get("metadata", {}),
            )
            self.adaptive_learning._outcomes[outcome.id] = outcome

        elif rec_type == "feedback_record":
            fb = FeedbackRecord(
                id=payload.get("id", ""),
                domain_id=payload.get("domain_id", "default"),
                prediction_id=payload.get("prediction_id", ""),
                outcome_id=payload.get("outcome_id", ""),
                model_id=payload.get("model_id", ""),
                model_version=payload.get("model_version", "1.0.0"),
                provider_id=payload.get("provider_id", "laya"),
                loss_or_error=float(payload.get("loss_or_error", 0.0)),
                metrics=payload.get("metrics", {}),
                feedback_type=payload.get("feedback_type", "direct_outcome"),
                payload=payload.get("payload", {}),
                authority="NONE",
            )
            self.adaptive_learning._feedback[fb.id] = fb

        elif rec_type == "learning_event":
            le = LearningEvent(
                id=payload.get("id", ""),
                domain_id=payload.get("domain_id", "default"),
                event_type=payload.get("event_type", "outcome_feedback"),
                feedback_ids=payload.get("feedback_ids", []),
                prediction_ids=payload.get("prediction_ids", []),
                outcome_ids=payload.get("outcome_ids", []),
                model_id=payload.get("model_id", ""),
                model_version=payload.get("model_version", "1.0.0"),
                provider_id=payload.get("provider_id", "laya"),
                sample_count=int(payload.get("sample_count", 0)),
                data_fingerprint=payload.get("data_fingerprint", ""),
                authority="NONE",
            )
            self.adaptive_learning._learning_events[le.id] = le

        elif rec_type == "learning_update":
            lu = LearningUpdate(
                id=payload.get("id", ""),
                domain_id=payload.get("domain_id", "default"),
                learning_event_id=payload.get("learning_event_id", ""),
                parent_model_id=payload.get("parent_model_id", ""),
                parent_model_version=payload.get("parent_model_version", "1.0.0"),
                candidate_model_id=payload.get("candidate_model_id", ""),
                candidate_model_version=payload.get("candidate_model_version", "1.1-candidate"),
                provider_id=payload.get("provider_id", "laya"),
                update_method=payload.get("update_method", "delta_update"),
                parameter_deltas=payload.get("parameter_deltas", {}),
                parameter_fingerprint=payload.get("parameter_fingerprint", ""),
                random_seed=int(payload.get("random_seed", 42)),
                authority="NONE",
            )
            self.adaptive_learning._learning_updates[lu.id] = lu

        elif rec_type == "model_candidate":
            mc = ModelCandidate(
                id=payload.get("id", ""),
                domain_id=payload.get("domain_id", "default"),
                candidate_model_id=payload.get("candidate_model_id", ""),
                candidate_model_version=payload.get("candidate_model_version", "1.1-candidate"),
                parent_model_id=payload.get("parent_model_id", ""),
                parent_model_version=payload.get("parent_model_version", "1.0.0"),
                provider_id=payload.get("provider_id", "laya"),
                provider_version=payload.get("provider_version", "1.0.0"),
                status=CandidateStatus(payload.get("status", "candidate")),
                parameter_fingerprint=payload.get("parameter_fingerprint", ""),
                parameters=payload.get("parameters", {}),
                creation_seed=int(payload.get("creation_seed", 42)),
                learning_event_ids=payload.get("learning_event_ids", []),
                is_deterministic=payload.get("is_deterministic", True),
                authority="NONE",
            )
            self.adaptive_learning._candidates[mc.id] = mc
            self.adaptive_learning._candidates[mc.candidate_model_version] = mc
            cand_record = ModelRecord(
                model_id=mc.candidate_model_id,
                model_version=mc.candidate_model_version,
                domain_id=mc.domain_id,
                provider=mc.provider_id,
                status=ModelStatus.CANDIDATE,
                is_deterministic=mc.is_deterministic,
                calibration_checksum=mc.parameter_fingerprint,
            )
            self.adaptive_learning.model_registry.register(cand_record)

        elif rec_type == "model_evaluation":
            me = ModelEvaluation(
                id=payload.get("id", ""),
                domain_id=payload.get("domain_id", "default"),
                model_id=payload.get("model_id", ""),
                model_version=payload.get("model_version", "1.0.0"),
                provider_id=payload.get("provider_id", "laya"),
                dataset_id=payload.get("dataset_id", ""),
                sample_count=int(payload.get("sample_count", 0)),
                metrics=payload.get("metrics", {}),
                is_deterministic=payload.get("is_deterministic", True),
                authority="NONE",
            )
            self.adaptive_learning._evaluations[me.id] = me

        elif rec_type == "model_promotion_proposal":
            prop = ModelPromotionProposal(
                id=payload.get("id", ""),
                domain_id=payload.get("domain_id", "default"),
                parent_model_id=payload.get("parent_model_id", ""),
                parent_model_version=payload.get("parent_model_version", "1.0.0"),
                candidate_model_id=payload.get("candidate_model_id", ""),
                candidate_model_version=payload.get("candidate_model_version", "1.1-candidate"),
                provider_id=payload.get("provider_id", "laya"),
                dataset_id=payload.get("dataset_id", ""),
                baseline_metrics=payload.get("baseline_metrics", {}),
                candidate_metrics=payload.get("candidate_metrics", {}),
                metric_deltas=payload.get("metric_deltas", {}),
                drift_context=payload.get("drift_context", {}),
                rationale=payload.get("rationale", ""),
                recommendation=payload.get("recommendation", "PROPOSE_CANDIDATE"),
                status=CandidateStatus(payload.get("status", "proposed")),
                authority="NONE",
            )
            self.adaptive_learning._proposals[prop.id] = prop

        elif rec_type == "promotion_decision":
            dec = PromotionDecisionRecord(
                id=payload.get("id", ""),
                proposal_id=payload.get("proposal_id", ""),
                candidate_model_id=payload.get("candidate_model_id", ""),
                candidate_model_version=payload.get("candidate_model_version", ""),
                decision=payload.get("decision", "REJECTED"),
                decider_id=payload.get("decider_id", ""),
                decider_authority=payload.get("decider_authority", ""),
                rationale=payload.get("rationale", ""),
                cognitia_authority="NONE",
            )
            self.adaptive_learning._decisions[dec.id] = dec

        elif rec_type == "learning_domain":
            domain = LearningDomain(
                domain_id=payload.get("domain_id", "default"),
                domain_version=payload.get("domain_version", "1.0.0"),
                description=payload.get("description", ""),
                representation_version=payload.get("representation_version", "1.0.0"),
                declared_providers=payload.get("declared_providers", payload.get("compatible_providers", ["laya"])),
                metadata=payload.get("metadata", {}),
            )
            self.adaptive_learning._domains[domain.domain_id] = domain

        elif rec_type == "learning_transfer_proposal":
            tp = LearningTransferProposal(
                id=payload.get("id", ""),
                source_domain_id=payload.get("source_domain_id", ""),
                target_domain_id=payload.get("target_domain_id", ""),
                transfer_type=TransferType(payload.get("transfer_type", "model_transfer")),
                knowledge_type=KnowledgeType(payload.get("knowledge_type", "feature_extractor")),
                source_model_id=payload.get("source_model_id", ""),
                source_model_version=payload.get("source_model_version", ""),
                target_model_id=payload.get("target_model_id", ""),
                target_base_model_version=payload.get("target_base_model_version", ""),
                rationale=payload.get("rationale", ""),
                transfer_payload=payload.get("transfer_payload", {}),
                authority="NONE",
                metadata=payload.get("metadata", {}),
            )
            self.adaptive_learning._transfer_proposals[tp.id] = tp

        elif rec_type == "transfer_compatibility_result":
            tcr = TransferCompatibilityResult(
                id=payload.get("id", ""),
                proposal_id=payload.get("proposal_id", ""),
                source_domain_id=payload.get("source_domain_id", ""),
                target_domain_id=payload.get("target_domain_id", ""),
                status=TransferCompatibilityStatus(payload.get("status", "incompatible")),
                score=float(payload.get("score", 0.0)),
                compatibility_details=payload.get("compatibility_details", {}),
                risks=payload.get("risks", []),
                advisory_recommendation=payload.get("advisory_recommendation", ""),
                authority="NONE",
                metadata=payload.get("metadata", {}),
            )
            self.adaptive_learning._transfer_compatibility[tcr.id] = tcr

        elif rec_type == "transfer_decision":
            td = TransferDecisionRecord(
                id=payload.get("id", ""),
                proposal_id=payload.get("proposal_id", ""),
                decision=payload.get("decision", "REJECTED"),
                decider_id=payload.get("decider_id", ""),
                decision_source=payload.get("decision_source", "EXTERNAL"),
                rationale=payload.get("rationale", ""),
                cognitia_authority="NONE",
                metadata=payload.get("metadata", {}),
            )
            self.adaptive_learning._transfer_decisions[td.id] = td


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


            models_list = [
                {
                    "model_id": m.model_id,
                    "model_version": m.model_version,
                    "provider": m.provider,
                    "status": m.status.value if hasattr(m.status, "value") else str(m.status),
                    "is_deterministic": m.is_deterministic,
                    "calibration_checksum": m.calibration_checksum,
                }
                for m in self.adaptive_learning.model_registry.list_versions("laya_acoustic_v1")
            ]
            learning_hist_list = [
                {
                    "id": r.id,
                    "model_id": r.model_id,
                    "model_version": r.model_version,
                    "provider_id": r.provider_id,
                    "task": r.task.value if hasattr(r.task, "value") else str(r.task),
                    "output": r.output,
                    "confidence": r.confidence,
                    "is_deterministic": r.is_deterministic,
                    "input_reference": r.input_reference,
                    "representation_version": r.representation_version,
                    "epistemic_status": r.epistemic_status,
                    "authority": r.authority,
                }
                for r in self.adaptive_learning.list_history()
            ]
            return {
                "observations": obs_list,
                "evidence": ev_list,
                "provenance": prov_list,
                "proposals": prop_list,
                "models": models_list,
                "learning_history": learning_hist_list,
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
