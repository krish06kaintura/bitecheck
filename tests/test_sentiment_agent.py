"""
Unit tests for Phase 6: Agent 3 (Consumer Sentiment & Review Detective).
Tests targeted query formulation, anti-bot/PR hype filtering, aspect analysis,
digestive distress alerts, and fault-isolation blast radius guarantees.
"""

import pytest
from bitecheck.agents.sentiment_agent import SentimentAgent
from bitecheck.schemas.sentiment import ConsumerReview, SentimentReport


@pytest.fixture
def sentiment_agent():
    return SentimentAgent()


def test_targeted_query_formulation(sentiment_agent):
    """Verifies queries target Indian Reddit communities and consumer complaint angles."""
    queries = sentiment_agent.formulate_queries(
        brand_name="Pintola",
        product_name="Dark Chocolate Peanut Butter",
        front_claims=["High Protein 30g", "Zero Added Sugar"],
    )

    assert len(queries) >= 4
    combined = " ".join(queries).lower()
    assert "pintola" in combined
    assert "reddit" in combined
    assert "r/fitness_india" in combined
    assert "bloating" in combined or "side effects" in combined
    assert "high protein 30g" in combined


def test_anti_bot_hype_filtering(sentiment_agent):
    """Verifies that PR marketing bot spam and uninformative reviews are filtered out."""
    test_reviews = [
        # Bot / PR hype review 1: Superlatives
        ConsumerReview(source="AMAZON", text="This is a miracle product life changing magic blindly trust it!!!!", rating=5.0),
        # Bot / PR hype review 2: Generic ultra-short
        ConsumerReview(source="AMAZON", text="osm product", rating=5.0),
        # Bot / PR hype review 3: Excessive repeated characters
        ConsumerReview(source="AMAZON", text="bestttttt quality everrrrr", rating=5.0),
        # Genuine human complaint 1
        ConsumerReview(
            source="REDDIT",
            text="Gave me serious bloating and acidity after 3 days. Checked the back, contains mostly palmolein.",
            rating=1.0,
        ),
        # Genuine human review 2
        ConsumerReview(
            source="REDDIT",
            text="Taste is chalky and leaves a chemical aftertaste. r/Fitness_India warned me but I still bought it.",
            rating=2.0,
        ),
    ]

    verified, metrics = sentiment_agent.filter_reviews(test_reviews)

    assert metrics.total_scraped == 5
    assert metrics.bot_reviews_detected == 3
    assert metrics.verified_human_reviews == 2
    assert metrics.bot_percentage == 60.0
    assert len(verified) == 2
    assert all(not r.is_bot_flagged for r in verified)


def test_digestive_distress_and_negative_sentiment(sentiment_agent):
    """Verifies detection of gastrointestinal complaints (bloating, acidity) and negative score."""
    deceptive_reviews = [
        ConsumerReview(
            source="REDDIT",
            text="Heavy bloating and acid reflux every time I eat this biscuit. Complete sugar crash an hour later.",
            rating=1.0,
        ),
        ConsumerReview(
            source="REDDIT",
            text="Disguised junk! Causes stomach cramps and tummy upset. High maltodextrin content.",
            rating=1.0,
        ),
        ConsumerReview(
            source="AMAZON",
            text="Terrible artificial chemical aftertaste. Not healthy at all.",
            rating=2.0,
        ),
    ]

    report = sentiment_agent.analyze_sentiment(
        brand_name="SugarBomb",
        product_name="Diet Oats Biscuit",
        raw_reviews=deceptive_reviews,
    )

    assert isinstance(report, SentimentReport)
    assert report.digestive_distress_alert is True
    assert "bloating" in report.top_side_effects
    assert "acidity" in report.top_side_effects
    assert "stomach cramps" in report.top_side_effects
    assert report.overall_sentiment == "NEGATIVE"
    assert report.sentiment_score < 4.5
    assert report.status == "SUCCESS"
    assert report.is_fallback is False


def test_clean_whole_food_positive_sentiment(sentiment_agent):
    """Verifies that clean whole food receives high sentiment and zero digestive distress."""
    clean_reviews = [
        ConsumerReview(
            source="REDDIT",
            text="Super clean oats from True Elements. No sugar, no palm oil, easy on digestion.",
            rating=5.0,
        ),
        ConsumerReview(
            source="REDDIT",
            text="Great staple on r/Fitness_India. High fiber and no bloating at all. Delicious taste.",
            rating=5.0,
        ),
        ConsumerReview(
            source="AMAZON",
            text="High quality rolled oats. Natural taste with zero chemical aftertaste.",
            rating=5.0,
        ),
    ]

    report = sentiment_agent.analyze_sentiment(
        brand_name="True Elements",
        product_name="Rolled Oats",
        raw_reviews=clean_reviews,
    )

    assert report.digestive_distress_alert is False
    assert report.overall_sentiment == "POSITIVE"
    assert report.sentiment_score >= 7.0
    assert report.authenticity_score == 100.0
    assert len(report.top_side_effects) == 0


def test_fault_isolation_graceful_degradation(sentiment_agent, monkeypatch):
    """
    CRITICAL BLAST RADIUS TEST:
    If external scraping throws an unexpected network error or crash,
    Agent 3 must NEVER propagate the exception. It must return a degraded SentimentReport.
    """
    def broken_filter(*args, **kwargs):
        raise ConnectionResetError("Reddit API blocked request with HTTP 429 Rate Limit")

    monkeypatch.setattr(sentiment_agent, "filter_reviews", broken_filter)

    # Calling analyze_sentiment must not raise ConnectionResetError
    degraded_report = sentiment_agent.analyze_sentiment(
        brand_name="CrashBrand",
        product_name="FailureSnack",
    )

    assert degraded_report.status == "DEGRADED"
    assert degraded_report.is_fallback is True
    assert degraded_report.overall_sentiment == "INSUFFICIENT_DATA"
    assert "unavailable" in degraded_report.reddit_discussion_summary.lower()
