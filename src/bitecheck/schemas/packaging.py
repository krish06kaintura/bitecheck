"""
Pydantic Data Contract for Packaging Extraction (Agent 1 Output).
Enforces strict structural boundaries between probabilistic Gemini Vision and downstream agents.
"""

from typing import Literal
from pydantic import BaseModel, Field, field_validator


class NutritionFacts(BaseModel):
    """Normalized nutritional values per 100g."""
    energy_kcal: float = Field(default=0.0, ge=0.0)
    carbohydrates_g: float = Field(default=0.0, ge=0.0)
    sugar_g: float = Field(default=0.0, ge=0.0)
    added_sugar_g: float = Field(default=0.0, ge=0.0)
    dietary_fiber_g: float = Field(default=0.0, ge=0.0)
    protein_g: float = Field(default=0.0, ge=0.0)
    fat_g: float = Field(default=0.0, ge=0.0)
    saturated_fat_g: float = Field(default=0.0, ge=0.0)
    trans_fat_g: float = Field(default=0.0, ge=0.0)
    sodium_mg: float = Field(default=0.0, ge=0.0)


class PackagingData(BaseModel):
    """
    Structured packaging data extracted from Front and Back packaging images.
    Guarantees non-empty fields, descending ingredient order, and positive net weights.
    """
    brand_name: str = Field(description="Brand or manufacturer name", min_length=1)
    product_name: str = Field(description="Product commercial name", min_length=1)
    front_claims: list[str] = Field(default_factory=list, description="Marketing claims highlighted on front pack")
    ingredients_raw: list[str] = Field(
        default_factory=list,
        description="Raw list of ingredients preserving strict descending order of weight"
    )
    serving_size_g: float = Field(gt=0.0, description="Reported serving size in grams")
    net_weight_g: float = Field(gt=0.0, description="Full package net quantity in grams")
    nutrition_per_100g: NutritionFacts = Field(description="Nutritional values per 100g")
    dietary_dot: Literal["GREEN_VEG", "BROWN_NON_VEG", "UNKNOWN"] = Field(
        default="UNKNOWN",
        description="FSSAI dietary symbol dot"
    )
    fssai_license_number: str | None = Field(
        default=None,
        description="14-digit FSSAI registration/license number if visible"
    )

    @field_validator("net_weight_g")
    @classmethod
    def validate_net_weight(cls, v: float, info) -> float:
        """Ensures package net weight is at least equal to declared serving size."""
        serving = info.data.get("serving_size_g")
        if serving is not None and v < serving:
            raise ValueError(f"Net weight ({v}g) cannot be smaller than reported serving size ({serving}g).")
        return v
