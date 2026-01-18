from fastapi import FastAPI, status
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="Controlla Test Pipeline API",
    description="A simple FastAPI application",
    version="1.0.0"
)


class HealthResponse(BaseModel):
    status: str
    message: str


class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None


@app.get("/")
async def root():
    """Root endpoint returning a welcome message."""
    return {"message": "Welcome to Controlla Test Pipeline API"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Service is running"
    )


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: Optional[str] = None):
    """Get an item by ID with optional query parameter."""
    return {"item_id": item_id, "q": q}


@app.post("/items/", status_code=status.HTTP_201_CREATED)
async def create_item(item: Item):
    """Create a new item."""
    item_dict = item.model_dump()
    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})
    return item_dict
