"""Cognitia Adaptive Learning Layer Contracts.

Defines the core provider abstraction, task types, inference request/result
schemas, representation boundary, evaluation structures, drift detection contracts,
AL1 outcome/feedback lifecycle, model candidates, AL2 domain scopes,
and controlled knowledge transfer proposals.

Fundamental Architectural Invariants:
1. Epistemic Novelty != Production Authority (authority is always NONE).
2. Adaptive Learning != Epistemic Truth (output is an advisory AdaptiveLearningResult/Candidate, not Evidence).
3. Frozen Epistemic Semantics (E0.5-E10) are preserved without modification.
4. Active model immutability: Learning generates ModelCandidate proposals, never overwriting active models.
5. Domain isolation: Learning within a domain is isolated; cross-domain knowledge transfer must be explicit and advisory.
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


class CandidateStatus(str, enum.Enum):
    """Lifecycle status of candidate model proposals."""

    CANDIDATE = "candidate"
    EVALUATED = "evaluated"
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEFERRED = "deferred"


# --- AL2 Domain & Knowledge Transfer Enums ---

class TransferType(str, enum.Enum):
    """Types of cross-domain knowledge transfer."""

    PARAMETER_TRANSFER = "parameter_transfer"
    REPRESENTATION_TRANSFER = "representation_transfer"
    STATISTICAL_PRIOR = "statistical_prior"
    HEURISTIC_TRANSFER = "heuristic_transfer"
    FEATURE_EXTRACTOR_TRANSFER = "feature_extractor_transfer"
    MODEL_TRANSFER = "model_transfer"
    WEIGHT_INITIALIZATION = "weight_initialization"


class TransferCompatibilityStatus(str, enum.Enum):
    """Status of cross-domain compatibility evaluation."""

    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    PARTIALLY_COMPATIBLE = "partially_compatible"
    UNKNOWN = "unknown"


class KnowledgeType(str, enum.Enum):
    """Categorization of learned knowledge artifacts eligible for transfer analysis."""

    MODEL_CANDIDATE = "model_candidate"
    MODEL_PARAMETERS = "model_parameters"
    STATISTICAL_SUMMARY = "statistical_summary"
    DRIFT_OBSERVATION = "drift_observation"
    REPRESENTATION_SCHEMA = "representation_schema"
    FEATURE_EXTRACTOR = "feature_extractor"
    MODEL_WEIGHTS = "model_weights"
    FULL_MODEL = "full_model"



@dataclass(frozen=True)
class LearningDomain(CognitiveObject):
    """Bounded semantic context defining the scope of adaptive learning.

    LearningDomain represents scope and metadata, not execution authority.
    """

    domain_id: str = "default"
    domain_version: str = "1.0.0"
    description: str = ""
    representation_version: str = "1.0.0"
    declared_providers: list[str] = field(default_factory=lambda: ["laya"])
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelInputRepresentation(CognitiveObject):
    """Sanitized representation boundary input passed to an adaptive model.

    Protects core Cognitia internals, ensures reproducibility, and isolates
    untrusted content.
    """

    domain_id: str = "default"
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
    domain_id: str = "default"
    parameters: dict[str, Any] = field(default_factory=dict)
    request_id: str = ""
    is_deterministic: bool = True
    random_seed: int = 42


@dataclass(frozen=True)
class AdaptiveLearningResult(CognitiveObject):
    """Canonical result produced by an adaptive learning model inference.

    Advisory only; authority is strictly NONE.
    """

    domain_id: str = "default"
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


# Alias for explicit AL1 PredictionRecord semantics
PredictionRecord = AdaptiveLearningResult


@dataclass(frozen=True)
class OutcomeRecord(CognitiveObject):
    """Measured ground truth or actual state from domain/host observation.

    Advisory only; authority is strictly NONE.
    """

    domain_id: str = "default"
    source_id: str = ""
    target_prediction_id: str = ""
    observation_id: str = ""
    actual_values: dict[str, Any] = field(default_factory=dict)
    is_ground_truth: bool = True
    authority: str = "NONE"
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.SENSOR,
            is_deterministic=True,
        )
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.authority != "NONE":
            raise ValueError("OutcomeRecord authority must strictly be 'NONE'")


@dataclass(frozen=True)
class FeedbackRecord(CognitiveObject):
    """Structured feedback linking a prediction to an observed outcome.

    Advisory only; authority is strictly NONE.
    """

    domain_id: str = "default"
    prediction_id: str = ""
    outcome_id: str = ""
    model_id: str = ""
    model_version: str = "1.0.0"
    provider_id: str = ""
    loss_or_error: float = 0.0
    metrics: dict[str, float] = field(default_factory=dict)
    feedback_type: str = "direct_outcome"
    payload: dict[str, Any] = field(default_factory=dict)
    authority: str = "NONE"
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            is_deterministic=True,
        )
    )

    def __post_init__(self) -> None:
        if self.authority != "NONE":
            raise ValueError("FeedbackRecord authority must strictly be 'NONE'")


@dataclass(frozen=True)
class LearningEvent(CognitiveObject):
    """Immutable record capturing feedback aggregation for model updates.

    Advisory only; authority is strictly NONE.
    """

    domain_id: str = "default"
    event_type: str = "outcome_feedback"
    feedback_ids: list[str] = field(default_factory=list)
    prediction_ids: list[str] = field(default_factory=list)
    outcome_ids: list[str] = field(default_factory=list)
    model_id: str = ""
    model_version: str = "1.0.0"
    provider_id: str = ""
    sample_count: int = 0
    data_fingerprint: str = ""
    authority: str = "NONE"
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            is_deterministic=True,
        )
    )

    def __post_init__(self) -> None:
        if self.authority != "NONE":
            raise ValueError("LearningEvent authority must strictly be 'NONE'")


@dataclass(frozen=True)
class LearningUpdate(CognitiveObject):
    """Computed parameter delta or structural update derived from learning.

    Advisory only; authority is strictly NONE.
    """

    domain_id: str = "default"
    learning_event_id: str = ""
    parent_model_id: str = ""
    parent_model_version: str = "1.0.0"
    candidate_model_id: str = ""
    candidate_model_version: str = "1.1-candidate"
    provider_id: str = ""
    update_method: str = "delta_update"
    parameter_deltas: dict[str, Any] = field(default_factory=dict)
    parameter_fingerprint: str = ""
    random_seed: int = 42
    authority: str = "NONE"
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            is_deterministic=True,
        )
    )

    def __post_init__(self) -> None:
        if self.authority != "NONE":
            raise ValueError("LearningUpdate authority must strictly be 'NONE'")


@dataclass(frozen=True)
class ModelCandidate(CognitiveObject):
    """Proposed candidate model state derived from learning updates or transfer proposals.

    Never overwrites or activates in production automatically.
    Advisory only; authority is strictly NONE.
    """

    domain_id: str = "default"
    candidate_model_id: str = ""
    candidate_model_version: str = "1.1-candidate"
    parent_model_id: str = ""
    parent_model_version: str = "1.0.0"
    provider_id: str = ""
    provider_version: str = "1.0.0"
    status: CandidateStatus = CandidateStatus.CANDIDATE
    parameter_fingerprint: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    creation_seed: int = 42
    learning_event_ids: list[str] = field(default_factory=list)
    transfer_proposal_id: str | None = None
    is_deterministic: bool = True
    authority: str = "NONE"
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            is_deterministic=True,
        )
    )

    def __post_init__(self) -> None:
        if self.authority != "NONE":
            raise ValueError("ModelCandidate authority must strictly be 'NONE'")


@dataclass(frozen=True)
class ModelEvaluation(CognitiveObject):
    """Formal statistical evaluation of a model or candidate on a dataset.

    Advisory only; authority is strictly NONE.
    """

    domain_id: str = "default"
    model_id: str = ""
    model_version: str = "1.0.0"
    provider_id: str = ""
    dataset_id: str = ""
    sample_count: int = 0
    metrics: dict[str, float] = field(default_factory=dict)
    is_deterministic: bool = True
    authority: str = "NONE"
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            is_deterministic=True,
        )
    )

    def __post_init__(self) -> None:
        if self.authority != "NONE":
            raise ValueError("ModelEvaluation authority must strictly be 'NONE'")


@dataclass(frozen=True)
class ModelPromotionProposal(CognitiveObject):
    """Advisory promotion proposal for external governance review.

    Contains factual comparison data. Authority is strictly NONE.
    Cognitia NEVER activates models autonomously.
    """

    domain_id: str = "default"
    parent_model_id: str = ""
    parent_model_version: str = "1.0.0"
    candidate_model_id: str = ""
    candidate_model_version: str = "1.1-candidate"
    provider_id: str = ""
    dataset_id: str = ""
    baseline_metrics: dict[str, float] = field(default_factory=dict)
    candidate_metrics: dict[str, float] = field(default_factory=dict)
    metric_deltas: dict[str, float] = field(default_factory=dict)
    drift_context: dict[str, Any] = field(default_factory=dict)
    rationale: str = ""
    recommendation: str = "PROPOSE_CANDIDATE"
    status: CandidateStatus = CandidateStatus.PROPOSED
    authority: str = "NONE"
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            is_deterministic=True,
        )
    )

    def __post_init__(self) -> None:
        if self.authority != "NONE":
            raise ValueError("ModelPromotionProposal authority must strictly be 'NONE'")


@dataclass(frozen=True)
class PromotionDecisionRecord(CognitiveObject):
    """Auditable record capturing an external domain authority decision.

    Cognitia records the decision, but Cognitia itself has authority='NONE'.
    """

    proposal_id: str = ""
    candidate_model_id: str = ""
    candidate_model_version: str = ""
    decision: str = "REJECTED"  # "ACCEPTED", "REJECTED", "DEFERRED"
    decider_id: str = ""
    decider_authority: str = ""
    rationale: str = ""
    cognitia_authority: str = "NONE"
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.HUMAN,
            is_deterministic=True,
        )
    )

    def __post_init__(self) -> None:
        if self.cognitia_authority != "NONE":
            raise ValueError("PromotionDecisionRecord cognitia_authority must strictly be 'NONE'")


# --- AL2 Knowledge Transfer Contracts ---

@dataclass(frozen=True)
class TransferCompatibilityResult(CognitiveObject):
    """Factual evaluation of representation and provider compatibility for cross-domain transfer.

    Advisory only; authority is strictly NONE.
    """

    proposal_id: str = ""
    source_domain_id: str = ""
    target_domain_id: str = ""
    source_domain: str = ""
    target_domain: str = ""
    is_compatible: bool = False
    status: TransferCompatibilityStatus = TransferCompatibilityStatus.UNKNOWN
    compatibility_status: TransferCompatibilityStatus = TransferCompatibilityStatus.UNKNOWN
    score: float = 0.0
    representation_compatible: bool = False
    provider_compatible: bool = False
    domain_separation_verified: bool = True
    compatibility_details: dict[str, Any] = field(default_factory=dict)
    risks: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    validation_requirements: list[str] = field(default_factory=list)
    advisory_recommendation: str = ""
    authority: str = "NONE"
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            producer_id="transfer_engine:compatibility",
            is_deterministic=True,
        )
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.authority != "NONE":
            raise ValueError("TransferCompatibilityResult authority must strictly be 'NONE'")
        if not self.source_domain and self.source_domain_id:
            object.__setattr__(self, "source_domain", self.source_domain_id)
        if not self.source_domain_id and self.source_domain:
            object.__setattr__(self, "source_domain_id", self.source_domain)
        if not self.target_domain and self.target_domain_id:
            object.__setattr__(self, "target_domain", self.target_domain_id)
        if not self.target_domain_id and self.target_domain:
            object.__setattr__(self, "target_domain_id", self.target_domain)
        if self.status != TransferCompatibilityStatus.UNKNOWN and self.compatibility_status == TransferCompatibilityStatus.UNKNOWN:
            object.__setattr__(self, "compatibility_status", self.status)
        elif self.compatibility_status != TransferCompatibilityStatus.UNKNOWN and self.status == TransferCompatibilityStatus.UNKNOWN:
            object.__setattr__(self, "status", self.compatibility_status)


@dataclass(frozen=True)
class LearningTransferProposal(CognitiveObject):
    """Explicit advisory proposal to transfer learned knowledge from a source domain to a target domain.

    Advisory only; authority is strictly NONE. No implicit transfer occurs.
    """

    source_domain_id: str = ""
    target_domain_id: str = ""
    source_domain: str = ""
    target_domain: str = ""
    source_model_id: str = ""
    source_model_version: str = "1.0.0"
    target_model_id: str = ""
    target_base_model_version: str = "1.0.0"
    source_candidate_version: str | None = None
    source_representation_version: str = "1.0.0"
    target_representation_version: str = "1.0.0"
    source_provider_id: str = "laya"
    target_provider_id: str = "laya"
    transfer_type: TransferType = TransferType.MODEL_TRANSFER
    knowledge_type: KnowledgeType = KnowledgeType.FEATURE_EXTRACTOR
    compatibility_status: TransferCompatibilityStatus = TransferCompatibilityStatus.UNKNOWN
    compatibility_reasons: list[str] = field(default_factory=list)
    validation_requirements: list[str] = field(default_factory=list)
    rationale: str = ""
    transfer_payload: dict[str, Any] = field(default_factory=dict)
    status: str = "PROPOSED"  # "PROPOSED", "VALIDATED", "ACCEPTED", "REJECTED"
    authority: str = "NONE"
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.ML_MODEL,
            producer_id="transfer_engine:proposal",
            is_deterministic=True,
        )
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.authority != "NONE":
            raise ValueError("LearningTransferProposal authority must strictly be 'NONE'")
        if not self.source_domain and self.source_domain_id:
            object.__setattr__(self, "source_domain", self.source_domain_id)
        if not self.source_domain_id and self.source_domain:
            object.__setattr__(self, "source_domain_id", self.source_domain)
        if not self.target_domain and self.target_domain_id:
            object.__setattr__(self, "target_domain", self.target_domain_id)
        if not self.target_domain_id and self.target_domain:
            object.__setattr__(self, "target_domain_id", self.target_domain)
        if not self.target_model_id and self.source_model_id:
            object.__setattr__(self, "target_model_id", self.source_model_id)


@dataclass(frozen=True)
class TransferDecisionRecord(CognitiveObject):
    """Auditable record capturing an external domain authority decision on a transfer proposal.

    Cognitia records the audit trail, but Cognitia itself has ZERO authority to activate models.
    """

    proposal_id: str = ""
    source_domain_id: str = ""
    target_domain_id: str = ""
    source_domain: str = ""
    target_domain: str = ""
    decision: str = "REJECTED"  # "ACCEPTED", "REJECTED", "DEFERRED"
    decision_source: str = "EXTERNAL"  # Strictly external
    decider_id: str = ""
    decider_authority: str = ""
    rationale: str = ""
    cognitia_authority: str = "NONE"
    provenance: ProvenanceRecord = field(
        default_factory=lambda: ProvenanceRecord(
            source_type=SourceType.HUMAN,
            producer_id="governance:transfer_decision",
            is_deterministic=True,
        )
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.cognitia_authority != "NONE":
            raise ValueError("TransferDecisionRecord cognitia_authority must strictly be 'NONE'")
        if not self.source_domain and self.source_domain_id:
            object.__setattr__(self, "source_domain", self.source_domain_id)
        if not self.source_domain_id and self.source_domain:
            object.__setattr__(self, "source_domain_id", self.source_domain)
        if not self.target_domain and self.target_domain_id:
            object.__setattr__(self, "target_domain", self.target_domain_id)
        if not self.target_domain_id and self.target_domain:
            object.__setattr__(self, "target_domain_id", self.target_domain)



@dataclass(frozen=True)
class LearningCurvePoint(CognitiveObject):
    """Single point on a model's learning curve trajectory."""

    domain_id: str = "default"
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

    domain_id: str = "default"
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

    domain_id: str = "default"
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

    def __init__(
        self,
        message: str,
        model_id: str = "",
        provider_id: str = "",
        domain_id: str = "",
        error_code: str = "INFERENCE_ERROR",
    ) -> None:
        super().__init__(message)
        self.model_id = model_id
        self.provider_id = provider_id
        self.domain_id = domain_id
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

    def learn(
        self,
        events: list[LearningEvent],
        base_model: ModelRecord,
        seed: int = 42,
        config: dict[str, Any] | None = None,
    ) -> tuple[ModelCandidate, LearningUpdate]: ...

    def evaluate_candidate(
        self,
        candidate: ModelCandidate,
        dataset: list[dict[str, Any]],
    ) -> ModelEvaluation: ...
