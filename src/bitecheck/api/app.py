"""
FastAPI Application Layer for BiteCheck India (Phase 9).
Serves the REST API for multi-agent food audits, image uploads, clean swaps,
and serves the Single Page Application (SPA) dashboard.
"""

from pathlib import Path
import tempfile
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from bitecheck.logger import get_logger
from bitecheck.config import settings
from bitecheck.schemas.packaging import PackagingData
from bitecheck.orchestrator.pipeline import MultiAgentOrchestrator

logger = get_logger("bitecheck.api")

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app() -> FastAPI:
    """Factory creating and configuring the BiteCheck FastAPI server."""
    app = FastAPI(
        title="BiteCheck India API",
        description="Autonomous Multimodal Food & Beverage Multi-Agent System",
        version="1.0.0",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    orchestrator = MultiAgentOrchestrator()

    @app.get("/health")
    async def health_check():
        """Health check endpoint providing runtime operational status."""
        return {
            "status": "healthy",
            "service": "BiteCheck India",
            "environment": settings.app_env,
            "version": "1.0.0",
        }

    @app.get("/api/swaps")
    async def get_swaps():
        """Returns the curated Indian FMCG clean swaps directory."""
        return orchestrator.transparency_agent.swaps_db

    @app.post("/api/audit/json")
    async def audit_json(packaging_data: PackagingData):
        """
        Fast-path audit endpoint: Evaluates pre-parsed PackagingData through
        Agent 2 (Auditor), Agent 3 (Sentiment), Scoring Engine, and Agent 4 (Transparency).
        """
        try:
            logger.info(f"API received JSON audit for: {packaging_data.brand_name} {packaging_data.product_name}")
            state = orchestrator.run(packaging_data=packaging_data)
            return state.model_dump(mode="json")
        except Exception as e:
            logger.error(f"Audit failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/audit/upload")
    async def audit_upload(
        front_image: UploadFile = File(...),
        back_image: UploadFile = File(...),
    ):
        """
        Full multimodal audit endpoint: Upload front and back packaging photos,
        extracts text via Agent 1 (Gemini Vision), and runs the entire state graph.
        """
        temp_dir = Path(tempfile.mkdtemp(prefix="bitecheck_upload_"))
        try:
            front_path = temp_dir / front_image.filename
            back_path = temp_dir / back_image.filename

            with open(front_path, "wb") as f:
                shutil.copyfileobj(front_image.file, f)
            with open(back_path, "wb") as f:
                shutil.copyfileobj(back_image.file, f)

            logger.info(f"Saved uploaded images to {temp_dir}; initiating multi-agent audit")
            state = orchestrator.run(
                front_image_path=front_path,
                back_image_path=back_path,
            )
            return state.model_dump(mode="json")
        except Exception as e:
            logger.error(f"Multimodal upload audit failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # Mount static assets for frontend SPA
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

        @app.get("/")
        async def serve_index():
            return FileResponse(STATIC_DIR / "index.html")

    return app


app = create_app()
