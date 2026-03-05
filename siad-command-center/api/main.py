"""SIAD Command Center FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from api.config import API_PREFIX, CORS_ORIGINS, TILES_DIR
from api.routes import aoi, detection, tiles
from api.services.data_loader import data_loader


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown."""
    # Startup: data_loader already initialized
    yield
    # Shutdown: close HDF5 file
    data_loader.close()


# Create FastAPI app
app = FastAPI(
    title="SIAD Command Center API",
    description="Backend API for Satellite Intelligence Anomaly Detection",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for tile imagery
app.mount("/static/tiles", StaticFiles(directory=str(TILES_DIR)), name="tiles")

# Include routers
app.include_router(aoi.router, prefix=API_PREFIX)
app.include_router(detection.router, prefix=API_PREFIX)
app.include_router(tiles.router, prefix=API_PREFIX)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SIAD Command Center API",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "SIAD Command Center API",
        "docs": "/docs",
        "health": "/health"
    }
