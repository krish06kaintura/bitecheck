"""
Unit tests for Phase 4: Agent 2 Deterministic Scientific Food Auditor.
Tests the 12 statutory FSSAI and food science compliance checks.
"""

import pytest
from bitecheck.agents.food_auditor import FoodAuditor
from bitecheck.schemas.packaging import PackagingData, NutritionFacts


@pytest.fixture
def auditor():
    return FoodAuditor()


@pytest.fixture
def ultra_processed_biscuit():
    """Typical misleading Indian 'healthy' commercial biscuit."""
    return PackagingData(
        brand_name="Britannia",
        product_name="NutriChoice Oats Cookies",
        front_claims=["Rich in Oats", "Goodness of Fiber", "Zero Added Sugar"],
        ingredients_raw=[
            "Refined Wheat Flour (Maida) 64%",
            "Palm Oil",
            "Maltodextrin",
            "Rolled Oats 7%",
            "Invert Sugar Syrup",
            "INS 150d",
            "INS 503(ii)",
            "Salt"
        ],
        serving_size_g=15.0,
        net_weight_g=75.0,  # 5x multiplier
        nutrition_per_100g=NutritionFacts(
            energy_kcal=480.0,
            carbohydrates_g=68.0,
            sugar_g=24.0,
            added_sugar_g=18.0,
            dietary_fiber_g=2.0,  # Carb:Fiber = 34:1 -> Spike alert!
            protein_g=6.5,
            fat_g=21.0,
            saturated_fat_g=10.0,
            trans_fat_g=0.1,
            sodium_mg=550.0,
        ),
        dietary_dot="GREEN_VEG",
        fssai_license_number="10015043001234",
    )


@pytest.fixture
def clean_whole_food():
    """Genuinely clean whole food product (e.g. Rolled Oats)."""
    return PackagingData(
        brand_name="True Elements",
        product_name="100% Whole Rolled Oats",
        front_claims=["100% Rolled Oats", "High Fiber", "No Added Sugar"],
        ingredients_raw=["Rolled Oats 100%"],
        serving_size_g=40.0,
        net_weight_g=40.0,  # 1x multiplier
        nutrition_per_100g=NutritionFacts(
            energy_kcal=380.0,
            carbohydrates_g=62.0,
            sugar_g=1.0,
            added_sugar_g=0.0,
            dietary_fiber_g=11.0,  # Carb:Fiber = 5.6:1 (clean)
            protein_g=13.0,
            fat_g=7.0,
            saturated_fat_g=1.2,
            trans_fat_g=0.0,
            sodium_mg=5.0,
        ),
        dietary_dot="GREEN_VEG",
        fssai_license_number="10017022006789",
    )


def test_ultra_processed_biscuit_audit(auditor, ultra_processed_biscuit):
    """Verifies that an ultra-processed biscuit triggers multiple statutory penalties."""
    report = auditor.audit(ultra_processed_biscuit)

    assert report.whole_pack_multiplier == 5.0
    assert report.whole_pack_sugar_g == 18.0
    assert report.glycemic_spike_alert is True
    assert report.nova_group == 4

    # Must catch the Atta vs Maida trap
    grain_violation = next((v for v in report.violations if "Grain Purity Check" in v.rule_name), None)
    assert grain_violation is not None
    assert grain_violation.penalty_points == 25

    # Must catch Chemical Sugar Fractionation (Maltodextrin + Invert Sugar)
    sugar_violation = next((v for v in report.violations if "Chemical Sugar Fractionation" in v.rule_name), None)
    assert sugar_violation is not None

    # Must catch Maltodextrin high GI (110)
    gi_violation = next((v for v in report.violations if "High Glycemic Index Additive" in v.rule_name), None)
    assert gi_violation is not None

    # Must catch Palm Oil
    palm_violation = next((v for v in report.violations if "Palm Oil" in v.rule_name), None)
    assert palm_violation is not None

    # Must catch Caramel Color IV (INS 150d)
    ins_violation = next((v for v in report.violations if "Caramel" in v.rule_name or "150d" in v.detected_snippet), None)
    assert ins_violation is not None

    # Provisional score should be severely reduced
    assert report.provisional_honesty_score < 40


def test_clean_whole_food_audit(auditor, clean_whole_food):
    """Verifies that a clean whole food gets zero or minimal penalties."""
    report = auditor.audit(clean_whole_food)

    assert report.whole_pack_multiplier == 1.0
    assert report.glycemic_spike_alert is False
    assert len(report.violations) == 0
    assert report.provisional_honesty_score == 100


def test_dietary_dot_conflict_detection(auditor):
    """Verifies that non-vegetarian ingredients with a green veg dot are penalized severely."""
    fraud_pack = PackagingData(
        brand_name="FraudFoods",
        product_name="Fruit Gummies",
        front_claims=["100% Pure Veg"],
        ingredients_raw=["Sugar", "Gelatin", "Glucose Syrup", "INS 102"],
        serving_size_g=25.0,
        net_weight_g=25.0,
        nutrition_per_100g=NutritionFacts(sugar_g=50.0),
        dietary_dot="GREEN_VEG",
    )
    report = auditor.audit(fraud_pack)

    veg_fraud = next((v for v in report.violations if "FSSAI Veg Fraud" in v.rule_name), None)
    assert veg_fraud is not None
    assert veg_fraud.severity == "CRITICAL"
    assert veg_fraud.penalty_points == 30
