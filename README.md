# controlla-test-pipeline

A simple FastAPI Python application with basic endpoints.

## Features

- FastAPI web framework
- RESTful API endpoints
- Health check endpoint
- Pydantic models for request/response validation
- Interactive API documentation (Swagger UI)

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/zzoutop/controlla-test-pipeline.git
cd controlla-test-pipeline
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the development server:

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

## API Documentation

Once the application is running, you can access:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## Available Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check endpoint
- `GET /items/{item_id}` - Get an item by ID
- `POST /items/` - Create a new item

## Example Usage

### Health Check
```bash
curl http://127.0.0.1:8000/health
```

### Get Item
```bash
curl http://127.0.0.1:8000/items/1?q=test
```

### Create Item
```bash
curl -X POST http://127.0.0.1:8000/items/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Item", "description": "A test item", "price": 10.5, "tax": 1.5}'
```

## Project Structure

```
controlla-test-pipeline/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── .gitignore          # Git ignore file
└── README.md           # This file
```