"""
Reports endpoint for retrieving and managing analyzed blood reports.
Provides access to stored reports and chat history.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Create router
router = APIRouter(prefix="/api", tags=["Reports"])


# ============================================================================
# Pydantic Models
# ============================================================================


class BloodParameter(BaseModel):
    """Blood parameter with validation status"""
    value: float
    unit: str
    status: str = Field(default="UNKNOWN", pattern="^(LOW|NORMAL|HIGH|UNKNOWN)$")
    reference_range: Optional[str] = None


class AnalysisResult(BaseModel):
    """Complete blood report analysis result"""
    parameters: Dict[str, BloodParameter]
    summary: Dict[str, Any]
    abnormal_parameters: List[Dict[str, Any]]
    recommendations: List[str]


class ReportResponse(BaseModel):
    """Response for report retrieval"""
    report_id: str
    analysis: AnalysisResult
    created_at: datetime
    file_name: str
    chat_history: List[Dict[str, str]]
    chat_enabled: bool


class UserReportsResponse(BaseModel):
    """Response for user's report list"""
    user_id: str
    reports: List[Dict[str, Any]]
    total_count: int


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/report/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str) -> ReportResponse:
    """
    Retrieve a previously analyzed report by ID

    **Parameters:**
    - `report_id`: UUID returned from /analyze endpoint

    **Returns:**
    - Complete report analysis with chat history
    """
    from ..main import _app_state

    report_meta = await _app_state.store.get(report_id)

    if not report_meta:
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")

    return ReportResponse(
        report_id=report_id,
        analysis=report_meta.analysis,
        created_at=report_meta.created_at,
        file_name=report_meta.file_name,
        chat_history=report_meta.chat_history,
        chat_enabled=_app_state.chat_service.ai_agent is not None,
    )


@router.get("/reports/user/{user_id}", tags=["Reports"])
async def get_user_reports(user_id: str) -> UserReportsResponse:
    """
    Retrieve all reports for a specific user

    **Parameters:**
    - `user_id`: User identifier

    **Returns:**
    - List of reports created by the user with basic metadata
    """
    from ..main import _app_state

    try:
        reports = await _app_state.store.get_user_reports(user_id)
        return UserReportsResponse(
            user_id=user_id,
            reports=reports,
            total_count=len(reports),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve reports: {str(e)}"
        )
