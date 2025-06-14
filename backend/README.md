# Perplexica Backend

This is the backend service for Perplexica, implementing core functionalities in Python.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the backend directory with:
```
SEARXNG_API_URL=your_searxng_endpoint_here
```

## Running the Service

Start the FastAPI server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once the server is running, you can access:
- API documentation: http://localhost:8000/docs
- Alternative API documentation: http://localhost:8000/redoc

## Available Endpoints

### Search
- `GET /api/v1/search`
  - Parameters:
    - `q` (required): Search query
    - `categories` (optional): Comma-separated list of categories
    - `engines` (optional): Comma-separated list of engines
    - `language` (optional): Search language
    - `pageno` (optional): Page number

## Development

The backend is built with:
- FastAPI - Modern web framework for building APIs
- httpx - Async HTTP client
- Pydantic - Data validation
- python-dotenv - Environment variable management 