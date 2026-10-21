"""
BiteCheck Mathematical Scoring Engine (Phase 5).
Executes deductive penalty calculations, category clamping, critical overrides,
badge emissions, and consumer honesty score synthesis.
"""

from bitecheck.logger import get_logger
from bitecheck.schemas.audit import AuditReport, AuditViolation
from bitecheck.schemas.scorecard import CategoryDeductions, HonestyScorecard
from bitecheck.scoring.matrix import (
    CATEGORY_CAPS,
    SCORE_TIERS,
    CRITICAL_CEILING_CAP,
    RULE_CATEGORY_MAP,
    BADGE_RULES,
)

logger = get_logger("bitecheck.scoring.engine")


class ScoringEngine:
    """
    Mathematical Scoring Engine for BiteCheck India.
    Calculates the FSSAI Honesty Score (0-100) using deductive multi-dimensional penalties.
    """

    @staticmethod
    def categorize_violation(violation: AuditViolation) -> str:
        """Maps an AuditViolation to one of the four regulatory deduction categories."""
        rule_lower = violation.rule_name.lower()
        for pattern, category in RULE_CATEGORY_MAP.items():
            if pattern in rule_lower:
                return category
        # Fallback based on severity or default to nutritional_hazard
        return "nutritional_hazard"

    @classmethod
    def generate_badges(cls, violations: list[AuditViolation]) -> list[str]:
        """Synthesizes unique standardized red-flag badges from detected violations."""
        active_badges = []
        for rule in BADGE_RULES:
            matched = False
            for v in violations:
                rule_text = f"{v.rule_name} {v.reason} {v.detected_snippet}".lower()
                if any(kw in rule_text for kw in rule["keywords"]):
                    matched = True
                    break
            if matched and rule["badge"] not in active_badges:
                active_badges.append(rule["badge"])
        return active_badges

    @classmethod
    def generate_verdict_summary(
        cls,
        product_name: str,
        score: int,
        bracket: str,
        active_badges: list[str],
        critical_override: bool,
    ) -> str:
        """Constructs an executive plain-English summary of the product audit."""
        prod = f"'{product_name}'" if product_name else "This product"
        if score >= SCORE_TIERS["CLEAN_MIN"]:
            return (
                f"{prod} scored {score}/100 ({bracket}). It demonstrates clean labeling, "
                "minimal processing, and adheres to FSSAI nutritional guidelines."
            )
        elif score >= SCORE_TIERS["MODERATE_MIN"]:
            badge_str = ", ".join(active_badges[:2]) if active_badges else "minor labeling concerns"
            return (
                f"{prod} scored {score}/100 ({bracket}). While not entirely ultra-processed, "
                f"it triggers moderate consumer alerts including {badge_str}."
            )
        else:
            override_msg = " [Statutory Critical Override Applied]" if critical_override else ""
            badge_str = ", ".join(active_badges[:3]) if active_badges else "multiple statutory violations"
            return (
                f"{prod} scored {score}/100 ({bracket}){override_msg}. It exhibits significant "
                f"marketing deception and health risks: {badge_str}."
            )

    def calculate_score(
        self,
        report: AuditReport,
        product_name: str = "",
        brand_name: str = "",
    ) -> HonestyScorecard:
        """
        Calculates the complete HonestyScorecard from an AuditReport.
        Guarantees strict score bounds [0, 100] and multi-dimensional category transparency.
        """
        raw_deductions = sum(v.penalty_points for v in report.violations)

        # 1. Accumulate raw deductions per category
        cat_sums = {
            "marketing_deception": 0,
            "chemical_additives": 0,
            "nutritional_hazard": 0,
            "statutory_violations": 0,
        }

        for v in report.violations:
            cat = self.categorize_violation(v)
            cat_sums[cat] += v.penalty_points

        # 2. Apply category deduction caps
        capped_breakdown = {
            cat: min(val, CATEGORY_CAPS[cat]) for cat, val in cat_sums.items()
        }

        # 3. Sum capped deductions and clamp to 100
        total_capped_deductions = min(100, sum(capped_breakdown.values()))

        # 4. Preliminary score calculation
        preliminary_score = max(0, 100 - total_capped_deductions)

        # 5. Check Critical Statutory Overrides
        # (Veg fraud or industrial trans fats permanently cap the score at CRITICAL_CEILING_CAP)
        critical_override_applied = False
        for v in report.violations:
            if v.severity == "CRITICAL":
                cat = self.categorize_violation(v)
                if cat == "statutory_violations" or "trans fat" in v.rule_name.lower():
                    if preliminary_score > CRITICAL_CEILING_CAP:
                        preliminary_score = CRITICAL_CEILING_CAP
                        critical_override_applied = True
                        logger.warning(
                            f"Critical statutory override applied for {v.rule_name}. "
                            f"Score capped to {CRITICAL_CEILING_CAP}."
                        )

        final_score = max(0, min(100, preliminary_score))

        # 6. Assign Score Bracket & Color Code
        if final_score >= SCORE_TIERS["CLEAN_MIN"]:
            bracket = "CLEAN & TRANSPARENT"
            color_code = "GREEN"
        elif final_score >= SCORE_TIERS["MODERATE_MIN"]:
            bracket = "MODERATE / MISLEADING"
            color_code = "AMBER"
        else:
            bracket = "HIGHLY DECEPTIVE"
            color_code = "RED"

        # 7. Generate Badges & Summary
        active_badges = self.generate_badges(report.violations)
        verdict = self.generate_verdict_summary(
            product_name=product_name,
            score=final_score,
            bracket=bracket,
            active_badges=active_badges,
            critical_override=critical_override_applied,
        )

        scorecard = HonestyScorecard(
            product_name=product_name,
            brand_name=brand_name,
            raw_deductions=raw_deductions,
            capped_deductions=total_capped_deductions,
            honesty_score=final_score,
            bracket=bracket,
            color_code=color_code,
            category_breakdown=CategoryDeductions(**capped_breakdown),
            critical_override_applied=critical_override_applied,
            active_badges=active_badges,
            verdict_summary=verdict,
        )

        logger.info(
            f"Scoring finalized for '{product_name or 'Product'}': "
            f"Score={final_score}/100 [{bracket}], Badges={active_badges}"
        )
        return scorecard
