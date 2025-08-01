"""
Custom exceptions and error handlers
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)

class PDFProcessingError(Exception):
    """Exception raised when PDF processing fails"""
    pass

class URLError(Exception):
    """Exception raised when URL is invalid or inaccessible"""
    pass

class TimeoutError(Exception):
    """Exception raised when request times out"""
    pass

def setup_exception_handlers(app: FastAPI):
    """Setup custom exception handlers for the FastAPI app"""
    
    @app.exception_handler(PDFProcessingError)
    async def pdf_processing_exception_handler(request: Request, exc: PDFProcessingError):
        logger.error(f"PDF processing error: {str(exc)}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "PDF Processing Error",
                "message": str(exc),
                "type": "pdf_processing_error"
            }
        )
    
    @app.exception_handler(URLError)
    async def url_exception_handler(request: Request, exc: URLError):
        logger.error(f"URL error: {str(exc)}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "URL Error",
                "message": str(exc),
                "type": "url_error"
            }
        )
    
    @app.exception_handler(TimeoutError)
    async def timeout_exception_handler(request: Request, exc: TimeoutError):
        logger.error(f"Timeout error: {str(exc)}")
        return JSONResponse(
            status_code=408,
            content={
                "error": "Timeout Error",
                "message": str(exc),
                "type": "timeout_error"
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"Validation error: {str(exc)}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "Validation Error",
                "message": "Invalid request data",
                "details": exc.errors(),
                "type": "validation_error"
            }
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": f"HTTP {exc.status_code}",
                "message": exc.detail,
                "type": "http_error"
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "type": "internal_error"
            }
        )
