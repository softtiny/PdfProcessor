"""
FastAPI routes and endpoint handlers
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any

from .models import URLRequest, TextResponse, HealthResponse
from .pdf_processor import PDFProcessor
from .exceptions import PDFProcessingError, URLError, TimeoutError

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize PDF processor
pdf_processor = PDFProcessor()

@router.get("/health_check", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint to verify API status
    
    Returns:
        HealthResponse: API status information
    """
    try:
        return HealthResponse(status="ok", message="API is running")
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")

@router.post("/get_text", response_model=TextResponse)
async def extract_text_from_pdf(request: URLRequest) -> TextResponse:
    """
    Extract text from PDF at the provided URL
    
    Args:
        request: URLRequest containing the PDF URL
        
    Returns:
        TextResponse: Extracted text content
        
    Raises:
        HTTPException: For various error conditions
    """
    try:
        logger.info(f"Processing PDF from URL: {request.url}")
        
        # Extract text from PDF
        extracted_text = await pdf_processor.extract_text_from_url(str(request.url))
        
        logger.info(f"Successfully extracted {len(extracted_text)} characters from PDF")
        
        return TextResponse(
            text=extracted_text,
            url=str(request.url),
            character_count=len(extracted_text)
        )
        
    except URLError as e:
        logger.error(f"URL error for {request.url}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"URL error: {str(e)}")
        
    except TimeoutError as e:
        logger.error(f"Timeout error for {request.url}: {str(e)}")
        raise HTTPException(status_code=408, detail=f"Request timeout: {str(e)}")
        
    except PDFProcessingError as e:
        logger.error(f"PDF processing error for {request.url}: {str(e)}")
        raise HTTPException(status_code=422, detail=f"PDF processing error: {str(e)}")
        
    except Exception as e:
        logger.error(f"Unexpected error processing {request.url}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "PDF Text Extraction API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health_check",
            "extract": "/get_text",
            "docs": "/docs"
        }
    }
