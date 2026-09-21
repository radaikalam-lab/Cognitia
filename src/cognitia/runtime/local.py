"""Cognitia Local Cognitive Runtime.

Provides in-process runtime assembly and composition of cognitive services,
persistence substrates, memory layers, and reference capability providers.
"""

from __future__ import annotations

from typing import Any

from cognitia.abi.types import Decision, Observation
from cognitia.capabilities.base import (
    BaseCapability,
    CapabilityType,
    DecisionCapability,
    DeterministicMockDecisionProvider,
)
from cognitia.capabilities.registry import (
    CapabilityRegistry,
    InMemoryCapabilityRegistry,
)
from cognitia.epistemic.service import (
    EpistemicService,
    InMemoryEpistemicService,
)
from cognitia.memory.consolidation import (
    ConsolidationService,
    InMemoryConsolidationService,
)
from cognitia.memory.store import (
    InMemoryMemoryStore,
    MemoryStore,
)
from cognitia.models.registry import (
    InMemoryModelRegistry,
    ModelRegistry,
)
from cognitia.persistence.store import (
    InMemoryPersistenceStore,
    PersistenceStore,
)
from cognitia.reasoning.capability import (
    DeterministicMockReasoner,
    ReasoningCapability,
)
from cognitia.reasoning.types import ReasoningMode, ReasoningTrace
from cognitia.rules.capability import RuleEvaluationCapability
from cognitia.rules.store import InMemoryRuleStore, RuleStore
from cognitia.service.facade import (
    CognitiveService,
    ExperienceService,
    InMemoryExperienceService,
)


class LocalCognitiveRuntime:
    """Local, in-process runtime managing service assembly, persistence, memory, and cognitive lifecycle."""

    def __init__(
        self,
        epistemic_service: EpistemicService | None = None,
        experience_service: ExperienceService | None = None,
        capability_registry: CapabilityRegistry | None = None,
        model_registry: ModelRegistry | None = None,
        persistence_store: PersistenceStore | None = None,
        memory_store: MemoryStore | None = None,
        consolidation_service: ConsolidationService | None = None,
        rule_store: RuleStore | None = None,
    ) -> None:
        self._epistemics = epistemic_service or InMemoryEpistemicService()
        self._experience = experience_service or InMemoryExperienceService()
        self._capabilities = capability_registry or InMemoryCapabilityRegistry()
        self._models = model_registry or InMemoryModelRegistry()
        self._persistence = persistence_store or InMemoryPersistenceStore()
        self._memory = memory_store or InMemoryMemoryStore(persistence_store=self._persistence)
        self._consolidation = consolidation_service or InMemoryConsolidationService()
        self._rules = rule_store or InMemoryRuleStore()

        # Bootstrap default deterministic reference providers if not already present
        if not self._capabilities.list_all():
            self._capabilities.register(DeterministicMockDecisionProvider())
            self._capabilities.register(DeterministicMockReasoner())
            self._capabilities.register(RuleEvaluationCapability(rule_store=self._rules))

    @property
    def epistemics(self) -> EpistemicService:
        return self._epistemics

    @property
    def experience(self) -> ExperienceService:
        return self._experience

    @property
    def capabilities(self) -> CapabilityRegistry:
        return self._capabilities

    @property
    def models(self) -> ModelRegistry:
        return self._models

    @property
    def persistence(self) -> PersistenceStore:
        return self._persistence

    @property
    def memory(self) -> MemoryStore:
        return self._memory

    @property
    def consolidation(self) -> ConsolidationService:
        return self._consolidation

    @property
    def rules(self) -> RuleStore:
        return self._rules

    def request_decision(
        self,
        observation: Observation,
        capability_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> Decision:
        """Query an advisory decision proposal from an eligible DecisionCapability."""
        if capability_id:
            cap = self._capabilities.get(capability_id)
            if not cap or not isinstance(cap, DecisionCapability):
                raise ValueError(f"DecisionCapability '{capability_id}' not found")
            return cap.propose_decision(observation, context)

        # Fallback to first registered decision capability
        decision_caps = self._capabilities.list_by_type(CapabilityType.DECISION)
        if not decision_caps:
            raise RuntimeError("No DecisionCapability registered in runtime")
        primary_cap = decision_caps[0]
        if not isinstance(primary_cap, DecisionCapability):
            raise TypeError("Registered capability does not implement DecisionCapability")
        return primary_cap.propose_decision(observation, context)

    def request_reasoning(
        self,
        mode: ReasoningMode,
        premises: list[Any],
        capability_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ReasoningTrace:
        """Perform structured cognitive reasoning via a ReasoningCapability."""
        if capability_id:
            cap = self._capabilities.get(capability_id)
            if not cap or not isinstance(cap, ReasoningCapability):
                raise ValueError(f"ReasoningCapability '{capability_id}' not found")
            return cap.reason(mode, premises, context)

        # Fallback to first registered reasoning capability supporting mode
        reasoning_caps = self._capabilities.list_by_type(CapabilityType.REASONING)
        for cap in reasoning_caps:
            if isinstance(cap, ReasoningCapability) and mode in cap.supported_modes:
                return cap.reason(mode, premises, context)

        # Also search general registered capabilities
        for cap in self._capabilities.list_all():
            if isinstance(cap, ReasoningCapability) and mode in cap.supported_modes:
                return cap.reason(mode, premises, context)

        raise RuntimeError(f"No ReasoningCapability registered for mode {mode.value}")
