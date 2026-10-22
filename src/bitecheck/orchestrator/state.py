"""
BiteCheck Multi-Agent State Graph Contract (Phase 7).
Defines the strongly-typed shared state machine passed between autonomous agents.
Tracks execution steps, agent payloads, latency benchmarks, and error recovery traces.
"""

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, Field

from bitecheck.schemas.packaging import PackagingData
from bitecheck.schemas.audit import AuditReport
from bitecheck.schemas.sentiment import SentimentReport
from bitecheck.schemas.scorecard import HonestyScorecard


PipelineStep = Literal[
    "INITIALIZED",
    "INGESTING_PACKAGING",
    "PACKAGING_INGESTED",
    "PARALLEL_EVALUATING",
    "EVALUATION_COMPLETED",
    "SCORING_SYNTHESIS",
    "COMPLETED",
    "FAILED",
]


class BiteCheckState(BaseModel):
    """
    Shared State Graph for BiteCheck Multi-Agent Pipeline.
    Maintains an auditable, immutable trail across Vision, Auditor, Sentiment, and Scoring engines.
    """
    session_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique audit session identifier")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Session initialization timestamp")
    current_step: PipelineStep = Field(default="INITIALIZED", description="Current stage in state machine")
    
    # Input File References
    front_image_path: str | None = Field(default=None, description="Path or URI to front packaging photo")
    back_image_path: str | None = Field(default=None, description="Path or URI to back nutrition photo")
    
    # Agent Artifacts
    packaging_data: PackagingData | None = Field(default=None, description="Agent 1 Vision OCR extraction")
    audit_report: AuditReport | None = Field(default=None, description="Agent 2 Deterministic FSSAI audit report")
    sentiment_report: SentimentReport | None = Field(default=None, description="Agent 3 Consumer sentiment & review report")
    scorecard: HonestyScorecard | None = Field(default=None, description="Scoring Engine final honesty scorecard")
    
    # Fault Isolation & Performance Observability
    errors: list[str] = Field(default_factory=list, description="Diagnostic error log captured during state machine transitions")
    execution_times_ms: dict[str, float] = Field(
        default_factory=dict,
        description="Execution latency in milliseconds for each pipeline node (e.g. {'vision': 1200.5, 'audit': 2.1})"
    )
    is_degraded: bool = Field(default=False, description="True if any non-critical branch degraded gracefully (e.g. sentiment fallback)")

    @property
    def is_successful(self) -> bool:
        """Returns True if the pipeline finished and generated a valid scorecard."""
        return self.current_step == "COMPLETED" and self.scorecard is not None

    @property
    def total_latency_ms(self) -> float:
        """Computes total pipeline runtime summed across all executed stages."""
        return sum(self.execution_times_ms.values())
