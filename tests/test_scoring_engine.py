"""
Unit tests for Phase 5: Mathematical Scoring Engine & Penalty Matrix.
Tests deductive scoring, category deduction caps, strict [0, 100] bounds,
critical statutory overrides, and red-flag badge synthesis.
"""

import pytest
from bitecheck.scoring import ScoringEngine, CATEGORY_CAPS, CRITICAL_CEILING_CAP
from bitecheck.schemas.audit import AuditReport, AuditViolation


@pytest.fixture
def scoring_engine():
    return ScoringEngine()


def make_report(violations: list[AuditViolation]) -> AuditReport:
    """Helper to construct an AuditReport with specific violations."""
    return AuditReport(
        whole_pack_multiplier=1.0,
        whole_pack_calories_kcal=200.0,
        whole_pack_sugar_g=5.0,
        whole_pack_sodium_mg=100.0,
        carb_to_fiber_ratio=3.0,
        glycemic_spike_alert=False,
        nova_group=1,
        icmr_sodium_daily_pct=5.0,
        icmr_sugar_daily_pct=10.0,
        violations=violations,
        total_penalty_deduction=0,
        provisional_honesty_score=100,
    )


def test_clean_whole_food_perfect_100(scoring_engine):
    """Clean food with zero violations receives a perfect 100 score in the Green tier."""
    report = make_report([])
    scorecard = scoring_engine.calculate_score(report, product_name="Rolled Oats", brand_name="True Elements")

    assert scorecard.honesty_score == 100
    assert scorecard.raw_deductions == 0
    assert scorecard.capped_deductions == 0
    assert scorecard.bracket == "CLEAN & TRANSPARENT"
    assert scorecard.color_code == "GREEN"
    assert len(scorecard.active_badges) == 0
    assert scorecard.critical_override_applied is False
    assert "scored 100/100" in scorecard.verdict_summary


def test_score_lower_bound_clamped_at_zero(scoring_engine):
    """Extreme violations totaling over 150 points must clamp the score at 0, never negative."""
    excessive_violations = [
        AuditViolation(
            rule_name="Grain Purity Check",
            severity="CRITICAL",
            penalty_points=35,
            reason="100% Maida",
            detected_snippet="Maida",
        ),
        AuditViolation(
            rule_name="Chemical Sugar Fractionation",
            severity="HIGH",
            penalty_points=30,
            reason="Multiple syrups",
            detected_snippet="Liquid Glucose, Invert Sugar",
        ),
        AuditViolation(
            rule_name="Palm Oil Detection",
            severity="HIGH",
            penalty_points=30,
            reason="Palmolein used",
            detected_snippet="Palmolein",
        ),
        AuditViolation(
            rule_name="Sodium Limit Exceedance",
            severity="CRITICAL",
            penalty_points=30,
            reason="Extreme sodium",
            detected_snippet="1800mg Sodium",
        ),
        AuditViolation(
            rule_name="Dietary Dot Conflict",
            severity="CRITICAL",
            penalty_points=35,
            reason="Non-veg in veg pack",
            detected_snippet="Gelatin",
        ),
    ]
    report = make_report(excessive_violations)
    scorecard = scoring_engine.calculate_score(report, product_name="JunkBomb", brand_name="BadBrand")

    assert scorecard.raw_deductions == 160
    assert scorecard.capped_deductions == 100
    assert scorecard.honesty_score == 0
    assert scorecard.bracket == "HIGHLY DECEPTIVE"
    assert scorecard.color_code == "RED"


def test_category_deduction_caps(scoring_engine):
    """
    Multiple violations in the same category must respect category caps.
    For example, 4 chemical additive violations (4 * 15 = 60 pts) should cap at 35 pts.
    """
    chemical_violations = [
        AuditViolation(
            rule_name="INS 102 Tartrazine",
            severity="HIGH",
            penalty_points=15,
            reason="Chemical color",
            detected_snippet="INS 102",
        ),
        AuditViolation(
            rule_name="INS 150d Caramel IV",
            severity="HIGH",
            penalty_points=15,
            reason="Caramel color",
            detected_snippet="INS 150d",
        ),
        AuditViolation(
            rule_name="INS 407 Carrageenan",
            severity="HIGH",
            penalty_points=15,
            reason="Inflammatory thickener",
            detected_snippet="INS 407",
        ),
        AuditViolation(
            rule_name="High Glycemic Index Additive Maltodextrin",
            severity="HIGH",
            penalty_points=15,
            reason="GI 110 spike",
            detected_snippet="Maltodextrin",
        ),
    ]
    report = make_report(chemical_violations)
    scorecard = scoring_engine.calculate_score(report, product_name="AdditiveDrink", brand_name="ChemCorp")

    assert scorecard.raw_deductions == 60
    # chemical_additives cap is 35
    assert scorecard.category_breakdown.chemical_additives == CATEGORY_CAPS["chemical_additives"]
    assert scorecard.capped_deductions == 35
    assert scorecard.honesty_score == 65
    assert scorecard.bracket == "MODERATE / MISLEADING"
    assert scorecard.color_code == "AMBER"


