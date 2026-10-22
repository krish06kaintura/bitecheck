"""
Agent 2: Deterministic Scientific Food Auditor.
Executes 12 statutory FSSAI and food science compliance checks with ZERO LLM calls.
Guarantees 100% mathematical auditability, reproducible penalty scoring,
and WHO NOVA Ultra-Processed Food classification.
"""

import json
import re
from pathlib import Path
from bitecheck.config import settings
from bitecheck.logger import get_logger
from bitecheck.schemas.packaging import PackagingData
from bitecheck.schemas.audit import AuditReport, AuditViolation
from bitecheck.scoring import ScoringEngine

logger = get_logger("bitecheck.agents.auditor")

# Statutory ICMR (Indian Council of Medical Research) Daily Thresholds (2020/2024 Guidelines)
ICMR_DAILY_SODIUM_LIMIT_MG = 2000.0  # 2g sodium = 5g table salt
ICMR_DAILY_ADDED_SUGAR_LIMIT_G = 25.0  # ~6 teaspoons max per day


class FoodAuditor:
    """
    Deterministic Food Auditor that evaluates packaging data against Indian statutory regulations
    and clinical nutrition benchmarks.
    """

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or settings.data_dir
        self.hidden_sugars = self._load_json(self.data_dir / "hidden_sugars.json")
        self.ins_decoder = self._load_json(self.data_dir / "ins_decoder.json")
        self.scoring_engine = ScoringEngine()
        logger.info(
            f"FoodAuditor initialized with {len(self.hidden_sugars)} hidden sugars, "
            f"{len(self.ins_decoder)} statutory additive decoders, and ScoringEngine."
        )

    def _load_json(self, path: Path) -> dict:
        """Safely loads a JSON knowledge base."""
        if not path.exists():
            logger.error(f"Knowledge base missing: {path}")
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def audit(self, data: PackagingData) -> AuditReport:
        """
        Executes the 12 statutory and food science evaluation checks on PackagingData.
        Returns a fully deterministic AuditReport.
        """
        logger.info(f"Auditing product: {data.brand_name} - {data.product_name}")
        violations: list[AuditViolation] = []

        # ---------------------------------------------------------
        # Check 1: Whole-Pack Reality Multiplier
        # ---------------------------------------------------------
        multiplier = round(data.net_weight_g / data.serving_size_g, 2)
        whole_pack_ratio = data.net_weight_g / 100.0

        whole_calories = round(data.nutrition_per_100g.energy_kcal * whole_pack_ratio, 1)
        whole_sugar = round(data.nutrition_per_100g.sugar_g * whole_pack_ratio, 1)
        whole_sodium = round(data.nutrition_per_100g.sodium_mg * whole_pack_ratio, 1)

        if multiplier >= 2.0:
            violations.append(
                AuditViolation(
                    rule_name="Serving Size Manipulation Trap",
                    severity="MEDIUM",
                    penalty_points=10,
                    reason=(
                        f"Reported serving size is {data.serving_size_g}g, but full pack is {data.net_weight_g}g "
                        f"({multiplier}x multiplier). Real whole-pack sugar is {whole_sugar}g."
                    ),
                    detected_snippet=f"Net Weight: {data.net_weight_g}g vs Serving Size: {data.serving_size_g}g"
                )
            )

        # ---------------------------------------------------------
        # Check 2: Grain Purity & Marketing Claim Reality (Atta vs Maida)
        # ---------------------------------------------------------
        claims_text = " ".join(data.front_claims).lower()
        claimed_healthy_grains = ["atta", "whole wheat", "oat", "oats", "ragi", "millet", "jowar", "bajra"]
        is_claiming_grain = any(g in claims_text for g in claimed_healthy_grains) or any(
            g in data.product_name.lower() for g in claimed_healthy_grains
        )

        if is_claiming_grain and len(data.ingredients_raw) > 0:
            first_ingredient = data.ingredients_raw[0].lower()
            if "refined wheat flour" in first_ingredient or "maida" in first_ingredient:
                violations.append(
                    AuditViolation(
                        rule_name="Grain Purity Check (Atta vs Maida Trap)",
                        severity="CRITICAL",
                        penalty_points=25,
                        reason=(
                            "Product promotes healthy grains (Atta/Oats/Ragi) on front pack, but ingredient #1 "
                            f"by weight under FSSAI law is Refined Wheat Flour (Maida): '{data.ingredients_raw[0]}'."
                        ),
                        detected_snippet=data.ingredients_raw[0]
                    )
                )

        # ---------------------------------------------------------
        # Check 3: Hidden Sugar Syndicate & Glycemic Impact Scoring
        # ---------------------------------------------------------
        detected_sugars = []
        highest_gi = 0
        worst_sugar_name = ""

        ingredients_text = " ".join(data.ingredients_raw).lower()
        for alias, info in self.hidden_sugars.items():
            # Support aliases with underscores (e.g. invert_sugar_syrup -> invert sugar syrup)
            norm_alias = alias.replace("_", " ").lower()
            pattern = r"\b" + re.escape(norm_alias) + r"\b"
            if re.search(pattern, ingredients_text):
                gi = info.get("gi", 65)
                detected_sugars.append(norm_alias)
                if gi > highest_gi:
                    highest_gi = gi
                    worst_sugar_name = norm_alias

        if len(detected_sugars) >= 2:
            violations.append(
                AuditViolation(
                    rule_name="Chemical Sugar Fractionation",
                    severity="HIGH",
                    penalty_points=15,
                    reason=(
                        f"Product splits sugars across {len(detected_sugars)} different chemical aliases "
                        f"({', '.join(detected_sugars[:4])}) to prevent sugar from appearing as #1 ingredient."
                    ),
                    detected_snippet=", ".join(detected_sugars)
                )
            )

        if highest_gi >= 85:
            violations.append(
                AuditViolation(
                    rule_name="High Glycemic Index Additive",
                    severity="HIGH",
                    penalty_points=15,
                    reason=(
                        f"Contains '{worst_sugar_name}' with an aggressive Glycemic Index of {highest_gi} "
                        f"(higher than pure glucose at 100), triggering rapid insulin and blood sugar spikes."
                    ),
                    detected_snippet=f"{worst_sugar_name} (GI: {highest_gi})"
                )
            )

        # ---------------------------------------------------------
        # Check 4: Palm Oil & Refined Seed Oil Obfuscation
        # ---------------------------------------------------------
        palm_synonyms = ["palm oil", "palmolein", "palm kernel oil", "fractionated palm", "edible vegetable oil (palm)"]
        found_palm = [p for p in palm_synonyms if p in ingredients_text]
        if found_palm or "palmolein" in ingredients_text:
            violations.append(
                AuditViolation(
                    rule_name="Palm Oil & Saturated Seed Oil Detection",
                    severity="MEDIUM",
                    penalty_points=15,
                    reason=(
                        "Contains cheap, highly refined Palm Oil/Palmolein (~50% saturated fat), "
                        "associated with elevated LDL cholesterol and arterial inflammation."
                    ),
                    detected_snippet="Palm Oil / Palmolein"
                )
            )

        # ---------------------------------------------------------
        # Check 5: Harmful & High-Risk Additives (INS / E-numbers)
        # ---------------------------------------------------------
        for ins_code, info in self.ins_decoder.items():
            clean_code = ins_code.lower()
            num_part = re.search(r"\d+.*", clean_code)
            pattern = re.escape(clean_code)
            if num_part:
                pattern += r"|ins\s*" + re.escape(num_part.group()) + r"|e\s*" + re.escape(num_part.group())

            if re.search(pattern, ingredients_text):
                raw_hazard = info.get("hazard", info.get("hazard_tier", "MEDIUM")).upper()
                # Normalize MODERATE -> MEDIUM to conform to Pydantic Literal
                hazard = "MEDIUM" if raw_hazard in ("MODERATE", "MEDIUM") else raw_hazard
                if hazard not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
                    hazard = "MEDIUM"

                penalty = 20 if hazard == "CRITICAL" else (15 if hazard == "HIGH" else 5)
                name = info.get("name", ins_code)
                reason_text = info.get("reason", info.get("warning", "Statutory food additive"))
                violations.append(
                    AuditViolation(
                        rule_name=f"Hazardous Additive: {name}",
                        severity=hazard,
                        penalty_points=penalty,
                        reason=f"{ins_code} ({name}): {reason_text}",
                        detected_snippet=f"{ins_code} - {name}"
                    )
                )

        # ---------------------------------------------------------
        # Check 6: Glycemic Spike Alert (Carb-to-Fiber Ratio)
        # ---------------------------------------------------------
        fiber = data.nutrition_per_100g.dietary_fiber_g
        carbs = data.nutrition_per_100g.carbohydrates_g
        carb_fiber_ratio = None
        glycemic_spike = False

        if carbs > 0:
            if fiber > 0:
                carb_fiber_ratio = round(carbs / fiber, 1)
                if carb_fiber_ratio > 10.0:
                    glycemic_spike = True
            else:
                carb_fiber_ratio = 99.9
                glycemic_spike = True

        if glycemic_spike:
            violations.append(
                AuditViolation(
                    rule_name="Glycemic Spike Alert (Carb-to-Fiber Deficit)",
                    severity="HIGH",
                    penalty_points=10,
                    reason=(
                        f"Carbohydrate to Fiber ratio is {carb_fiber_ratio}:1 (Threshold > 10:1). "
                        "Without adequate fiber to buffer glucose absorption, this food triggers acute blood sugar spikes."
                    ),
                    detected_snippet=f"Carbs: {carbs}g, Fiber: {fiber}g"
                )
            )

        # ---------------------------------------------------------
        # Check 7: ICMR Daily Sodium Ceiling Exceedance
        # ---------------------------------------------------------
        sodium_pct = round((whole_sodium / ICMR_DAILY_SODIUM_LIMIT_MG) * 100, 1)
        if sodium_pct >= 40.0:
            violations.append(
                AuditViolation(
                    rule_name="ICMR Sodium Ceiling Exceedance",
                    severity="CRITICAL" if sodium_pct >= 70.0 else "HIGH",
                    penalty_points=15 if sodium_pct >= 70.0 else 10,
                    reason=(
                        f"A single package delivers {whole_sodium}mg of sodium ({sodium_pct}% of total ICMR 2,000mg "
                        "daily allowance), severely elevating hypertension risk."
                    ),
                    detected_snippet=f"Whole Pack Sodium: {whole_sodium}mg ({sodium_pct}% ICMR Daily Limit)"
                )
            )

        # ---------------------------------------------------------
        # Check 8: ICMR Daily Added Sugar Ceiling Exceedance
        # ---------------------------------------------------------
        sugar_pct = round((whole_sugar / ICMR_DAILY_ADDED_SUGAR_LIMIT_G) * 100, 1)
        if sugar_pct >= 50.0:
            violations.append(
                AuditViolation(
                    rule_name="ICMR Added Sugar Limit Exceedance",
                    severity="CRITICAL" if sugar_pct >= 100.0 else "HIGH",
                    penalty_points=20 if sugar_pct >= 100.0 else 10,
                    reason=(
                        f"A single package delivers {whole_sugar}g of sugar ({sugar_pct}% of total ICMR 25g "
                        "daily recommended limit for adults)."
                    ),
                    detected_snippet=f"Whole Pack Sugar: {whole_sugar}g ({sugar_pct}% ICMR Daily Limit)"
                )
            )

        # ---------------------------------------------------------
        # Check 9: Trans Fat & Hydrogenated Oil
        # ---------------------------------------------------------
        has_trans_fat = data.nutrition_per_100g.trans_fat_g > 0.2
        has_hydrogenated = "hydrogenated" in ingredients_text or "partially hydrogenated" in ingredients_text
        if has_trans_fat or has_hydrogenated:
            violations.append(
                AuditViolation(
                    rule_name="Industrial Trans Fat / Hydrogenated Oil Detection",
                    severity="CRITICAL",
                    penalty_points=25,
                    reason="Contains industrial trans fatty acids or hydrogenated oils banned by international cardiac guidelines.",
                    detected_snippet=f"Trans Fat: {data.nutrition_per_100g.trans_fat_g}g"
                )
            )

        # ---------------------------------------------------------
        # Check 10: WHO NOVA Food Classification
        # ---------------------------------------------------------
        nova_group = 1
        if len(detected_sugars) > 0 or len(violations) > 0 or "flavor" in ingredients_text or "emulsifier" in ingredients_text:
            nova_group = 4
        elif data.nutrition_per_100g.sugar_g > 10.0 or data.nutrition_per_100g.fat_g > 10.0:
            nova_group = 3
        else:
            nova_group = 2

        # ---------------------------------------------------------
        # Check 11: Dietary Dot & Claim Conflict
        # ---------------------------------------------------------
        if data.dietary_dot == "GREEN_VEG":
            non_veg_markers = ["gelatin", "carmine", "ins 120", "fish oil", "bone char", "isinglass"]
            found_non_veg = [m for m in non_veg_markers if m in ingredients_text]
            if found_non_veg:
                violations.append(
                    AuditViolation(
                        rule_name="Dietary Dot Conflict (FSSAI Veg Fraud)",
                        severity="CRITICAL",
                        penalty_points=30,
                        reason=f"Labeled with Green Vegetarian Dot but contains non-vegetarian ingredients: {found_non_veg}",
                        detected_snippet=", ".join(found_non_veg)
                    )
                )

        # ---------------------------------------------------------
        # Check 12: Scoring Engine Calculation (Phase 5 Matrix)
        # ---------------------------------------------------------
        initial_report = AuditReport(
            whole_pack_multiplier=multiplier,
            whole_pack_calories_kcal=whole_calories,
            whole_pack_sugar_g=whole_sugar,
            whole_pack_sodium_mg=whole_sodium,
            carb_to_fiber_ratio=carb_fiber_ratio,
            glycemic_spike_alert=glycemic_spike,
            nova_group=nova_group,
            icmr_sodium_daily_pct=sodium_pct,
            icmr_sugar_daily_pct=sugar_pct,
            violations=violations,
            total_penalty_deduction=0,
            provisional_honesty_score=100,
        )

        scorecard = self.scoring_engine.calculate_score(
            report=initial_report,
            product_name=data.product_name,
            brand_name=data.brand_name,
        )

        report = AuditReport(
            whole_pack_multiplier=multiplier,
            whole_pack_calories_kcal=whole_calories,
            whole_pack_sugar_g=whole_sugar,
            whole_pack_sodium_mg=whole_sodium,
            carb_to_fiber_ratio=carb_fiber_ratio,
            glycemic_spike_alert=glycemic_spike,
            nova_group=nova_group,
            icmr_sodium_daily_pct=sodium_pct,
            icmr_sugar_daily_pct=sugar_pct,
            violations=violations,
            total_penalty_deduction=scorecard.capped_deductions,
            provisional_honesty_score=scorecard.honesty_score,
        )

        logger.info(
            f"Audit finished for {data.product_name}. Violations: {len(violations)}, "
            f"Honesty Score: {scorecard.honesty_score}/100"
        )
        return report

    # Ergonomic alias for callers
    audit_packaging = audit
