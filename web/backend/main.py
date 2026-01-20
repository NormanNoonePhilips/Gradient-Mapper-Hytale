"""FastAPI main application"""
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .api import routes, websocket
from .services.gradient_scanner import GradientScanner
from .services.job_queue import JobQueue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Gradient Mapper Web UI",
    description="Apply gradient maps to images with real-time preview and batch processing",
    version="1.0.0"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Folder paths
BASE_DIR = Path(__file__).parent.parent.parent
INPUT_FOLDER = BASE_DIR / "input"
GRADIENT_FOLDER = BASE_DIR / "gradient"
OUTPUT_FOLDER = BASE_DIR / "output"
FRONTEND_DIR = BASE_DIR / "web" / "frontend"

# Ensure folders exist
INPUT_FOLDER.mkdir(parents=True, exist_ok=True)
GRADIENT_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# Initialize services
gradient_scanner = GradientScanner(GRADIENT_FOLDER)
job_queue = JobQueue(INPUT_FOLDER, GRADIENT_FOLDER, OUTPUT_FOLDER)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Gradient Mapper Web UI...")
    logger.info(f"Base directory: {BASE_DIR}")
    logger.info(f"Input folder: {INPUT_FOLDER}")
    logger.info(f"Gradient folder: {GRADIENT_FOLDER}")
    logger.info(f"Output folder: {OUTPUT_FOLDER}")
    logger.info(f"Frontend directory: {FRONTEND_DIR}")

    # Scan gradients
    gradient_scanner.initialize()

    # Set dependencies in routes
    routes.set_dependencies(
        gradient_scanner,
        job_queue,
        INPUT_FOLDER,
        OUTPUT_FOLDER
    )

    # Set dependencies in websocket
    websocket.set_job_queue(job_queue)

    logger.info("Gradient Mapper Web UI started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Gradient Mapper Web UI...")


# Include routers
app.include_router(routes.router)
app.include_router(websocket.router)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def read_root():
    """Serve frontend HTML"""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        return {"message": "Gradient Mapper API", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "gradients_loaded": gradient_scanner.catalog is not None,
        "gradient_count": gradient_scanner.catalog.total_count if gradient_scanner.catalog else 0
    }
