"""
FastAPI Backend - Multi-Model AI Agent for Health Diagnostics
Production-ready async API with Groq LLM integration, Supabase-ready, and Streamlit compatibility
"""

import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys
import os

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import aiofiles

# Add src directory to path for imports
_src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src')
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# Import core modules
from core.ocr_engine import MedicalOCROrchestrator
from core.parser import parse_blood_report
from core.validator import validate_parameters
from core.interpreter import interpret_results
from core.enhanced_ai_agent import EnhancedAIAgent
from utils.llm_provider import get_llm_provider

# Import route modules
from routes import analyze_router, reports_router, chat_router

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
    risk_assessment: Optional[Dict[str, Any]] = None


class ReportMetadata(BaseModel):
    """Report metadata for storage"""
    report_id: str
    created_at: datetime
    file_name: str
    file_type: str
    user_id: Optional[str] = None
    analysis: AnalysisResult
    chat_history: List[Dict[str, str]] = Field(default_factory=list)
    is_archived: bool = False


# ============================================================================
# Global State Management
# ============================================================================


class ReportStore:
    """In-memory report store with expiration (until Supabase integration)"""

    def __init__(self, ttl_minutes: int = 1440):  # 24 hour default TTL
        self.reports: Dict[str, ReportMetadata] = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self._cleanup_lock = asyncio.Lock()

    async def store(
        self,
        report_id: str,
        analysis: AnalysisResult,
        file_name: str,
        file_type: str,
        user_id: Optional[str] = None,
    ) -> ReportMetadata:
        """Store a report analysis"""
        metadata = ReportMetadata(
            report_id=report_id,
            created_at=datetime.utcnow(),
            file_name=file_name,
            file_type=file_type,
            user_id=user_id,
            analysis=analysis,
        )
        self.reports[report_id] = metadata
        return metadata

    async def get(self, report_id: str) -> Optional[ReportMetadata]:
        """Retrieve a report"""
        return self.reports.get(report_id)

    async def update_chat_history(
        self, report_id: str, role: str, content: str
    ) -> bool:
        """Add message to report's chat history"""
        if report_id not in self.reports:
            return False

        self.reports[report_id].chat_history.append(
            {"role": role, "content": content, "timestamp": datetime.utcnow().isoformat()}
        )
        return True

    async def cleanup_expired(self):
        """Remove expired reports (TTL-based)"""
        async with self._cleanup_lock:
            now = datetime.utcnow()
            expired = [
                rid
                for rid, meta in self.reports.items()
                if now - meta.created_at > self.ttl
            ]
            for rid in expired:
                del self.reports[rid]

    async def list_user_reports(self, user_id: str) -> List[ReportMetadata]:
        """List reports for a user"""
        return [
            meta
            for meta in self.reports.values()
            if meta.user_id == user_id and not meta.is_archived
        ]

    def clear_all(self):
        """Clear all stored reports (for testing/shutdown)"""
        self.reports.clear()


# ============================================================================
# Service Layer
# ============================================================================


