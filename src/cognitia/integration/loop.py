"""Cognitia Phase 10: Integrated Cognitive Loop Orchestrator.

Composes existing deterministic subsystems into a single auditable cognitive
cycle without introducing new reasoning, memory, or authority semantics.

The loop is advisory-only. It never executes domain actions.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from cognitia.abi.types import (
    Action,
    CognitiveObject,
    Observation,
    Outcome,
    current_utc_timestamp,
    generate_entity_id,
)
from cognitia.attention.engine import AttentionEngine, DeterministicAttentionEngine
from cognitia.attention.types import AttentionQuery
from cognitia.capabilities.base import DeterministicMockDecisionProvider
from cognitia.context.engine import ContextAssembler, DeterministicContextAssembler
from cognitia.context.types import ContextQuery
from cognitia.directional.service import DirectionalService, InMemoryDirectionalService
from cognitia.directional.types import (
    DirectionalConstraint,
    DirectionalObjective,
    DirectionalSpecification,
    SuccessCriterion,
)
from cognitia.documents.service import DocumentService
from cognitia.documents.specification import DocumentSpecification, SectionSpecification
from cognitia.documents.types import SectionType
from cognitia.epistemic.service import EpistemicService, InMemoryEpistemicService
from cognitia.epistemic.types import EpistemicStatus
from cognitia.experience.record import ExperienceRecord
from cognitia.integration.types import CognitiveLoopResult
from cognitia.memory.store import InMemoryMemoryStore, MemoryStore
from cognitia.memory.types import MemoryQuery
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
from cognitia.provenance.record import ProvenanceRecord, SourceType
from cognitia.reasoning.engine import DeterministicReasoningEngine, ReasoningEngine
from cognitia.reasoning.types import ReasoningMode
from cognitia.recall.engine import InMemoryRecallEngine, RecallEngine
from cognitia.recall.types import RecallQuery, RecallObjectType
from cognitia.rules.store import InMemoryRuleStore, RuleStore


@runtime_checkable
class CognitiveLoop(Protocol):
    """Protocol for the integrated cognitive loop orchestrator."""

    def execute(
        self,
        observation: Observation,
        episode_id: str = "episode_0",
    ) -> CognitiveLoopResult:
        """Execute one complete cognitive cycle starting from an observation."""
        ...

    def accept_outcome(
        self,
        outcome: Outcome,
        loop_result: CognitiveLoopResult,
        episode_id: str = "episode_0",
    ) -> CognitiveLoopResult:
        """Accept an externally supplied outcome and persist it as future experience."""
        ...


class DeterministicCognitiveLoop:
    """Thin orchestrator composing existing Cognitia subsystems into a cycle.

    INVARIANTS:
    1. No new reasoning, memory, or authority semantics are introduced.
    2. Every stage delegates to an existing subsystem API.
    3. Failures are explicit; downstream artifacts are never fabricated.
    4. The loop is advisory-only. It never executes domain actions.
    5. Plasticity is not automatically activated.
    """

    def __init__(
        self,
        persistence_store: PersistenceStore | None = None,
        memory_store: MemoryStore | None = None,
        recall_engine: RecallEngine | None = None,
        context_assembler: ContextAssembler | None = None,
        attention_engine: AttentionEngine | None = None,
        reasoning_engine: ReasoningEngine | None = None,
        epistemic_service: EpistemicService | None = None,
        directional_service: DirectionalService | None = None,
        document_service: DocumentService | None = None,
        decision_provider: DeterministicMockDecisionProvider | None = None,
        rule_store: RuleStore | None = None,
        loop_id: str = "deterministic_cognitive_loop",
    ) -> None:
        self._loop_id = loop_id
        self._persistence = persistence_store or InMemoryPersistenceStore()
        self._memory = memory_store or InMemoryMemoryStore(self._persistence)
        self._recall = recall_engine or InMemoryRecallEngine(
            persistence_store=self._persistence,
            memory_store=self._memory,
        )
        self._epistemic = epistemic_service or InMemoryEpistemicService()
        self._reasoning = reasoning_engine or DeterministicReasoningEngine()
        self._attention = attention_engine or DeterministicAttentionEngine()
        self._directional = directional_service or InMemoryDirectionalService(
            persistence_store=self._persistence,
        )
        self._documents = document_service or DocumentService()
        self._decision = decision_provider or DeterministicMockDecisionProvider()
        self._rules = rule_store or InMemoryRuleStore()

        if context_assembler is not None:
            self._context = context_assembler
        else:
            self._context = DeterministicContextAssembler(
                persistence_store=self._persistence,
                memory_store=self._memory,
                rule_store=self._rules,
                epistemic_service=self._epistemic,
            )

    def execute(
        self,
        observation: Observation,
        episode_id: str = "episode_0",
    ) -> CognitiveLoopResult:
        """Execute one complete cognitive cycle.

        Stages (all required unless noted):
          1. Epistemic recording
          2. Experience building
          3. Persistence
          4. Memory assembly
          5. Recall
          6. Context assembly
          7. Attention
          8. Reasoning snapshot
          9. Reasoning execution
          10. Epistemic evaluation
          11. Directional proposal
          12. Decision (advisory)
          13. Document projection
        """
        provenance_chain: list[str] = [observation.id]

        # 1. Epistemic recording
        epistemic_node = self._epistemic.record_observation(observation)
        provenance_chain.append(epistemic_node.node_id)

        # 2. Experience building
        experience = self._build_experience(observation, episode_id, provenance_chain)
        provenance_chain.append(experience.id)

        # 3. Persistence
        self._persistence.save_object(observation)
        self._persistence.save_object(experience)
        self._append_events(observation, experience, episode_id, provenance_chain)

        # 4. Memory assembly
        memory_context = self._assemble_memory(episode_id)

        # 5. Recall
        recall_result = self._recall.recall(
            RecallQuery(
                agent_id=experience.agent_id,
                environment_id=experience.environment_id,
                episode_id=episode_id,
                object_types=(
                    RecallObjectType.EXPERIENCE_RECORD,
                    RecallObjectType.OBSERVATION,
                ),
                limit=5,
            )
        )
        provenance_chain.extend(candidate.object.id for candidate in recall_result.candidates)

        # 6. Context assembly
        cognitive_context = self._context.assemble_context(
            observation,
            ContextQuery(
                include_memory=True,
                include_epistemics=True,
                max_related_experiences=5,
                max_related_observations=5,
            ),
        )

        # 7. Attention
        attention_result = self._attention.focus(
            cognitive_context,
            AttentionQuery(
                task_type="general_focus",
                maximum_items=5,
            ),
        )

        # 8. Reasoning snapshot
        reasoning_input = self._reasoning.build_snapshot(
            context=cognitive_context,
            attention_result=attention_result,
            mode=ReasoningMode.DEDUCTION,
            premises=[observation],
        )

        # 9. Reasoning execution
        reasoning_trace, reasoning_result = self._reasoning.reason(reasoning_input)
        self._persistence.save_object(reasoning_trace)
        provenance_chain.append(reasoning_trace.id)

        # 10. Epistemic evaluation (register any hypotheses/claims from reasoning)
        self._evaluate_epistemic(reasoning_trace, reasoning_result)

        # 11. Directional proposal
        proposal = self._create_proposal(observation, experience, reasoning_trace)

        # 12. Decision (advisory)
        decision = self._decision.propose_decision(
            observation,
            context={"experience_id": experience.id},
        )
        self._persistence.save_object(decision)
        provenance_chain.append(decision.id)

        # 13. Document projection
        document = self._project_document(
            memory_context=memory_context,
            reasoning_trace=reasoning_trace,
            proposal=proposal,
            decision=decision,
        )
        if document:
            self._persistence.save_object(document)
            provenance_chain.append(document.id)

        return CognitiveLoopResult(
            observation_id=observation.id,
            experience_id=experience.id,
            reasoning_trace_id=reasoning_trace.id,
            proposal_id=proposal.id if proposal else None,
            decision_id=decision.id,
            document_id=document.id if document else None,
            provenance_chain=tuple(provenance_chain),
            loop_id=self._loop_id,
        )

    def accept_outcome(
        self,
        outcome: Outcome,
        loop_result: CognitiveLoopResult,
        episode_id: str = "episode_0",
    ) -> CognitiveLoopResult:
        """Persist an externally supplied outcome and return an updated loop result.

        The outcome becomes available as future experience for subsequent cycles.
        """
        self._persistence.save_object(outcome)
        self._persistence.append_event(
            CognitiveEvent(
                event_type=CognitiveEventType.OUTCOME_RECORDED.value,
                source_type=SourceType.SENSOR,
                source_id="external_authority",
                subject_id=outcome.id,
                payload={"linked_experience_id": loop_result.experience_id},
                provenance=ProvenanceRecord(
                    source_type=SourceType.COMPOSITE,
                    producer_id=self._loop_id,
                    parent_ids=[outcome.id, loop_result.experience_id],
                    is_deterministic=True,
                ),
            )
        )

        updated_chain = loop_result.provenance_chain + (outcome.id,)
        return CognitiveLoopResult(
            observation_id=loop_result.observation_id,
            experience_id=loop_result.experience_id,
            reasoning_trace_id=loop_result.reasoning_trace_id,
            proposal_id=loop_result.proposal_id,
            decision_id=loop_result.decision_id,
            document_id=loop_result.document_id,
            provenance_chain=updated_chain,
            loop_id=self._loop_id,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_experience(
        self,
        observation: Observation,
        episode_id: str,
        provenance_chain: list[str],
    ) -> ExperienceRecord:
        prov = ProvenanceRecord(
            source_type=SourceType.SENSOR,
            producer_id=self._loop_id,
            parent_ids=list(provenance_chain),
            is_deterministic=True,
        )
        return ExperienceRecord(
            source_application="cognitia_loop",
            source_node="loop_node",
            agent_id="loop_agent",
            environment_id="loop_env",
            episode_id=episode_id,
            observation=observation,
            action=Action(
                name="observe",
                parameters={"source_observation_id": observation.id},
                target_node=observation.source_id,
            ),
            expected_outcome=None,
            actual_outcome=None,
            provenance=prov,
        )

    def _append_events(
        self,
        observation: Observation,
        experience: ExperienceRecord,
        episode_id: str,
        provenance_chain: list[str],
    ) -> None:
        base_prov = ProvenanceRecord(
            source_type=SourceType.COMPOSITE,
            producer_id=self._loop_id,
            parent_ids=list(provenance_chain),
            is_deterministic=True,
        )
        self._persistence.append_event(
            CognitiveEvent(
                event_type=CognitiveEventType.OBSERVATION_RECORDED.value,
                source_type=SourceType.SENSOR,
                source_id=observation.source_id,
                subject_id=observation.id,
                payload={"episode_id": episode_id},
                provenance=base_prov,
            )
        )
        self._persistence.append_event(
            CognitiveEvent(
                event_type=CognitiveEventType.EXPERIENCE_RECORDED.value,
                source_type=SourceType.DETERMINISTIC_RULE,
                source_id=self._loop_id,
                subject_id=experience.id,
                payload={"observation_id": observation.id, "episode_id": episode_id},
                provenance=base_prov,
            )
        )

    def _assemble_memory(self, episode_id: str) -> Any:
        memory_query = MemoryQuery(
            source_application="cognitia_loop",
            episode_id=episode_id,
            object_types=["ExperienceRecord", "Observation", "Hypothesis", "Claim", "Evidence"],
        )
        return self._memory.get_context(memory_query)

    def _evaluate_epistemic(self, reasoning_trace: Any, reasoning_result: Any) -> None:
        """Register epistemic artifacts derived from reasoning without promotion."""
        conclusion = getattr(reasoning_result, "conclusion", None)
        if conclusion is None:
            return
        statement = getattr(conclusion, "derived_attributes_dict", {}).get("conclusion", "")
        if not statement:
            return
        hypothesis = __import__("cognitia.epistemic.types", fromlist=["Hypothesis"]).Hypothesis(
            statement=f"Derived from reasoning {reasoning_trace.id}: {statement}",
            initial_status=EpistemicStatus.HYPOTHESIS,
            provenance=ProvenanceRecord(
                source_type=SourceType.REASONING_ENGINE,
                producer_id=self._loop_id,
                parent_ids=[reasoning_trace.id],
                is_deterministic=True,
            ),
        )
        self._epistemic.register_hypothesis(hypothesis)
        self._persistence.save_object(hypothesis)
        self._persistence.append_event(
            CognitiveEvent(
                event_type=CognitiveEventType.HYPOTHESIS_REGISTERED.value,
                source_type=SourceType.REASONING_ENGINE,
                source_id=self._loop_id,
                subject_id=hypothesis.id,
                provenance=ProvenanceRecord(
                    source_type=SourceType.COMPOSITE,
                    producer_id=self._loop_id,
                    parent_ids=[reasoning_trace.id, hypothesis.id],
                    is_deterministic=True,
                ),
            )
        )

    def _create_proposal(self, observation: Observation, experience: ExperienceRecord, reasoning_trace: Any) -> Any:
        spec = self._directional.create_specification(
            objectives=[
                DirectionalObjective(
                    description=f"Address observation {observation.id} from experience {experience.id}",
                    target_state={"status": "addressed"},
                    priority=1.0,
                    metrics=["completeness"],
                )
            ],
            constraints=[
                DirectionalConstraint(
                    description="Cognitia remains advisory-only",
                    constraint_type="hard",
                    bound={"execution": "forbidden"},
                    is_hard=True,
                )
            ],
            success_criteria=[
                SuccessCriterion(
                    description="Proposal generated without execution",
                    metric_name="proposal_generated",
                    threshold=1.0,
                    direction=">=",
                )
            ],
        )
        proposal = self._directional.propose(
            specification_id=spec.id,
            provider_id="deterministic_directional_provider",
        )
        self._persistence.save_object(proposal)
        for residual in proposal.residuals:
            self._persistence.save_object(residual)
        self._persistence.append_event(
            CognitiveEvent(
                event_type=CognitiveEventType.DECISION_PROPOSED.value,
                source_type=SourceType.DETERMINISTIC_RULE,
                source_id=self._loop_id,
                subject_id=proposal.id,
                provenance=ProvenanceRecord(
                    source_type=SourceType.COMPOSITE,
                    producer_id=self._loop_id,
                    parent_ids=[spec.id, proposal.id],
                    is_deterministic=True,
                ),
            )
        )
        return proposal

    def _project_document(
        self,
        memory_context: Any,
        reasoning_trace: Any,
        proposal: Any,
        decision: Any,
    ) -> Any:
        doc_spec = DocumentSpecification(
            title=f"Cognitive Loop Result - {memory_context.query.episode_id or 'unknown'}",
            document_type="cognitive_loop",
            requested_sections=[
                SectionSpecification(
                    section_type=SectionType.OBSERVATIONS,
                    title="Observations",
                    artifact_types=["observation"],
                ),
                SectionSpecification(
                    section_type=SectionType.HYPOTHESES,
                    title="Hypotheses",
                    artifact_types=["hypothesis"],
                ),
                SectionSpecification(
                    section_type=SectionType.REASONING,
                    title="Reasoning",
                ),
                SectionSpecification(
                    section_type=SectionType.DECISIONS,
                    title="Decisions",
                ),
                SectionSpecification(
                    section_type=SectionType.PROVENANCE,
                    title="Provenance",
                ),
            ],
        )
        return self._documents.project(
            specification=doc_spec,
            memory_context=memory_context,
        )
