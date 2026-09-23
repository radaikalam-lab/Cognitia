"""Tests for Statistical Drift Detection."""

from cognitia.learning.contract import DriftType
from cognitia.learning.drift import StatisticalDriftDetector


def test_psi_and_prediction_drift():
    """Verify Population Stability Index (PSI) and prediction drift detection."""
    detector = StatisticalDriftDetector()

    baseline = {"resonance": 0.70, "harmonic": 0.20, "noise": 0.10}
    current_stable = {"resonance": 0.68, "harmonic": 0.22, "noise": 0.10}
    current_drifted = {"resonance": 0.10, "harmonic": 0.10, "noise": 0.80}

    rep_stable = detector.check_prediction_drift("laya_acoustic_v1", baseline, current_stable, threshold=0.15)
    assert rep_stable.drift_detected is False
    assert rep_stable.authority == "NONE"

    rep_drifted = detector.check_prediction_drift("laya_acoustic_v1", baseline, current_drifted, threshold=0.15)
    assert rep_drifted.drift_detected is True
    assert rep_drifted.drift_type == DriftType.PREDICTION
    assert "Prediction drift detected" in rep_drifted.recommendation


def test_performance_degradation_drift():
    """Verify performance metric degradation alert."""
    detector = StatisticalDriftDetector()

    report = detector.check_performance_drift(
        model_id="laya_acoustic_v1",
        baseline_metric=0.92,
        current_metric=0.75,
        metric_name="accuracy",
        threshold=0.10,
    )

    assert report.drift_detected is True
    assert report.drift_type == DriftType.PERFORMANCE
    assert report.drift_magnitude == 0.17
    assert report.authority == "NONE"
