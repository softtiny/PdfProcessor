# PDF Text Extraction API

A FastAPI-based REST API for extracting text from PDFs via URLs with multi-threading support and robust error handling.

## Features

- **REST API**: Clean FastAPI-based REST endpoints
- **PDF Processing**: Robust text extraction using PyMuPDF
- **Multi-threading**: Efficient concurrent processing of multiple URLs
- **Error Handling**: Comprehensive error handling for various failure scenarios
- **Input Validation**: Pydantic-based request/response validation
- **Docker Support**: Containerized deployment with Docker
- **Testing**: Comprehensive unit test suite with pytest
- **Documentation**: Auto-generated OpenAPI/Swagger documentation

## API Endpoints

### POST /get_text
Extract text from a PDF at the provided URL.

**Request:**
```json
{
    "url": "https://arxiv.org/pdf/2105.00001.pdf"
}
