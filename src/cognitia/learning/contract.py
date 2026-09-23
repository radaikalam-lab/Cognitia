"""Cognitia Adaptive Learning Layer Contracts.

Defines the core provider abstraction, task types, inference request/result
schemas, representation boundary, evaluation structures, drift detection contracts,
and provenance rules for adaptive machine learning providers.

Fundamental Architectural Invariants:
1. Epistemic Novelty != Production Authority (authority is always NONE).
2. Adaptive Learning != Epistemic Truth (output is an advisory AdaptiveLearningResult, not Evidence).
3. Frozen Epistemic Semantics (E0.5-E10) are preserved without modification.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from cognitia.abi.types import CognitiveObject, current_utc_timestamp
from cognitia.models.registry import ModelRecord
from cognitia.provenance.record import ProvenanceRecord, SourceType


class TaskType(str, enum.Enum):
    """Supported adaptive learning task types."""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    SCORING = "scoring"
    RANKING = "ranking"
    ANOMALY_DETECTION = "anomaly_detection"
    CONFIDENCE_ESTIMATION = "confidence_estimation"
    INTERPRETATION = "interpretation"


class DriftType(str, enum.Enum):
    """Types of model or data drift monitored by the adaptive layer."""

    INPUT = "input_drift"
    PREDICTION = "prediction_drift"
    PERFORMANCE = "performance_drift"
    CONFIDENCE = "confidence_drift"


class EvaluationMetric(str, enum.Enum):
    """Standard evaluation metrics tracked across models and tasks."""

    ACCURACY = "accuracy"
    PRECISION = "precision"
    RECALL = "recall"
    F1 = "f1"
    BRIER_SCORE = "brier_score"
    CALIBRATION_ERROR = "calibration_error"
    MSE = "mse"
    MAE = "mae"
    LOG_LOSS = "log_loss"
    ROC_AUC = "roc_auc"


@dataclass(frozen=True)
class ModelInputRepresentation(CognitiveObject):
    """Sanitized representation boundary input passed to an adaptive model.
    
    Protects core Cognitia internals, ensures reproducibility, and isolates
    untrusted content.
    """

    representation_version: str = "1.0.0"
    input_type: str = "canonical_observation"
    source_reference: str = ""
    features: dict[str, Any] = field(default_factory=dict)
    sanitized_text: str = ""
    sanitized_payload: dict[str, Any] = field(default_factory=dict)
    provenance_reference: str = ""
    is_trusted: bool = False


@dataclass(frozen=True)
class AdaptiveInferenceRequest:
    """Structured request for model inference."""

    model_id: str
    model_version: str
    task: TaskType
    representation: ModelInputRepresentation
    parameters: dict[str, Any] = field(default_factory=dict)
    request_id: str = ""
    is_deterministic: bool = True
    random_seed: int = 42


@dataclass(frozen=True)
class AdaptiveLearningResult(CognitiveObject):
    """Canonical result produced by an adaptive learning model inference.
    
    Advisory only; authority is strictly NONE.
    """

    model_id: str = ""
    model_version: str = "1.0.0"
    provider_id: str = ""
    provider_version: str = "1.0.0"
    input_reference: str = ""
    representation_version: str = "1.0.0"
    task: TaskType = TaskType.CLASSIFICATION
    output: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    is_deterministic: bool = True
    epistemic_status: str = "UNRESOLVED"
    authority: str = "NONE"
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.NEURAL_MODEL,
            is_deterministic=True,
        )
    )

    def __post_init__(self) -> None:
        if self.authority != "NONE":
            raise ValueError("AdaptiveLearningResult authority must strictly be 'NONE'")


@dataclass(frozen=True)
class LearningCurvePoint(CognitiveObject):
    """Single point on a model's learning curve trajectory."""

    model_id: str = ""
    model_version: str = "1.0.0"
    provider_id: str = ""
    sample_count: int = 0
    step_or_epoch: int = 0
    metrics: dict[str, float] = field(default_factory=dict)
    timestamp: str = field(default_factory=current_utc_timestamp)
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            is_deterministic=True,
        )
    )


@dataclass(frozen=True)
class ModelComparisonRecord(CognitiveObject):
    """Side-by-side comparative evaluation of multiple candidate models."""

    task: TaskType = TaskType.CLASSIFICATION
    dataset_id: str = ""
    candidate_models: list[str] = field(default_factory=list)
    metrics_by_model: dict[str, dict[str, float]] = field(default_factory=dict)
    advisory_summary: str = ""
    timestamp: str = field(default_factory=current_utc_timestamp)
    authority: str = "NONE"
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            is_deterministic=True,
        )
    )

    def __post_init__(self) -> None:
        if self.authority != "NONE":
            raise ValueError("ModelComparisonRecord authority must strictly be 'NONE'")


@dataclass(frozen=True)
class DriftReport(CognitiveObject):
    """Advisory report detailing detected input, prediction, or performance drift."""

    model_id: str = ""
    model_version: str = "1.0.0"
    drift_type: DriftType = DriftType.PREDICTION
    metric_name: str = ""
    baseline_value: float = 0.0
    current_value: float = 0.0
    drift_magnitude: float = 0.0
    drift_detected: bool = False
    recommendation: str = ""
    authority: str = "NONE"
    timestamp: str = field(default_factory=current_utc_timestamp)

    def __post_init__(self) -> None:
        if self.authority != "NONE":
            raise ValueError("DriftReport authority must strictly be 'NONE'")


class AdaptiveLearningFailure(Exception):
    """Raised when adaptive model inference or loading fails explicitly."""

    def __init__(self, message: str, model_id: str = "", provider_id: str = "", error_code: str = "INFERENCE_ERROR") -> None:
        super().__init__(message)
        self.model_id = model_id
        self.provider_id = provider_id
        self.error_code = error_code


@runtime_checkable
class AdaptiveLearningProvider(Protocol):
    """Protocol defining the contract for all adaptive learning providers."""

    @property
    def provider_id(self) -> str: ...

    @property
    def provider_version(self) -> str: ...

    @property
    def supported_tasks(self) -> list[TaskType]: ...

    @property
    def is_deterministic(self) -> bool: ...

    def load_model(self, record: ModelRecord, model_artifact: Any = None) -> None: ...

    def infer(self, request: AdaptiveInferenceRequest) -> AdaptiveLearningResult: ...

    def evaluate(self, model_id: str, dataset: list[dict[str, Any]]) -> dict[str, float]: ...
