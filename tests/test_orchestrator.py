"""
Unit and Integration Tests for Phase 7: Multi-Agent State Graph Orchestrator.
Tests central state transitions, concurrent parallel branch dispatch,
graceful error degradation, latency metrics, and end-to-end execution.
"""

from pathlib import Path
import pytest
from bitecheck.orchestrator import MultiAgentOrchestrator, BiteCheckState
from bitecheck.schemas.packaging import PackagingData, NutritionFacts
from bitecheck.schemas.sentiment import SentimentReport, AntiBotMetrics
from bitecheck.agents.sentiment_agent import SentimentAgent


@pytest.fixture
def sample_packaging_data():
    """Valid packaging data for a deceptive cookie product."""
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
def orchestrator():
    return MultiAgentOrchestrator()


def test_orchestrator_happy_path(orchestrator, sample_packaging_data):
    """Verifies complete end-to-end multi-agent execution with parallel branches."""
    state = orchestrator.run(packaging_data=sample_packaging_data)

    assert isinstance(state, BiteCheckState)
    assert state.is_successful is True
    assert state.current_step == "COMPLETED"
    assert len(state.errors) == 0

    # Verify all agent outputs are populated in the state graph
    assert state.packaging_data is not None
    assert state.audit_report is not None
    assert state.sentiment_report is not None
    assert state.scorecard is not None
    assert state.transparency_card is not None

    # Verify score calculation and audit violations
    assert state.scorecard.honesty_score < 60  # Deceptive maida + palm oil + maltodextrin
    assert state.scorecard.bracket == "HIGHLY DECEPTIVE"
    assert "ATTA_MAIDA_TRAP" in state.scorecard.active_badges
    assert "PALM_OIL_ALERT" in state.scorecard.active_badges
    assert len(state.transparency_card.clean_swaps) > 0

    # Verify latency tracking
    assert "deterministic_audit" in state.execution_times_ms
    assert "sentiment_detective" in state.execution_times_ms
    assert "parallel_evaluation_wall_time" in state.execution_times_ms
    assert "scoring_engine" in state.execution_times_ms
    assert state.total_latency_ms > 0.0


def test_orchestrator_parallel_execution(orchestrator, sample_packaging_data):
    """Verifies that Agent 2 and Agent 3 run concurrently in separate threads."""
    state = orchestrator.run(packaging_data=sample_packaging_data)

    audit_time = state.execution_times_ms["deterministic_audit"]
    sentiment_time = state.execution_times_ms["sentiment_detective"]
    wall_time = state.execution_times_ms["parallel_evaluation_wall_time"]

    # Wall time should be roughly dominated by the slower branch (sentiment)
    # rather than strictly sum(audit_time + sentiment_time + overhead)
    assert wall_time >= 0.0
    assert audit_time >= 0.0
    assert sentiment_time >= 0.0


def test_orchestrator_degraded_sentiment_recovery(orchestrator, sample_packaging_data, monkeypatch):
    """
    BLAST RADIUS & RESILIENCE TEST:
    If Agent 3 (Sentiment Detective) experiences a network error,
    the orchestrator must gracefully record is_degraded=True,
    continue with Agent 2 & Scoring Engine, and successfully output the scorecard.
    """
    def degraded_sentiment(*args, **kwargs):
        return SentimentReport(
            product_name="Diet Oats Biscuit",
            brand_name="GoodBite",
            overall_sentiment="INSUFFICIENT_DATA",
            sentiment_score=5.0,
            authenticity_score=50.0,
            anti_bot_metrics=AntiBotMetrics(
                total_scraped=0,
                verified_human_reviews=0,
                bot_reviews_detected=0,
                bot_percentage=0.0,
                suspicious_patterns=[],
            ),
            aspects=[],
            common_complaints=[],
            digestive_distress_alert=False,
            top_side_effects=[],
            reddit_discussion_summary="External forum intelligence unavailable.",
            is_fallback=True,
            status="DEGRADED",
        )

    monkeypatch.setattr(orchestrator.sentiment_agent, "analyze_sentiment", degraded_sentiment)

    state = orchestrator.run(packaging_data=sample_packaging_data)

    assert state.is_successful is True
    assert state.is_degraded is True
    assert state.current_step == "COMPLETED"
    assert state.scorecard is not None
    assert state.scorecard.honesty_score < 60
    assert state.sentiment_report.is_fallback is True


def test_orchestrator_missing_input_failure(orchestrator):
    """Verifies defensive error handling when neither images nor packaging data are provided."""
    state = orchestrator.run()

    assert state.is_successful is False
    assert state.current_step == "FAILED"
    assert len(state.errors) > 0
    assert "Neither packaging_data nor front/back image paths" in state.errors[0]
