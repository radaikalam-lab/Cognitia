"""Tests for Model Evaluation Engine and Multi-Model Competition."""

from cognitia.learning.contract import TaskType
from cognitia.learning.evaluation import ModelEvaluationEngine
from cognitia.learning.laya_provider import LayaProvider
from cognitia.learning.representation import RepresentationAdapter


def test_classification_metrics_calculation():
    """Verify precision, recall, f1, and brier score calculation."""
    preds = ["resonance", "resonance", "noise", "harmonic"]
    actuals = ["resonance", "noise", "noise", "harmonic"]
    probs = [0.9, 0.8, 0.7, 0.95]

    metrics = ModelEvaluationEngine.compute_classification_metrics(preds, actuals, probs)

    assert metrics["accuracy"] == 0.75
    assert metrics["f1"] > 0.0
    assert "brier_score" in metrics


def test_learning_curve_recording():
    """Verify learning curve trajectory point recording."""
    pt = ModelEvaluationEngine.record_learning_curve_step(
        model_id="laya_acoustic_v1",
        model_version="1.0.0",
        provider_id="laya",
        step=5,
        sample_count=500,
        metrics={"accuracy": 0.88, "f1": 0.86},
    )

    assert pt.model_id == "laya_acoustic_v1"
    assert pt.step_or_epoch == 5
    assert pt.sample_count == 500
    assert pt.metrics["accuracy"] == 0.88


def test_model_competition_advisory():
    """Verify multi-model competition comparison produces advisory records with ZERO authority."""
    provider = LayaProvider(is_deterministic=True)
    dataset = [
        {
            "representation": RepresentationAdapter.adapt_raw({"spl_db": 95.0, "frequency_hz": 440.0}),
            "expected": "resonance",
        },
        {
            "representation": RepresentationAdapter.adapt_raw({"spl_db": 20.0, "frequency_hz": 120.0}),
            "expected": "noise",
        },
    ]

    comp = ModelEvaluationEngine.compare_models(
        provider=provider,
        candidate_models=[("laya_acoustic_v1", "1.0.0"), ("laya_acoustic_v2", "2.0.0")],
        dataset=dataset,
        dataset_id="benchmark_suite_a",
    )

    assert comp.authority == "NONE"
    assert len(comp.candidate_models) == 2
    assert "laya_acoustic_v1:1.0.0" in comp.metrics_by_model
    assert "laya_acoustic_v2:2.0.0" in comp.metrics_by_model
    assert "Model Comparison" in comp.advisory_summary
