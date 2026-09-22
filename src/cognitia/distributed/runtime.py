"""Cognitia Central and Edge Cognitive Runtimes.

CentralCognitiveRuntime and EdgeCognitiveRuntime share the same cognitive
substrate. They differ only in deployment topology and configured capabilities.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from cognitia.abi.types import CognitiveObject, Observation
from cognitia.attention.engine import (
    AttentionEngine,
    DeterministicAttentionEngine,
)
from cognitia.attention.types import (
    AttentionQuery,
    AttentionResult,
)
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
from cognitia.context.engine import (
    ContextAssembler,
    DeterministicContextAssembler,
)
from cognitia.context.types import (
    CognitiveContext,
    ContextQuery,
)
from cognitia.directional.service import (
    DirectionalService,
    InMemoryDirectionalService,
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
    EngineReasoningCapability,
    ReasoningCapability,
)
from cognitia.reasoning.engine import (
    DeterministicReasoningEngine,
    ReasoningEngine,
)
from cognitia.reasoning.types import (
    ReasoningInput,
    ReasoningMode,
    ReasoningResult,
    ReasoningTrace,
)
from cognitia.recall.engine import InMemoryRecallEngine, RecallEngine
from cognitia.recall.types import RecallQuery, RecallResult
from cognitia.rules.capability import RuleEvaluationCapability
from cognitia.rules.store import InMemoryRuleStore, RuleStore
from cognitia.rules.types import CognitiveRule
from cognitia.service.facade import (
    CognitiveService,
    ExperienceService,
    InMemoryExperienceService,
)


class LocalCognitiveRuntime:
    """Local, in-process runtime managing service assembly, persistence, memory, context, attention, reasoning, and cognitive lifecycle."""

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
        context_assembler: ContextAssembler | None = None,
        attention_engine: AttentionEngine | None = None,
        reasoning_engine: ReasoningEngine | None = None,
    ) -> None:
        self._epistemics = epistemic_service or InMemoryEpistemicService()
        self._experience = experience_service or InMemoryExperienceService()
        self._capabilities = capability_registry or InMemoryCapabilityRegistry()
        self._models = model_registry or InMemoryModelRegistry()
        self._persistence = persistence_store or InMemoryPersistenceStore()
        self._memory = memory_store or InMemoryMemoryStore(persistence_store=self._persistence)
        self._consolidation = consolidation_service or InMemoryConsolidationService()
        self._rules = rule_store or InMemoryRuleStore()
        self._context_assembler = context_assembler or DeterministicContextAssembler(
            persistence_store=self._persistence,
            memory_store=self._memory,
            rule_store=self._rules,
            epistemic_service=self._epistemics,
        )
        self._attention_engine = attention_engine or DeterministicAttentionEngine()
        self._reasoning_engine = reasoning_engine or DeterministicReasoningEngine()
        self._recall_engine = InMemoryRecallEngine(
            persistence_store=self._persistence,
            memory_store=self._memory,
        )

        # Bootstrap default deterministic reference providers if not already present
        if not self._capabilities.list_all():
            self._capabilities.register(DeterministicMockDecisionProvider())
            self._capabilities.register(DeterministicMockReasoner())
            self._capabilities.register(EngineReasoningCapability(engine=self._reasoning_engine))
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

    @property
    def context_assembler(self) -> ContextAssembler:
        return self._context_assembler

    @property
    def attention_engine(self) -> AttentionEngine:
        return self._attention_engine

    @property
    def reasoning_engine(self) -> ReasoningEngine:
        return self._reasoning_engine

    @property
    def recall_engine(self) -> RecallEngine:
        return self._recall_engine

    def recall(self, query: RecallQuery) -> RecallResult:
        return self._recall_engine.recall(query)

    def recall_with_trace(self, query: RecallQuery) -> tuple[RecallResult, RecallTrace]:
        return self._recall_engine.recall_with_trace(query)

    def assemble_context(
        self,
        observation: Observation,
        query: ContextQuery | None = None,
    ) -> CognitiveContext:
        return self._context_assembler.assemble_context(observation, query)

    def focus_context(
        self,
        context: CognitiveContext,
        query: AttentionQuery | None = None,
    ) -> AttentionResult:
        return self._attention_engine.focus(context, query)

    def reason(
        self,
        reasoning_input: ReasoningInput,
    ) -> tuple[ReasoningTrace, ReasoningResult]:
        return self._reasoning_engine.reason(reasoning_input)

    def reason_over_attention(
        self,
        context: CognitiveContext,
        attention_result: AttentionResult | None = None,
        mode: ReasoningMode = ReasoningMode.DEDUCTION,
        premises: Sequence[CognitiveObject] | None = None,
        rules: Sequence[CognitiveRule] | None = None,
        constraints: Mapping[str, Any] | None = None,
        hypothetical_interventions: Mapping[str, Any] | None = None,
        causal_graph: Sequence[tuple[str, str, str]] | None = None,
        analogy_source: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> tuple[ReasoningTrace, ReasoningResult]:
        active_rules = rules if rules is not None else self._rules.list_active()
        snapshot = self._reasoning_engine.build_snapshot(
            context=context,
            attention_result=attention_result,
            mode=mode,
            premises=premises,
            rules=active_rules,
            constraints=constraints,
            hypothetical_interventions=hypothetical_interventions,
            causal_graph=causal_graph,
            analogy_source=analogy_source,
            metadata=metadata,
        )
        return self._reasoning_engine.reason(snapshot)

    def request_decision(
        self,
        observation: Observation,
        capability_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> Decision:
        if capability_id:
            cap = self._capabilities.get(capability_id)
            if not cap or not isinstance(cap, DecisionCapability):
                raise ValueError(f"DecisionCapability '{capability_id}' not found")
            return cap.propose_decision(observation, context)

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
        if capability_id:
            cap = self._capabilities.get(capability_id)
            if not cap or not isinstance(cap, ReasoningCapability):
                raise ValueError(f"ReasoningCapability '{capability_id}' not found")
            return cap.reason(mode, premises, context)

        reasoning_caps = self._capabilities.list_by_type(CapabilityType.REASONING)
        for cap in reasoning_caps:
            if isinstance(cap, ReasoningCapability) and mode in cap.supported_modes:
                return cap.reason(mode, premises, context)

        for cap in self._capabilities.list_all():
            if isinstance(cap, ReasoningCapability) and mode in cap.supported_modes:
                return cap.reason(mode, premises, context)

        raise RuntimeError(f"No ReasoningCapability registered for mode {mode.value}")


class CentralCognitiveRuntime(LocalCognitiveRuntime):
    """Central Cognitia runtime composition boundary.

    Inherits all cognitive capabilities from LocalCognitiveRuntime.
    Designated for central deployment topology.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.node_type = "central"


class EdgeCognitiveRuntime(LocalCognitiveRuntime):
    """Edge Cognitia runtime local execution boundary.

    Inherits all cognitive capabilities from LocalCognitiveRuntime.
    Designed for local execution with optional central connectivity.
    Exact capabilities are configurable via dependency injection.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.node_type = "edge"
