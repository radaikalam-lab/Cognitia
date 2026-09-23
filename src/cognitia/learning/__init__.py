"""Cognitia Adaptive Learning Layer (AL0).

Decoupled machine learning provider subsystem providing typed-decision learning,
model evaluation, learning history, drift detection, and advisory outputs with
ZERO production authority.
"""

from cognitia.learning.contract import (
    AdaptiveInferenceRequest,
    AdaptiveLearningFailure,
    AdaptiveLearningProvider,
    AdaptiveLearningResult,
    DriftReport,
    DriftType,
    EvaluationMetric,
    LearningCurvePoint,
    ModelComparisonRecord,
    ModelInputRepresentation,
    TaskType,
)
from cognitia.learning.drift import DriftDetector, StatisticalDriftDetector
from cognitia.learning.evaluation import ModelEvaluationEngine
from cognitia.learning.laya_provider import LayaProvider
from cognitia.learning.representation import RepresentationAdapter
from cognitia.learning.service import AdaptiveLearningService

__all__ = [
    "AdaptiveInferenceRequest",
    "AdaptiveLearningFailure",
    "AdaptiveLearningProvider",
    "AdaptiveLearningResult",
    "AdaptiveLearningService",
    "DriftDetector",
    "DriftReport",
    "DriftType",
    "EvaluationMetric",
    "LayaProvider",
    "LearningCurvePoint",
    "ModelComparisonRecord",
    "ModelEvaluationEngine",
    "ModelInputRepresentation",
    "RepresentationAdapter",
    "StatisticalDriftDetector",
    "TaskType",
]
