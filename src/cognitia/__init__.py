"""Cognitia: Domain-Neutral Cognitive Infrastructure and Epistemic Service Framework.

Phase 0 Architectural Foundation.
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
    ReasoningCapability,
)
from cognitia.reasoning.types import (
    ReasoningMode,
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
    "Action",
    "BaseCapability",
    "CandidateLearningArtifact",
    "CandidateType",
    "CapabilityDescriptor",
    "CapabilityRegistry",
    "CapabilityType",
    "Challenge",
    "Claim",
    "CognitiveEvent",
    "CognitiveEventType",
    "CognitiveObject",
    "CognitiveRule",
    "CognitiveService",
    "ConsolidationCapability",
    "ConsolidationResult",
    "ConsolidationService",
    "ConsolidationStatus",
    "Decision",
    "DecisionCapability",
    "DeterministicSerializer",
    "EpistemicNode",
    "EpistemicService",
    "EpistemicStatus",
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
    "ProvenanceRecord",
    "ReasoningCapability",
    "ReasoningMode",
    "ReasoningStep",
    "ReasoningTrace",
    "Residual",
    "RuleEvaluationCapability",
    "RuleStatus",
    "RuleStore",
    "SourceType",
    "TransitionOutcome",
    "__version__",
    "compute_checksum",
    "evaluate_predicate",
]
