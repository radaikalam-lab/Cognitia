"""Adaptive Learning Orchestration Service.

Integrates ModelRegistry, AdaptiveLearningProvider, RepresentationAdapter,
EvaluationEngine, DriftDetector, and FilePersistenceService into an auditable
adaptive learning loop with ZERO production authority.
"""

from __future__ import annotations

from typing import Any

from cognitia.abi.types import Observation
from cognitia.directional.types import DirectionalSpecification
from cognitia.epistemic.types import Evidence
from cognitia.learning.contract import (
    AdaptiveInferenceRequest,
    AdaptiveLearningFailure,
    AdaptiveLearningProvider,
    AdaptiveLearningResult,
    DriftReport,
    LearningCurvePoint,
    ModelComparisonRecord,
    TaskType,
)
from cognitia.learning.drift import DriftDetector, StatisticalDriftDetector
from cognitia.learning.evaluation import ModelEvaluationEngine
from cognitia.learning.laya_provider import LayaProvider
from cognitia.learning.representation import RepresentationAdapter
from cognitia.models.registry import InMemoryModelRegistry, ModelRecord, ModelRegistry, ModelStatus


class AdaptiveLearningService:
    """Central service coordinating models, inference, evaluation, and persistence."""

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
    ) -> AdaptiveLearningResult:
        """Direct inference through representation boundary."""
        provider = self.get_provider(provider_id)
        
        req = AdaptiveInferenceRequest(
            model_id=model_id,
            model_version="1.0.0",
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
