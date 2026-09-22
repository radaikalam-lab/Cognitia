"""Cognitia Deterministic Project Erector Tests."""

from __future__ import annotations

import hashlib
import json
import pathlib

import pytest

from cognitia.project_spec.types import ScaffoldSpec
from erector.project_erector import DeterministicProjectErector
from erector.types import (
    AcceptedScaffold,
    ErectionResult,
    ErectionStatus,
    GeneratedArtifact,
    GeneratedArtifactType,
)


def _make_scaffold() -> ScaffoldSpec:
    return ScaffoldSpec(
        spec_id="scf-pilot",
        required_boundaries=["provider_boundary", "observation_boundary"],
        required_surfaces=["core_surface", "interface_surface"],
        required_interfaces=["provider_interface", "observation_interface"],
        required_contract_surfaces=["authority_contract"],
        required_test_surfaces=["core_test_surface", "integration_test_surface"],
        prohibited_structural_patterns=["monolith", "circular_dependency"],
        implementation_freedoms=["any_persistence", "any_test_framework", "any_interface_technology"],
        traceability=["PROJECT-AUTH-001"],
    )


def _make_accepted_scaffold(
    scaffold: ScaffoldSpec | None = None,
    acceptance_reference: str = "ACCEPT-001",
    accepted_by: str = "governance",
    accepted_at: str = "2026-09-22T00:00:00+00:00",
) -> AcceptedScaffold:
    return AcceptedScaffold(
        scaffold=scaffold or _make_scaffold(),
        acceptance_reference=acceptance_reference,
        accepted_by=accepted_by,
        accepted_at=accepted_at,
    )


