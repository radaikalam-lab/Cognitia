"""PrintForge Cross-Domain Controlled Pilot.

This package contains the PrintForge-specific direction extraction adapter.
It translates PrintForge architectural intent into generic DP artifacts.

The generic DP kernel remains domain-neutral. This package is explicitly
the boundary where PrintForge-specific knowledge is translated.
"""

from __future__ import annotations

from pilot_printforge.direction_extraction import PrintForgeDirectionExtractor

__all__ = ["PrintForgeDirectionExtractor"]
