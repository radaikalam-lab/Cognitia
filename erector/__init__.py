"""Cognitia Deterministic Project Erector.

Provides deterministic project erection from an accepted scaffold.
The erector never creates acceptance; it only consumes externally
provided acceptance evidence.
"""

from __future__ import annotations

from erector.project_erector import (
    DeterministicProjectErector,
    ProjectErector,
)
from erector.types import (
    AcceptedScaffold,
    ErectionResult,
    ErectionStatus,
    GeneratedArtifact,
    GeneratedArtifactType,
)

__all__ = [
    "AcceptedScaffold",
    "DeterministicProjectErector",
    "ErectionResult",
    "ErectionStatus",
    "GeneratedArtifact",
    "GeneratedArtifactType",
    "ProjectErector",
]
