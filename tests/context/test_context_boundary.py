"""Tests for Cognitive Context Non-Authoritative Boundary and Side-Effect Freedom."""

import copy
import pytest

from cognitia.abi.types import Observation
from cognitia.context.types import CognitiveContext
from cognitia.rules.types import CognitiveRule
from cognitia.runtime.local import LocalCognitiveRuntime


def test_context_assembly_is_read_only_and_side_effect_free() -> None:
    runtime = LocalCognitiveRuntime()

    rule = CognitiveRule(
        rule_id="R-TEST-01",
        version="1.0.0",
        scope="monitoring",
        predicate={"field": "metric", "op": ">", "value": 10},
    )
    runtime.rules.create_rule(rule)

    obs = Observation(
        source_id="device_1",
        payload={"metric": 15, "state": "normal"},
        metadata={"subject_id": "DEV-1", "scope": "monitoring"},
    )
    runtime.persistence.save_object(obs)

    # Deepcopy before assembly to verify zero state mutation
    obs_copy = copy.deepcopy(obs)
    rule_copy = copy.deepcopy(rule)

    # Assemble context
    context = runtime.assemble_context(obs)

    assert isinstance(context, CognitiveContext)

    # Verification: Observation and Rule in runtime/persistence remain untouched
    persisted_obs = runtime.persistence.get_object(obs.id)
    assert persisted_obs == obs_copy

    stored_rule = runtime.rules.get_rule("R-TEST-01")
    assert stored_rule == rule_copy
