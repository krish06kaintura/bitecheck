"""
Pydantic Data Contract for Deterministic Food Audit (Agent 2 Output).
Structures compliance violations, whole-pack multipliers, and provisional honesty scoring.
"""

from typing import Literal
from pydantic import BaseModel, Field


class AuditViolation(BaseModel):
    """Individual statutory or food science violation."""
    rule_name: str = Field(description="Name of the evaluated check (e.g., 'Hidden Sugar Detection')")
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(description="Violation risk level")
    penalty_points: int = Field(ge=0, le=100, description="Deduction applied to the Honesty Score")
    reason: str = Field(description="Plain-English explanation of why this rule triggered")
    detected_snippet: str = Field(description="Specific ingredient or claim that caused the violation")


class AuditReport(BaseModel):
    """Complete structured audit produced deterministically by Agent 2."""
    whole_pack_multiplier: float = Field(ge=1.0, description="Net weight divided by serving size")
    whole_pack_calories_kcal: float = Field(ge=0.0)
    whole_pack_sugar_g: float = Field(ge=0.0)
    whole_pack_sodium_mg: float = Field(ge=0.0)

    carb_to_fiber_ratio: float | None = Field(default=None, description="Total carbs divided by dietary fiber")
    glycemic_spike_alert: bool = Field(default=False, description="True if carb:fiber > 10:1")

    nova_group: Literal[1, 2, 3, 4] = Field(default=4, description="WHO NOVA Ultra-Processed Food Level (1-4)")
    icmr_sodium_daily_pct: float = Field(ge=0.0, description="Percentage of ICMR 2,000mg sodium daily quota")
    icmr_sugar_daily_pct: float = Field(ge=0.0, description="Percentage of ICMR 25g added sugar quota")

    violations: list[AuditViolation] = Field(default_factory=list)
    total_penalty_deduction: int = Field(ge=0, le=100)
    provisional_honesty_score: int = Field(ge=0, le=100)
