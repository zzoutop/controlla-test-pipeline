import uuid
from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Union
from google.cloud import storage
from datetime import timedelta
from google.oauth2 import service_account
from src.database.supabase_db import get_db
import modal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # CORS settings
    cors_origins: Union[List[str], str] = ["http://localhost:5173"]

    # Google Cloud settings
    gcp_credentials_path: str = "controlla-4552f-327246db5a7b.json"
    gcp_project_id: str = "controlla-4552f"
    gcp_service_account_email: str = (
        "controlla-test-training-zz@controlla-4552f.iam.gserviceaccount.com"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string (comma-separated) or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from .env that aren't defined in this Settings class
    )


# Initialize settings
settings = Settings()

app = FastAPI(
    title="Controlla Test Pipeline API",
    description="A simple FastAPI application",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


class HealthResponse(BaseModel):
    status: str
    message: str


class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    tax: Optional[float] = None


class SignedUrlRequest(BaseModel):
    bucket_name: str
    blob_name: str
    expiration: Optional[int] = 3600  # Default to 1 hour in seconds
    method: Optional[str] = "GET"  # HTTP method: GET, PUT, POST, DELETE


class SignedUrlResponse(BaseModel):
    signed_url: str
    bucket_name: str
    blob_name: str
    expiration_seconds: int


class TrainRequest(BaseModel):
    file_path_list: List[str]


class TrainResponse(BaseModel):
    message: str
    job_id: str


@app.get("/")
async def root():
    """Root endpoint returning a welcome message."""
    return {"message": "Welcome to Controlla Test Pipeline API"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", message="Service is running")


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


@app.get("/signed-url", response_model=SignedUrlResponse)
async def generate_signed_url(
    bucket_name: str,
    blob_name: str,
    content_type: str,
    expiration: Optional[int] = 3600,
    method: Optional[str] = "GET",
):
    """Generate a signed URL for a Google Cloud Storage object."""
    try:
        # Initialize the GCS client
        credentials = service_account.Credentials.from_service_account_file(
            settings.gcp_credentials_path
        )

        client = storage.Client(
            project=settings.gcp_project_id, credentials=credentials
        )
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_name)

        # Validate HTTP method
        valid_methods = ["GET", "PUT", "POST", "DELETE"]
        method_upper = method.upper()
        if method_upper not in valid_methods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid method. Must be one of: {', '.join(valid_methods)}",
            )

        # Generate the signed URL
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expiration),
            method="PUT",
            service_account_email=settings.gcp_service_account_email,
            credentials=credentials,
            content_type=content_type,
        )

        return SignedUrlResponse(
            signed_url=signed_url,
            bucket_name=bucket_name,
            blob_name=blob_name,
            expiration_seconds=expiration,
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating signed URL: {str(e)}",
        ) from e


@app.post("/train-model", response_model=TrainResponse)
async def train_model(request: TrainRequest):
    """Train a model."""
    # Extract the file_path_list from the request body
    file_path_list = request.file_path_list

    # Process the file paths (you can add your training logic here)
    print(f"Training model with {len(file_path_list)} files: {file_path_list}")

    # Create record in database
    try:
        db = get_db()
        new_record = db.insert_training_job(file_path_list=file_path_list)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating database record: {str(e)}",
        ) from e

    clear_files_func = modal.Function.from_name("controlla-train-music", "clear_files")
    clear_files_func.remote()

    upload_files_func = modal.Function.from_name(
        "controlla-train-music", "upload_files"
    )
    for file_path in file_path_list:
        upload_files_func.remote(file_path, new_record["id"])

    modal_train_job = modal.Function.from_name("controlla-train-music", "train")
    modal_train_job.spawn(job_id=new_record["id"])

    try:
        db = get_db()
        db.update_training_job(job_id=new_record["id"], updates={"status": "training"})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating database record: {str(e)}",
        ) from e

    return TrainResponse(
        message=f"Model training started with {len(file_path_list)} files",
        job_id=new_record["id"],
    )
