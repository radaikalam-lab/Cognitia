"""Tests for Cognitive Service composition and facade coordination."""

from cognitia.abi.types import Action, Observation, Outcome
from cognitia.capabilities.base import DeterministicMockDecisionProvider
from cognitia.capabilities.registry import InMemoryCapabilityRegistry
from cognitia.epistemic.service import InMemoryEpistemicService
from cognitia.experience.record import ExperienceBuilder
from cognitia.models.registry import InMemoryModelRegistry
from cognitia.reasoning.capability import DeterministicMockReasoner
from cognitia.reasoning.types import ReasoningMode
from cognitia.runtime.local import LocalCognitiveRuntime
from cognitia.service.facade import InMemoryExperienceService


def test_experience_service_storage():
    """Verify experience recording and query by episode and agent."""
    exp_service = InMemoryExperienceService()
    exp1 = (
        ExperienceBuilder("app_a", "ep_1")
        .with_agent("agent_1")
        .with_observation(Observation(payload={"val": 1}))
        .build()
    )
    exp2 = (
        ExperienceBuilder("app_a", "ep_1")
        .with_agent("agent_2")
        .with_observation(Observation(payload={"val": 2}))
        .build()
    )
    exp3 = (
        ExperienceBuilder("app_a", "ep_2")
        .with_agent("agent_1")
        .with_observation(Observation(payload={"val": 3}))
        .build()
    )

    exp_service.record_experience(exp1)
    exp_service.record_experience(exp2)
    exp_service.record_experience(exp3)

    assert len(exp_service.list_by_episode("ep_1")) == 2
    assert len(exp_service.list_by_agent("agent_1")) == 2
    assert len(exp_service.list_all()) == 3


def test_runtime_service_composition_and_advisory_flow():
    """Verify end-to-end cognitive advisory queries through LocalCognitiveRuntime facade."""
    runtime = LocalCognitiveRuntime()

    # Verify subsystem compositions
    assert isinstance(runtime.epistemics, InMemoryEpistemicService)
    assert isinstance(runtime.experience, InMemoryExperienceService)
    assert isinstance(runtime.capabilities, InMemoryCapabilityRegistry)
    assert isinstance(runtime.models, InMemoryModelRegistry)

    # 1. Epistemics flow
    obs = Observation(source_id="flow_sensor", payload={"pressure_psi": 45.0})
    node = runtime.epistemics.record_observation(obs)
    assert node.node_id == obs.id

    # 2. Decision advisory query
    decision = runtime.request_decision(obs)
    assert decision.proposal_type == "deterministic_policy_proposal"

    # 3. Reasoning query
    trace = runtime.request_reasoning(
        mode=ReasoningMode.DEDUCTION,
        premises=[obs],
    )
    assert trace.mode == ReasoningMode.DEDUCTION
    assert len(trace.steps) == 2
