"""Tests for Cross-Source Correlation Enrichment.

Validates bounded multi-source temporal and structural correlations with explicit basis explanations.
"""

import pytest

from cognitia.abi.types import Observation
from cognitia.context.types import CorrelationReason
from cognitia.runtime.local import LocalCognitiveRuntime


def test_cross_source_correlation() -> None:
    runtime = LocalCognitiveRuntime()

    obs_acoustic = Observation(
        source_id="acoustiforge:evaluator:1",
        payload={"subject_id": "DESIGN-01", "alpha": 0.85},
        created_at="2026-09-21T10:15:32Z",
        metadata={"source_application": "acoustiforge", "subject_id": "DESIGN-01"},
    )
    obs_thermal = Observation(
        source_id="thermal:chamber:1",
        payload={"subject_id": "DESIGN-01", "temp": 42.0},
        created_at="2026-09-21T10:15:33Z",
        metadata={"source_application": "thermal_monitor", "subject_id": "DESIGN-01"},
    )
    obs_power = Observation(
        source_id="power:meter:1",
        payload={"current": 7.8},
        created_at="2026-09-21T10:15:34Z",
        metadata={"source_application": "power_supply"},
    )

    runtime.persistence.save_object(obs_acoustic)
    runtime.persistence.save_object(obs_thermal)
    runtime.persistence.save_object(obs_power)

    context = runtime.assemble_context(obs_power)

    assert len(context.correlations) >= 1
    # Check shared subject between acoustic and thermal
    corr_subject = [
        c for c in context.correlations
        if (c.source_a_id == obs_acoustic.id and c.source_b_id == obs_thermal.id)
        or (c.source_a_id == obs_thermal.id and c.source_b_id == obs_acoustic.id)
    ][0]
    assert corr_subject.correlation_reason == CorrelationReason.SHARED_SUBJECT
    assert corr_subject.time_delta_seconds == 1.0
