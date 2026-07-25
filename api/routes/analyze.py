"""
Analysis endpoint for blood report processing.
Handles file uploads and performs comprehensive blood report analysis.
"""

import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List

# Create router
router = APIRouter(prefix="/api", tags=["Analysis"])


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


class AnalyzeResponse(BaseModel):
    """Response from analyze endpoint"""
    report_id: str
    analysis: AnalysisResult
    created_at: datetime
    file_type: str
    file_name: str


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_report(
    file: UploadFile = File(...), user_id: Optional[str] = None
) -> AnalyzeResponse:
    """
    Analyze a blood report file

    **Supported formats:**
    - PDF (scanned or digital)
    - PNG, JPG, JPEG (images)
    - JSON (structured data)
    - CSV (tabular data)

    **Returns:**
    - Report ID (for later retrieval)
    - Complete analysis with parameters, abnormalities, and recommendations
    """
    from ..main import _app_state

    report_id = str(uuid.uuid4())

    try:
        # Validate file type
        file_extension = file.filename.split(".")[-1].lower()
        valid_types = {"pdf", "png", "jpg", "jpeg", "json", "csv", "txt"}
        if file_extension not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Supported: {', '.join(valid_types)}",
            )

        # Read file content
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="File is empty")

        # Perform analysis
        analysis = await _app_state.analysis_service.analyze_file(
            file_content, file_extension
        )

        # Store report
        await _app_state.store.store(
            report_id=report_id,
            analysis=analysis,
            file_name=file.filename,
            file_type=file_extension,
            user_id=user_id,
        )

        return AnalyzeResponse(
            report_id=report_id,
            analysis=analysis,
            created_at=datetime.utcnow(),
            file_type=file_extension,
            file_name=file.filename,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Analysis failed: {str(e)}"
        )
