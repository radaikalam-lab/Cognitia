"""Shared fixtures for embedded integration tests."""

from __future__ import annotations

import pytest

from cognitia.runtime.local import LocalCognitiveRuntime
from cognitia.recall.engine import InMemoryRecallEngine
from cognitia.recall.types import RecallObjectType, RecallQuery

from tests.embedded.fixtures.host_adapter import SyntheticHostAdapter
from tests.embedded.fixtures.synthetic_host import SyntheticBusinessApplication


@pytest.fixture
def host_app() -> SyntheticBusinessApplication:
    return SyntheticBusinessApplication(app_id="test_synthetic_app")


@pytest.fixture
def adapter(host_app: SyntheticBusinessApplication) -> SyntheticHostAdapter:
    return SyntheticHostAdapter(host_app, app_id="test_synthetic_app")


@pytest.fixture
def runtime() -> LocalCognitiveRuntime:
    return LocalCognitiveRuntime()