def test_critical_statutory_override(scoring_engine):
    """
    Statutory fraud (e.g., Veg Fraud) must force the final score to <= 49 (Red Tier),
    even if the product otherwise has minimal deductions.
    """
    veg_fraud_violation = [
        AuditViolation(
            rule_name="Dietary Dot Conflict (FSSAI Veg Fraud)",
            severity="CRITICAL",
            penalty_points=25,
            reason="Green Dot but contains Gelatin",
            detected_snippet="Gelatin",
        )
    ]
    report = make_report(veg_fraud_violation)
    scorecard = scoring_engine.calculate_score(report, product_name="VegGummies", brand_name="SneakBrand")

    # Normally 100 - 25 = 75 (Amber). But critical statutory override forces cap at 49 (Red)!
    assert scorecard.critical_override_applied is True
    assert scorecard.honesty_score <= CRITICAL_CEILING_CAP
    assert scorecard.honesty_score == 49
    assert scorecard.bracket == "HIGHLY DECEPTIVE"
    assert scorecard.color_code == "RED"
    assert "VEG_FRAUD_ALERT" in scorecard.active_badges
    assert "Statutory Critical Override Applied" in scorecard.verdict_summary


def test_badge_generation_accuracy(scoring_engine):
    """Verifies that detected violations generate standard red-flag badge strings."""
    violations = [
        AuditViolation(
            rule_name="Grain Purity Check (Atta vs Maida)",
            severity="CRITICAL",
            penalty_points=25,
            reason="Maida is #1",
            detected_snippet="Maida 65%",
        ),
        AuditViolation(
            rule_name="Palm Oil Detection",
            severity="HIGH",
            penalty_points=20,
            reason="Uses Palmolein",
            detected_snippet="Palmolein",
        ),
        AuditViolation(
            rule_name="Glycemic Spike Alert",
            severity="HIGH",
            penalty_points=10,
            reason="Carb to fiber ratio 34:1",
            detected_snippet="Carbs 68g, Fiber 2g",
        ),
        AuditViolation(
            rule_name="Serving Size Manipulation Trap",
            severity="MEDIUM",
            penalty_points=10,
            reason="Serving 15g on 75g pack",
            detected_snippet="15g serving",
        ),
    ]
    report = make_report(violations)
    scorecard = scoring_engine.calculate_score(report, product_name="DeceptiveCookie", brand_name="BigCorp")

    expected_badges = [
        "ATTA_MAIDA_TRAP",
        "PALM_OIL_ALERT",
        "GLYCEMIC_SPIKE_RISK",
        "SERVING_SIZE_TRAP",
    ]
    for b in expected_badges:
        assert b in scorecard.active_badges


def test_score_tier_threshold_boundaries(scoring_engine):
    """Verifies exact tier boundary mapping."""
    # Score 85 -> CLEAN & TRANSPARENT
    v_15 = [AuditViolation(rule_name="Sodium Limit Exceedance", severity="HIGH", penalty_points=15, reason="r", detected_snippet="s")]
    sc_85 = scoring_engine.calculate_score(make_report(v_15))
    assert sc_85.honesty_score == 85
    assert sc_85.bracket == "CLEAN & TRANSPARENT"
    assert sc_85.color_code == "GREEN"

    # Score 84 -> MODERATE / MISLEADING
    v_16 = [AuditViolation(rule_name="Sodium Limit Exceedance", severity="HIGH", penalty_points=16, reason="r", detected_snippet="s")]
    sc_84 = scoring_engine.calculate_score(make_report(v_16))
    assert sc_84.honesty_score == 84
    assert sc_84.bracket == "MODERATE / MISLEADING"
    assert sc_84.color_code == "AMBER"

    # Score 60 -> MODERATE / MISLEADING
    v_40 = [AuditViolation(rule_name="Sodium Limit Exceedance", severity="HIGH", penalty_points=40, reason="r", detected_snippet="s")]
    sc_60 = scoring_engine.calculate_score(make_report(v_40))
    assert sc_60.honesty_score == 60
    assert sc_60.bracket == "MODERATE / MISLEADING"
    assert sc_60.color_code == "AMBER"

    # Score 59 -> HIGHLY DECEPTIVE
    v_41 = [
        AuditViolation(rule_name="Sodium Limit Exceedance", severity="HIGH", penalty_points=25, reason="r", detected_snippet="s"),
        AuditViolation(rule_name="Grain Purity Check", severity="CRITICAL", penalty_points=16, reason="r", detected_snippet="s"),
    ]
    sc_59 = scoring_engine.calculate_score(make_report(v_41))
    assert sc_59.honesty_score == 59
    assert sc_59.bracket == "HIGHLY DECEPTIVE"
    assert sc_59.color_code == "RED"
