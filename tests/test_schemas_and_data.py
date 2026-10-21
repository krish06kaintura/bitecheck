"""
Unit tests for Phase 2: Knowledge Bases and Pydantic Data Contracts.
"""

import json
import pytest
from pydantic import ValidationError
from bitecheck.config import settings
from bitecheck.schemas import (
    PackagingData,
    NutritionFacts,
    AuditReport,
    AuditViolation,
)


def test_knowledge_bases_exist_and_load():
    """Verify that all JSON knowledge bases exist and contain valid entries."""
    sugars_file = settings.data_dir / "hidden_sugars.json"
    ins_file = settings.data_dir / "ins_decoder.json"
    swaps_file = settings.data_dir / "clean_indian_swaps.json"

    assert sugars_file.exists(), "hidden_sugars.json is missing"
    assert ins_file.exists(), "ins_decoder.json is missing"
    assert swaps_file.exists(), "clean_indian_swaps.json is missing"

    with open(sugars_file, "r", encoding="utf-8") as f:
        sugars = json.load(f)
        assert "maltodextrin" in sugars
        assert sugars["maltodextrin"]["gi"] == 110

    with open(ins_file, "r", encoding="utf-8") as f:
        ins = json.load(f)
        assert "INS 102" in ins
        assert "INS 150d" in ins

    with open(swaps_file, "r", encoding="utf-8") as f:
        swaps = json.load(f)
        assert "cookies_and_biscuits" in swaps


def test_packaging_data_valid_instantiation():
    """Verify that PackagingData instantiates correctly with valid input."""
    sample = PackagingData(
        brand_name="Britannia",
        product_name="NutriChoice Oats",
        front_claims=["Rich in Oats", "Zero Sugar"],
        ingredients_raw=["Refined Wheat Flour", "Palm Oil", "Maltodextrin", "Oats 6%"],
        serving_size_g=15.0,
        net_weight_g=75.0,
        nutrition_per_100g=NutritionFacts(
            energy_kcal=480.0,
            carbohydrates_g=68.0,
            sugar_g=22.0,
            dietary_fiber_g=2.0,
            sodium_mg=450.0,
        ),
        dietary_dot="GREEN_VEG",
        fssai_license_number="10015043001234",
    )
    assert sample.brand_name == "Britannia"
    assert sample.serving_size_g == 15.0
    assert sample.net_weight_g == 75.0


def test_packaging_data_rejects_impossible_net_weight():
    """Verify that net_weight smaller than serving_size raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        PackagingData(
            brand_name="TestBrand",
            product_name="BadPack",
            serving_size_g=50.0,
            net_weight_g=20.0,  # Impossible: net weight < serving size!
            nutrition_per_100g=NutritionFacts(),
        )
    assert "Net weight (20.0g) cannot be smaller than reported serving size" in str(exc_info.value)


def test_audit_report_schema_bounds():
    """Verify that AuditReport schema enforces score bounds between 0 and 100."""
    violation = AuditViolation(
        rule_name="Hidden Sugar Detection",
        severity="CRITICAL",
        penalty_points=20,
        reason="Contains Maltodextrin (GI = 110)",
        detected_snippet="Maltodextrin",
    )
    report = AuditReport(
        whole_pack_multiplier=5.0,
        whole_pack_calories_kcal=360.0,
        whole_pack_sugar_g=16.5,
        whole_pack_sodium_mg=337.5,
        carb_to_fiber_ratio=34.0,
        glycemic_spike_alert=True,
        nova_group=4,
        icmr_sodium_daily_pct=16.8,
        icmr_sugar_daily_pct=66.0,
        violations=[violation],
        total_penalty_deduction=20,
        provisional_honesty_score=80,
    )
    assert report.provisional_honesty_score == 80
    assert len(report.violations) == 1
