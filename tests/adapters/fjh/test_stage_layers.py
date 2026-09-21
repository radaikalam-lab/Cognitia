"""Tests for FJH Stage Layer Separation and No Domain Leakage."""

from __future__ import annotations

import pytest

from cognitia.abi.types import (
    Action,
    CognitiveObject,
    Decision,
    Observation,
    Outcome,
)
from cognitia.epistemic.types import Evidence, Hypothesis
from cognitia.provenance.record import ProvenanceRecord
from adapters.fjh.events import FJHEvent, FJHStage
from adapters.fjh.translator import FJHEventTranslator
from adapters.fjh.advisory import FJHAdvisory
from adapters.fjh.experience import FJHLifecycleType
from adapters.fjh.schemas import FJH_SCHEMA_VERSION


class TestFJHStageLayerSeparation:
    """Validate that FJH stages remain in adapter boundary and core is domain-neutral."""

    def test_fjh_stage_not_imported_in_core(self) -> None:
        """FJHStage must not be importable from cognitia core modules."""
        import cognitia.abi.types as abi_types
        assert not hasattr(abi_types, "FJHStage")

        import cognitia.provenance.record as prov
        assert not hasattr(prov, "FJHStage")

        import cognitia.experience.record as exp
        assert not hasattr(exp, "FJHStage")

    def test_fjh_event_not_imported_in_core(self) -> None:
        """FJHEvent must not be importable from cognitia core modules."""
        import cognitia.abi.types as abi_types
        assert not hasattr(abi_types, "FJHEvent")

    def test_fjh_advisory_not_imported_in_core(self) -> None:
        """FJHAdvisory must not be importable from cognitia core modules."""
        import cognitia.abi.types as abi_types
        assert not hasattr(abi_types, "FJHAdvisory")

    def test_core_abi_has_no_fjh_fields(self) -> None:
        """Core ABI types must not contain FJH-specific field names."""
        obs_fields = {f.name for f in Observation.__dataclass_fields__.values()}
        assert "stage" not in obs_fields
        assert "experiment_id" not in obs_fields
        assert "precursor_id" not in obs_fields
        assert "chamber_id" not in obs_fields

    def test_core_provenance_has_no_fjh_fields(self) -> None:
        """ProvenanceRecord must not contain FJH-specific field names."""
        prov_fields = {f.name for f in ProvenanceRecord.__dataclass_fields__.values()}
        assert "stage" not in prov_fields
        assert "experiment_id" not in prov_fields

    def test_six_stages_are_distinct(self) -> None:
        """The six FJH lifecycle stages must be unique and ordered."""
        stages = list(FJHStage)
        assert len(stages) == 6
        assert len(set(stages)) == 6
        assert FJHStage.REQUESTED.value == "FJH_REQUESTED"
        assert FJHStage.VALIDATED.value == "FJH_VALIDATED"
        assert FJHStage.EXECUTED.value == "FJH_EXECUTED"
        assert FJHStage.MEASURED.value == "FJH_MEASURED"
        assert FJHStage.DERIVED.value == "FJH_DERIVED"
        assert FJHStage.INTERPRETED.value == "FJH_INTERPRETED"

    def test_fjh_adapter_reuses_core_abi_types(self) -> None:
        """FJH adapter must produce core ABI types, not custom subclasses."""
        event = FJHEvent(
            stage=FJHStage.REQUESTED,
            experiment_id="FJH-EXP-2026-001",
            payload={},
        )
        obs = FJHEventTranslator.translate(event)
        assert type(obs) is Observation
        assert isinstance(obs, CognitiveObject)

    def test_schema_version_constant(self) -> None:
        """FJH schemas must declare their own schema version."""
        assert FJH_SCHEMA_VERSION == "1.0.0"

    def test_fjh_lifecycle_types_are_distinct(self) -> None:
        types = list(FJHLifecycleType)
        assert len(types) == 5
        assert len(set(types)) == 5

    def test_no_external_dependencies_in_adapter(self) -> None:
        """Verify adapter modules import only stdlib + cognitia core."""
        import adapters.fjh.events as events_mod
        import adapters.fjh.translator as translator_mod
        import adapters.fjh.schemas as schemas_mod
        import adapters.fjh.experience as experience_mod
        import adapters.fjh.advisory as advisory_mod
        import adapters.fjh.client as client_mod

        stdlib_prefixes = (
            "adapters.fjh",
            "cognitia",
            "builtins",
            "__",
            "typing",
            "dataclasses",
            "enum",
            "json",
            "_frozen_importlib",
        )

        for mod in [
            events_mod,
            translator_mod,
            schemas_mod,
            experience_mod,
            advisory_mod,
            client_mod,
        ]:
            for name in dir(mod):
                obj = getattr(mod, name)
                if hasattr(obj, "__module__"):
                    module = getattr(obj, "__module__", "") or ""
                    if module.startswith("_"):
                        continue
                    assert any(module.startswith(prefix) for prefix in stdlib_prefixes), (
                        f"Unexpected external dependency in {mod.__name__}: {name} from {module}"
                    )
