"""Cognitia Deterministic Project Erector.

The erector consumes an externally accepted scaffold and generates a
deterministic filesystem project skeleton.

Architectural boundary:
    AcceptedScaffold (governance has accepted)
           ↓
    Deterministic Erector
           ↓
    Project Filesystem

The erector never creates, infers, or manufactures acceptance.
The erector never modifies Cognitia itself.
The erector never chooses implementation technology unless explicitly required.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from cognitia.project_spec.types import ScaffoldSpec
from erector.types import (
    AcceptedScaffold,
    ErectionResult,
    ErectionStatus,
    GeneratedArtifact,
    GeneratedArtifactType,
)


@runtime_checkable
class ProjectErector(Protocol):
    """Protocol for deterministic project erectors."""

    def erect(
        self,
        accepted_scaffold: AcceptedScaffold,
        target_directory: str,
    ) -> ErectionResult: ...


class DeterministicProjectErector:
    """Deterministic baseline project erector.

    Generates a structural project skeleton from an accepted scaffold.
    Does not generate business logic, domain models, or implementation code.
    Does not choose implementation technology unless explicitly required.
    Contains no AI/ML/network/filesystem dependencies beyond local directory creation.
    """

    def __init__(
        self,
        erector_id: str = "deterministic_project_erector",
        erector_version: str = "1.0.0",
    ) -> None:
        self.erector_id = erector_id
        self.erector_version = erector_version

    def erect(
        self,
        accepted_scaffold: AcceptedScaffold,
        target_directory: str,
    ) -> ErectionResult:
        """Erect a project skeleton from an accepted scaffold.

        Args:
            accepted_scaffold: externally accepted scaffold specification
            target_directory: explicit target location for the project

        Returns:
            ErectionResult with generated artifacts and manifest
        """
        findings: list[str] = []
        generated_artifacts: list[GeneratedArtifact] = []

        scaffold = accepted_scaffold.scaffold
        if not isinstance(scaffold, ScaffoldSpec):
            return ErectionResult(
                erection_id="",
                scaffold_id=accepted_scaffold.scaffold.spec_id if hasattr(accepted_scaffold.scaffold, 'spec_id') else "",
                target_directory=target_directory,
                status=ErectionStatus.FAILED.value,
                findings=["accepted_scaffold must wrap a ScaffoldSpec"],
            )

        scaffold_id = scaffold.spec_id or scaffold.id

        target = self._validate_target(target_directory, findings)
        if target is None:
            return ErectionResult(
                erection_id="",
                scaffold_id=scaffold_id,
                target_directory=target_directory,
                status=ErectionStatus.FAILED.value,
                findings=tuple(findings),
            )

        if not accepted_scaffold.acceptance_reference:
            findings.append("accepted_scaffold missing acceptance_reference")
            return ErectionResult(
                erection_id="",
                scaffold_id=scaffold_id,
                target_directory=target_directory,
                status=ErectionStatus.FAILED.value,
                findings=tuple(findings),
            )

        try:
            if target.exists():
                findings.append("target_directory must not exist")
                return ErectionResult(
                    erection_id="",
                    scaffold_id=scaffold_id,
                    target_directory=target_directory,
                    status=ErectionStatus.FAILED.value,
                    findings=tuple(findings),
                )
            target.mkdir(parents=True, exist_ok=False)

            root_manifest = self._build_root_manifest(scaffold_id, accepted_scaffold)
            manifest_path = target / "project-manifest.json"
            manifest_path.write_text(json.dumps(root_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            manifest_checksum = self._sha256(manifest_path.read_bytes())
            generated_artifacts.append(
                GeneratedArtifact(
                    artifact_id="manifest-root",
                    relative_path="project-manifest.json",
                    artifact_type=GeneratedArtifactType.MANIFEST.value,
                    content_checksum=manifest_checksum,
                    source_reference=scaffold_id,
                )
            )

            for boundary in scaffold.required_boundaries:
                artifact = self._generate_boundary(target, boundary, scaffold_id)
                generated_artifacts.append(artifact)

            for surface in scaffold.required_surfaces:
                artifact = self._generate_surface(target, surface, scaffold_id)
                generated_artifacts.append(artifact)

            for interface in scaffold.required_interfaces:
                artifact = self._generate_interface(target, interface, scaffold_id)
                generated_artifacts.append(artifact)

            for contract in scaffold.required_contract_surfaces:
                artifact = self._generate_contract(target, contract, scaffold_id)
                generated_artifacts.append(artifact)

            for test_surface in scaffold.required_test_surfaces:
                artifact = self._generate_test_surface(target, test_surface, scaffold_id)
                generated_artifacts.append(artifact)

            readme_path = target / "README.md"
            readme_content = self._build_readme(scaffold, scaffold_id, accepted_scaffold)
            readme_path.write_text(readme_content, encoding="utf-8")
            readme_checksum = self._sha256(readme_path.read_bytes())
            generated_artifacts.append(
                GeneratedArtifact(
                    artifact_id="readme-root",
                    relative_path="README.md",
                    artifact_type=GeneratedArtifactType.DOCUMENT.value,
                    content_checksum=readme_checksum,
                    source_reference=scaffold_id,
                )
            )

            erection_id = f"erection-{scaffold_id}"
            return ErectionResult(
                erection_id=erection_id,
                scaffold_id=scaffold_id,
                target_directory=str(target),
                status=ErectionStatus.SUCCESS.value,
                generated_artifacts=tuple(generated_artifacts),
                findings=tuple(findings),
            )

        except OSError as exc:
            findings.append(f"erection failed: {exc}")
            return ErectionResult(
                erection_id="",
                scaffold_id=scaffold_id,
                target_directory=target_directory,
                status=ErectionStatus.FAILED.value,
                findings=tuple(findings),
            )

    def _validate_target(self, target_directory: str, findings: list[str]) -> Path | None:
        if not target_directory or not target_directory.strip():
            findings.append("target_directory must not be empty")
            return None

        target = Path(target_directory).resolve()
        cognitia_src = Path(__file__).resolve().parents[2]
        try:
            target.relative_to(cognitia_src)
            findings.append(
                "target_directory must not be inside Cognitia source tree"
            )
            return None
        except ValueError:
            pass

        normalized = str(target).lower()
        if "src/cognitia" in normalized or "\\cognitia\\src" in normalized:
            findings.append("target_directory must not be inside Cognitia source tree")
            return None

        return target

    def _safe_relative_path(self, base: Path, name: str) -> str:
        safe = name.strip().replace("..", "_").replace("/", "_").replace("\\", "_")
        if not safe:
            safe = "unnamed"
        return safe

    def _build_root_manifest(
        self,
        scaffold_id: str,
        accepted_scaffold: AcceptedScaffold,
    ) -> dict[str, Any]:
        return {
            "erector_id": self.erector_id,
            "erector_version": self.erector_version,
            "scaffold_id": scaffold_id,
            "acceptance_reference": accepted_scaffold.acceptance_reference,
            "accepted_by": accepted_scaffold.accepted_by,
            "accepted_at": accepted_scaffold.accepted_at,
            "artifacts": [],
            "provenance": {
                "source_type": accepted_scaffold.provenance.source_type.value,
                "producer_id": accepted_scaffold.provenance.producer_id,
                "is_deterministic": accepted_scaffold.provenance.is_deterministic,
            },
        }

    def _sha256(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _write_artifact(
        self,
        target: Path,
        relative_path: str,
        content: str,
        artifact_type: str,
        source_reference: str,
    ) -> GeneratedArtifact:
        path = target / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        checksum = self._sha256(path.read_bytes())
        return GeneratedArtifact(
            artifact_id=f"artifact-{len(relative_path)}",
            relative_path=relative_path,
            artifact_type=artifact_type,
            content_checksum=checksum,
            source_reference=source_reference,
        )

    def _generate_boundary(
        self,
        target: Path,
        boundary: str,
        source_reference: str,
    ) -> GeneratedArtifact:
        name = self._safe_relative_path(target, boundary)
        relative_path = f"boundaries/{name}.md"
        content = f"# Boundary: {boundary}\n\nThis boundary is required by the accepted scaffold.\n"
        return self._write_artifact(target, relative_path, content, GeneratedArtifactType.CONTRACT.value, source_reference)

    def _generate_surface(
        self,
        target: Path,
        surface: str,
        source_reference: str,
    ) -> GeneratedArtifact:
        name = self._safe_relative_path(target, surface)
        relative_path = f"surfaces/{name}.md"
        content = f"# Surface: {surface}\n\nThis surface is required by the accepted scaffold.\n"
        return self._write_artifact(target, relative_path, content, GeneratedArtifactType.CONTRACT.value, source_reference)

    def _generate_interface(
        self,
        target: Path,
        interface: str,
        source_reference: str,
    ) -> GeneratedArtifact:
        name = self._safe_relative_path(target, interface)
        relative_path = f"interfaces/{name}.md"
        content = (
            f"# Interface: {interface}\n\n"
            f"This interface surface is required by the accepted scaffold.\n"
            f"Implementation technology is not prescribed here.\n"
        )
        return self._write_artifact(target, relative_path, content, GeneratedArtifactType.INTERFACE_SURFACE.value, source_reference)

    def _generate_contract(
        self,
        target: Path,
        contract: str,
        source_reference: str,
    ) -> GeneratedArtifact:
        name = self._safe_relative_path(target, contract)
        relative_path = f"contracts/{name}.md"
        content = f"# Contract: {contract}\n\nThis contract surface is required by the accepted scaffold.\n"
        return self._write_artifact(target, relative_path, content, GeneratedArtifactType.CONTRACT.value, source_reference)

    def _generate_test_surface(
        self,
        target: Path,
        test_surface: str,
        source_reference: str,
    ) -> GeneratedArtifact:
        name = self._safe_relative_path(target, test_surface)
        relative_path = f"tests/{name}.md"
        content = f"# Test Surface: {test_surface}\n\nThis test surface is required by the accepted scaffold.\n"
        return self._write_artifact(target, relative_path, content, GeneratedArtifactType.TEST_SURFACE.value, source_reference)

    def _build_readme(
        self,
        scaffold: ScaffoldSpec,
        scaffold_id: str,
        accepted_scaffold: AcceptedScaffold,
    ) -> str:
        lines = [
            f"# Project Skeleton",
            f"",
            f"Generated from accepted scaffold: {scaffold_id}",
            f"Acceptance reference: {accepted_scaffold.acceptance_reference}",
            f"",
            f"## Required Boundaries",
        ]
        lines.extend(f"- {b}" for b in scaffold.required_boundaries)
        lines.append("")
        lines.append("## Required Surfaces")
        lines.extend(f"- {s}" for s in scaffold.required_surfaces)
        lines.append("")
        lines.append("## Required Interfaces")
        lines.extend(f"- {i}" for i in scaffold.required_interfaces)
        lines.append("")
        lines.append("## Required Contracts")
        lines.extend(f"- {c}" for c in scaffold.required_contract_surfaces)
        lines.append("")
        lines.append("## Required Test Surfaces")
        lines.extend(f"- {t}" for t in scaffold.required_test_surfaces)
        lines.append("")
        lines.append("## Implementation Freedoms")
        lines.extend(f"- {f}" for f in scaffold.implementation_freedoms or ["implementation choice is unrestricted"])
        lines.append("")
        lines.append("## Prohibited Structural Patterns")
        lines.extend(f"- {p}" for p in scaffold.prohibited_structural_patterns)
        lines.append("")
        lines.append("## Traceability")
        lines.extend(f"- {tr}" for tr in scaffold.traceability)
        lines.append("")
        return "\n".join(lines)
