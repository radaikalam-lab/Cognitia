"""Adaptive Learning Orchestration Service.

Integrates ModelRegistry, AdaptiveLearningProvider, RepresentationAdapter,
EvaluationEngine, DriftDetector, LearningReplayEngine, LearningTransferEngine,
and FilePersistenceService into an auditable outcome-driven and domain-scoped
adaptive learning loop with ZERO production authority.
"""

from __future__ import annotations

import hashlib
from typing import Any

from cognitia.abi.types import Observation
from cognitia.directional.types import DirectionalSpecification
from cognitia.epistemic.types import Evidence
from cognitia.learning.contract import (
    AdaptiveInferenceRequest,
    AdaptiveLearningFailure,
    AdaptiveLearningProvider,
    AdaptiveLearningResult,
    CandidateStatus,
    DomainFreezeMode,
    DriftReport,
    FeedbackRecord,
    KnowledgeType,
    LearningCurvePoint,
    LearningDomain,
    LearningEvent,
    LearningTransferProposal,
    LearningUpdate,
    LifecycleEventType,
    ModelActivationObservation,
    ModelArtifactProvenance,
    ModelCandidate,
    ModelComparisonRecord,
    ModelComparisonReport,
    ModelEvaluation,
    ModelLifecycleEvent,
    ModelLifecycleState,
    ModelPromotionDecision,
    ModelPromotionProposal,
    ModelRollbackDecision,
    ModelRollbackProposal,
    OutcomeRecord,
    PredictionRecord,
    PromotionDecisionRecord,
    RuntimeActivationState,
    TaskType,
    TransferCompatibilityResult,
    TransferDecisionRecord,
    TransferType,
)
from cognitia.learning.drift import DriftDetector, StatisticalDriftDetector
from cognitia.learning.evaluation import ModelEvaluationEngine
from cognitia.learning.laya_provider import LayaProvider, LayaSurrogateProvider, RealLayaProvider
from cognitia.learning.replay import LearningReplayEngine, ReplayVerificationResult
from cognitia.learning.representation import RepresentationAdapter
from cognitia.learning.transfer import LearningTransferEngine
from cognitia.models.registry import (
    InMemoryModelRegistry,
    ModelLifecycleState,
    ModelRecord,
    ModelRegistry,
    ModelStatus,
    RuntimeActivationState,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType


class AdaptiveLearningService:
    """Central service coordinating domains, models, inference, outcomes, feedback, candidates, evaluation, transfer, lifecycle governance, and persistence."""

    def __init__(
        self,
        model_registry: ModelRegistry | None = None,
        persistence_service: Any = None,
        drift_detector: DriftDetector | None = None,
    ) -> None:
        self.model_registry = model_registry or InMemoryModelRegistry()
        self.persistence_service = persistence_service
        self.drift_detector = drift_detector or StatisticalDriftDetector()
        self._providers: dict[str, AdaptiveLearningProvider] = {}
        self._learning_history: list[AdaptiveLearningResult] = []
        self._learning_curves: list[LearningCurvePoint] = []
        self._comparisons: list[ModelComparisonRecord] = []
        self._drift_reports: list[DriftReport] = []

        # AL1 Lifecycle Storage
        self._outcomes: dict[str, OutcomeRecord] = {}
        self._feedback: dict[str, FeedbackRecord] = {}
        self._learning_events: dict[str, LearningEvent] = {}
        self._learning_updates: dict[str, LearningUpdate] = {}
        self._candidates: dict[str, ModelCandidate] = {}
        self._evaluations: dict[str, ModelEvaluation] = {}
        self._proposals: dict[str, ModelPromotionProposal] = {}
        self._decisions: dict[str, PromotionDecisionRecord] = {}

        # AL2 Domain & Transfer Storage
        self._domains: dict[str, LearningDomain] = {}
        self._transfer_proposals: dict[str, LearningTransferProposal] = {}
        self._transfer_compatibility: dict[str, TransferCompatibilityResult] = {}
        self._transfer_decisions: dict[str, TransferDecisionRecord] = {}

        # AL3 Lifecycle, Governance, Freeze, & Rollback Storage
        self._domain_freeze_modes: dict[str, DomainFreezeMode] = {}
        self._lifecycle_events: list[ModelLifecycleEvent] = []
        self._rollback_proposals: dict[str, ModelRollbackProposal] = {}
        self._rollback_decisions: dict[str, ModelRollbackDecision] = {}
        self._activation_observations: list[ModelActivationObservation] = []

        # Register default surrogate provider
        laya_surrogate = LayaSurrogateProvider()
        self.register_provider(laya_surrogate)

        # Register default legacy domain for AL1 backwards compatibility
        self.register_domain(
            LearningDomain(
                domain_id="default",
                domain_version="1.0.0",
                description="Legacy AL1 default domain scope",
                representation_version="1.0.0",
                declared_providers=["laya"],
            )
        )

    # --- Domain Registration & Validation ---

    def register_domain(self, domain: LearningDomain) -> LearningDomain:
        """Register a bounded semantic learning domain. Must be explicitly registered."""
        if not domain.domain_id:
            raise ValueError("LearningDomain domain_id cannot be empty")

        self._domains[domain.domain_id] = domain

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="learning_domain",
                    record_id=f"domain:{domain.domain_id}",
                    payload={
                        "id": domain.id,
                        "domain_id": domain.domain_id,
                        "domain_version": domain.domain_version,
                        "description": domain.description,
                        "representation_version": domain.representation_version,
                        "declared_providers": domain.declared_providers,
                        "metadata": domain.metadata,
                    },
                )
            except Exception:
                pass

        return domain

    def get_domain(self, domain_id: str) -> LearningDomain:
        """Retrieve a registered learning domain. Fails closed if domain is unknown."""
        if domain_id not in self._domains:
            raise AdaptiveLearningFailure(
                f"Domain '{domain_id}' is not registered; learning operations require an explicitly registered domain scope",
                domain_id=domain_id,
                error_code="UNREGISTERED_DOMAIN",
            )
        return self._domains[domain_id]

    def list_domains(self) -> list[LearningDomain]:
        return list(self._domains.values())

    # --- AL3 Domain Freeze Management ---

    def get_domain_freeze_mode(self, domain_id: str = "default") -> DomainFreezeMode:
        """Get current governance freeze mode for a domain (NORMAL, FROZEN, OBSERVATION_ONLY)."""
        return self._domain_freeze_modes.get(domain_id, DomainFreezeMode.NORMAL)

    def freeze_domain(self, domain_id: str, mode: DomainFreezeMode = DomainFreezeMode.FROZEN) -> DomainFreezeMode:
        """Set freeze mode for a domain. Persists freeze event in audit stream."""
        self.get_domain(domain_id)
        prev_mode = self.get_domain_freeze_mode(domain_id)
        self._domain_freeze_modes[domain_id] = mode

        event = ModelLifecycleEvent(
            domain_id=domain_id,
            event_type=LifecycleEventType.MODEL_FROZEN if mode != DomainFreezeMode.NORMAL else LifecycleEventType.MODEL_UNFROZEN,
            payload={"previous_mode": prev_mode.value, "new_mode": mode.value},
            authority="NONE",
            provenance=ProvenanceRecord(
                source_type=SourceType.HUMAN,
                producer_id=f"freeze:{domain_id}",
                capability_id="governance.freeze",
                is_deterministic=True,
            ),
        )
        self.record_lifecycle_event(event)
        return mode

    def unfreeze_domain(self, domain_id: str) -> DomainFreezeMode:
        """Unfreeze a domain back to NORMAL operation."""
        return self.freeze_domain(domain_id, mode=DomainFreezeMode.NORMAL)

    # --- Provider Management ---

    def register_provider(self, provider: AdaptiveLearningProvider) -> None:
        """Register an adaptive learning provider."""
        self._providers[provider.provider_id] = provider

    def get_provider(self, provider_id: str = "laya") -> AdaptiveLearningProvider:
        """Retrieve a registered learning provider."""
        if provider_id not in self._providers:
            raise AdaptiveLearningFailure(
                f"Provider '{provider_id}' is not registered",
                provider_id=provider_id,
                error_code="PROVIDER_NOT_FOUND",
            )
        return self._providers[provider_id]

    # --- Model Registration ---

    def register_model(self, record: ModelRecord) -> None:
        """Register a model record with its provider, domain, and persistence."""
        # Validate domain if not default
        self.get_domain(record.domain_id)

        self.model_registry.register(record)
        if record.provider in self._providers:
            self._providers[record.provider].load_model(record)

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="model_registered",
                    record_id=f"model:{record.domain_id}:{record.model_id}:{record.model_version}",
                    payload={
                        "model_id": record.model_id,
                        "model_version": record.model_version,
                        "domain_id": record.domain_id,
                        "provider": record.provider,
                        "status": record.status.value if hasattr(record.status, "value") else str(record.status),
                        "is_deterministic": record.is_deterministic,
                        "calibration_checksum": record.calibration_checksum,
                    },
                )
            except Exception:
                pass

    # --- Inference ---

    def predict_from_observation(
        self,
        obs: Observation,
        model_id: str = "laya_acoustic_v1",
        provider_id: str = "laya",
        task: TaskType = TaskType.CLASSIFICATION,
        parameters: dict[str, Any] | None = None,
        is_deterministic: bool = True,
        domain_id: str = "default",
    ) -> AdaptiveLearningResult:
        """Execute inference from a canonical Observation within a domain scope."""
        self.get_domain(domain_id)
        rep = RepresentationAdapter.adapt_observation(obs)
        return self.infer(
            model_id=model_id,
            provider_id=provider_id,
            task=task,
            representation=rep,
            parameters=parameters,
            is_deterministic=is_deterministic,
            domain_id=domain_id,
        )

    def predict_from_directional_spec(
        self,
        spec: DirectionalSpecification,
        model_id: str = "laya_directional_v1",
        provider_id: str = "laya",
        task: TaskType = TaskType.INTERPRETATION,
        parameters: dict[str, Any] | None = None,
        is_deterministic: bool = True,
        domain_id: str = "default",
    ) -> AdaptiveLearningResult:
        """Execute inference / candidate generation from a DirectionalSpecification."""
        self.get_domain(domain_id)
        rep = RepresentationAdapter.adapt_directional_spec(spec)
        return self.infer(
            model_id=model_id,
            provider_id=provider_id,
            task=task,
            representation=rep,
            parameters=parameters,
            is_deterministic=is_deterministic,
            domain_id=domain_id,
        )

    def infer(
        self,
        model_id: str,
        provider_id: str,
        task: TaskType,
        representation: Any,
        parameters: dict[str, Any] | None = None,
        is_deterministic: bool = True,
        model_version: str = "1.0.0",
        domain_id: str = "default",
    ) -> AdaptiveLearningResult:
        """Direct inference through representation boundary within domain scope."""
        self.get_domain(domain_id)
        provider = self.get_provider(provider_id)

        req = AdaptiveInferenceRequest(
            model_id=model_id,
            model_version=model_version,
            task=task,
            representation=representation,
            domain_id=domain_id,
            parameters=parameters or {},
            is_deterministic=is_deterministic,
        )
        result = provider.infer(req)

        if result.authority != "NONE":
            raise ValueError("AdaptiveLearningResult must carry authority='NONE'")

        # Ensure result carries the domain_id
        if getattr(result, "domain_id", "default") != domain_id:
            object.__setattr__(result, "domain_id", domain_id)

        self._learning_history.append(result)

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="adaptive_learning_result",
                    record_id=result.id,
                    payload={
                        "id": result.id,
                        "domain_id": domain_id,
                        "model_id": result.model_id,
                        "model_version": result.model_version,
                        "provider_id": result.provider_id,
                        "task": result.task.value if hasattr(result.task, "value") else str(result.task),
                        "output": result.output,
                        "confidence": result.confidence,
                        "is_deterministic": result.is_deterministic,
                        "input_reference": result.input_reference,
                        "representation_version": result.representation_version,
                        "epistemic_status": result.epistemic_status,
                        "authority": result.authority,
                    },
                )
            except Exception:
                pass

        return result

    # --- AL1 Outcome & Feedback Lifecycle (Domain-Scoped) ---

    def record_outcome(self, outcome: OutcomeRecord) -> OutcomeRecord:
        """Record domain-measured ground truth or operational outcome. Authority is strictly NONE."""
        self.get_domain(outcome.domain_id)
        if outcome.authority != "NONE":
            raise ValueError("OutcomeRecord must carry authority='NONE'")

        self._outcomes[outcome.id] = outcome

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="outcome_record",
                    record_id=outcome.id,
                    payload={
                        "id": outcome.id,
                        "domain_id": outcome.domain_id,
                        "source_id": outcome.source_id,
                        "target_prediction_id": outcome.target_prediction_id,
                        "observation_id": outcome.observation_id,
                        "actual_values": outcome.actual_values,
                        "is_ground_truth": outcome.is_ground_truth,
                        "authority": outcome.authority,
                        "metadata": outcome.metadata,
                    },
                )
            except Exception:
                pass

        return outcome

    def record_feedback(self, feedback: FeedbackRecord) -> FeedbackRecord:
        """Record feedback linking prediction to outcome. Authority is strictly NONE."""
        self.get_domain(feedback.domain_id)
        if feedback.authority != "NONE":
            raise ValueError("FeedbackRecord must carry authority='NONE'")

        self._feedback[feedback.id] = feedback

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="feedback_record",
                    record_id=feedback.id,
                    payload={
                        "id": feedback.id,
                        "domain_id": feedback.domain_id,
                        "prediction_id": feedback.prediction_id,
                        "outcome_id": feedback.outcome_id,
                        "model_id": feedback.model_id,
                        "model_version": feedback.model_version,
                        "provider_id": feedback.provider_id,
                        "loss_or_error": feedback.loss_or_error,
                        "metrics": feedback.metrics,
                        "feedback_type": feedback.feedback_type,
                        "payload": feedback.payload,
                        "authority": feedback.authority,
                    },
                )
            except Exception:
                pass

        return feedback

    def create_feedback_from_outcome(
        self,
        prediction_id: str,
        outcome: OutcomeRecord,
        feedback_type: str = "direct_outcome",
        custom_metrics: dict[str, float] | None = None,
        domain_id: str | None = None,
    ) -> FeedbackRecord:
        """Link a prediction to an observed outcome and calculate error/metrics."""
        effective_domain = domain_id or outcome.domain_id
        self.get_domain(effective_domain)

        # Find prediction in history
        pred_match = next((p for p in self._learning_history if p.id == prediction_id), None)
        if pred_match and getattr(pred_match, "domain_id", "default") != outcome.domain_id:
            raise AdaptiveLearningFailure(
                f"Domain mismatch: Prediction is from domain '{getattr(pred_match, 'domain_id', 'default')}', but outcome is from domain '{outcome.domain_id}'. Cross-domain feedback is forbidden.",
                domain_id=effective_domain,
                error_code="DOMAIN_MISMATCH",
            )
        if domain_id and outcome.domain_id != domain_id:
            raise AdaptiveLearningFailure(
                f"Domain mismatch: Target domain '{domain_id}' does not match outcome domain '{outcome.domain_id}'.",
                domain_id=domain_id,
                error_code="DOMAIN_MISMATCH",
            )

        model_id = pred_match.model_id if pred_match else "unknown"
        model_version = pred_match.model_version if pred_match else "1.0.0"
        provider_id = pred_match.provider_id if pred_match else "laya"

        loss = 0.0
        metrics = custom_metrics or {}

        if pred_match:
            pred_decision = str(pred_match.output.get("decision", ""))
            actual_label = str(outcome.actual_values.get("label", outcome.actual_values.get("expected", "")))
            if actual_label:
                is_match = pred_decision == actual_label
                loss = 0.0 if is_match else 1.0
                metrics["exact_match"] = 1.0 if is_match else 0.0
                metrics["loss"] = loss

        prov = ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            producer_id=f"feedback:{prediction_id}:{outcome.id}",
            capability_id="learn.adaptive.feedback",
            is_deterministic=True,
        )

        feedback = FeedbackRecord(
            domain_id=effective_domain,
            prediction_id=prediction_id,
            outcome_id=outcome.id,
            model_id=model_id,
            model_version=model_version,
            provider_id=provider_id,
            loss_or_error=loss,
            metrics=metrics,
            feedback_type=feedback_type,
            payload={"outcome_values": outcome.actual_values},
            authority="NONE",
            provenance=prov,
        )

        return self.record_feedback(feedback)

    def learn_from_feedback(
        self,
        feedback_ids: list[str],
        base_model_id: str = "laya_acoustic_v1",
        base_model_version: str | None = None,
        seed: int = 42,
        config: dict[str, Any] | None = None,
        domain_id: str = "default",
    ) -> tuple[ModelCandidate, LearningUpdate, LearningEvent]:
        """Trigger deterministic candidate generation from feedback events within a domain scope."""
        self.get_domain(domain_id)

        # AL3 Domain freeze check: OBSERVATION_ONLY blocks candidate generation
        mode = self.get_domain_freeze_mode(domain_id)
        if mode == DomainFreezeMode.OBSERVATION_ONLY:
            raise AdaptiveLearningFailure(
                f"Domain '{domain_id}' is in OBSERVATION_ONLY freeze mode; candidate generation and learning updates are disabled",
                domain_id=domain_id,
                error_code="DOMAIN_OBSERVATION_ONLY",
            )

        feedbacks = [self._feedback[fid] for fid in feedback_ids if fid in self._feedback]
        if not feedbacks:
            raise AdaptiveLearningFailure(
                f"No valid feedback records found for IDs: {feedback_ids}",
                model_id=base_model_id,
                provider_id="laya",
                domain_id=domain_id,
                error_code="INVALID_FEEDBACK",
            )

        # Enforce domain isolation: feedback from other domains cannot be used without explicit transfer
        foreign_feedbacks = [f for f in feedbacks if f.domain_id != domain_id]
        if foreign_feedbacks:
            raise AdaptiveLearningFailure(
                f"Cross-domain feedback contamination forbidden: feedback {foreign_feedbacks[0].id} belongs to domain '{foreign_feedbacks[0].domain_id}', not '{domain_id}'",
                model_id=base_model_id,
                domain_id=domain_id,
                error_code="DOMAIN_MISMATCH",
            )

        active_rec = self.model_registry.get_active(base_model_id, domain_id=domain_id)
        effective_base_ver = base_model_version or (active_rec.model_version if active_rec else "1.0.0")

        base_record = ModelRecord(
            model_id=base_model_id,
            model_version=effective_base_ver,
            domain_id=domain_id,
            provider="laya",
            is_deterministic=True,
        )

        data_fingerprint_src = f"{seed}:" + "|".join(sorted(f.id for f in feedbacks))
        data_fingerprint = hashlib.sha256(data_fingerprint_src.encode("utf-8")).hexdigest()

        event_prov = ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            producer_id=f"learning_event:{domain_id}:{base_model_id}:{effective_base_ver}",
            capability_id="learn.adaptive.event",
            is_deterministic=True,
        )

        learning_event = LearningEvent(
            domain_id=domain_id,
            event_type="outcome_feedback",
            feedback_ids=feedback_ids,
            prediction_ids=[f.prediction_id for f in feedbacks],
            outcome_ids=[f.outcome_id for f in feedbacks],
            model_id=base_model_id,
            model_version=effective_base_ver,
            provider_id="laya",
            sample_count=len(feedbacks),
            data_fingerprint=data_fingerprint,
            authority="NONE",
            provenance=event_prov,
        )
        self._learning_events[learning_event.id] = learning_event

        provider = self.get_provider("laya")
        candidate, update = provider.learn(
            events=[learning_event],
            base_model=base_record,
            seed=seed,
            config=config,
        )

        # Ensure candidate and update carry the domain_id
        if getattr(candidate, "domain_id", "default") != domain_id:
            object.__setattr__(candidate, "domain_id", domain_id)
        if getattr(update, "domain_id", "default") != domain_id:
            object.__setattr__(update, "domain_id", domain_id)

        # Store candidate and update
        self._candidates[f"{domain_id}:{candidate.candidate_model_version}"] = candidate
        self._candidates[candidate.candidate_model_version] = candidate
        self._candidates[candidate.id] = candidate
        self._learning_updates[update.id] = update

        # Register candidate in registry with CANDIDATE status in the scoped domain
        cand_model_rec = ModelRecord(
            model_id=candidate.candidate_model_id,
            model_version=candidate.candidate_model_version,
            domain_id=domain_id,
            provider=candidate.provider_id,
            status=ModelStatus.CANDIDATE,
            lifecycle_state=ModelLifecycleState.CANDIDATE,
            is_deterministic=candidate.is_deterministic,
            calibration_checksum=candidate.parameter_fingerprint,
        )
        self.model_registry.register(cand_model_rec)

        # Emit AL3 lifecycle event
        cand_event = ModelLifecycleEvent(
            domain_id=domain_id,
            event_type=LifecycleEventType.MODEL_CANDIDATE_CREATED,
            model_id=candidate.candidate_model_id,
            model_version=candidate.candidate_model_version,
            previous_state=ModelLifecycleState.REGISTERED,
            new_state=ModelLifecycleState.CANDIDATE,
            payload={
                "parent_version": candidate.parent_model_version,
                "learning_event_id": learning_event.id,
                "parameter_fingerprint": candidate.parameter_fingerprint,
            },
            authority="NONE",
        )
        self.record_lifecycle_event(cand_event)

        # Persist all 3 artifacts
        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="learning_event",
                    record_id=learning_event.id,
                    payload={
                        "id": learning_event.id,
                        "domain_id": learning_event.domain_id,
                        "event_type": learning_event.event_type,
                        "feedback_ids": learning_event.feedback_ids,
                        "prediction_ids": learning_event.prediction_ids,
                        "outcome_ids": learning_event.outcome_ids,
                        "model_id": learning_event.model_id,
                        "model_version": learning_event.model_version,
                        "provider_id": learning_event.provider_id,
                        "sample_count": learning_event.sample_count,
                        "data_fingerprint": learning_event.data_fingerprint,
                        "authority": learning_event.authority,
                    },
                )
                self.persistence_service.append_record(
                    record_type="learning_update",
                    record_id=update.id,
                    payload={
                        "id": update.id,
                        "domain_id": update.domain_id,
                        "learning_event_id": update.learning_event_id,
                        "parent_model_id": update.parent_model_id,
                        "parent_model_version": update.parent_model_version,
                        "candidate_model_id": update.candidate_model_id,
                        "candidate_model_version": update.candidate_model_version,
                        "provider_id": update.provider_id,
                        "update_method": update.update_method,
                        "parameter_deltas": update.parameter_deltas,
                        "parameter_fingerprint": update.parameter_fingerprint,
                        "random_seed": update.random_seed,
                        "authority": update.authority,
                    },
                )
                self.persistence_service.append_record(
                    record_type="model_candidate",
                    record_id=candidate.id,
                    payload={
                        "id": candidate.id,
                        "domain_id": candidate.domain_id,
                        "candidate_model_id": candidate.candidate_model_id,
                        "candidate_model_version": candidate.candidate_model_version,
                        "parent_model_id": candidate.parent_model_id,
                        "parent_model_version": candidate.parent_model_version,
                        "provider_id": candidate.provider_id,
                        "provider_version": candidate.provider_version,
                        "status": candidate.status.value if hasattr(candidate.status, "value") else str(candidate.status),
                        "parameter_fingerprint": candidate.parameter_fingerprint,
                        "parameters": candidate.parameters,
                        "creation_seed": candidate.creation_seed,
                        "learning_event_ids": candidate.learning_event_ids,
                        "transfer_proposal_id": candidate.transfer_proposal_id,
                        "is_deterministic": candidate.is_deterministic,
                        "authority": candidate.authority,
                    },
                )
            except Exception:
                pass

        return candidate, update, learning_event

    def evaluate_candidate(
        self,
        candidate_version_or_id: str,
        dataset: list[dict[str, Any]],
        model_id: str = "laya_acoustic_v1",
        domain_id: str = "default",
    ) -> ModelEvaluation:
        """Evaluate a ModelCandidate on a validation dataset. Authority is strictly NONE."""
        self.get_domain(domain_id)
        candidate = self._candidates.get(f"{domain_id}:{candidate_version_or_id}")
        if not candidate:
            candidate = self._candidates.get(candidate_version_or_id)
        if not candidate:
            candidate = next(
                (c for c in self._candidates.values() if (c.candidate_model_version == candidate_version_or_id or c.id == candidate_version_or_id) and (c.domain_id == domain_id or domain_id == "default")),
                None,
            )

        if not candidate:
            raise AdaptiveLearningFailure(
                f"Candidate '{candidate_version_or_id}' not found in domain '{domain_id}'",
                model_id=model_id,
                domain_id=domain_id,
                provider_id="laya",
                error_code="CANDIDATE_NOT_FOUND",
            )

        provider = self.get_provider(candidate.provider_id)
        evaluation = provider.evaluate_candidate(candidate, dataset)
        if getattr(evaluation, "domain_id", "default") != domain_id:
            object.__setattr__(evaluation, "domain_id", domain_id)

        self._evaluations[evaluation.id] = evaluation

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="model_evaluation",
                    record_id=evaluation.id,
                    payload={
                        "id": evaluation.id,
                        "domain_id": evaluation.domain_id,
                        "model_id": evaluation.model_id,
                        "model_version": evaluation.model_version,
                        "provider_id": evaluation.provider_id,
                        "dataset_id": evaluation.dataset_id,
                        "sample_count": evaluation.sample_count,
                        "metrics": evaluation.metrics,
                        "is_deterministic": evaluation.is_deterministic,
                        "authority": evaluation.authority,
                    },
                )
            except Exception:
                pass

        return evaluation

    def create_promotion_proposal(
        self,
        candidate_version: str,
        baseline_model_version: str = "1.0.0",
        model_id: str = "laya_acoustic_v1",
        dataset: list[dict[str, Any]] | None = None,
        dataset_id: str = "eval_dataset_v1",
        drift_context: dict[str, Any] | None = None,
        domain_id: str = "default",
    ) -> ModelPromotionProposal:
        """Create an advisory promotion proposal comparing candidate against active baseline model in domain.

        Cognitia NEVER activates or promotes models autonomously; authority is strictly NONE.
        """
        self.get_domain(domain_id)
        candidate = self._candidates.get(f"{domain_id}:{candidate_version}")
        if not candidate:
            candidate = self._candidates.get(candidate_version)
        if not candidate:
            candidate = next((c for c in self._candidates.values() if c.candidate_model_version == candidate_version and (c.domain_id == domain_id or domain_id == "default")), None)

        if not candidate:
            raise AdaptiveLearningFailure(
                f"Candidate '{candidate_version}' not found for promotion proposal in domain '{domain_id}'",
                model_id=model_id,
                domain_id=domain_id,
                provider_id="laya",
                error_code="CANDIDATE_NOT_FOUND",
            )

        provider = self.get_provider(candidate.provider_id)
        proposal = ModelEvaluationEngine.evaluate_candidate_vs_baseline(
            provider=provider,
            candidate=candidate,
            baseline_model_id=model_id,
            baseline_model_version=baseline_model_version,
            dataset=dataset or [],
            dataset_id=dataset_id,
            drift_context=drift_context,
        )
        if getattr(proposal, "domain_id", "default") != domain_id:
            object.__setattr__(proposal, "domain_id", domain_id)

        self._proposals[proposal.id] = proposal

        # Emit PROMOTION_PROPOSED lifecycle event
        prop_event = ModelLifecycleEvent(
            domain_id=domain_id,
            event_type=LifecycleEventType.PROMOTION_PROPOSED,
            model_id=proposal.candidate_model_id,
            model_version=proposal.candidate_model_version,
            previous_state=ModelLifecycleState.EVALUATED,
            new_state=ModelLifecycleState.PROPOSED,
            payload={
                "proposal_id": proposal.id,
                "parent_version": proposal.parent_model_version,
                "recommendation": proposal.recommendation,
                "metric_deltas": proposal.metric_deltas,
            },
            authority="NONE",
        )
        self.record_lifecycle_event(prop_event)

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="model_promotion_proposal",
                    record_id=proposal.id,
                    payload={
                        "id": proposal.id,
                        "domain_id": proposal.domain_id,
                        "parent_model_id": proposal.parent_model_id,
                        "parent_model_version": proposal.parent_model_version,
                        "candidate_model_id": proposal.candidate_model_id,
                        "candidate_model_version": proposal.candidate_model_version,
                        "provider_id": proposal.provider_id,
                        "dataset_id": proposal.dataset_id,
                        "baseline_metrics": proposal.baseline_metrics,
                        "candidate_metrics": proposal.candidate_metrics,
                        "metric_deltas": proposal.metric_deltas,
                        "drift_context": proposal.drift_context,
                        "rationale": proposal.rationale,
                        "recommendation": proposal.recommendation,
                        "status": proposal.status.value if hasattr(proposal.status, "value") else str(proposal.status),
                        "authority": proposal.authority,
                    },
                )
            except Exception:
                pass

        return proposal

    def record_promotion_decision(
        self,
        proposal_id: str,
        decision: str,
        decider_id: str,
        decider_authority: str = "domain_governance_board",
        rationale: str = "",
    ) -> PromotionDecisionRecord:
        """Record an external authority governance decision regarding a candidate model proposal.

        CRITICAL ARCHITECTURAL GUARANTEE:
        Cognitia records the audit trail and updates candidate state to APPROVED if accepted.
        Cognitia itself has ZERO authority to activate models. Activation MUST be performed by the host domain.
        """
        proposal = self._proposals.get(proposal_id)
        cand_id = proposal.candidate_model_id if proposal else "unknown"
        cand_ver = proposal.candidate_model_version if proposal else "unknown"
        domain_id = proposal.domain_id if proposal else "default"

        prov = ProvenanceRecord(
            source_type=SourceType.HUMAN,
            producer_id=f"decision:{decider_id}:{proposal_id}",
            capability_id="governance.decision",
            is_deterministic=True,
        )

        dec_upper = decision.upper()
        is_approved = dec_upper in ("ACCEPTED", "APPROVED")

        decision_rec = PromotionDecisionRecord(
            proposal_id=proposal_id,
            candidate_model_id=cand_id,
            candidate_model_version=cand_ver,
            decision=dec_upper,
            decider_id=decider_id,
            decider_authority=decider_authority,
            rationale=rationale,
            cognitia_authority="NONE",
            provenance=prov,
        )

        self._decisions[decision_rec.id] = decision_rec

        # Update candidate state in candidate storage and registry if approved
        if is_approved and cand_id and cand_ver:
            try:
                cand_rec = self.model_registry.get(cand_id, cand_ver, domain_id=domain_id)
                if cand_rec:
                    self.model_registry.set_lifecycle_state(
                        cand_id,
                        cand_ver,
                        ModelLifecycleState.APPROVED,
                        domain_id=domain_id,
                    )
            except Exception:
                pass

        # Emit PROMOTION_DECIDED lifecycle event
        dec_event = ModelLifecycleEvent(
            domain_id=domain_id,
            event_type=LifecycleEventType.PROMOTION_DECIDED,
            model_id=cand_id,
            model_version=cand_ver,
            previous_state=ModelLifecycleState.PROPOSED,
            new_state=ModelLifecycleState.APPROVED if is_approved else ModelLifecycleState.CANDIDATE,
            actor_id=decider_id,
            decision_reference=proposal_id,
            payload={
                "decision": dec_upper,
                "approved": is_approved,
                "decider_id": decider_id,
                "decider_authority": decider_authority,
                "rationale": rationale,
            },
            authority="NONE",
        )
        self.record_lifecycle_event(dec_event)

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="promotion_decision",
                    record_id=decision_rec.id,
                    payload={
                        "id": decision_rec.id,
                        "proposal_id": decision_rec.proposal_id,
                        "candidate_model_id": decision_rec.candidate_model_id,
                        "candidate_model_version": decision_rec.candidate_model_version,
                        "decision": decision_rec.decision,
                        "decider_id": decision_rec.decider_id,
                        "decider_authority": decision_rec.decider_authority,
                        "rationale": decision_rec.rationale,
                        "cognitia_authority": decision_rec.cognitia_authority,
                    },
                )
            except Exception:
                pass

        return decision_rec

    # --- AL2 Cross-Domain Knowledge Transfer Operations ---

    def create_transfer_proposal(
        self,
        source_domain_id: str,
        target_domain_id: str,
        source_model_id: str,
        source_model_version: str = "1.0.0",
        target_model_id: str | None = None,
        target_base_model_version: str = "1.0.0",
        source_candidate_version: str | None = None,
        source_provider_id: str = "laya",
        target_provider_id: str = "laya",
        transfer_type: TransferType = TransferType.MODEL_TRANSFER,
        knowledge_type: KnowledgeType = KnowledgeType.FEATURE_EXTRACTOR,
        rationale: str = "",
        transfer_payload: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LearningTransferProposal:
        """Create an explicit, advisory cross-domain transfer proposal and evaluate compatibility."""
        src_domain = self.get_domain(source_domain_id)
        tgt_domain = self.get_domain(target_domain_id)

        proposal, compat = LearningTransferEngine.create_proposal(
            source_domain=src_domain,
            target_domain=tgt_domain,
            source_model_id=source_model_id,
            source_model_version=source_model_version,
            target_model_id=target_model_id,
            target_base_model_version=target_base_model_version,
            source_candidate_version=source_candidate_version,
            source_provider_id=source_provider_id,
            target_provider_id=target_provider_id,
            transfer_type=transfer_type,
            knowledge_type=knowledge_type,
            rationale=rationale,
            transfer_payload=transfer_payload,
            metadata=metadata,
        )

        self._transfer_proposals[proposal.id] = proposal
        self._transfer_compatibility[proposal.id] = compat

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="learning_transfer_proposal",
                    record_id=proposal.id,
                    payload={
                        "id": proposal.id,
                        "source_domain_id": proposal.source_domain_id,
                        "target_domain_id": proposal.target_domain_id,
                        "source_model_id": proposal.source_model_id,
                        "source_model_version": proposal.source_model_version,
                        "target_model_id": proposal.target_model_id,
                        "target_base_model_version": proposal.target_base_model_version,
                        "transfer_type": proposal.transfer_type.value if hasattr(proposal.transfer_type, "value") else str(proposal.transfer_type),
                        "knowledge_type": proposal.knowledge_type.value if hasattr(proposal.knowledge_type, "value") else str(proposal.knowledge_type),
                        "rationale": proposal.rationale,
                        "transfer_payload": proposal.transfer_payload,
                        "authority": proposal.authority,
                        "metadata": proposal.metadata,
                    },
                )
                self.persistence_service.append_record(
                    record_type="transfer_compatibility_result",
                    record_id=compat.id,
                    payload={
                        "id": compat.id,
                        "proposal_id": compat.proposal_id,
                        "source_domain_id": compat.source_domain_id,
                        "target_domain_id": compat.target_domain_id,
                        "status": compat.status.value if hasattr(compat.status, "value") else str(compat.status),
                        "score": compat.score,
                        "compatibility_details": compat.compatibility_details,
                        "risks": compat.risks,
                        "advisory_recommendation": compat.advisory_recommendation,
                        "authority": compat.authority,
                        "metadata": compat.metadata,
                    },
                )
            except Exception:
                pass

        return proposal

    def propose_transfer(
        self,
        source_domain_id: str,
        target_domain_id: str,
        source_model_id: str,
        source_model_version: str = "1.0.0",
        source_candidate_version: str | None = None,
        source_provider_id: str = "laya",
        target_provider_id: str = "laya",
        transfer_type: TransferType = TransferType.PARAMETER_TRANSFER,
        knowledge_type: KnowledgeType = KnowledgeType.MODEL_CANDIDATE,
        rationale: str = "",
    ) -> tuple[LearningTransferProposal, TransferCompatibilityResult]:
        """Propose transfer and return tuple (proposal, compat)."""
        prop = self.create_transfer_proposal(
            source_domain_id=source_domain_id,
            target_domain_id=target_domain_id,
            source_model_id=source_model_id,
            source_model_version=source_model_version,
            source_candidate_version=source_candidate_version,
            source_provider_id=source_provider_id,
            target_provider_id=target_provider_id,
            transfer_type=transfer_type,
            knowledge_type=knowledge_type,
            rationale=rationale,
        )
        compat = self._transfer_compatibility[prop.id]
        return prop, compat

    def evaluate_transfer_compatibility(
        self,
        proposal: LearningTransferProposal | None = None,
        proposal_id: str | None = None,
    ) -> TransferCompatibilityResult:
        """Evaluate or re-evaluate compatibility for a transfer proposal."""
        if proposal is None and proposal_id is not None:
            if proposal_id in self._transfer_compatibility:
                return self._transfer_compatibility[proposal_id]
            proposal = self._transfer_proposals.get(proposal_id)
            if not proposal:
                raise AdaptiveLearningFailure(
                    f"Transfer proposal '{proposal_id}' not found",
                    error_code="PROPOSAL_NOT_FOUND",
                )

        if proposal is None:
            raise ValueError("Must provide either proposal or proposal_id")

        src_domain = self.get_domain(proposal.source_domain_id or proposal.source_domain)
        tgt_domain = self.get_domain(proposal.target_domain_id or proposal.target_domain)

        compat = LearningTransferEngine.evaluate_compatibility(
            proposal=proposal,
            source_domain=src_domain,
            target_domain=tgt_domain,
        )
        if proposal.id:
            self._transfer_compatibility[proposal.id] = compat
        return compat

    def evaluate_transfer(self, proposal_id: str) -> TransferCompatibilityResult:
        """Alias for evaluate_transfer_compatibility by proposal_id."""
        return self.evaluate_transfer_compatibility(proposal_id=proposal_id)

    def instantiate_transfer_candidate(
        self,
        proposal_id: str,
        target_model_id: str | None = None,
        target_candidate_version: str | None = None,
        seed: int = 42,
    ) -> ModelCandidate:
        """Instantiate a target-domain ModelCandidate from an authorized transfer proposal.

        CRITICAL CONTRACT:
        Creates a new target candidate only. Never modifies, overwrites, replaces, activates,
        or mutates the target domain's active model.
        """
        proposal = self._transfer_proposals.get(proposal_id)
        if not proposal:
            raise AdaptiveLearningFailure(
                f"Transfer proposal '{proposal_id}' not found",
                error_code="PROPOSAL_NOT_FOUND",
            )

        tgt_model = target_model_id or proposal.target_model_id or proposal.source_model_id
        src_domain = proposal.source_domain_id or proposal.source_domain
        tgt_domain = proposal.target_domain_id or proposal.target_domain

        source_candidate = None
        if proposal.source_candidate_version:
            source_candidate = self._candidates.get(f"{src_domain}:{proposal.source_candidate_version}") or self._candidates.get(proposal.source_candidate_version)

        source_rec = self.model_registry.get(
            model_id=proposal.source_model_id,
            version=proposal.source_model_version,
            domain_id=src_domain,
        ) or ModelRecord(
            model_id=proposal.source_model_id,
            model_version=proposal.source_model_version,
            domain_id=src_domain,
        )

        target_candidate = LearningTransferEngine.instantiate_transfer_candidate(
            proposal=proposal,
            source_candidate=source_candidate,
            source_model_record=source_rec,
            target_model_id=tgt_model,
            target_candidate_version=target_candidate_version,
            seed=seed,
        )

        # Store in candidates
        self._candidates[f"{target_candidate.domain_id}:{target_candidate.candidate_model_version}"] = target_candidate
        self._candidates[target_candidate.candidate_model_version] = target_candidate
        self._candidates[target_candidate.id] = target_candidate

        # Register in model registry with target domain and CANDIDATE status
        cand_model_rec = ModelRecord(
            model_id=target_candidate.candidate_model_id,
            model_version=target_candidate.candidate_model_version,
            domain_id=target_candidate.domain_id,
            provider=target_candidate.provider_id,
            status=ModelStatus.CANDIDATE,
            is_deterministic=target_candidate.is_deterministic,
            calibration_checksum=target_candidate.parameter_fingerprint,
        )
        self.model_registry.register(cand_model_rec)

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="model_candidate",
                    record_id=target_candidate.id,
                    payload={
                        "id": target_candidate.id,
                        "domain_id": target_candidate.domain_id,
                        "candidate_model_id": target_candidate.candidate_model_id,
                        "candidate_model_version": target_candidate.candidate_model_version,
                        "parent_model_id": target_candidate.parent_model_id,
                        "parent_model_version": target_candidate.parent_model_version,
                        "provider_id": target_candidate.provider_id,
                        "provider_version": target_candidate.provider_version,
                        "status": target_candidate.status.value if hasattr(target_candidate.status, "value") else str(target_candidate.status),
                        "parameter_fingerprint": target_candidate.parameter_fingerprint,
                        "parameters": target_candidate.parameters,
                        "creation_seed": target_candidate.creation_seed,
                        "learning_event_ids": target_candidate.learning_event_ids,
                        "transfer_proposal_id": target_candidate.transfer_proposal_id,
                        "is_deterministic": target_candidate.is_deterministic,
                        "authority": target_candidate.authority,
                    },
                )
            except Exception:
                pass

        return target_candidate

    def record_transfer_decision(
        self,
        proposal_id: str,
        decision: str,
        decider_id: str,
        rationale: str = "",
        metadata: dict[str, Any] | None = None,
        decider_authority: str = "target_domain_authority",
    ) -> TransferDecisionRecord:
        """Record an external domain governance decision regarding a transfer proposal.

        Cognitia records the audit trail; Cognitia itself has ZERO authority to activate models.
        """
        proposal = self._transfer_proposals.get(proposal_id)
        src_d = (proposal.source_domain_id if proposal else "unknown") or "unknown"
        tgt_d = (proposal.target_domain_id if proposal else "unknown") or "unknown"

        decision_rec = TransferDecisionRecord(
            proposal_id=proposal_id,
            source_domain_id=src_d,
            target_domain_id=tgt_d,
            decision=decision.upper(),
            decision_source="EXTERNAL",
            decider_id=decider_id,
            decider_authority=decider_authority,
            rationale=rationale,
            cognitia_authority="NONE",
            metadata=metadata or {},
            provenance=ProvenanceRecord(
                source_type=SourceType.HUMAN,
                producer_id=f"transfer_decision:{decider_id}:{proposal_id}",
                capability_id="governance.transfer",
                is_deterministic=True,
            ),
        )

        self._transfer_decisions[decision_rec.id] = decision_rec

        if proposal:
            object.__setattr__(proposal, "status", "ACCEPTED" if decision.upper() == "ACCEPTED" else "REJECTED")

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="transfer_decision",
                    record_id=decision_rec.id,
                    payload={
                        "id": decision_rec.id,
                        "proposal_id": decision_rec.proposal_id,
                        "source_domain_id": decision_rec.source_domain_id,
                        "target_domain_id": decision_rec.target_domain_id,
                        "decision": decision_rec.decision,
                        "decision_source": decision_rec.decision_source,
                        "decider_id": decision_rec.decider_id,
                        "decider_authority": decision_rec.decider_authority,
                        "rationale": decision_rec.rationale,
                        "cognitia_authority": decision_rec.cognitia_authority,
                        "metadata": decision_rec.metadata,
                    },
                )
            except Exception:
                pass

        return decision_rec


    # --- Replay ---

    def replay_learning(
        self,
        candidate_version: str,
        model_id: str = "laya_acoustic_v1",
        seed: int = 42,
        domain_id: str = "default",
    ) -> ReplayVerificationResult:
        """Replay candidate generation deterministically and verify parameter parity."""
        self.get_domain(domain_id)
        candidate = self._candidates.get(f"{domain_id}:{candidate_version}") or self._candidates.get(candidate_version)
        if not candidate:
            candidate = next((c for c in self._candidates.values() if c.candidate_model_version == candidate_version and (c.domain_id == domain_id or domain_id == "default")), None)

        if not candidate:
            return ReplayVerificationResult(
                domain_id=domain_id,
                candidate_model_id=model_id,
                candidate_model_version=candidate_version,
                is_replayable=False,
                is_exact_match=False,
                status="NON_REPLAYABLE",
                reason=f"Candidate version '{candidate_version}' not found in domain '{domain_id}'",
                authority="NONE",
            )

        events = [self._learning_events[eid] for eid in candidate.learning_event_ids if eid in self._learning_events]
        base_record = ModelRecord(
            model_id=candidate.parent_model_id,
            model_version=candidate.parent_model_version,
            domain_id=candidate.domain_id,
            provider=candidate.provider_id,
            is_deterministic=candidate.is_deterministic,
        )

        provider = self.get_provider(candidate.provider_id)
        return LearningReplayEngine.replay_candidate_learning(
            provider=provider,
            base_model=base_record,
            candidate=candidate,
            learning_events=events,
            seed=candidate.creation_seed,
        )

    # --- Query Methods (Domain Scoped) ---

    def list_outcomes(self, domain_id: str | None = None) -> list[OutcomeRecord]:
        if domain_id:
            return [o for o in self._outcomes.values() if o.domain_id == domain_id]
        return list(self._outcomes.values())

    def list_feedback(self, domain_id: str | None = None) -> list[FeedbackRecord]:
        if domain_id:
            return [f for f in self._feedback.values() if f.domain_id == domain_id]
        return list(self._feedback.values())

    def list_learning_events(self, domain_id: str | None = None) -> list[LearningEvent]:
        if domain_id:
            return [e for e in self._learning_events.values() if e.domain_id == domain_id]
        return list(self._learning_events.values())

    def list_learning_updates(self, domain_id: str | None = None) -> list[LearningUpdate]:
        if domain_id:
            return [u for u in self._learning_updates.values() if u.domain_id == domain_id]
        return list(self._learning_updates.values())

    def list_candidates(self, model_id: str | None = None, domain_id: str | None = None) -> list[ModelCandidate]:
        unique = {c.id: c for c in self._candidates.values()}.values()
        results = list(unique)
        if domain_id:
            results = [c for c in results if c.domain_id == domain_id]
        if model_id:
            results = [c for c in results if c.candidate_model_id == model_id]
        return results

    def list_evaluations(self, model_id: str | None = None, domain_id: str | None = None) -> list[ModelEvaluation]:
        results = list(self._evaluations.values())
        if domain_id:
            results = [e for e in results if e.domain_id == domain_id]
        if model_id:
            results = [e for e in results if e.model_id == model_id]
        return results

    def list_proposals(self, model_id: str | None = None, domain_id: str | None = None) -> list[ModelPromotionProposal]:
        results = list(self._proposals.values())
        if domain_id:
            results = [p for p in results if p.domain_id == domain_id]
        if model_id:
            results = [p for p in results if p.candidate_model_id == model_id]
        return results

    def list_decisions(self, proposal_id: str | None = None) -> list[PromotionDecisionRecord]:
        if proposal_id:
            return [d for d in self._decisions.values() if d.proposal_id == proposal_id]
        return list(self._decisions.values())

    def list_transfer_proposals(self, source_domain: str | None = None, target_domain: str | None = None) -> list[LearningTransferProposal]:
        results = list(self._transfer_proposals.values())
        if source_domain:
            results = [p for p in results if p.source_domain == source_domain]
        if target_domain:
            results = [p for p in results if p.target_domain == target_domain]
        return results

    def list_transfer_decisions(self, proposal_id: str | None = None) -> list[TransferDecisionRecord]:
        if proposal_id:
            return [d for d in self._transfer_decisions.values() if d.proposal_id == proposal_id]
        return list(self._transfer_decisions.values())

    def record_learning_point(
        self,
        model_id: str,
        model_version: str,
        provider_id: str,
        step: int,
        sample_count: int,
        metrics: dict[str, float],
        domain_id: str = "default",
    ) -> LearningCurvePoint:
        """Record a learning curve point and persist it."""
        self.get_domain(domain_id)
        pt = ModelEvaluationEngine.record_learning_curve_step(
            model_id=model_id,
            model_version=model_version,
            provider_id=provider_id,
            step=step,
            sample_count=sample_count,
            metrics=metrics,
        )
        if getattr(pt, "domain_id", "default") != domain_id:
            object.__setattr__(pt, "domain_id", domain_id)
        self._learning_curves.append(pt)

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="learning_curve_point",
                    record_id=pt.id,
                    payload={
                        "id": pt.id,
                        "domain_id": domain_id,
                        "model_id": pt.model_id,
                        "model_version": pt.model_version,
                        "provider_id": pt.provider_id,
                        "step_or_epoch": pt.step_or_epoch,
                        "sample_count": pt.sample_count,
                        "metrics": pt.metrics,
                    },
                )
            except Exception:
                pass

        return pt

    def compare_candidate_models(
        self,
        candidate_models: list[tuple[str, str]],
        dataset: list[dict[str, Any]],
        dataset_id: str = "eval_dataset_v1",
        provider_id: str = "laya",
        task: TaskType = TaskType.CLASSIFICATION,
        domain_id: str = "default",
    ) -> ModelComparisonRecord:
        """Run model competition on dataset and record comparison."""
        self.get_domain(domain_id)
        provider = self.get_provider(provider_id)
        comp = ModelEvaluationEngine.compare_models(
            provider=provider,
            candidate_models=candidate_models,
            dataset=dataset,
            dataset_id=dataset_id,
            task=task,
        )
        if getattr(comp, "domain_id", "default") != domain_id:
            object.__setattr__(comp, "domain_id", domain_id)
        self._comparisons.append(comp)

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="model_comparison",
                    record_id=comp.id,
                    payload={
                        "id": comp.id,
                        "domain_id": domain_id,
                        "task": comp.task.value if hasattr(comp.task, "value") else str(comp.task),
                        "dataset_id": comp.dataset_id,
                        "candidate_models": comp.candidate_models,
                        "metrics_by_model": comp.metrics_by_model,
                        "advisory_summary": comp.advisory_summary,
                        "authority": comp.authority,
                    },
                )
            except Exception:
                pass

        return comp

    def check_drift(
        self,
        model_id: str,
        baseline_distribution: dict[str, float],
        current_distribution: dict[str, float],
        threshold: float = 0.15,
        domain_id: str = "default",
    ) -> DriftReport:
        """Check prediction drift and record advisory drift report."""
        self.get_domain(domain_id)
        report = self.drift_detector.check_prediction_drift(
            model_id=model_id,
            baseline_distribution=baseline_distribution,
            current_distribution=current_distribution,
            threshold=threshold,
        )
        if getattr(report, "domain_id", "default") != domain_id:
            object.__setattr__(report, "domain_id", domain_id)
        self._drift_reports.append(report)

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="drift_report",
                    record_id=report.id,
                    payload={
                        "id": report.id,
                        "domain_id": domain_id,
                        "model_id": report.model_id,
                        "drift_type": report.drift_type.value if hasattr(report.drift_type, "value") else str(report.drift_type),
                        "metric_name": report.metric_name,
                        "baseline_value": report.baseline_value,
                        "current_value": report.current_value,
                        "drift_magnitude": report.drift_magnitude,
                        "drift_detected": report.drift_detected,
                        "recommendation": report.recommendation,
                        "authority": report.authority,
                    },
                )
            except Exception:
                pass

        return report

    def list_history(self, domain_id: str | None = None) -> list[AdaptiveLearningResult]:
        if domain_id:
            return [r for r in self._learning_history if getattr(r, "domain_id", "default") == domain_id]
        return list(self._learning_history)

    def list_learning_curves(self, model_id: str | None = None, domain_id: str | None = None) -> list[LearningCurvePoint]:
        results = list(self._learning_curves)
        if domain_id:
            results = [pt for pt in results if getattr(pt, "domain_id", "default") == domain_id]
        if model_id:
            results = [pt for pt in results if pt.model_id == model_id]
        return results

    def list_comparisons(self, domain_id: str | None = None) -> list[ModelComparisonRecord]:
        if domain_id:
            return [c for c in self._comparisons if getattr(c, "domain_id", "default") == domain_id]
        return list(self._comparisons)

    def list_drift_reports(self, model_id: str | None = None, domain_id: str | None = None) -> list[DriftReport]:
        results = list(self._drift_reports)
        if domain_id:
            results = [r for r in results if getattr(r, "domain_id", "default") == domain_id]
        if model_id:
            results = [r for r in results if r.model_id == model_id]
        return results

    # --- AL3 Lifecycle Audit Stream ---

    def record_lifecycle_event(self, event: ModelLifecycleEvent) -> ModelLifecycleEvent:
        """Record an immutable model lifecycle audit trail event and persist it."""
        if event.authority != "NONE":
            raise ValueError("ModelLifecycleEvent authority must strictly be 'NONE'")

        self._lifecycle_events.append(event)

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="model_lifecycle_event",
                    record_id=event.id,
                    payload={
                        "id": event.id,
                        "domain_id": event.domain_id,
                        "event_type": event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type),
                        "model_id": event.model_id,
                        "model_version": event.model_version,
                        "previous_state": event.previous_state.value if hasattr(event.previous_state, "value") else str(event.previous_state),
                        "new_state": event.new_state.value if hasattr(event.new_state, "value") else str(event.new_state),
                        "actor_id": event.actor_id,
                        "decision_reference": event.decision_reference,
                        "payload": event.payload,
                        "authority": event.authority,
                        "timestamp": event.timestamp,
                    },
                )
            except Exception:
                pass

        return event

    def list_lifecycle_events(
        self,
        domain_id: str | None = None,
        model_id: str | None = None,
    ) -> list[ModelLifecycleEvent]:
        """List persisted model lifecycle events filtered by domain or model."""
        results = list(self._lifecycle_events)
        if domain_id:
            results = [e for e in results if e.domain_id == domain_id]
        if model_id:
            results = [e for e in results if e.model_id == model_id]
        return results

    # --- AL3 Model Rollback Governance ---

    def propose_model_rollback(
        self,
        target_model_id: str,
        target_model_version: str,
        current_active_model_id: str | None = None,
        reason: str = "",
        risk_assessment: dict[str, Any] | None = None,
        factual_comparison: dict[str, Any] | None = None,
        drift_context: dict[str, Any] | None = None,
        domain_id: str = "default",
        task_type: TaskType = TaskType.CLASSIFICATION,
        model_role: str = "primary",
    ) -> ModelRollbackProposal:
        """Create an advisory rollback proposal to return to a previous valid model version.

        CRITICAL ARCHITECTURAL GUARANTEE:
        Authority is strictly NONE. Cognitia NEVER executes rollbacks autonomously.
        """
        self.get_domain(domain_id)

        # Look up current active model in the scope
        active_rec = self.model_registry.get_active(
            model_id=current_active_model_id,
            domain_id=domain_id,
            task_type=task_type.value if hasattr(task_type, "value") else str(task_type),
            model_role=model_role,
        )

        curr_id = active_rec.model_id if active_rec else (current_active_model_id or "unknown")
        curr_ver = active_rec.model_version if active_rec else "unknown"

        # Verify target model exists in registry
        target_rec = self.model_registry.get(target_model_id, target_model_version, domain_id=domain_id)
        if not target_rec:
            raise AdaptiveLearningFailure(
                f"Target rollback model '{target_model_id}' version '{target_model_version}' not found in domain '{domain_id}'",
                model_id=target_model_id,
                domain_id=domain_id,
                error_code="MODEL_NOT_FOUND",
            )

        proposal = ModelRollbackProposal(
            domain_id=domain_id,
            task_type=task_type,
            model_role=model_role,
            current_active_model_id=curr_id,
            current_active_model_version=curr_ver,
            target_model_id=target_model_id,
            target_model_version=target_model_version,
            reason=reason or f"Rollback requested from {curr_id}:{curr_ver} to {target_model_id}:{target_model_version}",
            risk_assessment=risk_assessment or {"risk_level": "LOW", "regression_risk": "CONTROLLED"},
            factual_comparison=factual_comparison or {},
            drift_context=drift_context or {},
            authority="NONE",
            provenance=ProvenanceRecord(
                source_type=SourceType.ML_MODEL,
                producer_id=f"rollback_proposal:{domain_id}:{target_model_id}",
                capability_id="governance.rollback",
                is_deterministic=True,
            ),
        )

        self._rollback_proposals[proposal.id] = proposal

        # Emit ROLLBACK_PROPOSED lifecycle event
        event = ModelLifecycleEvent(
            domain_id=domain_id,
            event_type=LifecycleEventType.ROLLBACK_PROPOSED,
            model_id=target_model_id,
            model_version=target_model_version,
            payload={
                "proposal_id": proposal.id,
                "current_active_id": curr_id,
                "current_active_version": curr_ver,
                "target_id": target_model_id,
                "target_version": target_model_version,
                "reason": proposal.reason,
            },
            authority="NONE",
        )
        self.record_lifecycle_event(event)

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="model_rollback_proposal",
                    record_id=proposal.id,
                    payload={
                        "id": proposal.id,
                        "domain_id": proposal.domain_id,
                        "current_active_model_id": proposal.current_active_model_id,
                        "current_active_model_version": proposal.current_active_model_version,
                        "target_model_id": proposal.target_model_id,
                        "target_model_version": proposal.target_model_version,
                        "reason": proposal.reason,
                        "risk_assessment": proposal.risk_assessment,
                        "factual_comparison": proposal.factual_comparison,
                        "authority": proposal.authority,
                    },
                )
            except Exception:
                pass

        return proposal

    def record_rollback_decision(
        self,
        proposal_id: str,
        approved: bool,
        decider_id: str,
        rationale: str = "",
        decider_authority: str = "domain_governance_board",
        metadata: dict[str, Any] | None = None,
    ) -> ModelRollbackDecision:
        """Record an external authority governance decision regarding a rollback proposal.

        CRITICAL ARCHITECTURAL GUARANTEE:
        Cognitia records the audit trail; Cognitia DOES NOT execute the rollback.
        Rollback execution must occur on the host/domain, and then be observed via record_activation_observation.
        """
        proposal = self._rollback_proposals.get(proposal_id)
        domain_id = proposal.domain_id if proposal else "default"
        target_id = proposal.target_model_id if proposal else "unknown"
        target_ver = proposal.target_model_version if proposal else "unknown"
        curr_id = proposal.current_active_model_id if proposal else "unknown"
        curr_ver = proposal.current_active_model_version if proposal else "unknown"

        decision_rec = ModelRollbackDecision(
            proposal_id=proposal_id,
            domain_id=domain_id,
            current_active_model_id=curr_id,
            current_active_model_version=curr_ver,
            target_model_id=target_id,
            target_model_version=target_ver,
            approved=approved,
            decider_id=decider_id,
            decision_source="EXTERNAL",
            decider_authority=decider_authority,
            rationale=rationale,
            cognitia_authority="NONE",
            provenance=ProvenanceRecord(
                source_type=SourceType.HUMAN,
                producer_id=f"rollback_decision:{decider_id}:{proposal_id}",
                capability_id="governance.rollback_decision",
                is_deterministic=True,
            ),
            metadata=metadata or {},
        )

        self._rollback_decisions[decision_rec.id] = decision_rec

        # Emit ROLLBACK_DECIDED lifecycle event
        event = ModelLifecycleEvent(
            domain_id=domain_id,
            event_type=LifecycleEventType.ROLLBACK_DECIDED,
            model_id=target_id,
            model_version=target_ver,
            actor_id=decider_id,
            decision_reference=proposal_id,
            payload={
                "approved": approved,
                "decider_id": decider_id,
                "decider_authority": decider_authority,
                "rationale": rationale,
            },
            authority="NONE",
        )
        self.record_lifecycle_event(event)

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="model_rollback_decision",
                    record_id=decision_rec.id,
                    payload={
                        "id": decision_rec.id,
                        "proposal_id": decision_rec.proposal_id,
                        "domain_id": decision_rec.domain_id,
                        "target_model_id": decision_rec.target_model_id,
                        "target_model_version": decision_rec.target_model_version,
                        "approved": decision_rec.approved,
                        "decision_source": decision_rec.decision_source,
                        "decider_id": decision_rec.decider_id,
                        "decider_authority": decision_rec.decider_authority,
                        "rationale": decision_rec.rationale,
                        "cognitia_authority": decision_rec.cognitia_authority,
                    },
                )
            except Exception:
                pass

        return decision_rec

    def list_rollback_proposals(self, domain_id: str | None = None) -> list[ModelRollbackProposal]:
        results = list(self._rollback_proposals.values())
        if domain_id:
            results = [p for p in results if p.domain_id == domain_id]
        return results

    def list_rollback_decisions(self, proposal_id: str | None = None) -> list[ModelRollbackDecision]:
        if proposal_id:
            return [d for d in self._rollback_decisions.values() if d.proposal_id == proposal_id]
        return list(self._rollback_decisions.values())

    # --- AL3 Host/Domain Activation Observation & Reconciliation ---

    def record_activation_observation(
        self,
        observation: ModelActivationObservation,
    ) -> ModelActivationObservation:
        """Record an observed runtime activation from the host domain system.

        CRITICAL ARCHITECTURAL CONTRACT:
        1. Cognitia does not autonomously activate production models.
        2. When an external domain activates a model, Cognitia observes and reconciles its registry state.
        3. Prior active model in scope (domain_id, task_type, model_role) is transitioned to SUPERSEDED.
        4. Historical models are NEVER deleted.
        """
        self.get_domain(observation.domain_id)
        if observation.authority != "NONE":
            raise ValueError("ModelActivationObservation authority must strictly be 'NONE'")

        task_str = observation.task_type.value if hasattr(observation.task_type, "value") else str(observation.task_type)
        role_str = observation.model_role

        # Find prior active model in same scope before activating
        prior_active = self.model_registry.get_active(
            domain_id=observation.domain_id,
            task_type=task_str,
            model_role=role_str,
        )

        # Reconcile registry: activate target model in registry
        self.model_registry.set_runtime_activation(
            model_id=observation.model_id,
            version=observation.model_version,
            activation=RuntimeActivationState.ACTIVE,
            domain_id=observation.domain_id,
            task_type=task_str,
            model_role=role_str,
        )

        self._activation_observations.append(observation)

        # Emit MODEL_ACTIVATION_OBSERVED or MODEL_ROLLBACK_OBSERVED
        ev_type = (
            LifecycleEventType.MODEL_ROLLBACK_OBSERVED
            if observation.activation_type == "ROLLBACK"
            else LifecycleEventType.MODEL_ACTIVATION_OBSERVED
        )

        obs_event = ModelLifecycleEvent(
            domain_id=observation.domain_id,
            event_type=ev_type,
            model_id=observation.model_id,
            model_version=observation.model_version,
            previous_state=ModelLifecycleState.SUPERSEDED if observation.activation_type == "ROLLBACK" else ModelLifecycleState.APPROVED,
            new_state=ModelLifecycleState.ACTIVE,
            actor_id=observation.external_actor_id,
            decision_reference=observation.decision_reference_id,
            payload={
                "activation_type": observation.activation_type,
                "external_actor_id": observation.external_actor_id,
                "task_type": task_str,
                "model_role": role_str,
                "prior_active_id": prior_active.model_id if prior_active else None,
                "prior_active_version": prior_active.model_version if prior_active else None,
            },
            authority="NONE",
        )
        self.record_lifecycle_event(obs_event)

        # If prior active existed, emit MODEL_SUPERSEDED
        if prior_active and (prior_active.model_id != observation.model_id or prior_active.model_version != observation.model_version):
            sup_event = ModelLifecycleEvent(
                domain_id=observation.domain_id,
                event_type=LifecycleEventType.MODEL_SUPERSEDED,
                model_id=prior_active.model_id,
                model_version=prior_active.model_version,
                previous_state=ModelLifecycleState.ACTIVE,
                new_state=ModelLifecycleState.SUPERSEDED,
                actor_id=observation.external_actor_id,
                decision_reference=observation.decision_reference_id,
                payload={
                    "superseded_by_id": observation.model_id,
                    "superseded_by_version": observation.model_version,
                },
                authority="NONE",
            )
            self.record_lifecycle_event(sup_event)

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="model_activation_observation",
                    record_id=observation.id,
                    payload={
                        "id": observation.id,
                        "domain_id": observation.domain_id,
                        "model_id": observation.model_id,
                        "model_version": observation.model_version,
                        "task_type": task_str,
                        "model_role": role_str,
                        "activation_type": observation.activation_type,
                        "external_actor_id": observation.external_actor_id,
                        "decision_reference_id": observation.decision_reference_id,
                        "authority": observation.authority,
                    },
                )
            except Exception:
                pass

        return observation

    def list_activation_observations(self, domain_id: str | None = None) -> list[ModelActivationObservation]:
        results = list(self._activation_observations)
        if domain_id:
            results = [o for o in results if o.domain_id == domain_id]
        return results

    # --- AL3 Full Lineage Reconstruction ---

    def reconstruct_model_lineage(
        self,
        model_id: str,
        model_version: str,
        domain_id: str = "default",
    ) -> dict[str, Any]:
        """Reconstruct the complete backward lineage and provenance chain for any model.

        Chain:
        Observed Active Model
          -> Parent Model
          -> Candidate Model
          -> Learning Events
          -> Feedback Records
          -> Outcome Records
          -> Model Evaluation
          -> Promotion Proposal
          -> External Promotion Decision
          -> Activation Observation
          -> (If transferred: source domain, transfer proposal, compatibility, transfer decision)
        """
        self.get_domain(domain_id)
        model_rec = self.model_registry.get(model_id, model_version, domain_id=domain_id)

        candidate = (
            self._candidates.get(f"{domain_id}:{model_version}")
            or self._candidates.get(model_version)
            or next((c for c in self._candidates.values() if c.candidate_model_id == model_id and c.candidate_model_version == model_version and c.domain_id == domain_id), None)
        )

        parent_version = candidate.parent_model_version if candidate else "1.0.0"
        parent_id = candidate.parent_model_id if candidate else model_id

        parent_rec = self.model_registry.get(parent_id, parent_version, domain_id=domain_id)

        learning_event_ids = candidate.learning_event_ids if candidate else []
        learning_events = [self._learning_events[eid] for eid in learning_event_ids if eid in self._learning_events]

        feedback_ids = []
        for le in learning_events:
            feedback_ids.extend(le.feedback_ids)
        feedback_records = [self._feedback[fid] for fid in feedback_ids if fid in self._feedback]

        outcome_ids = [f.outcome_id for f in feedback_records if f.outcome_id]
        outcome_records = [self._outcomes[oid] for oid in outcome_ids if oid in self._outcomes]

        evals = [
            e for e in self._evaluations.values()
            if e.model_id == model_id and e.model_version == model_version and e.domain_id == domain_id
        ]

        proposals = [
            p for p in self._proposals.values()
            if p.candidate_model_id == model_id and p.candidate_model_version == model_version and p.domain_id == domain_id
        ]

        decisions = []
        for prop in proposals:
            decisions.extend([d for d in self._decisions.values() if d.proposal_id == prop.id])

        obs = [
            o for o in self._activation_observations
            if o.model_id == model_id and o.model_version == model_version and o.domain_id == domain_id
        ]

        # Transfer lineage check
        transfer_info = None
        if candidate and candidate.transfer_proposal_id:
            t_prop = self._transfer_proposals.get(candidate.transfer_proposal_id)
            t_compat = self._transfer_compatibility.get(candidate.transfer_proposal_id)
            t_dec = next((d for d in self._transfer_decisions.values() if d.proposal_id == candidate.transfer_proposal_id), None)
            transfer_info = {
                "source_domain": t_prop.source_domain if t_prop else "unknown",
                "transfer_proposal_id": candidate.transfer_proposal_id,
                "transfer_type": t_prop.transfer_type.value if t_prop and hasattr(t_prop.transfer_type, "value") else str(getattr(t_prop, "transfer_type", "")),
                "compatibility_score": t_compat.score if t_compat else None,
                "compatibility_status": t_compat.status.value if t_compat and hasattr(t_compat.status, "value") else str(getattr(t_compat, "status", "")),
                "transfer_decision": t_dec.decision if t_dec else None,
                "decider_id": t_dec.decider_id if t_dec else None,
            }

        return {
            "domain_id": domain_id,
            "model_id": model_id,
            "model_version": model_version,
            "lifecycle_state": model_rec.lifecycle_state.value if model_rec and hasattr(model_rec.lifecycle_state, "value") else "registered",
            "runtime_activation_state": model_rec.runtime_activation_state.value if model_rec and hasattr(model_rec.runtime_activation_state, "value") else "not_active",
            "parent_model": {
                "model_id": parent_id,
                "model_version": parent_version,
            } if parent_rec else None,
            "candidate": {
                "id": candidate.id,
                "parameter_fingerprint": candidate.parameter_fingerprint,
                "creation_seed": candidate.creation_seed,
            } if candidate else None,
            "learning_events_count": len(learning_events),
            "learning_event_ids": [e.id for e in learning_events],
            "feedback_count": len(feedback_records),
            "feedback_ids": [f.id for f in feedback_records],
            "outcome_count": len(outcome_records),
            "outcome_ids": [o.id for o in outcome_records],
            "evaluations_count": len(evals),
            "evaluations": [{"id": e.id, "metrics": e.metrics, "sample_count": e.sample_count} for e in evals],
            "promotion_proposals_count": len(proposals),
            "promotion_proposals": [{"id": p.id, "recommendation": p.recommendation, "metric_deltas": p.metric_deltas} for p in proposals],
            "promotion_decisions_count": len(decisions),
            "promotion_decisions": [{"id": d.id, "decision": d.decision, "decider_id": d.decider_id} for d in decisions],
            "activation_observations_count": len(obs),
            "activation_observations": [{"id": o.id, "activation_type": o.activation_type, "external_actor_id": o.external_actor_id, "observed_at": o.observed_at} for o in obs],
            "transfer_lineage": transfer_info,
            "authority": "NONE",
        }

    # --- AL3 Drift to Governance Integration ---

    def propose_drift_remediation(
        self,
        drift_report: DriftReport,
        dataset: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Convert detected drift into advisory remediation proposals.

        CRITICAL ARCHITECTURAL GUARANTEE:
        Drift detection NEVER autonomously replaces or activates a model.
        It generates factual advisory recommendations for governance review.
        """
        remediation: dict[str, Any] = {
            "domain_id": drift_report.domain_id,
            "model_id": drift_report.model_id,
            "drift_type": drift_report.drift_type.value if hasattr(drift_report.drift_type, "value") else str(drift_report.drift_type),
            "drift_magnitude": drift_report.drift_magnitude,
            "drift_detected": drift_report.drift_detected,
            "recommendation": drift_report.recommendation,
            "authority": "NONE",
        }

        if drift_report.drift_detected:
            if drift_report.drift_magnitude > 0.3:
                remediation["governance_action"] = "RECOMMEND_DOMAIN_FREEZE"
                remediation["freeze_proposal"] = {
                    "mode": DomainFreezeMode.FROZEN.value,
                    "reason": f"Severe {drift_report.drift_type.value} drift magnitude ({drift_report.drift_magnitude}) exceeds safe operating threshold",
                }
            else:
                remediation["governance_action"] = "PROPOSE_MODEL_REEVALUATION"
                remediation["reevaluation_proposal"] = {
                    "reason": f"Moderate {drift_report.drift_type.value} drift ({drift_report.drift_magnitude}); re-evaluation and candidate retraining recommended",
                }
        else:
            remediation["governance_action"] = "MONITORING_NORMAL"

        return remediation
