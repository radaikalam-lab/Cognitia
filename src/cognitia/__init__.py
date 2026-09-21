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
from cognitia.models.registry import (
    InMemoryModelRegistry,
    ModelRecord,
    ModelRegistry,
    ModelStatus,
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
    "CapabilityDescriptor",
    "CapabilityRegistry",
    "CapabilityType",
    "Challenge",
    "Claim",
    "CognitiveObject",
    "CognitiveService",
    "Decision",
    "DecisionCapability",
    "DeterministicSerializer",
    "EpistemicNode",
    "EpistemicService",
    "EpistemicStatus",
    "EpistemicTransition",
    "Evidence",
    "EvidenceDirection",
    "ExperienceBuilder",
    "ExperienceRecord",
    "ExperienceService",
    "Hypothesis",
    "InMemoryCapabilityRegistry",
    "InMemoryEpistemicService",
    "InMemoryExperienceService",
    "InMemoryModelRegistry",
    "LineageChain",
    "LocalCognitiveRuntime",
    "ModelRecord",
    "ModelRegistry",
    "ModelStatus",
    "Observation",
    "Outcome",
    "ProvenanceRecord",
    "ReasoningCapability",
    "ReasoningMode",
    "ReasoningStep",
    "ReasoningTrace",
    "Residual",
    "SourceType",
    "TransitionOutcome",
    "__version__",
    "compute_checksum",
]