class TestDeterministicProjectErector:
    def test_erector_attributes(self) -> None:
        erector = DeterministicProjectErector(
            erector_id="custom",
            erector_version="2.0.0",
        )
        assert erector.erector_id == "custom"
        assert erector.erector_version == "2.0.0"

    def test_erect_returns_success(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        result = erector.erect(accepted, str(tmp_path / "project"))
        assert result.status == ErectionStatus.SUCCESS.value

    def test_erect_creates_target_directory(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "new_project"
        assert not target.exists()
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        assert target.exists()
        assert target.is_dir()

    def test_erect_generates_manifest(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        manifest = target / "project-manifest.json"
        assert manifest.exists()
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["scaffold_id"] == "scf-pilot"
        assert data["acceptance_reference"] == "ACCEPT-001"

    def test_erect_generates_readme(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        readme = target / "README.md"
        assert readme.exists()
        content = readme.read_text(encoding="utf-8")
        assert "provider_boundary" in content
        assert "any_persistence" in content

    def test_erect_generates_artifacts_for_boundaries(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        boundary_artifacts = [a for a in result.generated_artifacts if "boundaries/" in a.relative_path]
        assert len(boundary_artifacts) == 2

    def test_erect_generates_artifacts_for_surfaces(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        surface_artifacts = [a for a in result.generated_artifacts if "surfaces/" in a.relative_path]
        assert len(surface_artifacts) == 2

    def test_erect_generates_artifacts_for_interfaces(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        interface_artifacts = [a for a in result.generated_artifacts if "interfaces/" in a.relative_path]
        assert len(interface_artifacts) == 2

    def test_erect_generates_artifacts_for_contracts(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        contract_artifacts = [a for a in result.generated_artifacts if "contracts/" in a.relative_path]
        assert len(contract_artifacts) == 1

    def test_erect_generates_artifacts_for_test_surfaces(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        test_artifacts = [a for a in result.generated_artifacts if "tests/" in a.relative_path]
        assert len(test_artifacts) == 2

    def test_erect_artifacts_have_checksums(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        for artifact in result.generated_artifacts:
            if artifact.artifact_type == GeneratedArtifactType.MANIFEST.value:
                continue
            path = target / artifact.relative_path
            assert path.exists()
            actual_checksum = hashlib.sha256(path.read_bytes()).hexdigest()
            assert artifact.content_checksum == actual_checksum

    def test_erect_deterministic_output(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target1 = tmp_path / "project1"
        target2 = tmp_path / "project2"
        r1 = erector.erect(accepted, str(target1))
        r2 = erector.erect(accepted, str(target2))
        assert r1.status == r2.status == ErectionStatus.SUCCESS.value
        assert len(r1.generated_artifacts) == len(r2.generated_artifacts)
        for a1, a2 in zip(sorted(r1.generated_artifacts, key=lambda a: a.relative_path), sorted(r2.generated_artifacts, key=lambda a: a.relative_path)):
            assert a1.relative_path == a2.relative_path
            assert a1.artifact_type == a2.artifact_type
            assert a1.content_checksum == a2.content_checksum
            assert a1.source_reference == a2.source_reference

    def test_erect_empty_target_directory_fails(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        target.mkdir()
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.FAILED.value
        assert any("target_directory must not exist" in f for f in result.findings)

    def test_erect_non_empty_target_directory_fails(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        target.mkdir()
        (target / "existing_file.txt").write_text("content", encoding="utf-8")
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.FAILED.value
        assert any("target_directory must not exist" in f for f in result.findings)

    def test_erect_missing_acceptance_reference_fails(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        scaffold = _make_scaffold()
        accepted = AcceptedScaffold(scaffold=scaffold, acceptance_reference="", accepted_by="", accepted_at="")
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.FAILED.value
        assert any("missing acceptance_reference" in f for f in result.findings)

    def test_erect_does_not_create_acceptance(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert not hasattr(result, "accept")
        assert not hasattr(result, "approve")
        assert not hasattr(result, "authorize")

    def test_erect_target_inside_cognitia_src_fails(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        cognitia_src = pathlib.Path(__file__).resolve().parents[2] / "src" / "cognitia"
        if not cognitia_src.exists():
            cognitia_src = pathlib.Path(__file__).resolve().parents[2] / "cognitia" / "src"
        target = cognitia_src / "erector_test_target"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.FAILED.value

    def test_erect_preserves_implementation_freedom(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        scaffold = _make_scaffold()
        accepted = _make_accepted_scaffold(scaffold)
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        readme = (target / "README.md").read_text(encoding="utf-8")
        assert "any_persistence" in readme
        assert "any_test_framework" in readme
        assert "any_interface_technology" in readme

    def test_erect_prohibits_structural_patterns(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        readme = (target / "README.md").read_text(encoding="utf-8")
        assert "monolith" in readme
        assert "circular_dependency" in readme

    def test_erect_no_domain_terms_in_generated_content(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        forbidden = ["PrintForge", "AcoustiForge", "FJH", "Frappe", "printer", "speaker", "reactor", "PostgreSQL", "FastAPI"]
        for artifact in result.generated_artifacts:
            path = target / artifact.relative_path
            if path.exists():
                content = path.read_text(encoding="utf-8").lower()
                for term in forbidden:
                    assert term.lower() not in content, f"Forbidden term '{term}' found in {artifact.relative_path}"

    def test_erect_result_never_returns_accepted_status(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status != "accepted"
        assert result.status != "approved"
        assert result.status != "authorized"
        assert result.status != "executed"
        assert result.status != "deployed"

    def test_erect_manifest_contains_erector_info(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        manifest = json.loads((target / "project-manifest.json").read_text(encoding="utf-8"))
        assert manifest["erector_id"] == "deterministic_project_erector"
        assert manifest["erector_version"] == "1.0.0"


class TestErectorSafetyBoundaries:
    def test_erector_has_no_accept_method(self) -> None:
        erector = DeterministicProjectErector()
        assert not hasattr(erector, "accept")
        assert not hasattr(erector, "approve")
        assert not hasattr(erector, "authorize")
        assert not hasattr(erector, "deploy")
        assert not hasattr(erector, "execute")

    def test_erector_does_not_modify_cognitia(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        cognitia_src = pathlib.Path(__file__).resolve().parents[2] / "src" / "cognitia"
        if not cognitia_src.exists():
            cognitia_src = pathlib.Path(__file__).resolve().parents[2] / "cognitia" / "src"
        assert not any(cognitia_src in p.parents for p in target.rglob("*") if p.is_file())


class TestErectorDirectionVsImplementation:
    def test_erector_preserves_unrestricted_technology_freedom(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        scaffold = ScaffoldSpec(
            spec_id="scf-free",
            required_boundaries=["provider_boundary"],
            required_surfaces=["core_surface"],
            required_interfaces=["provider_interface"],
            implementation_freedoms=["any_persistence", "any_framework", "any_interface_technology"],
        )
        accepted = AcceptedScaffold(
            scaffold=scaffold,
            acceptance_reference="ACCEPT-FREE",
            accepted_by="governance",
            accepted_at="2026-09-22T00:00:00+00:00",
        )
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        readme = (target / "README.md").read_text(encoding="utf-8")
        forbidden_tech = ["python", "fastapi", "postgresql", "docker", "kubernetes", "rest", "graphql"]
        for term in forbidden_tech:
            assert term not in readme.lower()

    def test_erector_does_not_prescribe_frameworks(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        scaffold = _make_scaffold()
        accepted = _make_accepted_scaffold(scaffold)
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        for artifact in result.generated_artifacts:
            path = target / artifact.relative_path
            if path.exists() and path.is_file():
                content = path.read_text(encoding="utf-8").lower()
                forbidden = ["class ", "def ", "import ", "fastapi", "django", "flask"]
                for term in forbidden:
                    assert term not in content, f"Erector prescribed implementation: {term} in {artifact.relative_path}"


class TestErectorDomainNeutrality:
    FORBIDDEN_TERMS = [
        "PrintForge",
        "AcoustiForge",
        "FJH",
        "Frappe",
        "ERPNext",
        "speaker",
        "printer",
        "reactor",
        "farm",
        "actuator",
        "Oracle",
        "FastAPI",
        "PostgreSQL",
        "Django",
        "REST",
        "HTTP",
        "SalesOrder",
        "PurchaseOrder",
        "Invoice",
        "Customer",
        "DocType",
    ]

    def test_erector_source_no_forbidden_terms(self) -> None:
        src_dir = pathlib.Path(__file__).resolve().parents[2] / "erector"
        violations = []
        for file_path in src_dir.rglob("*.py"):
            text = file_path.read_text(encoding="utf-8")
            for term in self.FORBIDDEN_TERMS:
                if term in text:
                    violations.append((file_path, term))
        assert violations == [], f"Forbidden domain terms in erector source: {violations}"

    def test_generated_artifacts_no_forbidden_terms(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        violations = []
        for artifact in result.generated_artifacts:
            path = target / artifact.relative_path
            if path.exists() and path.is_file():
                text = path.read_text(encoding="utf-8")
                for term in self.FORBIDDEN_TERMS:
                    if term in text:
                        violations.append((artifact.relative_path, term))
        assert violations == [], f"Forbidden domain terms in generated artifacts: {violations}"


class TestErectorDeterminism:
    def test_repeated_erection_semantically_identical(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target1 = tmp_path / "project1"
        target2 = tmp_path / "project2"
        r1 = erector.erect(accepted, str(target1))
        r2 = erector.erect(accepted, str(target2))
        assert r1.status == r2.status == ErectionStatus.SUCCESS.value
        assert len(r1.generated_artifacts) == len(r2.generated_artifacts)
        artifacts1 = sorted(r1.generated_artifacts, key=lambda a: a.relative_path)
        artifacts2 = sorted(r2.generated_artifacts, key=lambda a: a.relative_path)
        for a1, a2 in zip(artifacts1, artifacts2):
            assert a1.relative_path == a2.relative_path
            assert a1.artifact_type == a2.artifact_type
            assert a1.content_checksum == a2.content_checksum
            assert a1.source_reference == a2.source_reference
        files1 = sorted(str(p.relative_to(target1)) for p in target1.rglob("*") if p.is_file())
        files2 = sorted(str(p.relative_to(target2)) for p in target2.rglob("*") if p.is_file())
        assert files1 == files2
        for f1, f2 in zip(files1, files2):
            content1 = (target1 / f1).read_bytes()
            content2 = (target2 / f2).read_bytes()
            assert content1 == content2

    def test_manifest_serialization_deterministic(self, tmp_path: pathlib.Path) -> None:
        erector = DeterministicProjectErector()
        accepted = _make_accepted_scaffold()
        target = tmp_path / "project"
        result = erector.erect(accepted, str(target))
        assert result.status == ErectionStatus.SUCCESS.value
        manifest_path = target / "project-manifest.json"
        first = manifest_path.read_text(encoding="utf-8")
        second = manifest_path.read_text(encoding="utf-8")
        assert first == second
