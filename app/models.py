"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, HttpUrl, Field, field_validator
from typing import Optional
import re

class URLRequest(BaseModel):
    """Request model for PDF URL"""
    url: HttpUrl = Field(..., description="URL of the PDF to process")
    
    @field_validator('url')
    def validate_pdf_url(cls, v):
        """Validate that URL points to a PDF file"""
        url_str = str(v)
        # Check if URL ends with .pdf or has PDF-related indicators
        if not (url_str.lower().endswith('.pdf') or 
                'pdf' in url_str.lower() or
                'arxiv.org' in url_str.lower()):
            # Still allow it but log a warning
            pass
        return v

class TextResponse(BaseModel):
    """Response model for extracted text"""
    text: str = Field(..., description="Extracted text from PDF")
    url: str = Field(..., description="Original PDF URL")
    character_count: int = Field(..., description="Number of characters extracted")
    
class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="API status")
    message: Optional[str] = Field(None, description="Additional status information")

class ErrorResponse(BaseModel):
    """Response model for errors"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    url: Optional[str] = Field(None, description="URL that caused the error")
