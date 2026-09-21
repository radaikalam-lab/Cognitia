"""Cognitia: Domain-Neutral Cognitive Infrastructure and Epistemic Service Framework.

Phase 0-4 Architectural Foundation.
"""

from cognitia.abi.types import (
    SCHEMA_VERSION_V1,
    Action,
    CognitiveObject,
    Decision,
    DeterministicSerializer,
    Observation,
    Outcome,
)
from cognitia.attention.engine import (
    AttentionEngine,
    DeterministicAttentionEngine,
)
from cognitia.attention.types import (
    AttentionItem,
    AttentionQuery,
    AttentionReason,
    AttentionResult,
)
from cognitia.capabilities.base import (
    BaseCapability,
    CapabilityDescriptor,
    CapabilityType,
    DecisionCapability,
)
from cognitia.capabilities.registry import (
    CapabilityRegistry,
    InMemoryCapabilityRegistry,
)
from cognitia.context.engine import (
    ContextAssembler,
    DeterministicContextAssembler,
)
from cognitia.context.types import (
    AggregateContext,
    CognitiveContext,
    ContextCompression,
    ContextConflict,
    ContextDeviation,
    ContextItem,
    ContextQuery,
    CorrelationReason,
    CrossSourceCorrelation,
    DeviationType,
    EntityRelation,
    EntityRelationType,
    EpistemicTension,
    ProvenanceNeighbourhood,
    RecurrenceContext,
    RelevanceReason,
    SequenceContext,
    StateReconstruction,
    StateVariable,
    TemporalContext,
    TemporalRelation,
    TemporalRelationType,
)
from cognitia.epistemic.service import (
    EpistemicService,
    InMemoryEpistemicService,
)
from cognitia.epistemic.types import (
    Challenge,
    Claim,
    EpistemicNode,
    EpistemicStatus,
    EpistemicTransition,
    Evidence,
    EvidenceDirection,
    Hypothesis,
    Residual,
    TransitionOutcome,
)
from cognitia.experience.record import (
    ExperienceBuilder,
    ExperienceRecord,
)
from cognitia.memory.consolidation import (
    ConsolidationCapability,
    ConsolidationService,
    InMemoryConsolidationService,
    PlasticityOperator,
)
from cognitia.memory.store import (
    InMemoryMemoryStore,
    MemoryStore,
)
from cognitia.memory.types import (
    CandidateLearningArtifact,
    CandidateType,
    ConsolidationResult,
    ConsolidationStatus,
    MemoryContext,
    MemoryQuery,
)
from cognitia.models.registry import (
    InMemoryModelRegistry,
    ModelRecord,
    ModelRegistry,
    ModelStatus,
)
from cognitia.persistence.events import (
    CognitiveEvent,
    CognitiveEventType,
    EventQuery,
    ObjectQuery,
)
from cognitia.persistence.store import (
    InMemoryPersistenceStore,
    PersistenceStore,
)
from cognitia.provenance.record import (
    LineageChain,
    ProvenanceRecord,
    SourceType,
    compute_checksum,
)
from cognitia.reasoning.capability import (
    DeterministicMockReasoner,
    EngineReasoningCapability,
    ReasoningCapability,
)
from cognitia.reasoning.engine import (
    DeterministicReasoningEngine,
    ReasoningEngine,
)
from cognitia.reasoning.strategies import (
    AbductiveReasoner,
    AnalogicalReasoner,
    CausalReasoner,
    CounterfactualReasoner,
    DeductiveReasoner,
    ReasoningStrategy,
)
from cognitia.reasoning.types import (
    AbductiveHypotheses,
    AnalogicalMapping,
    CausalHypothesis,
    CounterfactualScenario,
    DeductiveConclusion,
    ReasoningInput,
    ReasoningMode,
    ReasoningResidual,
    ReasoningResult,
    ReasoningStep,
    ReasoningTrace,
)
from cognitia.rules.capability import (
    RuleEvaluationCapability,
    evaluate_predicate,
)
from cognitia.rules.store import (
    InMemoryRuleStore,
    RuleStore,
)
from cognitia.rules.types import (
    CognitiveRule,
    RuleStatus,
)
from cognitia.runtime.local import LocalCognitiveRuntime
from cognitia.service.facade import (
    CognitiveService,
    ExperienceService,
    InMemoryExperienceService,
)

