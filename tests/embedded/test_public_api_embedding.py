"""Phase 5A: Public API Embedding Tests."""

from __future__ import annotations

import pytest

from cognitia.runtime.local import LocalCognitiveRuntime


class TestPublicAPIEmbedding:
    """External application can embed Cognitia via public API only."""

    def test_embed_via_local_cognitive_runtime(self) -> None:
        runtime = LocalCognitiveRuntime()
        assert runtime is not None
        assert hasattr(runtime, "persistence")
        assert hasattr(runtime, "memory")
        assert hasattr(runtime, "recall_engine")
        assert hasattr(runtime, "context_assembler")
        assert hasattr(runtime, "attention_engine")
        assert hasattr(runtime, "reasoning_engine")

    def test_runtime_provides_cognitive_apis(self) -> None:
        runtime = LocalCognitiveRuntime()
        assert callable(getattr(runtime, "recall", None))
        assert callable(getattr(runtime, "recall_with_trace", None))
        assert callable(getattr(runtime, "assemble_context", None))
        assert callable(getattr(runtime, "focus_context", None))
        assert callable(getattr(runtime, "reason", None))
        assert callable(getattr(runtime, "request_decision", None))
        assert callable(getattr(runtime, "request_reasoning", None))
