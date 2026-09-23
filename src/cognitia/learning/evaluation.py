"""Model Evaluation and Competition Engine.

Provides standard statistical metrics, calibration measurement, learning curve
generation, multi-model comparison, and candidate promotion proposals without
autonomous model promotion or activation.
"""

from __future__ import annotations

import math
from typing import Any

from cognitia.abi.types import current_utc_timestamp
from cognitia.learning.contract import (
    AdaptiveInferenceRequest,
    AdaptiveLearningProvider,
    CandidateStatus,
    EvaluationMetric,
    LearningCurvePoint,
    ModelCandidate,
    ModelComparisonRecord,
    ModelPromotionProposal,
    TaskType,
)
from cognitia.provenance.record import ProvenanceRecord, SourceType


class ModelEvaluationEngine:
    """Engine for assessing model performance, learning curves, and multi-model competition."""

    @classmethod
    def compute_classification_metrics(
        cls,
        predictions: list[str],
        actuals: list[str],
        probabilities: list[float] | None = None,
    ) -> dict[str, float]:
        """Compute standard classification metrics: accuracy, precision, recall, f1, brier score."""
        if not predictions or len(predictions) != len(actuals):
            return {
                EvaluationMetric.ACCURACY.value: 0.0,
                EvaluationMetric.F1.value: 0.0,
                EvaluationMetric.BRIER_SCORE.value: 0.0,
            }

        total = len(predictions)
        correct = sum(1 for p, a in zip(predictions, actuals) if p == a)
        accuracy = correct / total

        classes = sorted(list(set(actuals) | set(predictions)))
        precisions = []
        recalls = []

        for c in classes:
            tp = sum(1 for p, a in zip(predictions, actuals) if p == c and a == c)
            fp = sum(1 for p, a in zip(predictions, actuals) if p == c and a != c)
            fn = sum(1 for p, a in zip(predictions, actuals) if p != c and a == c)

            p_c = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            r_c = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            precisions.append(p_c)
            recalls.append(r_c)

        macro_precision = sum(precisions) / len(precisions) if precisions else 0.0
        macro_recall = sum(recalls) / len(recalls) if recalls else 0.0
        f1 = (
            2 * (macro_precision * macro_recall) / (macro_precision + macro_recall)
            if (macro_precision + macro_recall) > 0
            else 0.0
        )

        brier_score = 0.0
        if probabilities and len(probabilities) == total:
            brier_score = sum(
                (1.0 - prob) ** 2 if p == a else prob ** 2
                for p, a, prob in zip(predictions, actuals, probabilities)
            ) / total

        return {
            EvaluationMetric.ACCURACY.value: round(accuracy, 4),
            EvaluationMetric.PRECISION.value: round(macro_precision, 4),
            EvaluationMetric.RECALL.value: round(macro_recall, 4),
            EvaluationMetric.F1.value: round(f1, 4),
            EvaluationMetric.BRIER_SCORE.value: round(brier_score, 4),
        }

    @classmethod
    def evaluate_model_on_dataset(
        cls,
        provider: AdaptiveLearningProvider,
        model_id: str,
        model_version: str,
        dataset: list[dict[str, Any]],
        task: TaskType = TaskType.CLASSIFICATION,
    ) -> dict[str, float]:
        """Evaluate a single model on an evaluation dataset."""
        preds = []
        actuals = []
        probs = []

        for item in dataset:
            rep = item.get("representation")
            exp = item.get("expected") if item.get("expected") is not None else item.get("expected_label")
            if not rep or exp is None:
                continue

            req = AdaptiveInferenceRequest(
                model_id=model_id,
                model_version=model_version,
                task=task,
                representation=rep,
                is_deterministic=True,
            )
            res = provider.infer(req)
            if task == TaskType.CLASSIFICATION:
                pred_label = str(res.output.get("decision", ""))
                scores = res.output.get("scores", {})
                prob = float(scores.get(str(exp), res.confidence))
                preds.append(pred_label)
                actuals.append(str(exp))
                probs.append(prob)

        metrics = cls.compute_classification_metrics(preds, actuals, probs)
        metrics["sample_count"] = float(len(preds))
        return metrics

    @classmethod
    def record_learning_curve_step(
        cls,
        model_id: str,
        model_version: str,
        provider_id: str,
        step: int,
        sample_count: int,
        metrics: dict[str, float],
    ) -> LearningCurvePoint:
        """Create a durable LearningCurvePoint record."""
        return LearningCurvePoint(
            model_id=model_id,
            model_version=model_version,
            provider_id=provider_id,
            step_or_epoch=step,
            sample_count=sample_count,
            metrics=metrics,
            timestamp=current_utc_timestamp(),
            provenance=ProvenanceRecord(
                source_type=SourceType.ML_MODEL,
                producer_id=f"eval_engine:{model_id}",
                is_deterministic=True,
            ),
        )

    @classmethod
    def compare_models(
        cls,
        provider: AdaptiveLearningProvider,
        candidate_models: list[tuple[str, str]],
        dataset: list[dict[str, Any]],
        dataset_id: str = "eval_dataset_v1",
        task: TaskType = TaskType.CLASSIFICATION,
    ) -> ModelComparisonRecord:
        """Compare multiple candidate models side-by-side on the same evaluation dataset.

        Advisory only; does NOT autonomously promote or activate models.
        """
        metrics_by_model: dict[str, dict[str, float]] = {}

        for m_id, m_ver in candidate_models:
            key = f"{m_id}:{m_ver}"
            m_metrics = cls.evaluate_model_on_dataset(
                provider=provider,
                model_id=m_id,
                model_version=m_ver,
                dataset=dataset,
                task=task,
            )
            metrics_by_model[key] = m_metrics

        summary_parts = []
        for k, v in metrics_by_model.items():
            acc = v.get(EvaluationMetric.ACCURACY.value, 0.0)
            f1 = v.get(EvaluationMetric.F1.value, 0.0)
            summary_parts.append(f"{k} -> Acc: {acc:.2f}, F1: {f1:.2f}")

        advisory_summary = "Model Comparison: " + "; ".join(summary_parts)

        return ModelComparisonRecord(
            task=task,
            dataset_id=dataset_id,
            candidate_models=[f"{m}:{v}" for m, v in candidate_models],
            metrics_by_model=metrics_by_model,
            advisory_summary=advisory_summary,
            timestamp=current_utc_timestamp(),
            authority="NONE",
            provenance=ProvenanceRecord(
                source_type=SourceType.ML_MODEL,
                producer_id="eval_engine:comparison",
                is_deterministic=True,
            ),
        )

    @classmethod
    def evaluate_candidate_vs_baseline(
        cls,
        provider: AdaptiveLearningProvider,
        candidate: ModelCandidate,
        baseline_model_id: str,
        baseline_model_version: str,
        dataset: list[dict[str, Any]],
        dataset_id: str = "eval_dataset_v1",
        drift_context: dict[str, Any] | None = None,
        task: TaskType = TaskType.CLASSIFICATION,
    ) -> ModelPromotionProposal:
        """Evaluate a ModelCandidate against its parent/baseline model and generate an advisory promotion proposal.

        Authority is strictly NONE. Activation remains an external governance decision.
        """
        baseline_metrics = cls.evaluate_model_on_dataset(
            provider=provider,
            model_id=baseline_model_id,
            model_version=baseline_model_version,
            dataset=dataset,
            task=task,
        )

        candidate_metrics = cls.evaluate_model_on_dataset(
            provider=provider,
            model_id=candidate.candidate_model_id,
            model_version=candidate.candidate_model_version,
            dataset=dataset,
            task=task,
        )

        metric_deltas: dict[str, float] = {}
        for k in set(baseline_metrics.keys()) | set(candidate_metrics.keys()):
            b_val = baseline_metrics.get(k, 0.0)
            c_val = candidate_metrics.get(k, 0.0)
            metric_deltas[f"{k}_delta"] = round(c_val - b_val, 4)

        acc_delta = metric_deltas.get(f"{EvaluationMetric.ACCURACY.value}_delta", 0.0)
        f1_delta = metric_deltas.get(f"{EvaluationMetric.F1.value}_delta", 0.0)
        brier_delta = metric_deltas.get(f"{EvaluationMetric.BRIER_SCORE.value}_delta", 0.0)

        rationale = (
            f"Candidate {candidate.candidate_model_id}:{candidate.candidate_model_version} evaluated vs "
            f"baseline {baseline_model_id}:{baseline_model_version}. "
            f"Accuracy delta: {acc_delta:+.4f}, F1 delta: {f1_delta:+.4f}, Brier delta: {brier_delta:+.4f}."
        )

        prov = ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            producer_id=f"eval_engine:proposal:{candidate.candidate_model_id}:{candidate.candidate_model_version}",
            capability_id="learn.adaptive.proposal",
            is_deterministic=True,
        )

        return ModelPromotionProposal(
            parent_model_id=baseline_model_id,
            parent_model_version=baseline_model_version,
            candidate_model_id=candidate.candidate_model_id,
            candidate_model_version=candidate.candidate_model_version,
            provider_id=candidate.provider_id,
            dataset_id=dataset_id,
            baseline_metrics=baseline_metrics,
            candidate_metrics=candidate_metrics,
            metric_deltas=metric_deltas,
            drift_context=drift_context or {},
            rationale=rationale,
            recommendation="PROPOSE_CANDIDATE" if acc_delta >= 0.0 else "DEFER_CANDIDATE",
            status=CandidateStatus.PROPOSED,
            authority="NONE",
            provenance=prov,
        )
