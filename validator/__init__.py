"""Cognitia Independent Deterministic Validator.

Provides project directional programming conformance validation
independent of Cognitia's reasoning authority.

The validator consumes public project_spec artifacts and produces
structured evidence. It does not approve, authorize, or execute.
"""

from __future__ import annotations

from validator.project_spec_validator import (
    DeterministicProjectSpecValidator,
    ProjectSpecValidator,
)
from validator.types import (
    ValidationFinding,
    ValidationResult,
    ValidationStatus,
)

__all__ = [
    "DeterministicProjectSpecValidator",
    "ProjectSpecValidator",
    "ValidationFinding",
    "ValidationResult",
    "ValidationStatus",
]
