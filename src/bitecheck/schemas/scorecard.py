"""
Pydantic Data Contract for BiteCheck Mathematical Scoring & Honesty Scorecard (Phase 5).
Structures penalty categorization, score bounds, badges, and consumer risk brackets.
"""

from typing import Literal
from pydantic import BaseModel, Field


class CategoryDeductions(BaseModel):
    """Breakdown of penalty deductions across key audit dimensions."""
    marketing_deception: int = Field(ge=0, le=50, default=0, description="Deductions for front vs back contradictions & claims")
    chemical_additives: int = Field(ge=0, le=50, default=0, description="Deductions for INS codes, high-GI syrups & chemical fractionations")
    nutritional_hazard: int = Field(ge=0, le=50, default=0, description="Deductions for high sodium, palm oil, trans fats, glycemic spike")
    statutory_violations: int = Field(ge=0, le=50, default=0, description="Deductions for veg/non-veg dot fraud, missing licenses")


class HonestyScorecard(BaseModel):
    """
    Final mathematical scorecard produced by the Scoring Engine.
    Guarantees strict 0-100 clamping, category transparency, and badge highlights.
    """
    product_name: str = Field(default="", description="Name of the audited product")
    brand_name: str = Field(default="", description="Brand manufacturer")
    
    raw_deductions: int = Field(ge=0, description="Total unbounded penalty points summed across all violations")
    capped_deductions: int = Field(ge=0, le=100, description="Category-capped total penalty points applied to score")
    
    honesty_score: int = Field(ge=0, le=100, description="Final clamped score: 100 - capped_deductions")
    
    bracket: Literal["CLEAN & TRANSPARENT", "MODERATE / MISLEADING", "HIGHLY DECEPTIVE"] = Field(
        description="Consumer risk classification tier"
    )
    color_code: Literal["GREEN", "AMBER", "RED"] = Field(
        description="Visual indicator: GREEN (85-100), AMBER (60-84), RED (0-59)"
    )
    
    category_breakdown: CategoryDeductions = Field(
        default_factory=CategoryDeductions,
        description="Segmented penalties by regulatory dimension"
    )
    
    critical_override_applied: bool = Field(
        default=False,
        description="True if critical statutory fraud (e.g. veg fraud, trans fat) forced a ceiling cap"
    )
    
    active_badges: list[str] = Field(
        default_factory=list,
        description="Standardized red-flag badge identifiers (e.g., 'ATTA_MAIDA_TRAP', 'PALM_OIL_ALERT')"
    )
    
    verdict_summary: str = Field(
        description="Concise plain-English executive summary of the score and risks"
    )
