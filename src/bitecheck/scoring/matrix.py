"""
BiteCheck Mathematical Scoring Matrix & Regulatory Configuration (Phase 5).
Defines category bounds, penalty weights, badge identifiers, and statutory overrides.
"""

# Regulatory Category Maximum Deduction Caps
# Prevents any single dimension from disproportionately overwhelming the multi-agent score
CATEGORY_CAPS = {
    "marketing_deception": 40,
    "chemical_additives": 35,
    "nutritional_hazard": 45,
    "statutory_violations": 40,
}

# Score Tier Thresholds
SCORE_TIERS = {
    "CLEAN_MIN": 85,       # 85 - 100: Clean & Transparent (Green)
    "MODERATE_MIN": 60,    # 60 - 84:  Moderate / Misleading (Amber)
    # 0 - 59:   Highly Deceptive / Ultra-Processed (Red)
}

# Critical Override Cap: If high-risk statutory fraud is present (e.g. Veg Fraud, Industrial Trans Fat),
# the final score cannot exceed this ceiling regardless of other positive nutrients.
CRITICAL_CEILING_CAP = 49

# Mapping of violation rule substrings to categorical dimensions
RULE_CATEGORY_MAP = {
    # Marketing Deception
    "grain purity": "marketing_deception",
    "serving size manipulation": "marketing_deception",
    "claim contradiction": "marketing_deception",
    "atta vs maida": "marketing_deception",
    "misleading claim": "marketing_deception",

    # Chemical Additives
    "sugar fractionation": "chemical_additives",
    "high glycemic index additive": "chemical_additives",
    "ins": "chemical_additives",
    "caramel": "chemical_additives",
    "additive": "chemical_additives",
    "chemical": "chemical_additives",

    # Nutritional Hazard
    "palm oil": "nutritional_hazard",
    "sodium limit": "nutritional_hazard",
    "added sugar limit": "nutritional_hazard",
    "trans fat": "nutritional_hazard",
    "glycemic spike": "nutritional_hazard",
    "vanaspati": "nutritional_hazard",

    # Statutory Violations
    "veg fraud": "statutory_violations",
    "dietary dot": "statutory_violations",
    "fssai license": "statutory_violations",
    "mandatory markings": "statutory_violations",
}

# Standardized Red-Flag Badge Map
BADGE_RULES = [
    {
        "badge": "ATTA_MAIDA_TRAP",
        "keywords": ["grain purity", "atta vs maida"],
        "description": "Front claims healthy whole grains but primary ingredient by weight is Refined Maida.",
    },
    {
        "badge": "HIDDEN_SUGAR_SPIKE",
        "keywords": ["sugar fractionation", "high glycemic index", "maltodextrin", "liquid glucose"],
        "description": "Conceals disguised sugars or ultra-high GI syrups (e.g. Maltodextrin GI 110).",
    },
    {
        "badge": "PALM_OIL_ALERT",
        "keywords": ["palm oil", "palmolein", "fractionated palm"],
        "description": "Uses cheap, highly saturated Palmolein or palm fat fractions.",
    },
    {
        "badge": "HIGH_SODIUM_BOMB",
        "keywords": ["sodium limit"],
        "description": "Delivers over 50% of the entire ICMR 2,000mg daily sodium limit in a single pack.",
    },
    {
        "badge": "CHEMICAL_COCKTAIL",
        "keywords": ["ins", "caramel", "additive"],
        "description": "Formulated with synthetic colors or high-caution statutory chemical additives.",
    },
    {
        "badge": "GLYCEMIC_SPIKE_RISK",
        "keywords": ["glycemic spike", "carb to fiber"],
        "description": "Severe carbohydrate-to-fiber ratio (> 10:1) triggering rapid blood glucose surge.",
    },
    {
        "badge": "SERVING_SIZE_TRAP",
        "keywords": ["serving size manipulation"],
        "description": "Unrealistic tiny portion size reports low calories while whole pack is 2x-5x larger.",
    },
    {
        "badge": "TRANS_FAT_ALERT",
        "keywords": ["trans fat", "hydrogenated"],
        "description": "Contains industrial trans fatty acids or partially hydrogenated vegetable oils.",
    },
    {
        "badge": "VEG_FRAUD_ALERT",
        "keywords": ["veg fraud", "dietary dot"],
        "description": "Displays Green Vegetarian dot but contains animal-derived ingredients.",
    },
]
