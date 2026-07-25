"""
API routes package for Multi-Model AI Agent Health Diagnostics.
Provides modularized endpoints for analysis, reports, and chat.
"""

from .analyze import router as analyze_router
from .reports import router as reports_router
from .chat import router as chat_router

__all__ = ["analyze_router", "reports_router", "chat_router"]
