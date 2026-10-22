"""
Pydantic Data Contracts for Agent 4: Transparency Scorecard & Clean Swaps (Phase 8).
Defines the final consumer-facing audit payload:
- Traceable evidence chain linking label claims to scientific violations
- Whole-pack consumption reality pills
- Verified clean Indian FMCG brand swaps
"""

from typing import Literal
from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    """Traceable evidence linking a specific red-flag badge to label text and regulatory rules."""
    badge: str = Field(description="Standardized badge token (e.g. 'ATTA_MAIDA_TRAP', 'PALM_OIL_ALERT')")
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(description="Regulatory risk level")
    penalty_deduction: int = Field(ge=0, description="Points subtracted from honesty score for this item")
    scientific_reason: str = Field(description="Plain-English explanation of the health or regulatory hazard")
    label_evidence_snippet: str = Field(description="Exact snippet extracted from ingredients or claims")


class CleanSwapItem(BaseModel):
    """Healthier, transparent Indian FMCG alternative available on quick commerce."""
    brand: str = Field(description="Clean brand name (e.g. 'The Whole Truth', 'Slurrp Farm')")
    product: str = Field(description="Product title")
    why_clean: str = Field(description="Explanation of why this product is superior (e.g. zero palm oil, 100% whole grains)")
    platforms: list[str] = Field(default_factory=list, description="Available quick-commerce channels (e.g. Blinkit, Zepto, Instamart)")


class WholePackReality(BaseModel):
    """Side-by-side comparison of deceptive per-serving claims vs whole-pack consumption reality."""
    serving_size_g: float
    net_weight_g: float
    multiplier: float = Field(description="Net weight divided by serving size (e.g. 5.0x)")
    
    # Nutritional reality: Advertised per serving vs Actual consumed per pack
    calories_advertised: float
    calories_whole_pack: float
    
    sugar_advertised_g: float
    sugar_whole_pack_g: float
    
    sodium_advertised_mg: float
    sodium_whole_pack_mg: float
    
    carb_to_fiber_ratio: float | None = Field(default=None)
    glycemic_spike_alert: bool = Field(default=False)
    icmr_sodium_daily_pct: float = Field(default=0.0)


class ProductTransparencyCard(BaseModel):
    """
    Final Master Scorecard emitted by Agent 4.
    The primary data contract consumed by the Phase 9 Web Dashboard and API layers.
    """
    product_name: str
    brand_name: str
    honesty_score: int = Field(ge=0, le=100)
    bracket: Literal["CLEAN & TRANSPARENT", "MODERATE / MISLEADING", "HIGHLY DECEPTIVE"]
    color_code: Literal["GREEN", "AMBER", "RED"]
    verdict_summary: str
    
    is_clean_product: bool = Field(description="True if product scored >= 85 in the Clean & Transparent tier")
    
    # Dimensional breakdown & Badges
    active_badges: list[str] = Field(default_factory=list)
    whole_pack_reality: WholePackReality
    evidence_chain: list[EvidenceItem] = Field(default_factory=list)
    
    # Consumer Sentiment Pulse (Agent 3 Intelligence)
    sentiment_pulse: dict = Field(
        default_factory=dict,
        description="Condensed sentiment metrics (score, overall tier, authenticity, digestive distress alert)"
    )
    
    # Clean Brand Recommendations
    clean_swaps: list[CleanSwapItem] = Field(
        default_factory=list,
        description="Recommended clean Indian alternatives if product is deceptive or moderate"
    )
    
    critical_override_applied: bool = Field(default=False)
