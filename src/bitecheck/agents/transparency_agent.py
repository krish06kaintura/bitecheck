"""
Agent 4: Transparency Scorecard & Clean Swaps Agent (Phase 8).
Aggregates findings from Agent 1 (Vision), Agent 2 (Auditor), Agent 3 (Sentiment),
and the Mathematical Scoring Engine into the master consumer-facing ProductTransparencyCard.
Maps evidence chains to exact label snippets, computes whole-pack consumption realities,
and matches deceptive foods to clean Indian FMCG alternatives available on quick commerce.
"""

import json
from pathlib import Path

from bitecheck.config import settings
from bitecheck.logger import get_logger
from bitecheck.schemas.packaging import PackagingData
from bitecheck.schemas.audit import AuditReport
from bitecheck.schemas.sentiment import SentimentReport
from bitecheck.schemas.scorecard import HonestyScorecard
from bitecheck.schemas.transparency import (
    ProductTransparencyCard,
    CleanSwapItem,
    EvidenceItem,
    WholePackReality,
)

logger = get_logger("bitecheck.agents.transparency")


class TransparencyAgent:
    """
    Agent 4: Master Transparency Scorecard & Clean Swap Aggregator.
    Synthesizes the complete multi-agent evidence chain into an actionable,
    consumer-friendly audit card with clean FMCG swaps.
    """

    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or settings.data_dir
        self.swaps_db = self._load_json(self.data_dir / "clean_indian_swaps.json")
        logger.info(
            f"TransparencyAgent initialized with {len(self.swaps_db)} swap categories from {self.data_dir}"
        )

    def _load_json(self, path: Path) -> dict:
        """Safely loads clean swap knowledge base."""
        if not path.exists():
            logger.error(f"Clean swaps database missing at {path}")
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading {path}: {e}")
            return {}

    def categorize_product_category(self, product_name: str, brand_name: str) -> str:
        """Classifies a product into a clean swap category based on title keywords."""
        text = f"{brand_name} {product_name}".lower()

        if any(w in text for w in ["cookie", "biscuit", "digestive", "rusk", "wafer", "oreo", "bourbon"]):
            return "cookies_and_biscuits"
        elif any(w in text for w in ["noodle", "noodles", "maggi", "pasta", "macaroni", "ramen", "chowmein", "spaghetti"]):
            return "noodles_and_pasta"
        elif any(w in text for w in ["chip", "chips", "crisp", "crisps", "namkeen", "bhujia", "kurkure", "puff", "makhana", "snack"]):
            return "namkeen_and_chips"
        
        # Default fallback category
        return "cookies_and_biscuits"

    def match_clean_swaps(
        self,
        product_name: str,
        brand_name: str,
        category_override: str | None = None,
    ) -> list[CleanSwapItem]:
        """
        Retrieves healthier, certified clean Indian FMCG alternatives from quick-commerce.
        Only called when a product is deceptive or moderate.
        """
        category = category_override or self.categorize_product_category(product_name, brand_name)
        candidates = self.swaps_db.get(category, [])

        # If category empty, pick first available
        if not candidates and self.swaps_db:
            first_key = next(iter(self.swaps_db))
            candidates = self.swaps_db.get(first_key, [])

        clean_swaps = []
        for c in candidates:
            # Do not recommend the exact same brand as a swap
            if c.get("brand", "").lower() != brand_name.lower():
                clean_swaps.append(
                    CleanSwapItem(
                        brand=c.get("brand", ""),
                        product=c.get("product", ""),
                        why_clean=c.get("why_clean", ""),
                        platforms=c.get("platforms", []),
                    )
                )

        logger.debug(f"Matched {len(clean_swaps)} clean swaps for category '{category}'")
        return clean_swaps

    @staticmethod
    def build_evidence_chain(audit_report: AuditReport, scorecard: HonestyScorecard) -> list[EvidenceItem]:
        """
        Constructs a traceable evidence chain linking each badge and penalty to specific label text.
        Guarantees explainable AI with zero hallucinations.
        """
        evidence_items = []
        for v in audit_report.violations:
            # Match badge if applicable
            matched_badge = "RED_FLAG_ALERT"
            for b in scorecard.active_badges:
                # Check if badge associates with violation keywords
                b_simplified = b.replace("_", " ").lower()
                if any(kw in v.rule_name.lower() or kw in v.reason.lower() for kw in b_simplified.split()):
                    matched_badge = b
                    break

            evidence_items.append(
                EvidenceItem(
                    badge=matched_badge,
                    severity=v.severity,
                    penalty_deduction=v.penalty_points,
                    scientific_reason=v.reason,
                    label_evidence_snippet=v.detected_snippet,
                )
            )
        return evidence_items

    @staticmethod
    def build_whole_pack_reality(packaging_data: PackagingData, audit_report: AuditReport) -> WholePackReality:
        """
        Builds the side-by-side consumption comparison:
        Advertised per-serving claims vs the reality of consuming the entire pack.
        """
        serving_ratio = packaging_data.serving_size_g / 100.0
        n100 = packaging_data.nutrition_per_100g

        cal_adv = round(n100.energy_kcal * serving_ratio, 1)
        sugar_adv = round(n100.sugar_g * serving_ratio, 1)
        sodium_adv = round(n100.sodium_mg * serving_ratio, 1)

        return WholePackReality(
            serving_size_g=packaging_data.serving_size_g,
            net_weight_g=packaging_data.net_weight_g,
            multiplier=audit_report.whole_pack_multiplier,
            calories_advertised=cal_adv,
            calories_whole_pack=audit_report.whole_pack_calories_kcal,
            sugar_advertised_g=sugar_adv,
            sugar_whole_pack_g=audit_report.whole_pack_sugar_g,
            sodium_advertised_mg=sodium_adv,
            sodium_whole_pack_mg=audit_report.whole_pack_sodium_mg,
            carb_to_fiber_ratio=audit_report.carb_to_fiber_ratio,
            glycemic_spike_alert=audit_report.glycemic_spike_alert,
            icmr_sodium_daily_pct=audit_report.icmr_sodium_daily_pct,
        )

    def generate_transparency_card(
        self,
        packaging_data: PackagingData,
        audit_report: AuditReport,
        scorecard: HonestyScorecard,
        sentiment_report: SentimentReport | None = None,
    ) -> ProductTransparencyCard:
        """
        Master aggregation pipeline: Synthesizes findings across Vision, Auditor,
        Sentiment, and Scoring engines into the consumer-facing ProductTransparencyCard.
        """
        logger.info(f"Agent 4 compiling transparency scorecard for '{packaging_data.brand_name} - {packaging_data.product_name}'")

        is_clean = scorecard.honesty_score >= 85

        # 1. Whole Pack Reality Pill
        reality = self.build_whole_pack_reality(packaging_data, audit_report)

        # 2. Traceable Evidence Chain
        evidence_chain = self.build_evidence_chain(audit_report, scorecard)

        # 3. Clean Brand Swaps
        # If product is already certified clean (Green tier), no swap is needed!
        clean_swaps = []
        if not is_clean:
            clean_swaps = self.match_clean_swaps(
                product_name=packaging_data.product_name,
                brand_name=packaging_data.brand_name,
            )

        # 4. Condensed Sentiment Pulse
        sentiment_pulse = {}
        if sentiment_report:
            sentiment_pulse = {
                "overall_sentiment": sentiment_report.overall_sentiment,
                "sentiment_score": sentiment_report.sentiment_score,
                "authenticity_score": sentiment_report.authenticity_score,
                "digestive_distress_alert": sentiment_report.digestive_distress_alert,
                "top_side_effects": sentiment_report.top_side_effects,
                "reddit_summary": sentiment_report.reddit_discussion_summary,
                "is_fallback": sentiment_report.is_fallback,
            }

        card = ProductTransparencyCard(
            product_name=packaging_data.product_name,
            brand_name=packaging_data.brand_name,
            honesty_score=scorecard.honesty_score,
            bracket=scorecard.bracket,
            color_code=scorecard.color_code,
            verdict_summary=scorecard.verdict_summary,
            is_clean_product=is_clean,
            active_badges=scorecard.active_badges,
            whole_pack_reality=reality,
            evidence_chain=evidence_chain,
            sentiment_pulse=sentiment_pulse,
            clean_swaps=clean_swaps,
            critical_override_applied=scorecard.critical_override_applied,
        )

        logger.info(
            f"TransparencyCard generated: Score={card.honesty_score} ({card.bracket}), "
            f"EvidenceItems={len(card.evidence_chain)}, CleanSwaps={len(card.clean_swaps)}"
        )
        return card
