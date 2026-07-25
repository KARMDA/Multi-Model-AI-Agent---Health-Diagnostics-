"""
Database package for Health Diagnostics API.
Provides Supabase async client, models, and repository patterns.
"""

from .client import init_supabase, get_db, get_supabase_client
from .models import Report, User, ChatHistoryRecord
from .repository import ReportRepository

__all__ = [
    "init_supabase",
    "get_db",
    "get_supabase_client",
    "Report",
    "User",
    "ChatHistoryRecord",
    "ReportRepository",
]
