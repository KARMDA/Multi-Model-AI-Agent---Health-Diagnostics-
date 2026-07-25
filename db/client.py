"""
Supabase async client initialization and dependency injection.
Handles connection pooling and FastAPI lifespan integration.
"""

import os
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
import logging

from supabase import create_client, Client
from fastapi import Depends

logger = logging.getLogger(__name__)

# Global client instance
_supabase_client: Optional[Client] = None


def get_config() -> dict:
    """Load Supabase configuration from environment variables."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    service_key = os.getenv("SUPABASE_SERVICE_KEY", supabase_key)

    if not supabase_url or not supabase_key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY environment variables are required"
        )

    return {
        "url": supabase_url,
        "key": supabase_key,
        "service_key": service_key,
    }


def init_supabase() -> Client:
    """
    Initialize Supabase client singleton.
    Call once during FastAPI startup.
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    config = get_config()

    try:
        _supabase_client = create_client(config["url"], config["key"])
        logger.info(f"✓ Supabase client initialized: {config['url']}")
        return _supabase_client
    except Exception as e:
        logger.error(f"✗ Failed to initialize Supabase: {e}")
        raise


def get_supabase_client() -> Client:
    """Get the global Supabase client instance."""
    if _supabase_client is None:
        raise RuntimeError(
            "Supabase client not initialized. Call init_supabase() during startup."
        )
    return _supabase_client


async def get_db() -> AsyncGenerator[Client, None]:
    """
    FastAPI dependency for database access.
    Yields the Supabase client for use in route handlers.

    Usage:
        @router.get("/report/{report_id}")
        async def get_report(report_id: str, db: Client = Depends(get_db)):
            ...
    """
    client = get_supabase_client()
    try:
        yield client
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise


def close_supabase() -> None:
    """
    Close the Supabase client connection.
    Call during FastAPI shutdown.
    """
    global _supabase_client

    if _supabase_client is not None:
        try:
            logger.info("Closing Supabase connection")
            _supabase_client = None
        except Exception as e:
            logger.error(f"Error closing Supabase connection: {e}")
