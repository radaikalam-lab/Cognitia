"""Phase 5A: Embedded Reasoning Integration Tests."""

from __future__ import annotations

import pytest

from cognitia.runtime.local import LocalCognitiveRuntime
from cognitia.reasoning.types import ReasoningInput, ReasoningMode

from tests.embedded.fixtures.host_adapter import SyntheticHostAdapter


class TestEmbeddedReasoning:
    """Host application can perform deterministic reasoning inside the same process."""

    def test_reasoning_over_attention_result(self, adapter: SyntheticHostAdapter) -> None:
        runtime = LocalCognitiveRuntime()
        for i in range(3):
            obs = adapter.create_order_submitted_observation(f"order_{i}", f"cust_{i}", float(i * 10))
            exp = adapter.create_experience_from_observation(obs).with_agent("host_app").build()
            runtime.persistence.save_object(exp)
        current_obs = adapter.create_order_submitted_observation("order_current", "cust_current", 500.0)
        context = runtime.assemble_context(current_obs)
        attention_result = runtime.focus_context(context)
        reasoning_input = ReasoningInput(
            reasoning_mode=ReasoningMode.DEDUCTION,
            premises=(),
            attention_result_id=attention_result.id,
        )
        trace, result = runtime.reason(reasoning_input)
        assert trace is not None
        assert result is not None

    def test_reasoning_result_is_advisory_not_truth(self, adapter: SyntheticHostAdapter) -> None:
        runtime = LocalCognitiveRuntime()
        obs = adapter.create_order_submitted_observation("order_1", "cust_1", 100.0)
        context = runtime.assemble_context(obs)
        attention_result = runtime.focus_context(context)
        reasoning_input = ReasoningInput(
            reasoning_mode=ReasoningMode.DEDUCTION,
            premises=(),
            attention_result_id=attention_result.id,
        )
        _, result = runtime.reason(reasoning_input)
        assert result.candidate_conclusions is not None
