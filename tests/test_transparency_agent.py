"""
Unit tests for Phase 8: Agent 4 (Transparency Scorecard & Clean Swaps).
Tests evidence chain mapping, whole-pack reality calculations,
clean Indian FMCG swap matching, and master scorecard aggregation.
"""

import pytest
from bitecheck.agents.transparency_agent import TransparencyAgent
from bitecheck.agents.food_auditor import FoodAuditor
from bitecheck.scoring.engine import ScoringEngine
from bitecheck.schemas.packaging import PackagingData, NutritionFacts
from bitecheck.schemas.sentiment import SentimentReport, AntiBotMetrics
from bitecheck.schemas.transparency import ProductTransparencyCard


@pytest.fixture
def transparency_agent():
    return TransparencyAgent()


@pytest.fixture
def food_auditor():
    return FoodAuditor()


@pytest.fixture
def scoring_engine():
    return ScoringEngine()


@pytest.fixture
def deceptive_cookie():
    return PackagingData(
        brand_name="GoodBite",
        product_name="Diet Oats Biscuit",
        front_claims=["Rich in Oats", "Zero Added Sugar"],
        ingredients_raw=["Refined Wheat Flour (Maida) 55%", "Palm Oil", "Maltodextrin", "Oats 4%", "Salt"],
        net_weight_g=100.0,
        serving_size_g=20.0,
        nutrition_per_100g=NutritionFacts(
            energy_kcal=450.0,
            fat_g=18.0,
            saturated_fat_g=8.0,
            trans_fat_g=0.0,
            carbohydrates_g=68.0,
            dietary_fiber_g=2.0,
            sugar_g=1.0,
            added_sugar_g=0.0,
            sodium_mg=550.0,
            protein_g=5.0,
        ),
        fssai_license_number="10012011000123",
        dietary_dot="GREEN_VEG",
    )


@pytest.fixture
def clean_oats():
    return PackagingData(
        brand_name="True Elements",
        product_name="Rolled Oats",
        front_claims=["100% Whole Grain", "High Fiber"],
        ingredients_raw=["Rolled Oats 100%"],
        net_weight_g=500.0,
        serving_size_g=40.0,
        nutrition_per_100g=NutritionFacts(
            energy_kcal=380.0,
            fat_g=7.0,
            saturated_fat_g=1.2,
            trans_fat_g=0.0,
            carbohydrates_g=65.0,
            dietary_fiber_g=10.0,
            sugar_g=0.5,
            added_sugar_g=0.0,
            sodium_mg=5.0,
            protein_g=13.0,
        ),
        fssai_license_number="10019022009876",
        dietary_dot="GREEN_VEG",
    )


def test_deceptive_product_clean_swaps(transparency_agent, food_auditor, scoring_engine, deceptive_cookie):
    """Verifies that deceptive products receive evidence mappings and clean FMCG alternatives."""
    audit_rep = food_auditor.audit(deceptive_cookie)
    scorecard = scoring_engine.calculate_score(audit_rep, product_name=deceptive_cookie.product_name, brand_name=deceptive_cookie.brand_name)
    
    sentiment_rep = SentimentReport(
        product_name=deceptive_cookie.product_name,
        brand_name=deceptive_cookie.brand_name,
        overall_sentiment="NEGATIVE",
        sentiment_score=3.5,
        authenticity_score=75.0,
        anti_bot_metrics=AntiBotMetrics(
            total_scraped=10,
            verified_human_reviews=7,
            bot_reviews_detected=3,
            bot_percentage=30.0,
            suspicious_patterns=[],
        ),
        aspects=[],
        common_complaints=["Acidity", "Mostly maida"],
        digestive_distress_alert=True,
        top_side_effects=["bloating", "acidity"],
        reddit_discussion_summary="Discussions warn of high maida and bloating.",
        is_fallback=False,
        status="SUCCESS",
    )

    card = transparency_agent.generate_transparency_card(
        packaging_data=deceptive_cookie,
        audit_report=audit_rep,
        scorecard=scorecard,
        sentiment_report=sentiment_rep,
    )

    assert isinstance(card, ProductTransparencyCard)
    assert card.is_clean_product is False
    assert card.honesty_score < 60
    assert card.bracket == "HIGHLY DECEPTIVE"
    assert card.color_code == "RED"

    # Evidence chain verification
    assert len(card.evidence_chain) > 0
    snippets = [e.label_evidence_snippet.lower() for e in card.evidence_chain]
    assert any("maida" in s for s in snippets)
    assert any("palm oil" in s or "palmolein" in s for s in snippets)

    # Clean swaps verification
    assert len(card.clean_swaps) > 0
    swap_brands = [s.brand for s in card.clean_swaps]
    assert "The Whole Truth" in swap_brands or "Early Foods" in swap_brands
    for s in card.clean_swaps:
        assert len(s.platforms) > 0
        assert any(p in ["Blinkit", "Zepto", "Instamart", "Amazon"] for p in s.platforms)

    # Sentiment pulse verification
    assert card.sentiment_pulse["digestive_distress_alert"] is True
    assert "bloating" in card.sentiment_pulse["top_side_effects"]


def test_clean_product_no_swaps_needed(transparency_agent, food_auditor, scoring_engine, clean_oats):
    """Verifies that clean foods (>= 85) do not recommend swaps because they are already clean."""
    audit_rep = food_auditor.audit(clean_oats)
    scorecard = scoring_engine.calculate_score(audit_rep, product_name=clean_oats.product_name, brand_name=clean_oats.brand_name)

    card = transparency_agent.generate_transparency_card(
        packaging_data=clean_oats,
        audit_report=audit_rep,
        scorecard=scorecard,
    )

    assert card.is_clean_product is True
    assert card.honesty_score >= 85
    assert card.bracket == "CLEAN & TRANSPARENT"
    assert card.color_code == "GREEN"
    assert len(card.clean_swaps) == 0  # No swaps needed for clean product!


def test_whole_pack_reality_pill(transparency_agent, food_auditor, deceptive_cookie):
    """Verifies advertised per-serving vs whole pack arithmetic."""
    audit_rep = food_auditor.audit(deceptive_cookie)
    reality = transparency_agent.build_whole_pack_reality(deceptive_cookie, audit_rep)

    assert reality.multiplier == 5.0  # 100g pack / 20g serving
    assert reality.calories_advertised == 90.0  # 450 * 0.2
    assert reality.calories_whole_pack == 450.0
    assert reality.carb_to_fiber_ratio == 34.0  # 68g / 2g
    assert reality.glycemic_spike_alert is True
