"""Tests for Reasoning Snapshot Semantics and Store Mutation Isolation."""

import pytest

from cognitia.abi.types import Observation
from cognitia.attention.engine import DeterministicAttentionEngine
from cognitia.attention.types import AttentionQuery
from cognitia.context.engine import DeterministicContextAssembler
from cognitia.epistemic.service import InMemoryEpistemicService
from cognitia.memory.store import InMemoryMemoryStore
from cognitia.models.registry import InMemoryModelRegistry, ModelRecord
from cognitia.persistence.store import InMemoryPersistenceStore
from cognitia.reasoning import (
    DeterministicReasoningEngine,
    ReasoningMode,
)
from cognitia.rules.store import InMemoryRuleStore
from cognitia.rules.types import CognitiveRule, RuleStatus


def test_reasoning_input_snapshot_isolation_from_live_store_mutation():
    """Verify that mutations to stores after ReasoningInput snapshot creation do NOT affect reasoning outcome."""
    persistence = InMemoryPersistenceStore()
    memory = InMemoryMemoryStore(persistence_store=persistence)
    epistemics = InMemoryEpistemicService()
    rules = InMemoryRuleStore()
    models = InMemoryModelRegistry()

    # Setup initial rule at T1
    rule_t1 = CognitiveRule(
        rule_id="r_snap",
        name="Snapshot Rule",
        predicate={"speed": {">": 80}},
        recommendation={"status": "HIGH_SPEED_CRUISE"},
    )
    rules.create_rule(rule_t1)

    obs = Observation(id="obs_snap_1", payload={"speed": 95})
    persistence.save_object(obs)

    assembler = DeterministicContextAssembler(
        persistence_store=persistence,
        memory_store=memory,
        rule_store=rules,
        epistemic_service=epistemics,
    )
    context = assembler.assemble_context(obs)

    att_engine = DeterministicAttentionEngine()
    att_result = att_engine.focus(context, AttentionQuery())

    reasoning_engine = DeterministicReasoningEngine()
    # T1: Snapshot constructed
    snapshot_input = reasoning_engine.build_snapshot(
        context=context,
        attention_result=att_result,
        mode=ReasoningMode.DEDUCTION,
        premises=[obs],
        rules=rules.list_rules(status=RuleStatus.ACTIVE),
    )

    # T2: Live stores mutated heavily
    # Mutate rules: retire old rule, add new contradicting rule
    rules.retire_rule("r_snap")
    rule_t2 = CognitiveRule(
        rule_id="r_snap_new",
        name="Mutated Rule",
        predicate={"speed": {">": 80}},
        recommendation={"status": "MUTATED_STATE"},
    )
    rules.create_rule(rule_t2)

    # Mutate persistence: add new observations
    obs_t2 = Observation(id="obs_snap_2", payload={"speed": 20})
    persistence.save_object(obs_t2)

    # T3: Execute reasoning on the original T1 snapshot
    trace, result = reasoning_engine.reason(snapshot_input)

    # Invariant: Output strictly reflects T1 snapshot
    assert trace.conclusion.derived_attributes_dict["status"] == "HIGH_SPEED_CRUISE"
    assert "r_snap" in trace.conclusion.matched_rule_ids
    assert "r_snap_new" not in trace.conclusion.matched_rule_ids
