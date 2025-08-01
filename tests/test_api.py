"""
Unit tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import asyncio

from main import app
from app.exceptions import PDFProcessingError, URLError, TimeoutError

client = TestClient(app)

class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check_success(self):
        """Test successful health check"""
        response = client.get("/health_check")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data

class TestExtractText:
    """Test text extraction endpoint"""
    
    def test_extract_text_success(self):
        """Test successful text extraction"""
        with patch('app.pdf_processor.PDFProcessor.extract_text_from_url') as mock_extract:
            mock_extract.return_value = "Sample extracted text from PDF"
            
            response = client.post(
                "/get_text",
                json={"url": "https://example.com/sample.pdf"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "text" in data
            assert "url" in data
            assert "character_count" in data
            assert data["url"] == "https://example.com/sample.pdf"
    
    def test_extract_text_invalid_url(self):
        """Test text extraction with invalid URL"""
        response = client.post(
            "/get_text",
            json={"url": "not-a-valid-url"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_extract_text_missing_url(self):
        """Test text extraction with missing URL"""
        response = client.post(
            "/get_text",
            json={}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
    
    def test_extract_text_url_error(self):
        """Test text extraction with URL error"""
        with patch('app.pdf_processor.PDFProcessor.extract_text_from_url') as mock_extract:
            mock_extract.side_effect = URLError("Failed to download PDF")
            
            response = client.post(
                "/get_text",
                json={"url": "https://example.com/nonexistent.pdf"}
            )
            
            assert response.status_code == 400
            data = response.json()
            assert "URL error" in data["message"]
    
    def test_extract_text_pdf_processing_error(self):
        """Test text extraction with PDF processing error"""
        with patch('app.pdf_processor.PDFProcessor.extract_text_from_url') as mock_extract:
            mock_extract.side_effect = PDFProcessingError("Corrupted PDF file")
            
            response = client.post(
                "/get_text",
                json={"url": "https://example.com/corrupted.pdf"}
            )
            
            assert response.status_code == 422
            data = response.json()
            assert "PDF processing error" in data["message"]
    
    def test_extract_text_timeout_error(self):
        """Test text extraction with timeout error"""
        with patch('app.pdf_processor.PDFProcessor.extract_text_from_url') as mock_extract:
            mock_extract.side_effect = TimeoutError("Request timeout")
            
            response = client.post(
                "/get_text",
                json={"url": "https://example.com/slow.pdf"}
            )
            
            assert response.status_code == 408
            data = response.json()
            assert "Request timeout" in data["message"]

class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns API information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert data["version"] == "1.0.0"

class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_internal_server_error(self):
        """Test internal server error handling"""
        with patch('app.pdf_processor.PDFProcessor.extract_text_from_url') as mock_extract:
            mock_extract.side_effect = Exception("Unexpected error")
            
            response = client.post(
                "/get_text",
                json={"url": "https://example.com/test.pdf"}
            )
            
            assert response.status_code == 500
            data = response.json()
            
            assert "Internal server error" in data["message"]
    
    def test_malformed_json(self):
        """Test malformed JSON request"""
        response = client.post(
            "/get_text",
            content="not-json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400

if __name__ == "__main__":
    pytest.main([__file__])
