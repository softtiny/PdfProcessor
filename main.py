"""
FastAPI PDF Text Extraction Service
Main application entry point
"""
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api import router
from app.config import settings
from app.exceptions import setup_exception_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("PDF Text Extraction API starting up...")
    logger.info(f"Max threads: {settings.max_threads}")
    logger.info(f"Request timeout: {settings.request_timeout}s")
    yield
    # Shutdown logic
    logger.info("PDF Text Extraction API shutting down...")

# Create FastAPI application
app = FastAPI(
    title="PDF Text Extraction API",
    description="A REST API for extracting text from PDFs via URLs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup exception handlers
setup_exception_handlers(app)

# Include API routes
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
