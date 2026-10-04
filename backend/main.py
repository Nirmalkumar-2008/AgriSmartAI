"""
AgriSmartAI - Main FastAPI Application Server with Mounted React Frontend
Entry point for Uvicorn REST API server and static web UI hosting.
"""

import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from backend.routes import predict, feedback
from backend.services.prediction_service import PredictionService
from backend.middleware.error_handler import validation_exception_handler

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager: loads ML models once during server startup."""
    print("Initializing AgriSmartAI REST API Server...")
    PredictionService.initialize_models()
    yield
    print("Shutting down AgriSmartAI REST API Server...")

app = FastAPI(
    title="AgriSmartAI | An Intelligent Machine Learning-Based Decision Support System for Crop Recommendation, Yield Prediction, Fertilizer Optimization, and Smart Irrigation Management",
    description="Production-ready AI decision support system powering Crop Recommendation, Yield Prediction, Fertilizer Strategy, Smart Irrigation, SHAP Explainability, and Agricultural Insights.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Include API Routers
app.include_router(predict.router)
app.include_router(feedback.router)

# Serve React Frontend Static Files with Cache-Busting Headers
frontend_dir = os.path.join(project_root, "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", include_in_schema=False)
    @app.get("/app", include_in_schema=False)
    @app.get("/ui", include_in_schema=False)
    def serve_frontend_app():
        return FileResponse(
            os.path.join(frontend_dir, "index.html"),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )

    @app.get("/favicon.ico", include_in_schema=False)
    def serve_favicon():
        from fastapi.responses import Response
        svg_favicon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🌱</text></svg>'
        return Response(content=svg_favicon, media_type="image/svg+xml")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
