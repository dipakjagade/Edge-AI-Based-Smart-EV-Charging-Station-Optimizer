"""
Main FastAPI Application Entrypoint.
Edge AI Based Smart EV Charging Station Optimizer.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import db_manager
from app.services.ml_service import ml_service
from app.api import (
    routes_health,
    routes_sessions,
    routes_predict,
    routes_optimize,
    routes_datasets,
    routes_models,
    routes_analytics,
    routes_alerts
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    print(f"[*] Starting {settings.PROJECT_NAME} (v{settings.VERSION})...")
    db_manager.connect()
    ml_service.load_model()
    yield
    # Shutdown sequence
    print(f"[*] Shutting down {settings.PROJECT_NAME}...")
    if db_manager.client:
        db_manager.client.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Edge AI software platform for EV charging demand prediction and constrained power allocation optimization.",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local React Vite frontend dev server & edge clients
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(routes_health.router)
app.include_router(routes_sessions.router)
app.include_router(routes_predict.router)
app.include_router(routes_optimize.router)
app.include_router(routes_datasets.router)
app.include_router(routes_models.router)
app.include_router(routes_analytics.router)
app.include_router(routes_alerts.router)


@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs_url": "/docs",
        "health_url": "/health",
        "dashboard_summary_url": "/api/dashboard/summary"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
