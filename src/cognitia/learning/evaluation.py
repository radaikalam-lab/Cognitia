"""Model Evaluation and Competition Engine.

Provides standard statistical metrics, calibration measurement, learning curve
generation, and multi-model comparison without autonomous model promotion.
"""

from __future__ import annotations

import math
from typing import Any

from cognitia.abi.types import current_utc_timestamp
from cognitia.learning.contract import (
    AdaptiveInferenceRequest,
    AdaptiveLearningProvider,
    EvaluationMetric,
    LearningCurvePoint,
    ModelComparisonRecord,
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
            exp = item.get("expected")
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
