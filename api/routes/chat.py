"""
Chat endpoint for interactive Q&A about blood reports.
Enables users to ask questions and get AI-powered responses.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Create router
router = APIRouter(prefix="/api", tags=["Chat"])


# ============================================================================
# Pydantic Models
# ============================================================================


class ChatMessage(BaseModel):
    """Chat message request"""
    report_id: str
    message: str
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response"""
    message: str
    timestamp: datetime
    report_id: str


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatMessage) -> ChatResponse:
    """
    Ask questions about a blood report

    **Parameters:**
    - `report_id`: UUID of the report to ask about
    - `message`: Your question about the report
    - `user_id` (optional): User identifier for tracking

    **Returns:**
    - AI-generated response about the report
    - Timestamp of response
    """
    from ..main import _app_state

    try:
        if not request.message or len(request.message.strip()) < 3:
            raise HTTPException(
                status_code=400, detail="Message must be at least 3 characters"
            )

        response_text = await _app_state.chat_service.process_message(
            report_id=request.report_id,
            message=request.message,
            user_id=request.user_id,
        )

        return ChatResponse(
            message=response_text,
            timestamp=datetime.utcnow(),
            report_id=request.report_id,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")
