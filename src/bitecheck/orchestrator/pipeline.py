"""
Multi-Agent State Graph Orchestrator (Phase 7).
Coordinates the lifecycle execution of BiteCheck India:
- Node 1: Vision Ingestion (Agent 1)
- Node 2: Concurrent Parallel Evaluation (Agent 2 Food Auditor & Agent 3 Sentiment Detective)
- Node 3: Mathematical Scoring Engine (Phase 5)
Provides thread-safe state graph transitions, latency profiling, and isolated fault recovery.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from pathlib import Path

from bitecheck.logger import get_logger
from bitecheck.schemas.packaging import PackagingData
from bitecheck.agents.vision_agent import VisionAgent
from bitecheck.agents.food_auditor import FoodAuditor
from bitecheck.agents.sentiment_agent import SentimentAgent
from bitecheck.scoring.engine import ScoringEngine
from bitecheck.orchestrator.state import BiteCheckState

logger = get_logger("bitecheck.orchestrator")


class MultiAgentOrchestrator:
    """
    Central State Machine and Concurrency Engine for BiteCheck India.
    Orchestrates the multi-agent graph with parallel branch dispatch and fault isolation.
    """

    def __init__(
        self,
        vision_agent: VisionAgent | None = None,
        food_auditor: FoodAuditor | None = None,
        sentiment_agent: SentimentAgent | None = None,
        scoring_engine: ScoringEngine | None = None,
    ):
        self.vision_agent = vision_agent or VisionAgent()
        self.food_auditor = food_auditor or FoodAuditor()
        self.sentiment_agent = sentiment_agent or SentimentAgent()
        self.scoring_engine = scoring_engine or ScoringEngine()
        logger.info("MultiAgentOrchestrator initialized with 4 autonomous engine nodes.")

    def run(
        self,
        front_image_path: Path | str | None = None,
        back_image_path: Path | str | None = None,
        packaging_data: PackagingData | None = None,
        session_id: str | None = None,
    ) -> BiteCheckState:
        """
        Executes the full end-to-end multi-agent pipeline.
        Accepts either raw packaging photographs or pre-parsed PackagingData.
        Guarantees that state is never lost and errors are safely contained.
        """
        state = BiteCheckState()
        if session_id:
            state.session_id = session_id

        if front_image_path:
            state.front_image_path = str(front_image_path)
        if back_image_path:
            state.back_image_path = str(back_image_path)

        logger.info(f"Starting Multi-Agent Pipeline [Session ID: {state.session_id}]")

        try:
            # ------------------------------------------------------------------
            # NODE 1: Ingestion & Optical Parsing (Agent 1)
            # ------------------------------------------------------------------
            state.current_step = "INGESTING_PACKAGING"
            t0 = time.perf_counter()

            if packaging_data is not None:
                state.packaging_data = packaging_data
                state.execution_times_ms["vision_ingestion"] = 0.0
                logger.info("Pre-parsed PackagingData provided; skipping OCR ingestion.")
            elif state.front_image_path and state.back_image_path:
                logger.info(f"Dispatching Agent 1 Vision OCR for session {state.session_id}")
                state.packaging_data = self.vision_agent.ingest_packaging(
                    front_image_path=state.front_image_path,
                    back_image_path=state.back_image_path,
                )
                t1 = time.perf_counter()
                state.execution_times_ms["vision_ingestion"] = round((t1 - t0) * 1000, 2)
                logger.info(f"Node 1 (Vision) completed in {state.execution_times_ms['vision_ingestion']}ms")
            else:
                raise ValueError("Neither packaging_data nor front/back image paths were provided to orchestrator.")

            state.current_step = "PACKAGING_INGESTED"

            # ------------------------------------------------------------------
            # NODE 2: Concurrent Parallel Evaluation (Agents 2 & 3)
            # ------------------------------------------------------------------
            state.current_step = "PARALLEL_EVALUATING"
            t_parallel_start = time.perf_counter()
            pkg = state.packaging_data

            logger.info("Dispatching parallel branches: Agent 2 (Auditor) & Agent 3 (Sentiment Detective)...")

            with ThreadPoolExecutor(max_workers=2, thread_name_prefix="BiteCheck-Branch") as executor:
                # Dispatch Branch A: Deterministic Food Auditor
                future_audit = executor.submit(self._run_audit_branch, pkg)
                # Dispatch Branch B: Consumer Sentiment Detective
                future_sentiment = executor.submit(self._run_sentiment_branch, pkg)

                # Collect Branch A (Auditor)
                try:
                    audit_res, audit_time_ms = future_audit.result()
                    state.audit_report = audit_res
                    state.execution_times_ms["deterministic_audit"] = audit_time_ms
                except Exception as audit_err:
                    logger.error(f"Critical failure in Agent 2 Audit Branch: {audit_err}", exc_info=True)
                    state.errors.append(f"Agent 2 Audit Error: {audit_err}")

                # Collect Branch B (Sentiment Detective)
                try:
                    sentiment_res, sentiment_time_ms = future_sentiment.result()
                    state.sentiment_report = sentiment_res
                    state.execution_times_ms["sentiment_detective"] = sentiment_time_ms
                    if sentiment_res.is_fallback:
                        state.is_degraded = True
                        logger.warning("Sentiment branch degraded; continuing with audit and scoring.")
                except Exception as sent_err:
                    logger.error(f"Unexpected crash in Agent 3 Sentiment Branch: {sent_err}", exc_info=True)
                    state.errors.append(f"Agent 3 Sentiment Error: {sent_err}")
                    state.is_degraded = True

            t_parallel_end = time.perf_counter()
            state.execution_times_ms["parallel_evaluation_wall_time"] = round((t_parallel_end - t_parallel_start) * 1000, 2)
            logger.info(
                f"Node 2 (Parallel Evaluation) completed in {state.execution_times_ms['parallel_evaluation_wall_time']}ms "
                f"[Audit: {state.execution_times_ms.get('deterministic_audit', 0)}ms, "
                f"Sentiment: {state.execution_times_ms.get('sentiment_detective', 0)}ms]"
            )

            if not state.audit_report:
                raise RuntimeError("Deterministic Audit branch failed to produce an AuditReport; cannot calculate score.")

            state.current_step = "EVALUATION_COMPLETED"

            # ------------------------------------------------------------------
            # NODE 3: Mathematical Scoring Synthesis (Scoring Engine)
            # ------------------------------------------------------------------
            state.current_step = "SCORING_SYNTHESIS"
            t_score_start = time.perf_counter()

            logger.info("Executing Node 3: Deductive Mathematical Scoring Engine...")
            state.scorecard = self.scoring_engine.calculate_score(
                report=state.audit_report,
                product_name=pkg.product_name,
                brand_name=pkg.brand_name,
            )

            t_score_end = time.perf_counter()
            state.execution_times_ms["scoring_engine"] = round((t_score_end - t_score_start) * 1000, 2)
            logger.info(f"Node 3 (Scoring Engine) completed in {state.execution_times_ms['scoring_engine']}ms")

            # Finalize State
            state.current_step = "COMPLETED"
            logger.info(
                f"Pipeline successfully completed for '{pkg.brand_name} - {pkg.product_name}': "
                f"Score={state.scorecard.honesty_score}/100 [{state.scorecard.bracket}], "
                f"Total Wall Time={state.total_latency_ms:.1f}ms, Degraded={state.is_degraded}"
            )
            return state

        except Exception as exc:
            state.current_step = "FAILED"
            state.errors.append(str(exc))
            logger.error(f"Pipeline execution halted with error: {exc}", exc_info=True)
            return state

    def _run_audit_branch(self, pkg: PackagingData) -> tuple:
        """Executes Agent 2 Deterministic Food Auditor with millisecond timing."""
        t0 = time.perf_counter()
        report = self.food_auditor.audit(pkg)
        t1 = time.perf_counter()
        return report, round((t1 - t0) * 1000, 2)

    def _run_sentiment_branch(self, pkg: PackagingData) -> tuple:
        """Executes Agent 3 Consumer Sentiment Detective with millisecond timing."""
        t0 = time.perf_counter()
        report = self.sentiment_agent.analyze_sentiment(
            brand_name=pkg.brand_name,
            product_name=pkg.product_name,
            front_claims=pkg.front_claims,
        )
        t1 = time.perf_counter()
        return report, round((t1 - t0) * 1000, 2)
