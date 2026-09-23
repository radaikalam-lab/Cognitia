"""Cognitia Adaptive Learning Layer (AL1 & AL2).

Decoupled machine learning provider subsystem providing typed-decision learning,
outcome-based learning, feedback loops, candidate models, evaluation, promotion proposals,
drift detection, deterministic replay, domain-scoped learning, knowledge isolation,
and explicit advisory transfer proposals with ZERO production authority.
"""

from cognitia.learning.contract import (
    AdaptiveInferenceRequest,
    AdaptiveLearningFailure,
    AdaptiveLearningProvider,
    AdaptiveLearningResult,
    CandidateStatus,
    DriftReport,
    DriftType,
    EvaluationMetric,
    FeedbackRecord,
    KnowledgeType,
    LearningCurvePoint,
    LearningDomain,
    LearningEvent,
    LearningTransferProposal,
    LearningUpdate,
    ModelCandidate,
    ModelComparisonRecord,
    ModelEvaluation,
    ModelInputRepresentation,
    ModelPromotionProposal,
    OutcomeRecord,
    PredictionRecord,
    PromotionDecisionRecord,
    TaskType,
    TransferCompatibilityResult,
    TransferCompatibilityStatus,
    TransferDecisionRecord,
    TransferType,
)
from cognitia.learning.drift import DriftDetector, StatisticalDriftDetector
from cognitia.learning.evaluation import ModelEvaluationEngine
from cognitia.learning.laya_provider import LayaProvider
from cognitia.learning.replay import LearningReplayEngine, ReplayVerificationResult
from cognitia.learning.representation import RepresentationAdapter
from cognitia.learning.service import AdaptiveLearningService
from cognitia.learning.transfer import LearningTransferEngine

__all__ = [
    "AdaptiveInferenceRequest",
    "AdaptiveLearningFailure",
    "AdaptiveLearningProvider",
    "AdaptiveLearningResult",
    "AdaptiveLearningService",
    "CandidateStatus",
    "DriftDetector",
    "DriftReport",
    "DriftType",
    "EvaluationMetric",
    "FeedbackRecord",
    "KnowledgeType",
    "LayaProvider",
    "LearningCurvePoint",
    "LearningDomain",
    "LearningEvent",
    "LearningReplayEngine",
    "LearningTransferEngine",
    "LearningTransferProposal",
    "LearningUpdate",
    "ModelCandidate",
    "ModelComparisonRecord",
    "ModelEvaluation",
    "ModelEvaluationEngine",
    "ModelInputRepresentation",
    "ModelPromotionProposal",
    "OutcomeRecord",
    "PredictionRecord",
    "PromotionDecisionRecord",
    "ReplayVerificationResult",
    "RepresentationAdapter",
    "StatisticalDriftDetector",
    "TaskType",
    "TransferCompatibilityResult",
    "TransferCompatibilityStatus",
    "TransferDecisionRecord",
    "TransferType",
]
