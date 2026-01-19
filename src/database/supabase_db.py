"""Supabase database connection and interface module."""

from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
from supabase import create_client, Client
from pydantic_settings import BaseSettings, SettingsConfigDict


class SupabaseSettings(BaseSettings):
    """Supabase settings loaded from environment variables."""

    supabase_url: str
    supabase_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra fields from .env that aren't defined in this Settings class
    )


class SupabaseDB:
    """Supabase database interface for database operations."""

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Initialize Supabase client.

        Args:
            url: Supabase project URL. If not provided, will be loaded from settings.
            key: Supabase anon/service role key. If not provided, will be loaded from settings.

        Raises:
            ValueError: If required settings are missing or invalid.
        """
        if url and key:
            if not url.strip() or not key.strip():
                raise ValueError("Supabase URL and key cannot be empty")
            self.client: Client = create_client(url, key)
        else:
            try:
                settings = SupabaseSettings()
            except Exception as e:
                raise ValueError(
                    f"Failed to load Supabase settings from environment variables: {str(e)}. "
                    "Please ensure SUPABASE_URL and SUPABASE_KEY are set in your .env file."
                ) from e

            # Validate that settings are not empty
            if not settings.supabase_url or not settings.supabase_key:
                raise ValueError(
                    "Supabase URL and key are required. "
                    "Please set SUPABASE_URL and SUPABASE_KEY in your .env file."
                )

            # Validate that settings are not just whitespace
            if not settings.supabase_url.strip() or not settings.supabase_key.strip():
                raise ValueError(
                    "Supabase URL and key cannot be empty or whitespace. "
                    "Please check your .env file."
                )

            try:
                print(settings.supabase_url.strip(), settings.supabase_key.strip())
                self.client = create_client(
                    settings.supabase_url.strip(), settings.supabase_key.strip()
                )
            except Exception as e:
                raise ValueError(
                    f"Failed to create Supabase client: {str(e)}. "
                    "Please verify that your SUPABASE_URL and SUPABASE_KEY are correct."
                ) from e

    def execute_query(
        self, query: str, params: Optional[tuple] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a raw SQL query using Supabase RPC or direct query.

        Note: Supabase Python client doesn't support raw SQL directly.
        For raw SQL, you would need to use the REST API or create RPC functions.
        This method provides a wrapper for common operations.

        Args:
            query: SQL query string
            params: Query parameters (if using parameterized queries)

        Returns:
            Query results as a list of dictionaries, or None if no results
        """
        # Supabase Python client doesn't support raw SQL directly
        # This is a placeholder - you would need to use RPC functions or REST API
        # For now, we'll use the table methods which are the recommended approach
        raise NotImplementedError(
            "Raw SQL queries are not directly supported. "
            "Use table methods or create RPC functions in Supabase."
        )

    def insert_training_job(
        self,
        file_path_list: List[str],
    ) -> Dict[str, Any]:
        """
        Insert a training job record into the database.

        Args:
            job_id: Unique job identifier
            file_path_list: List of file paths used for training

        Returns:
            Inserted record as a dictionary

        Raises:
            ValueError: If API key is invalid or other configuration issues
            RuntimeError: If the insert operation fails
        """
        data = {
            "id": str(uuid.uuid4()),
            "file_path_list": file_path_list,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "started",
        }

        try:
            result = self.client.table("training_jobs").insert(data).execute()
        except Exception as e:
            error_msg = str(e)
            if "Invalid API key" in error_msg or "api key" in error_msg.lower():
                raise ValueError(
                    f"Invalid Supabase API key: {error_msg}. "
                    "Please verify that your SUPABASE_KEY in the .env file is correct. "
                    "You can find your API key in your Supabase project settings."
                ) from e
            raise RuntimeError(f"Failed to insert train job record: {error_msg}") from e

        if result.data:
            return result.data[0]
        raise RuntimeError("Failed to insert train job record: No data returned")

    def get_training_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a training job record by job_id.

        Args:
            job_id: Unique job identifier

        Returns:
            Job record as a dictionary, or None if not found
        """
        result = (
            self.client.table("training_jobs").select("*").eq("id", job_id).execute()
        )

        if result.data:
            return result.data[0]
        return None

    def update_training_job(
        self, job_id: str, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a training job record.

        Args:
            job_id: Unique job identifier
            updates: Dictionary of fields to update

        Returns:
            Updated record as a dictionary, or None if not found
        """
        result = (
            self.client.table("training_jobs")
            .update(updates)
            .eq("id", job_id)
            .execute()
        )

        if result.data:
            return result.data[0]
        return None

    def list_training_jobs(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List training job records.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of job records as dictionaries
        """
        query = (
            self.client.table("training_jobs")
            .select("*")
            .order("created_at", desc=True)
        )

        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)

        result = query.execute()
        return result.data if result.data else []


# Global database instance (can be initialized on app startup)
_db_instance: Optional[SupabaseDB] = None


def get_db() -> SupabaseDB:
    """
    Get or create the global database instance.

    Returns:
        SupabaseDB instance
    """
    global _db_instance  # pylint: disable=global-statement
    if _db_instance is None:
        _db_instance = SupabaseDB()
    return _db_instance


def init_db(url: Optional[str] = None, key: Optional[str] = None) -> SupabaseDB:
    """
    Initialize the global database instance.

    Args:
        url: Supabase project URL
        key: Supabase anon/service role key

    Returns:
        SupabaseDB instance
    """
    global _db_instance  # pylint: disable=global-statement
    _db_instance = SupabaseDB(url, key)
    return _db_instance
