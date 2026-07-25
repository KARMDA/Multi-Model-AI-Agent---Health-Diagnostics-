"""
Pydantic models for Supabase database tables.
Provides type hints and validation for database operations.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class BloodParameter(BaseModel):
    """Blood parameter value with reference range and status."""
    value: float
    unit: str
    status: str = Field(pattern="^(LOW|NORMAL|HIGH|UNKNOWN|CRITICAL)$")
    reference_range: Optional[str] = None
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None


class AnalysisData(BaseModel):
    """Blood report analysis data."""
    parameters: Dict[str, BloodParameter]
    summary: Dict[str, Any]
    abnormal_parameters: List[Dict[str, Any]]
    recommendations: List[str]


class RiskAssessment(BaseModel):
    """Risk assessment data for health conditions."""
    condition: str
    risk_level: str = Field(pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$")
    confidence: float = Field(ge=0.0, le=1.0)
    indicators: List[str]


class Report(BaseModel):
    """Report database model matching Supabase schema."""
    id: str  # UUID
    user_id: Optional[str] = None  # UUID or null
    created_at: datetime
    updated_at: Optional[datetime] = None
    parameters: Dict[str, BloodParameter]
    analysis: AnalysisData
    risks: List[RiskAssessment] = Field(default_factory=list)
    recommendations: List[str]
    summary: Dict[str, Any]
    status: str = Field(default="completed", pattern="^(pending|processing|completed|error)$")
    file_name: Optional[str] = None
    file_type: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "650e8400-e29b-41d4-a716-446655440000",
                "created_at": "2026-05-05T10:30:00Z",
                "parameters": {},
                "analysis": {},
                "risks": [],
                "recommendations": [],
                "summary": {},
                "status": "completed",
                "file_name": "report.pdf",
                "file_type": "pdf",
            }
        }


class User(BaseModel):
    """User database model matching Supabase schema."""
    id: str  # UUID
    email: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "created_at": "2026-05-05T10:30:00Z",
                "full_name": "John Doe",
                "is_active": True,
            }
        }


class ChatMessage(BaseModel):
    """Individual chat message in conversation."""
    role: str = Field(pattern="^(user|assistant)$")
    content: str
    timestamp: datetime


class ChatHistoryRecord(BaseModel):
    """Chat history database model matching Supabase schema."""
    id: str  # UUID
    report_id: str  # UUID
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: Optional[datetime] = None
    message_count: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "report_id": "650e8400-e29b-41d4-a716-446655440000",
                "messages": [
                    {
                        "role": "user",
                        "content": "What do my results mean?",
                        "timestamp": "2026-05-05T10:30:00Z",
                    }
                ],
                "created_at": "2026-05-05T10:30:00Z",
                "message_count": 1,
            }
        }


class ReportCreate(BaseModel):
    """Request model for creating a report."""
    user_id: Optional[str] = None
    parameters: Dict[str, BloodParameter]
    analysis: AnalysisData
    risks: List[RiskAssessment] = Field(default_factory=list)
    recommendations: List[str]
    summary: Dict[str, Any]
    file_name: Optional[str] = None
    file_type: Optional[str] = None


class ReportUpdate(BaseModel):
    """Request model for updating a report."""
    analysis: Optional[AnalysisData] = None
    risks: Optional[List[RiskAssessment]] = None
    recommendations: Optional[List[str]] = None
    summary: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class UserCreate(BaseModel):
    """Request model for creating a user."""
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class ChatMessageCreate(BaseModel):
    """Request model for adding a chat message."""
    role: str = Field(pattern="^(user|assistant)$")
    content: str