__version__ = "0.1.0"

__all__ = [
    "SCHEMA_VERSION_V1",
    "AbductiveHypotheses",
    "AbductiveReasoner",
    "Action",
    "AggregateContext",
    "AnalogicalMapping",
    "AnalogicalReasoner",
    "AttentionEngine",
    "AttentionItem",
    "AttentionQuery",
    "AttentionReason",
    "AttentionResult",
    "BaseCapability",
    "CandidateLearningArtifact",
    "CandidateType",
    "CapabilityDescriptor",
    "CapabilityRegistry",
    "CapabilityType",
    "CausalHypothesis",
    "CausalReasoner",
    "Challenge",
    "Claim",
    "CognitiveContext",
    "CognitiveEvent",
    "CognitiveEventType",
    "CognitiveObject",
    "CognitiveRule",
    "CognitiveService",
    "ConsolidationCapability",
    "ConsolidationResult",
    "ConsolidationService",
    "ConsolidationStatus",
    "ContextAssembler",
    "ContextCompression",
    "ContextConflict",
    "ContextDeviation",
    "ContextItem",
    "ContextQuery",
    "CorrelationReason",
    "CounterfactualReasoner",
    "CounterfactualScenario",
    "CrossSourceCorrelation",
    "Decision",
    "DecisionCapability",
    "DeductiveConclusion",
    "DeductiveReasoner",
    "DeterministicAttentionEngine",
    "DeterministicContextAssembler",
    "DeterministicMockReasoner",
    "DeterministicReasoningEngine",
    "DeterministicSerializer",
    "DeviationType",
    "EngineReasoningCapability",
    "EntityRelation",
    "EntityRelationType",
    "EpistemicNode",
    "EpistemicService",
    "EpistemicStatus",
    "EpistemicTension",
    "EpistemicTransition",
    "EventQuery",
    "Evidence",
    "EvidenceDirection",
    "ExperienceBuilder",
    "ExperienceRecord",
    "ExperienceService",
    "Hypothesis",
    "InMemoryCapabilityRegistry",
    "InMemoryConsolidationService",
    "InMemoryEpistemicService",
    "InMemoryExperienceService",
    "InMemoryMemoryStore",
    "InMemoryModelRegistry",
    "InMemoryPersistenceStore",
    "InMemoryRuleStore",
    "LineageChain",
    "LocalCognitiveRuntime",
    "MemoryContext",
    "MemoryQuery",
    "MemoryStore",
    "ModelRecord",
    "ModelRegistry",
    "ModelStatus",
    "ObjectQuery",
    "Observation",
    "Outcome",
    "PersistenceStore",
    "PlasticityOperator",
    "ProvenanceNeighbourhood",
    "ProvenanceRecord",
    "ReasoningCapability",
    "ReasoningEngine",
    "ReasoningInput",
    "ReasoningMode",
    "ReasoningResidual",
    "ReasoningResult",
    "ReasoningStep",
    "ReasoningStrategy",
    "ReasoningTrace",
    "RecurrenceContext",
    "RelevanceReason",
    "Residual",
    "RuleEvaluationCapability",
    "RuleStatus",
    "RuleStore",
    "SequenceContext",
    "SourceType",
    "StateReconstruction",
    "StateVariable",
    "TemporalContext",
    "TemporalRelation",
    "TemporalRelationType",
    "TransitionOutcome",
    "__version__",
    "compute_checksum",
    "evaluate_predicate",
]