class AnalysisService:
    """Core analysis service orchestrating OCR → Parsing → Validation → Interpretation"""

    def __init__(self):
        self.ocr = MedicalOCROrchestrator()
        self.ocr_provider = None
        try:
            self.ocr_provider = get_llm_provider()
        except Exception:
            pass

    async def analyze_file(self, file_content: bytes, file_type: str) -> AnalysisResult:
        """
        Complete analysis pipeline: Extract → Parse → Validate → Interpret
        """
        # Step 1: Extract text from file
        extracted_text = await self._extract_text(file_content, file_type)
        if not extracted_text or len(extracted_text.strip()) < 10:
            raise ValueError(
                "Could not extract meaningful text from file. Ensure it's a valid medical report."
            )

        # Step 2: Parse blood parameters
        parsed_params = parse_blood_report(extracted_text)
        if not parsed_params:
            raise ValueError(
                "No blood parameters detected. Ensure the file contains blood test data."
            )

        # Step 3: Validate against reference ranges
        validated_params = validate_parameters(parsed_params)

        # Step 4: Generate interpretation
        interpretation = interpret_results(validated_params)

        # Step 5: Convert to response model
        parameters_dict = {
            name: BloodParameter(
                value=param.get("value", 0),
                unit=param.get("unit", "N/A"),
                status=param.get("status", "UNKNOWN"),
                reference_range=param.get("reference_range"),
            )
            for name, param in validated_params.items()
        }

        return AnalysisResult(
            parameters=parameters_dict,
            summary=interpretation.get("summary", {}),
            abnormal_parameters=interpretation.get("abnormal_parameters", []),
            recommendations=interpretation.get("recommendations", []),
            risk_assessment=await self._calculate_risk_assessment(validated_params),
        )

    async def _extract_text(self, file_content: bytes, file_type: str) -> str:
        """Extract text based on file type"""
        try:
            if file_type == "json":
                return file_content.decode("utf-8")
            elif file_type == "csv":
                return file_content.decode("utf-8")
            elif file_type == "txt":
                return file_content.decode("utf-8")
            elif file_type == "pdf":
                return await self._extract_from_pdf(file_content)
            elif file_type in ["png", "jpg", "jpeg"]:
                return await self._extract_from_image(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            raise ValueError(f"Failed to extract text: {str(e)}")

    async def _extract_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF"""
        return await asyncio.to_thread(self.ocr.extract_text_from_pdf_bytes, file_content)

    async def _extract_from_image(self, file_content: bytes) -> str:
        """Extract text from image"""
        return await asyncio.to_thread(self.ocr.extract_text_from_image_bytes, file_content)

    async def _calculate_risk_assessment(
        self, validated_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate health risk based on parameters"""
        risk_factors = []
        risk_score = 0.0

        for param_name, param_data in validated_params.items():
            status = param_data.get("status")
            if status in ["LOW", "HIGH"]:
                risk_score += 0.1
                risk_factors.append(
                    {
                        "parameter": param_name,
                        "status": status,
                        "severity": "high" if status == "HIGH" else "low",
                    }
                )

        risk_level = "low" if risk_score < 0.2 else "medium" if risk_score < 0.5 else "high"

        return {
            "risk_score": round(min(risk_score, 1.0), 2),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
        }


class ChatService:
    """Chat service for Q&A about blood reports"""

    def __init__(self, store: ReportStore):
        self.store = store
        self.ai_agent = None
        try:
            self.ai_agent = EnhancedAIAgent()
        except Exception:
            pass

    async def process_message(
        self, report_id: str, message: str, user_id: Optional[str] = None
    ) -> str:
        """Process user message and generate response"""
        report_meta = await self.store.get(report_id)
        if not report_meta:
            raise ValueError(f"Report not found: {report_id}")

        context = {
            "report": report_meta.analysis.dict(),
            "chat_history": report_meta.chat_history,
            "user_id": user_id or "anonymous",
        }

        if self.ai_agent:
            try:
                response = await asyncio.to_thread(
                    self._get_ai_response, message, context
                )
            except Exception:
                response = await self._get_fallback_response(message, report_meta)
        else:
            response = await self._get_fallback_response(message, report_meta)

        await self.store.update_chat_history(report_id, "user", message)
        await self.store.update_chat_history(report_id, "assistant", response)

        return response

    def _get_ai_response(self, message: str, context: Dict) -> str:
        """Get response from AI agent"""
        try:
            result = self.ai_agent.process_user_message(message, context)
            return result.get("message", "I couldn't generate a response.")
        except Exception as e:
            return f"Analysis: {str(e)}"

    async def _get_fallback_response(
        self, message: str, report_meta: ReportMetadata
    ) -> str:
        """Fallback response when AI is unavailable"""
        message_lower = message.lower()
        analysis = report_meta.analysis

        if any(term in message_lower for term in ["summary", "overview", "what"]):
            abnormal_count = len(analysis.abnormal_parameters)
            total = len(analysis.parameters)
            return (
                f"Your report has {total} parameters analyzed. "
                f"{abnormal_count} are outside normal ranges. "
                f"Key recommendations: {'; '.join(analysis.recommendations[:2])}"
            )

        if any(term in message_lower for term in ["risk", "danger", "serious"]):
            risk = analysis.risk_assessment or {}
            risk_level = risk.get("risk_level", "unknown").upper()
            risk_score = risk.get("risk_score", 0)
            return (
                f"Based on your parameters, overall risk level is {risk_level} "
                f"(score: {risk_score:.1%}). Please consult your doctor for detailed advice."
            )

        if any(term in message_lower for term in ["normal", "abnormal", "high", "low"]):
            abnormal = analysis.abnormal_parameters[:3]
            if abnormal:
                param_names = ", ".join([p["parameter"] for p in abnormal])
                return f"Abnormal parameters found: {param_names}. See recommendations above."
            return "Your parameters appear to be within normal ranges."

        return (
            f"Your report shows {len(analysis.abnormal_parameters)} abnormal parameters. "
            f"Recommendations: {analysis.recommendations[0]}"
        )


# ============================================================================
# Lifespan and Application Initialization
# ============================================================================


class AppState:
    """Global application state"""

    def __init__(self):
        self.store = ReportStore()
        self.analysis_service = AnalysisService()
        self.chat_service = ChatService(self.store)
        self.cleanup_task: Optional[asyncio.Task] = None


_app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # ===== STARTUP =====
    print("[STARTUP] Initializing Health Diagnostics API...")

    # Initialize services
    _app_state.store = ReportStore(ttl_minutes=1440)
    _app_state.analysis_service = AnalysisService()
    _app_state.chat_service = ChatService(_app_state.store)

    # Start background cleanup task
    async def cleanup_loop():
        while True:
            try:
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                await _app_state.store.cleanup_expired()
            except Exception as e:
                print(f"[CLEANUP] Error: {e}")

    _app_state.cleanup_task = asyncio.create_task(cleanup_loop())
    print("[STARTUP] API initialized successfully")

    yield

    # ===== SHUTDOWN =====
    print("[SHUTDOWN] Cleaning up resources...")

    if _app_state.cleanup_task:
        _app_state.cleanup_task.cancel()
        try:
            await _app_state.cleanup_task
        except asyncio.CancelledError:
            pass

    _app_state.store.clear_all()
    print("[SHUTDOWN] API shutdown complete")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Health Diagnostics API",
    description="Multi-Model AI Agent for Blood Report Analysis",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Include Routers
# ============================================================================

app.include_router(analyze_router)
app.include_router(reports_router)
app.include_router(chat_router)


# ============================================================================
# Global Exception Handler
# ============================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return {
        "success": False,
        "error": exc.detail,
        "status": exc.status_code,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    error_message = str(exc)
    return {
        "success": False,
        "error": error_message,
        "status": 500,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# Health Check Endpoint
# ============================================================================


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "reports_stored": len(_app_state.store.reports),
    }


# ============================================================================
# System Endpoints
# ============================================================================


@app.get("/stats", tags=["System"])
async def get_stats() -> Dict[str, Any]:
    """Get system statistics"""
    return {
        "total_reports_stored": len(_app_state.store.reports),
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_info": "Reports cached in-memory. Data persists until server restart.",
    }


@app.delete("/reports/{report_id}", tags=["Reports"])
async def delete_report(report_id: str) -> Dict[str, Any]:
    """
    Delete a report from cache

    **Note:** This removes the report from in-memory storage. Future integration with Supabase
    will provide persistent deletion.
    """
    if report_id not in _app_state.store.reports:
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")

    del _app_state.store.reports[report_id]

    return {
        "success": True,
        "message": f"Report {report_id} deleted",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# Root Endpoint
# ============================================================================


@app.get("/", tags=["Info"])
async def root():
    """
    Health Diagnostics API - Root endpoint with API documentation
    """
    return {
        "name": "Health Diagnostics API",
        "version": "1.0.0",
        "description": "Multi-Model AI Agent for Blood Report Analysis",
        "docs_url": "/docs",
        "endpoints": {
            "health": "GET /health",
            "analyze": "POST /analyze",
            "get_report": "GET /report/{report_id}",
            "chat": "POST /chat",
            "list_reports": "GET /reports/user/{user_id}",
            "stats": "GET /stats",
            "delete_report": "DELETE /reports/{report_id}",
        },
        "status": "operational",
    }


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
