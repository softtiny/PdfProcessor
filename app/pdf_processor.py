"""
PDF processing module with multi-threading support
"""
import asyncio
import aiohttp
import fitz  # PyMuPDF
import io
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import time

from .config import settings
from .exceptions import PDFProcessingError, URLError, TimeoutError

logger = logging.getLogger(__name__)

class PDFProcessor:
    """PDF processing class with multi-threading capabilities"""
    
    def __init__(self):
        self.max_threads = settings.max_threads
        self.request_timeout = settings.request_timeout
        self.max_file_size = settings.max_file_size_mb * 1024 * 1024  # Convert to bytes
        
    async def extract_text_from_url(self, url: str) -> str:
        """
        Extract text from a PDF at the given URL
        
        Args:
            url: URL of the PDF to process
            
        Returns:
            str: Extracted text content
            
        Raises:
            URLError: If URL is invalid or inaccessible
            PDFProcessingError: If PDF cannot be processed
            TimeoutError: If request times out
        """
        try:
            # Download PDF content
            pdf_content = await self._download_pdf(url)
            
            # Extract text in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=1) as executor:
                text = await loop.run_in_executor(
                    executor, 
                    self._extract_text_from_bytes, 
                    pdf_content
                )
            
            if not text or not text.strip():
                raise PDFProcessingError("No text content found in PDF")
                
            return text.strip()
            
        except aiohttp.ClientError as e:
            raise URLError(f"Failed to download PDF: {str(e)}")
        except asyncio.TimeoutError:
            raise TimeoutError(f"Request timed out after {self.request_timeout} seconds")
        except Exception as e:
            if isinstance(e, (URLError, PDFProcessingError, TimeoutError)):
                raise
            raise PDFProcessingError(f"Unexpected error: {str(e)}")
    
    async def _download_pdf(self, url: str) -> bytes:
        """
        Download PDF content from URL
        
        Args:
            url: PDF URL
            
        Returns:
            bytes: PDF content
            
        Raises:
            URLError: If download fails
            TimeoutError: If request times out
        """
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, allow_redirects=True) as response:
                    # Check if response is successful
                    if response.status != 200:
                        print("------------------------------>>")
                        print(response)
                        raise URLError(f"HTTP {response.status}: {response.reason}")
                    
                    # Check content type
                    content_type = response.headers.get('content-type', '').lower()
                    if content_type and 'pdf' not in content_type:
                        logger.warning(f"Content-Type is {content_type}, expected PDF")
                    
                    # Check file size
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > self.max_file_size:
                        raise URLError(f"File too large: {content_length} bytes")
                    
                    # Read content with size limit
                    content = await self._read_with_limit(response, self.max_file_size)
                    
                    if len(content) == 0:
                        raise URLError("Empty file downloaded")
                    
                    return content
                    
        except asyncio.TimeoutError:
            raise TimeoutError(f"Download timed out after {self.request_timeout} seconds")
        except aiohttp.ClientError as e:
            raise URLError(f"Download failed: {str(e)}")
    
    async def _read_with_limit(self, response: aiohttp.ClientResponse, limit: int) -> bytes:
        """
        Read response content with size limit
        
        Args:
            response: aiohttp response object
            limit: Maximum bytes to read
            
        Returns:
            bytes: Response content
            
        Raises:
            URLError: If file exceeds size limit
        """
        content = b""
        async for chunk in response.content.iter_chunked(8192):
            content += chunk
            if len(content) > limit:
                raise URLError(f"File exceeds maximum size limit of {limit} bytes")
        return content
    
    def _extract_text_from_bytes(self, pdf_content: bytes) -> str:
        """
        Extract text from PDF bytes using PyMuPDF
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            str: Extracted text
            
        Raises:
            PDFProcessingError: If PDF processing fails
        """
        try:
            # Open PDF document from bytes
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            
            if doc.is_encrypted:
                raise PDFProcessingError("PDF is encrypted and cannot be processed")
            
            if doc.page_count == 0:
                raise PDFProcessingError("PDF has no pages")
            
            # Extract text from all pages
            text_parts = []
            for page_num in range(doc.page_count):
                try:
                    page = doc[page_num]
                    page_text = page.get_text("text")
                    if page_text.strip():
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {str(e)}")
                    continue
            
            doc.close()
            
            if not text_parts:
                raise PDFProcessingError("No readable text found in PDF")
            
            # Join all text parts
            full_text = "\n\n".join(text_parts)
            
            # Basic text cleaning
            full_text = self._clean_text(full_text)
            
            return full_text
            
        except fitz.FileDataError:
            raise PDFProcessingError("Invalid or corrupted PDF file")
        except Exception as e:
            if isinstance(e, PDFProcessingError):
                raise
            raise PDFProcessingError(f"PDF processing failed: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text
        
        Args:
            text: Raw extracted text
            
        Returns:
            str: Cleaned text
        """
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:  # Skip empty lines
                cleaned_lines.append(line)
        
        # Join with single newlines
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove excessive spaces
        import re
        cleaned_text = re.sub(r' +', ' ', cleaned_text)
        
        return cleaned_text
    
    async def extract_text_from_multiple_urls(self, urls: List[str]) -> Dict[str, Any]:
        """
        Extract text from multiple URLs concurrently
        
        Args:
            urls: List of PDF URLs
            
        Returns:
            Dict containing results and errors
        """
        results = {}
        errors = {}
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.max_threads)
        
        async def process_single_url(url: str):
            async with semaphore:
                try:
                    text = await self.extract_text_from_url(url)
                    return url, text, None
                except Exception as e:
                    return url, None, str(e)
        
        # Process all URLs concurrently
        tasks = [process_single_url(url) for url in urls]
        
        for task in asyncio.as_completed(tasks):
            url, text, error = await task
            if error:
                errors[url] = error
            else:
                results[url] = text
        
        return {
            "results": results,
            "errors": errors,
            "total_processed": len(urls),
            "successful": len(results),
            "failed": len(errors)
        }
