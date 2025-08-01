"""
Configuration settings for the PDF processing API
"""
import os
from typing import Optional

class Settings:
    """Application settings"""
    
    # Threading configuration
    max_threads: int = int(os.getenv("MAX_THREADS", "5"))
    
    # Request timeout in seconds
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # Maximum file size in MB
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    
    # Logging level
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API configuration
    api_title: str = "PDF Text Extraction API"
    api_version: str = "1.0.0"
    api_description: str = "A REST API for extracting text from PDFs via URLs"
    
    # CORS settings
    allow_origins: list = ["*"]
    allow_credentials: bool = True
    allow_methods: list = ["*"]
    allow_headers: list = ["*"]

# Global settings instance
settings = Settings()
