"""Tests for selective Memory Retrieval and MemoryContext assembly."""

import pytest

from cognitia.abi.types import Action, Decision, Observation, Outcome
from cognitia.epistemic.types import Claim, Evidence, Hypothesis
from cognitia.experience.record import ExperienceBuilder
from cognitia.memory.store import InMemoryMemoryStore
from cognitia.memory.types import MemoryContext, MemoryQuery
from cognitia.persistence.store import InMemoryPersistenceStore
from cognitia.provenance.record import ProvenanceRecord
from cognitia.reasoning.types import ReasoningMode, ReasoningStep, ReasoningTrace


def test_selective_memory_retrieval_by_dimensions():
    """Verify memory retrieval filtering by agent_id, episode_id, and object_type."""
    persistence = InMemoryPersistenceStore()

    exp1 = (
        ExperienceBuilder("robotics_app", "episode_101")
        .with_agent("drone_alpha")
        .with_observation(Observation(payload={"alt": 100}))
        .build()
    )
    exp2 = (
        ExperienceBuilder("robotics_app", "episode_101")
        .with_agent("drone_beta")
        .with_observation(Observation(payload={"alt": 150}))
        .build()
    )
    exp3 = (
        ExperienceBuilder("cell_app", "episode_202")
        .with_agent("analyzer_gamma")
        .with_observation(Observation(payload={"ph": 7.4}))
        .build()
    )

    for exp in [exp1, exp2, exp3]:
        persistence.save_object(exp)

    memory = InMemoryMemoryStore(persistence_store=persistence)

    # Filter by agent_id
    q_agent = memory.retrieve(MemoryQuery(agent_id="drone_alpha"))
    assert len(q_agent) == 1
    assert q_agent[0].id == exp1.id

    # Filter by episode_id
    q_episode = memory.retrieve(MemoryQuery(episode_id="episode_101"))
    assert len(q_episode) == 2
    assert {e.id for e in q_episode} == {exp1.id, exp2.id}

    # Filter by source_application
    q_app = memory.retrieve(MemoryQuery(source_application="cell_app"))
    assert len(q_app) == 1
    assert q_app[0].id == exp3.id


def test_memory_context_assembly():
    """Verify complete assembly of structured MemoryContext across multiple entity types."""
    persistence = InMemoryPersistenceStore()

    obs = Observation(source_id="sensor_0", payload={"val": 10})
    ev = Evidence(target_id="hypo_0", observation_ids=[obs.id])
    hyp = Hypothesis(statement="Flow rate scales with valve opening")
    claim = Claim(statement="System is calibrated")
    trace = ReasoningTrace(
        mode=ReasoningMode.DEDUCTION,
        steps=[ReasoningStep(step_number=1, inference_rule="rule_1")],
    )
    dec = Decision(proposal_type="adjust_valve", proposed_action=Action(name="open_valve"))
    outcome = Outcome(status="valve_opened", metrics={"flow_lpm": 5.2})

    for obj in [obs, ev, hyp, claim, trace, dec, outcome]:
        persistence.save_object(obj)

    memory = InMemoryMemoryStore(persistence_store=persistence)
    ctx = memory.get_context(MemoryQuery())

    assert isinstance(ctx, MemoryContext)
    assert len(ctx.observations) == 1
    assert len(ctx.evidence) == 1
    assert len(ctx.hypotheses) == 1
    assert len(ctx.claims) == 1
    assert len(ctx.reasoning_traces) == 1
    assert len(ctx.decisions) == 1
    assert len(ctx.outcomes) == 1

    # Invariant: Original object identities must be preserved exactly
    assert ctx.observations[0].id == obs.id
    assert ctx.hypotheses[0].id == hyp.id
    assert ctx.decisions[0].id == dec.id
