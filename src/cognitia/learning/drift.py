"""Drift Detection Contract and Baseline Implementations.

Defines the contract and reference algorithms for monitoring:
- Input data drift
- Prediction distribution drift
- Performance degradation drift
- Confidence calibration drift
"""

from __future__ import annotations

import math
from typing import Any, Protocol, runtime_checkable

from cognitia.abi.types import current_utc_timestamp
from cognitia.learning.contract import DriftReport, DriftType


@runtime_checkable
class DriftDetector(Protocol):
    """Protocol for detecting data, prediction, or performance drift."""

    def check_prediction_drift(
        self,
        model_id: str,
        baseline_distribution: dict[str, float],
        current_distribution: dict[str, float],
        threshold: float = 0.15,
    ) -> DriftReport: ...

    def check_performance_drift(
        self,
        model_id: str,
        baseline_metric: float,
        current_metric: float,
        metric_name: str = "accuracy",
        threshold: float = 0.10,
    ) -> DriftReport: ...


class StatisticalDriftDetector(DriftDetector):
    """Reference statistical drift detector using Population Stability Index (PSI) & metric delta."""

    @classmethod
    def calculate_psi(
        cls,
        baseline: dict[str, float],
        current: dict[str, float],
        epsilon: float = 1e-4,
    ) -> float:
        """Calculate Population Stability Index (PSI) between two discrete distributions."""
        all_keys = set(baseline.keys()) | set(current.keys())
        psi = 0.0

        for k in all_keys:
            b_val = max(baseline.get(k, 0.0), epsilon)
            c_val = max(current.get(k, 0.0), epsilon)
            psi += (c_val - b_val) * math.log(c_val / b_val)

        return round(psi, 4)

    def check_prediction_drift(
        self,
        model_id: str,
        baseline_distribution: dict[str, float],
        current_distribution: dict[str, float],
        threshold: float = 0.15,
    ) -> DriftReport:
        """Check if output prediction distribution has drifted significantly from baseline."""
        psi = self.calculate_psi(baseline_distribution, current_distribution)
        drift_detected = psi >= threshold

        rec = (
            f"Advisory: Prediction drift detected (PSI={psi:.4f} >= {threshold:.4f}). Recommend review."
            if drift_detected
            else f"Prediction distribution stable (PSI={psi:.4f} < {threshold:.4f})."
        )

        return DriftReport(
            model_id=model_id,
            drift_type=DriftType.PREDICTION,
            metric_name="psi",
            baseline_value=0.0,
            current_value=psi,
            drift_magnitude=psi,
            drift_detected=drift_detected,
            recommendation=rec,
            authority="NONE",
            timestamp=current_utc_timestamp(),
        )

    def check_performance_drift(
        self,
        model_id: str,
        baseline_metric: float,
        current_metric: float,
        metric_name: str = "accuracy",
        threshold: float = 0.10,
    ) -> DriftReport:
        """Check if model accuracy or F1 has degraded beyond allowable threshold."""
        delta = baseline_metric - current_metric
        drift_detected = delta >= threshold

        rec = (
            f"Advisory: Performance degraded on {metric_name} by {delta:.4f} (>= {threshold:.4f}). Recommend recalibration."
            if drift_detected
            else f"Performance stable on {metric_name} (delta={delta:.4f} < {threshold:.4f})."
        )

        return DriftReport(
            model_id=model_id,
            drift_type=DriftType.PERFORMANCE,
            metric_name=metric_name,
            baseline_value=round(baseline_metric, 4),
            current_value=round(current_metric, 4),
            drift_magnitude=round(max(0.0, delta), 4),
            drift_detected=drift_detected,
            recommendation=rec,
            authority="NONE",
            timestamp=current_utc_timestamp(),
        )
