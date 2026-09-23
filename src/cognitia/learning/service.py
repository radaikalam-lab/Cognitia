"""Adaptive Learning Orchestration Service.

Integrates ModelRegistry, AdaptiveLearningProvider, RepresentationAdapter,
EvaluationEngine, DriftDetector, LearningReplayEngine, and FilePersistenceService
into an auditable outcome-driven adaptive learning loop with ZERO production authority.
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
    DriftReport,
    FeedbackRecord,
    LearningCurvePoint,
    LearningEvent,
    LearningUpdate,
    ModelCandidate,
    ModelComparisonRecord,
    ModelEvaluation,
    ModelPromotionProposal,
    OutcomeRecord,
    PredictionRecord,
    PromotionDecisionRecord,
    TaskType,
)
from cognitia.learning.drift import DriftDetector, StatisticalDriftDetector
from cognitia.learning.evaluation import ModelEvaluationEngine
from cognitia.learning.laya_provider import LayaProvider
from cognitia.learning.replay import LearningReplayEngine, ReplayVerificationResult
from cognitia.learning.representation import RepresentationAdapter
from cognitia.models.registry import InMemoryModelRegistry, ModelRecord, ModelRegistry, ModelStatus
from cognitia.provenance.record import ProvenanceRecord, SourceType


class AdaptiveLearningService:
    """Central service coordinating models, inference, outcomes, feedback, candidates, evaluation, and persistence."""

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

        laya = LayaProvider()
        self.register_provider(laya)

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

    def register_model(self, record: ModelRecord) -> None:
        """Register a model record with its provider and persistence."""
        self.model_registry.register(record)
        if record.provider in self._providers:
            self._providers[record.provider].load_model(record)

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="model_registered",
                    record_id=f"model:{record.model_id}:{record.model_version}",
                    payload={
                        "model_id": record.model_id,
                        "model_version": record.model_version,
                        "provider": record.provider,
                        "status": record.status.value if hasattr(record.status, "value") else str(record.status),
                        "is_deterministic": record.is_deterministic,
                        "calibration_checksum": record.calibration_checksum,
                    },
                )
            except Exception:
                pass

    def predict_from_observation(
        self,
        obs: Observation,
        model_id: str = "laya_acoustic_v1",
        provider_id: str = "laya",
        task: TaskType = TaskType.CLASSIFICATION,
        parameters: dict[str, Any] | None = None,
        is_deterministic: bool = True,
    ) -> AdaptiveLearningResult:
        """Execute inference from a canonical Observation."""
        rep = RepresentationAdapter.adapt_observation(obs)
        return self.infer(
            model_id=model_id,
            provider_id=provider_id,
            task=task,
            representation=rep,
            parameters=parameters,
            is_deterministic=is_deterministic,
        )

    def predict_from_directional_spec(
        self,
        spec: DirectionalSpecification,
        model_id: str = "laya_directional_v1",
        provider_id: str = "laya",
        task: TaskType = TaskType.INTERPRETATION,
        parameters: dict[str, Any] | None = None,
        is_deterministic: bool = True,
    ) -> AdaptiveLearningResult:
        """Execute inference / candidate generation from a DirectionalSpecification."""
        rep = RepresentationAdapter.adapt_directional_spec(spec)
        return self.infer(
            model_id=model_id,
            provider_id=provider_id,
            task=task,
            representation=rep,
            parameters=parameters,
            is_deterministic=is_deterministic,
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
    ) -> AdaptiveLearningResult:
        """Direct inference through representation boundary."""
        provider = self.get_provider(provider_id)

        req = AdaptiveInferenceRequest(
            model_id=model_id,
            model_version=model_version,
            task=task,
            representation=representation,
            parameters=parameters or {},
            is_deterministic=is_deterministic,
        )
        result = provider.infer(req)

        if result.authority != "NONE":
            raise ValueError("AdaptiveLearningResult must carry authority='NONE'")

        self._learning_history.append(result)

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="adaptive_learning_result",
                    record_id=result.id,
                    payload={
                        "id": result.id,
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

    # --- AL1 Outcome & Feedback Lifecycle ---

    def record_outcome(self, outcome: OutcomeRecord) -> OutcomeRecord:
        """Record domain-measured ground truth or operational outcome. Authority is strictly NONE."""
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
    ) -> FeedbackRecord:
        """Link a prediction to an observed outcome and calculate error/metrics."""
        # Find prediction in history
        pred_match = next((p for p in self._learning_history if p.id == prediction_id), None)
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
    ) -> tuple[ModelCandidate, LearningUpdate, LearningEvent]:
        """Trigger deterministic candidate generation from feedback events without modifying active model."""
        feedbacks = [self._feedback[fid] for fid in feedback_ids if fid in self._feedback]
        if not feedbacks:
            raise AdaptiveLearningFailure(
                f"No valid feedback records found for IDs: {feedback_ids}",
                model_id=base_model_id,
                provider_id="laya",
                error_code="INVALID_FEEDBACK",
            )

        active_rec = self.model_registry.get_active(base_model_id)
        effective_base_ver = base_model_version or (active_rec.model_version if active_rec else "1.0.0")

        base_record = ModelRecord(
            model_id=base_model_id,
            model_version=effective_base_ver,
            provider="laya",
            is_deterministic=True,
        )

        data_fingerprint_src = f"{seed}:" + "|".join(sorted(f.id for f in feedbacks))
        data_fingerprint = hashlib.sha256(data_fingerprint_src.encode("utf-8")).hexdigest()

        event_prov = ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            producer_id=f"learning_event:{base_model_id}:{effective_base_ver}",
            capability_id="learn.adaptive.event",
            is_deterministic=True,
        )

        learning_event = LearningEvent(
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

        # Store candidate and update
        self._candidates[candidate.candidate_model_version] = candidate
        self._candidates[candidate.id] = candidate
        self._learning_updates[update.id] = update

        # Register candidate in registry with CANDIDATE status (immutability guarantee: active model remains active)
        cand_model_rec = ModelRecord(
            model_id=candidate.candidate_model_id,
            model_version=candidate.candidate_model_version,
            provider=candidate.provider_id,
            status=ModelStatus.CANDIDATE,
            is_deterministic=candidate.is_deterministic,
            calibration_checksum=candidate.parameter_fingerprint,
        )
        self.model_registry.register(cand_model_rec)

        # Persist all 3 artifacts
        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="learning_event",
                    record_id=learning_event.id,
                    payload={
                        "id": learning_event.id,
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
    ) -> ModelEvaluation:
        """Evaluate a ModelCandidate on a validation dataset. Authority is strictly NONE."""
        candidate = self._candidates.get(candidate_version_or_id)
        if not candidate:
            candidate = next((c for c in self._candidates.values() if c.candidate_model_version == candidate_version_or_id or c.id == candidate_version_or_id), None)

        if not candidate:
            raise AdaptiveLearningFailure(
                f"Candidate '{candidate_version_or_id}' not found",
                model_id=model_id,
                provider_id="laya",
                error_code="CANDIDATE_NOT_FOUND",
            )

        provider = self.get_provider(candidate.provider_id)
        evaluation = provider.evaluate_candidate(candidate, dataset)
        self._evaluations[evaluation.id] = evaluation

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="model_evaluation",
                    record_id=evaluation.id,
                    payload={
                        "id": evaluation.id,
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
    ) -> ModelPromotionProposal:
        """Create an advisory promotion proposal comparing candidate against active baseline model.

        Cognitia NEVER activates or promotes models autonomously; authority is strictly NONE.
        """
        candidate = self._candidates.get(candidate_version)
        if not candidate:
            candidate = next((c for c in self._candidates.values() if c.candidate_model_version == candidate_version), None)

        if not candidate:
            raise AdaptiveLearningFailure(
                f"Candidate '{candidate_version}' not found for promotion proposal",
                model_id=model_id,
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

        self._proposals[proposal.id] = proposal

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="model_promotion_proposal",
                    record_id=proposal.id,
                    payload={
                        "id": proposal.id,
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

        Cognitia records the audit trail, but Cognitia itself has ZERO authority to activate models.
        """
        proposal = self._proposals.get(proposal_id)
        cand_id = proposal.candidate_model_id if proposal else "unknown"
        cand_ver = proposal.candidate_model_version if proposal else "unknown"

        prov = ProvenanceRecord(
            source_type=SourceType.HUMAN,
            producer_id=f"decision:{decider_id}:{proposal_id}",
            capability_id="governance.decision",
            is_deterministic=True,
        )

        decision_rec = PromotionDecisionRecord(
            proposal_id=proposal_id,
            candidate_model_id=cand_id,
            candidate_model_version=cand_ver,
            decision=decision.upper(),
            decider_id=decider_id,
            decider_authority=decider_authority,
            rationale=rationale,
            cognitia_authority="NONE",
            provenance=prov,
        )

        self._decisions[decision_rec.id] = decision_rec

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

    def replay_learning(
        self,
        candidate_version: str,
        model_id: str = "laya_acoustic_v1",
        seed: int = 42,
    ) -> ReplayVerificationResult:
        """Replay candidate generation deterministically and verify parameter parity."""
        candidate = self._candidates.get(candidate_version)
        if not candidate:
            candidate = next((c for c in self._candidates.values() if c.candidate_model_version == candidate_version), None)

        if not candidate:
            return ReplayVerificationResult(
                candidate_model_id=model_id,
                candidate_model_version=candidate_version,
                is_replayable=False,
                is_exact_match=False,
                status="NON_REPLAYABLE",
                reason=f"Candidate version '{candidate_version}' not found in registry",
                authority="NONE",
            )

        events = [self._learning_events[eid] for eid in candidate.learning_event_ids if eid in self._learning_events]
        base_record = ModelRecord(
            model_id=candidate.parent_model_id,
            model_version=candidate.parent_model_version,
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

    # --- Query Methods ---

    def list_outcomes(self) -> list[OutcomeRecord]:
        return list(self._outcomes.values())

    def list_feedback(self) -> list[FeedbackRecord]:
        return list(self._feedback.values())

    def list_learning_events(self) -> list[LearningEvent]:
        return list(self._learning_events.values())

    def list_learning_updates(self) -> list[LearningUpdate]:
        return list(self._learning_updates.values())

    def list_candidates(self, model_id: str | None = None) -> list[ModelCandidate]:
        unique = {c.candidate_model_version: c for c in self._candidates.values()}.values()
        if model_id:
            return [c for c in unique if c.candidate_model_id == model_id]
        return list(unique)

    def list_evaluations(self, model_id: str | None = None) -> list[ModelEvaluation]:
        if model_id:
            return [e for e in self._evaluations.values() if e.model_id == model_id]
        return list(self._evaluations.values())

    def list_proposals(self, model_id: str | None = None) -> list[ModelPromotionProposal]:
        if model_id:
            return [p for p in self._proposals.values() if p.candidate_model_id == model_id]
        return list(self._proposals.values())

    def list_decisions(self, proposal_id: str | None = None) -> list[PromotionDecisionRecord]:
        if proposal_id:
            return [d for d in self._decisions.values() if d.proposal_id == proposal_id]
        return list(self._decisions.values())

    def record_learning_point(
        self,
        model_id: str,
        model_version: str,
        provider_id: str,
        step: int,
        sample_count: int,
        metrics: dict[str, float],
    ) -> LearningCurvePoint:
        """Record a learning curve point and persist it."""
        pt = ModelEvaluationEngine.record_learning_curve_step(
            model_id=model_id,
            model_version=model_version,
            provider_id=provider_id,
            step=step,
            sample_count=sample_count,
            metrics=metrics,
        )
        self._learning_curves.append(pt)

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="learning_curve_point",
                    record_id=pt.id,
                    payload={
                        "id": pt.id,
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
    ) -> ModelComparisonRecord:
        """Run model competition on dataset and record comparison."""
        provider = self.get_provider(provider_id)
        comp = ModelEvaluationEngine.compare_models(
            provider=provider,
            candidate_models=candidate_models,
            dataset=dataset,
            dataset_id=dataset_id,
            task=task,
        )
        self._comparisons.append(comp)

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="model_comparison",
                    record_id=comp.id,
                    payload={
                        "id": comp.id,
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
    ) -> DriftReport:
        """Check prediction drift and record advisory drift report."""
        report = self.drift_detector.check_prediction_drift(
            model_id=model_id,
            baseline_distribution=baseline_distribution,
            current_distribution=current_distribution,
            threshold=threshold,
        )
        self._drift_reports.append(report)

        if self.persistence_service and hasattr(self.persistence_service, "append_record"):
            try:
                self.persistence_service.append_record(
                    record_type="drift_report",
                    record_id=report.id,
                    payload={
                        "id": report.id,
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

    def list_history(self) -> list[AdaptiveLearningResult]:
        return list(self._learning_history)

    def list_learning_curves(self, model_id: str | None = None) -> list[LearningCurvePoint]:
        if model_id:
            return [pt for pt in self._learning_curves if pt.model_id == model_id]
        return list(self._learning_curves)

    def list_comparisons(self) -> list[ModelComparisonRecord]:
        return list(self._comparisons)

    def list_drift_reports(self, model_id: str | None = None) -> list[DriftReport]:
        if model_id:
            return [r for r in self._drift_reports if r.model_id == model_id]
        return list(self._drift_reports)
