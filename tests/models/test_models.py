"""Tests for Model Registry, version immutability, and lifecycle management."""

import pytest

from cognitia.capabilities.base import CapabilityType
from cognitia.models.registry import (
    InMemoryModelRegistry,
    ModelRecord,
    ModelStatus,
)


def test_model_registration_and_immutability():
    """Verify model version registration and immutability."""
    registry = InMemoryModelRegistry()

    record_v1 = ModelRecord(
        model_id="acoustic_dispersion_estimator",
        model_version="1.0.0",
        provider="deterministic_lookup",
        capability_type=CapabilityType.DECISION,
        calibration_checksum="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        status=ModelStatus.ACTIVE,
    )

    registry.register(record_v1)

    # Attempting to re-register the exact same version must raise ValueError
    with pytest.raises(ValueError, match="already registered and immutable"):
        registry.register(record_v1)


def test_model_version_preservation_on_upgrade():
    """Verify historical version preservation when registering upgraded models."""
    registry = InMemoryModelRegistry()

    v1 = ModelRecord(
        model_id="fluid_boundary_model",
        model_version="1.0.0",
        calibration_checksum="hash_v1",
        status=ModelStatus.DEPRECATED,
    )
    v2 = ModelRecord(
        model_id="fluid_boundary_model",
        model_version="2.0.0",
        calibration_checksum="hash_v2",
        status=ModelStatus.ACTIVE,
    )

    registry.register(v1)
    registry.register(v2)

    versions = registry.list_versions("fluid_boundary_model")
    assert len(versions) == 2

    active = registry.get_active("fluid_boundary_model")
    assert active is not None
    assert active.model_version == "2.0.0"

    old_v1 = registry.get("fluid_boundary_model", "1.0.0")
    assert old_v1 is not None
    assert old_v1.calibration_checksum == "hash_v1"
