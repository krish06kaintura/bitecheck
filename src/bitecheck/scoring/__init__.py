"""
BiteCheck Mathematical Scoring Package (Phase 5).
Exports ScoringEngine, score tiers, and matrix configurations.
"""

from bitecheck.scoring.engine import ScoringEngine
from bitecheck.scoring.matrix import (
    CATEGORY_CAPS,
    SCORE_TIERS,
    CRITICAL_CEILING_CAP,
    BADGE_RULES,
)

__all__ = [
    "ScoringEngine",
    "CATEGORY_CAPS",
    "SCORE_TIERS",
    "CRITICAL_CEILING_CAP",
    "BADGE_RULES",
]
