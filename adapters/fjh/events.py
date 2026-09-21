"""Flash Joule Heating (FJH) Event Vocabulary and Schemas.

Defines standard FJH experiment lifecycle stages and data containers.
This file lives strictly in the adapter boundary and is not imported by Cognitia Core.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class FJHStage(str, enum.Enum):
    """Standard Flash Joule Heating experiment lifecycle stages."""

    REQUESTED = "FJH_REQUESTED"
    VALIDATED = "FJH_VALIDATED"
    EXECUTED = "FJH_EXECUTED"
    MEASURED = "FJH_MEASURED"
    DERIVED = "FJH_DERIVED"
    INTERPRETED = "FJH_INTERPRETED"


@dataclass(frozen=True)
class FJHEvent:
    """Container for an incoming Flash Joule Heating domain event."""

    stage: FJHStage | str
    experiment_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    precursor_id: str | None = None
    chamber_id: str | None = None
    operator_id: str = "fjh_operator"
    timestamp: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
