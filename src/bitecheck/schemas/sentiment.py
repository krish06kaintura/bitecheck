"""
Pydantic Data Contract for Consumer Sentiment & Review Detective (Agent 3 Output - Phase 6).
Structures forum queries, anti-bot metrics, aspect sentiments, side effect alerts, and degraded states.
"""

from typing import Literal
from pydantic import BaseModel, Field


class AspectSentiment(BaseModel):
    """Specific consumer experience dimension evaluated from public discourse."""
    aspect: str = Field(description="Aspect evaluated (e.g., 'Taste & Texture', 'Health Reality', 'Digestive Effects')")
    sentiment: Literal["POSITIVE", "NEUTRAL", "NEGATIVE", "MIXED"] = Field(description="Aggregated sentiment tier")
    summary: str = Field(description="Summary of consumer sentiment regarding this aspect")
    sample_quotes: list[str] = Field(default_factory=list, description="Direct consumer quotes extracted from forum/reviews")


class AntiBotMetrics(BaseModel):
    """Metrics tracking bot detection, sponsored review filtering, and PR hype removal."""
    total_scraped: int = Field(ge=0, description="Total raw reviews collected across all sources")
    verified_human_reviews: int = Field(ge=0, description="Number of reviews passing anti-bot and anti-hype heuristics")
    bot_reviews_detected: int = Field(ge=0, description="Number of reviews flagged as sponsored, bot-generated, or fake hype")
    bot_percentage: float = Field(ge=0.0, le=100.0, description="Percentage of scraped reviews flagged as bot/fake")
    suspicious_patterns: list[str] = Field(default_factory=list, description="Patterns identified in fake reviews")


class ConsumerReview(BaseModel):
    """Normalized representation of a single customer review before and after anti-bot filtering."""
    source: Literal["REDDIT", "AMAZON", "CONSUMER_FORUM", "MOCK"] = Field(description="Platform origin")
    text: str = Field(description="Full text or snippet of the review")
    rating: float | None = Field(default=None, description="Star rating if available (1.0 to 5.0)")
    is_bot_flagged: bool = Field(default=False, description="True if review triggered anti-bot/hype filters")
    flag_reason: str | None = Field(default=None, description="Reason for flagging as bot/sponsored")


class SentimentReport(BaseModel):
    """
    Complete structured consumer sentiment report produced by Agent 3.
    Includes fault-isolated status, anti-bot filtering, aspect breakdowns, and digestive distress warnings.
    """
    product_name: str = Field(default="", description="Name of the audited product")
    brand_name: str = Field(default="", description="Brand manufacturer")
    
    overall_sentiment: Literal["POSITIVE", "MIXED", "NEGATIVE", "INSUFFICIENT_DATA"] = Field(
        description="Overall synthesized public sentiment"
    )
    sentiment_score: float = Field(
        ge=0.0, le=10.0,
        description="Public perception score from 0.0 (Extremely Negative) to 10.0 (Universally Loved)"
    )
    authenticity_score: float = Field(
        ge=0.0, le=100.0,
        description="Review authenticity percentage (100% = entirely organic authentic human reviews)"
    )
    
    anti_bot_metrics: AntiBotMetrics = Field(
        description="Metrics detailing anti-bot and anti-hype filtering"
    )
    
    aspects: list[AspectSentiment] = Field(
        default_factory=list,
        description="Aspect-based breakdown: Taste, Health vs Marketing, Side Effects, Value"
    )
    
    common_complaints: list[str] = Field(
        default_factory=list,
        description="Top repeated consumer grievances"
    )
    
    digestive_distress_alert: bool = Field(
        default=False,
        description="True if multiple consumers report bloating, acidity, stomach cramps, or sugar crashes"
    )
    top_side_effects: list[str] = Field(
        default_factory=list,
        description="Specific physiological complaints reported by consumers (e.g. 'Bloating', 'Acidity')"
    )
    
    reddit_discussion_summary: str = Field(
        default="",
        description="Digest of Indian Reddit community discussions (r/Fitness_India, r/india, r/indiasocial)"
    )
    
    is_fallback: bool = Field(
        default=False,
        description="True if external network retrieval failed and graceful degraded fallback was used"
    )
    status: Literal["SUCCESS", "DEGRADED", "FAILED"] = Field(
        default="SUCCESS",
        description="Pipeline execution status of Agent 3"
    )
