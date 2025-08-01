"""
Unit tests for PDF processor module
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import io
import aiohttp

from app.pdf_processor import PDFProcessor
from app.exceptions import PDFProcessingError, URLError, TimeoutError


class MockAsyncIterator:
    def __init__(self, chunks):
        self.chunks = chunks
        self.maxidx=len(chunks)
        self.index = 0
        self.step=1
    def __call__(self,step):
        self.step = step
        return self

    def __aiter__(self):
        return self

    async def __anext__(self):
        if (self.index+self.step) < self.maxidx:
            result = self.chunks[self.index:(self.index+self.step)]
            self.index += self.step
            return b''.join(result)
        elif self.index < self.maxidx:
            result = self.chunks[self.index:self.maxidx]
            self.index = self.maxidx
            return b''.join(result)
        raise StopAsyncIteration


class TestPDFProcessor:
    """Test PDF processor functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.processor = PDFProcessor()
    
    @pytest.mark.asyncio
    async def test_extract_text_from_url_success(self):
        """Test successful text extraction from URL"""
        # Mock PDF content
        mock_pdf_content = b"%PDF-1.4 mock pdf content"
        
        with patch.object(self.processor, '_download_pdf') as mock_download, \
             patch.object(self.processor, '_extract_text_from_bytes') as mock_extract:
            
            mock_download.return_value = mock_pdf_content
            mock_extract.return_value = "Extracted text content"
            
            result = await self.processor.extract_text_from_url("https://example.com/test.pdf")
            
            assert result == "Extracted text content"
            mock_download.assert_called_once_with("https://example.com/test.pdf")
            mock_extract.assert_called_once_with(mock_pdf_content)
    
    @pytest.mark.asyncio
    async def test_extract_text_from_url_download_failure(self):
        """Test text extraction with download failure"""
        with patch.object(self.processor, '_download_pdf') as mock_download:
            mock_download.side_effect = URLError("Download failed")
            
            with pytest.raises(URLError, match="Download failed"):
                await self.processor.extract_text_from_url("https://example.com/test.pdf")
    
    @pytest.mark.asyncio
    async def test_extract_text_from_url_processing_failure(self):
        """Test text extraction with processing failure"""
        mock_pdf_content = b"invalid pdf content"
        
        with patch.object(self.processor, '_download_pdf') as mock_download, \
             patch.object(self.processor, '_extract_text_from_bytes') as mock_extract:
            
            mock_download.return_value = mock_pdf_content
            mock_extract.side_effect = PDFProcessingError("Invalid PDF")
            
            with pytest.raises(PDFProcessingError, match="Invalid PDF"):
                await self.processor.extract_text_from_url("https://example.com/test.pdf")
    
    @pytest.mark.asyncio
    async def test_extract_text_empty_result(self):
        """Test text extraction with empty result"""
        mock_pdf_content = b"%PDF-1.4 mock pdf content"
        
        with patch.object(self.processor, '_download_pdf') as mock_download, \
             patch.object(self.processor, '_extract_text_from_bytes') as mock_extract:
            
            mock_download.return_value = mock_pdf_content
            mock_extract.return_value = ""
            
            with pytest.raises(PDFProcessingError, match="No text content found"):
                await self.processor.extract_text_from_url("https://example.com/test.pdf")
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_download_pdf_success(self,mock_function):
        """Test successful PDF download"""
        mock_content = b"%PDF-1.4 mock pdf content"
        
        # Mock aiohttp response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {'content-type': 'application/pdf', 'content-length': str(len(mock_content))}
        mock_response.content.iter_chunked = MockAsyncIterator([mock_content])
        # mock_session = MagicMock()
        # mock_session.get.return_value.__aenter__.return_value = mock_response
        
        #with patch('aiohttp.ClientSession.get') as mock_function:
        mock_function.return_value.__aenter__.return_value = mock_response
        result = await self.processor._download_pdf("https://example.com/test.pdf")
        assert result == mock_content
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_download_pdf_http_error(self,mock_function):
        """Test PDF download with HTTP error"""
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.reason = "Not Found"
        
        mock_function.return_value.__aenter__.return_value = mock_response
        
        with pytest.raises(URLError, match="HTTP 404"):
            await self.processor._download_pdf("https://example.com/test.pdf")
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_download_pdf_file_too_large(self,mock_function):
        """Test PDF download with file too large"""
        large_size = str(self.processor.max_file_size + 1)
        
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {'content-length': large_size}
        
        mock_function.return_value.__aenter__.return_value = mock_response
        
        with pytest.raises(URLError, match="File too large"):
            await self.processor._download_pdf("https://example.com/test.pdf")
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_download_pdf_timeout(self,mock_function):
        """Test PDF download with timeout"""
        mock_function.return_value.__aenter__.side_effect = asyncio.TimeoutError()

        with pytest.raises(TimeoutError, match="Download timed out"):
            await self.processor._download_pdf("https://example.com/test.pdf")
    
    def test_extract_text_from_bytes_success(self):
        """Test successful text extraction from bytes"""
        # This would require a real PDF file for testing
        # For now, we'll mock the fitz library
        with patch('fitz.open') as mock_fitz:
            mock_doc = MagicMock()
            mock_doc.is_encrypted = False
            mock_doc.page_count = 1
            
            mock_page = MagicMock()
            mock_page.get_text.return_value = "Sample PDF text content"
            mock_doc.__getitem__.return_value = mock_page
            
            mock_fitz.return_value = mock_doc
            
            result = self.processor._extract_text_from_bytes(b"mock pdf bytes")
            assert "Sample PDF text content" in result
    
    def test_extract_text_from_bytes_encrypted(self):
        """Test text extraction from encrypted PDF"""
        with patch('fitz.open') as mock_fitz:
            mock_doc = MagicMock()
            mock_doc.is_encrypted = True
            mock_fitz.return_value = mock_doc
            
            with pytest.raises(PDFProcessingError, match="PDF is encrypted"):
                self.processor._extract_text_from_bytes(b"mock pdf bytes")
    
    def test_extract_text_from_bytes_no_pages(self):
        """Test text extraction from PDF with no pages"""
        with patch('fitz.open') as mock_fitz:
            mock_doc = MagicMock()
            mock_doc.is_encrypted = False
            mock_doc.page_count = 0
            mock_fitz.return_value = mock_doc
            
            with pytest.raises(PDFProcessingError, match="PDF has no pages"):
                self.processor._extract_text_from_bytes(b"mock pdf bytes")
    
    def test_extract_text_from_bytes_invalid_pdf(self):
        """Test text extraction from invalid PDF"""
        with patch('fitz.open') as mock_fitz:
            mock_fitz.side_effect = Exception("Invalid PDF format")
            
            with pytest.raises(PDFProcessingError, match="PDF processing failed"):
                self.processor._extract_text_from_bytes(b"invalid pdf bytes")
    
    def test_clean_text(self):
        """Test text cleaning functionality"""
        dirty_text = "  Line 1  \n\n  \n  Line 2   \n\n\n  Line 3  "
        cleaned = self.processor._clean_text(dirty_text)
        expected = "Line 1\nLine 2\nLine 3"
        assert cleaned == expected
    
    @pytest.mark.asyncio
    async def test_extract_text_from_multiple_urls(self):
        """Test extracting text from multiple URLs"""
        urls = [
            "https://example.com/test1.pdf",
            "https://example.com/test2.pdf",
            "https://example.com/test3.pdf"
        ]
        
        with patch.object(self.processor, 'extract_text_from_url') as mock_extract:
            # Mock successful extraction for first two URLs, failure for third
            mock_extract.side_effect = [
                "Text from PDF 1",
                "Text from PDF 2",
                URLError("Download failed")
            ]
            
            result = await self.processor.extract_text_from_multiple_urls(urls)
            
            assert result["total_processed"] == 3
            assert result["successful"] == 2
            assert result["failed"] == 1
            assert len(result["results"]) == 2
            assert len(result["errors"]) == 1

if __name__ == "__main__":
    pytest.main([__file__])
