"""
Unified Health Diagnostics Orchestrator
Consolidates OCR, parsing, validation, LLM analysis, and report generation into a single async pipeline.
Replaces: enhanced_ai_agent.py, phase2_orchestrator.py, phase2_integration_safe.py
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .ocr_engine import MedicalOCROrchestrator
from .parser import parse_blood_report
from .validator import validate_parameters
from .interpreter import interpret_results
from .advanced_risk_calculator import AdvancedRiskCalculator
from .comprehensive_report_generator import ComprehensiveReportGenerator
from .dynamic_reference_ranges import get_dynamic_reference
from .unit_converter import convert_to_standard_unit
from ..utils.llm_provider import get_llm_provider

logger = logging.getLogger(__name__)


class HealthOrchestrator:
    """
    Unified orchestrator for health diagnostics analysis pipeline.
    Handles: extraction → validation → analysis → LLM enhancement → report generation
    All exceptions are handled internally; never raises to caller.
    """

    def __init__(self):
        """Initialize orchestrator components"""
        self.ocr = MedicalOCROrchestrator()
        self.risk_calculator = AdvancedRiskCalculator()
        self.report_generator = ComprehensiveReportGenerator()
        self.llm_provider = None

        try:
            self.llm_provider = get_llm_provider()
        except Exception as e:
            logger.warning(f"LLM provider initialization failed: {e}")

    async def run(
        self,
        file_bytes: bytes,
        file_type: str,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute complete health diagnostics analysis pipeline.

        Args:
            file_bytes: Raw file content (PDF, image, JSON, CSV, TXT)
            file_type: File extension (pdf, png, jpg, jpeg, json, csv, txt)
            user_context: Optional user demographic and medical context
                         {age, gender, medical_history, lifestyle, etc.}

        Returns:
            Structured result dict with structure:
            {
                "success": bool,
                "parameters": Dict[str, ParameterData],
                "analysis": Dict[str, Any],
                "risks": Dict[str, Any],
                "recommendations": List[str],
                "disclaimer": str,
                "errors": List[str],  # If any occurred during processing
                "metadata": {
                    "file_type": str,
                    "processing_time_ms": float,
                    "components_executed": List[str]
                }
            }

        Never raises exceptions - all errors are captured and returned in result.
        """
        start_time = datetime.utcnow()
        components_executed = []
        errors = []
        
        # Initialize result structure
        result = {
            "success": False,
            "parameters": {},
            "analysis": {},
            "risks": {},
            "recommendations": [],
            "disclaimer": self._get_disclaimer(),
            "errors": [],
            "metadata": {
                "file_type": file_type,
                "processing_time_ms": 0,
                "components_executed": [],
            },
        }

        try:
            # Normalize context
            context = user_context or {}

            # ===== STEP 1: EXTRACTION =====
            try:
                logger.info(f"[EXTRACT] Processing {file_type} file")
                extracted_text = await self._extract_text(file_bytes, file_type)
                components_executed.append("extraction")

                if not extracted_text or len(extracted_text.strip()) < 10:
                    errors.append("Extraction: Could not extract meaningful text from file")
                    result["errors"] = errors
                    return result

            except Exception as e:
                errors.append(f"Extraction failed: {str(e)}")
                result["errors"] = errors
                return result

            # ===== STEP 2: PARSING =====
            try:
                logger.info("[PARSE] Extracting blood parameters")
                parsed_params = await asyncio.to_thread(
                    parse_blood_report, extracted_text
                )
                components_executed.append("parsing")

                if not parsed_params:
                    errors.append("Parsing: No blood parameters detected in file")
                    result["errors"] = errors
                    return result

            except Exception as e:
                errors.append(f"Parsing failed: {str(e)}")
                result["errors"] = errors
                return result

            # ===== STEP 3: VALIDATION =====
            try:
                logger.info("[VALIDATE] Validating against reference ranges")
                validated_params = await asyncio.to_thread(
                    validate_parameters, parsed_params
                )
                components_executed.append("validation")

                # Apply dynamic reference ranges if context available
                if context.get("age") or context.get("gender"):
                    validated_params = await self._apply_dynamic_ranges(
                        validated_params, context
                    )

            except Exception as e:
                errors.append(f"Validation failed: {str(e)}")
                result["errors"] = errors
                return result

            # ===== STEP 4: INTERPRETATION =====
            try:
                logger.info("[INTERPRET] Generating initial interpretation")
                interpretation = await asyncio.to_thread(
                    interpret_results, validated_params
                )
                components_executed.append("interpretation")

            except Exception as e:
                errors.append(f"Interpretation failed: {str(e)}")
                interpretation = {"summary": {}, "abnormal_parameters": []}

            # ===== STEP 5: RISK ASSESSMENT =====
            try:
                logger.info("[RISK] Calculating health risks")
                risk_assessment = await self._calculate_risks(validated_params, context)
                components_executed.append("risk_assessment")

            except Exception as e:
                errors.append(f"Risk calculation failed: {str(e)}")
                risk_assessment = {"risk_score": 0, "risk_level": "unknown", "factors": []}

            # ===== STEP 6: LLM ANALYSIS =====
            llm_insights = {}
            try:
                if self.llm_provider:
                    logger.info("[LLM] Generating LLM-powered insights")
                    llm_insights = await self._generate_llm_insights(
                        validated_params, interpretation, context
                    )
                    components_executed.append("llm_analysis")
                else:
                    logger.warning("[LLM] LLM provider not available, skipping")
                    llm_insights = {"status": "unavailable", "insights": []}

            except Exception as e:
                errors.append(f"LLM analysis failed: {str(e)}")
                llm_insights = {"status": "error", "insights": []}

            # ===== STEP 7: RECOMMENDATIONS =====
            try:
                logger.info("[RECOMMEND] Generating recommendations")
                recommendations = await self._generate_recommendations(
                    interpretation, risk_assessment, llm_insights
                )
                components_executed.append("recommendations")

            except Exception as e:
                errors.append(f"Recommendation generation failed: {str(e)}")
                recommendations = interpretation.get("recommendations", [])

            # ===== BUILD RESULT =====
            result["success"] = True
            result["parameters"] = self._format_parameters(validated_params)
            result["analysis"] = {
                "interpretation": interpretation,
                "llm_insights": llm_insights,
            }
            result["risks"] = risk_assessment
            result["recommendations"] = recommendations
            result["errors"] = errors if errors else []
            result["metadata"]["components_executed"] = components_executed

        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Unexpected error: {e}", exc_info=True)
            result["errors"].append(f"Orchestrator fatal error: {str(e)}")

        finally:
            # Calculate processing time
            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            result["metadata"]["processing_time_ms"] = round(elapsed_ms, 2)

        return result

    # ========================================================================
    # PRIVATE EXTRACTION METHODS
    # ========================================================================

    async def _extract_text(self, file_bytes: bytes, file_type: str) -> str:
        """Extract text from various file formats"""
        try:
            file_type = file_type.lower().strip(".")

            if file_type == "json":
                return file_bytes.decode("utf-8")

            elif file_type == "csv":
                return file_bytes.decode("utf-8")

            elif file_type == "txt":
                return file_bytes.decode("utf-8")

            elif file_type == "pdf":
                return await asyncio.to_thread(
                    self.ocr.extract_text_from_pdf_bytes, file_bytes
                )

            elif file_type in ["png", "jpg", "jpeg"]:
                return await asyncio.to_thread(
                    self.ocr.extract_text_from_image_bytes, file_bytes
                )

            else:
                raise ValueError(f"Unsupported file type: {file_type}")

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            raise

    # ========================================================================
    # PRIVATE VALIDATION & PROCESSING METHODS
    # ========================================================================

    async def _apply_dynamic_ranges(
        self, validated_params: Dict, context: Dict
    ) -> Dict:
        """Apply dynamic reference ranges based on age/gender if context available"""
        try:
            age = context.get("age")
            gender = context.get("gender")

            if not age or not gender:
                return validated_params

            # Apply dynamic ranges to each parameter
            for param_name, param_data in validated_params.items():
                try:
                    dynamic_range = await asyncio.to_thread(
                        get_dynamic_reference, param_name, age, gender
                    )

                    if dynamic_range:
                        param_data["reference_range"] = (
                            f"{dynamic_range.get('min')} - {dynamic_range.get('max')} "
                            f"{dynamic_range.get('unit', 'N/A')}"
                        )
                        # Recalculate status with new range
                        value = param_data.get("value", 0)
                        min_val = dynamic_range.get("min", 0)
                        max_val = dynamic_range.get("max", 1000)

                        if value < min_val:
                            param_data["status"] = "LOW"
                        elif value > max_val:
                            param_data["status"] = "HIGH"
                        else:
                            param_data["status"] = "NORMAL"

                except Exception as e:
                    logger.debug(f"Dynamic range failed for {param_name}: {e}")
                    continue

            return validated_params

        except Exception as e:
            logger.warning(f"Dynamic range application failed: {e}")
            return validated_params

    async def _calculate_risks(self, validated_params: Dict, context: Dict) -> Dict:
        """Calculate health risks based on parameters"""
        try:
            risk_factors = []
            risk_score = 0.0

            # Basic risk scoring: abnormal parameters increase risk
            for param_name, param_data in validated_params.items():
                status = param_data.get("status", "UNKNOWN")

                if status == "HIGH":
                    risk_score += 0.15
                    risk_factors.append(
                        {"parameter": param_name, "status": status, "severity": "high"}
                    )
                elif status == "LOW":
                    risk_score += 0.10
                    risk_factors.append(
                        {"parameter": param_name, "status": status, "severity": "medium"}
                    )

            # Determine risk level
            risk_score = min(risk_score, 1.0)
            if risk_score < 0.2:
                risk_level = "low"
            elif risk_score < 0.5:
                risk_level = "medium"
            else:
                risk_level = "high"

            # Advanced Framingham if context available
            framingham_risk = {}
            if context.get("age") and context.get("gender"):
                try:
                    framingham_result = await asyncio.to_thread(
                        self.risk_calculator.calculate_framingham_risk,
                        validated_params,
                        context,
                    )
                    if framingham_result:
                        framingham_risk = framingham_result
                except Exception as e:
                    logger.debug(f"Framingham calculation failed: {e}")

            return {
                "risk_score": round(risk_score, 2),
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "framingham_risk": framingham_risk,
            }

        except Exception as e:
            logger.error(f"Risk calculation failed: {e}")
            return {
                "risk_score": 0,
                "risk_level": "unknown",
                "risk_factors": [],
                "error": str(e),
            }

    # ========================================================================
    # PRIVATE LLM & RECOMMENDATION METHODS
    # ========================================================================

    async def _generate_llm_insights(
        self, validated_params: Dict, interpretation: Dict, context: Dict
    ) -> Dict:
        """Generate LLM-powered insights using Groq (or fallback provider)"""
        try:
            if not self.llm_provider:
                return {"status": "unavailable", "insights": []}

            # Prepare parameter summary for LLM
            abnormal_params = interpretation.get("abnormal_parameters", [])
            summary = interpretation.get("summary", {})

            if not abnormal_params:
                return {
                    "status": "no_abnormalities",
                    "insights": [],
                    "summary": "All parameters within normal ranges.",
                }

            # Build context for LLM
            param_text = "\n".join(
                [
                    f"- {p['parameter']}: {p['value']} {p['status']}"
                    for p in abnormal_params[:10]  # Limit to top 10 for context window
                ]
            )

            system_prompt = (
                "You are a medical specialist analyzing blood test results. "
                "Provide 2-3 key clinical insights based on the abnormal parameters. "
                "Be concise, professional, and evidence-based. "
                "Always recommend consulting with a healthcare provider."
            )

            prompt = f"""Analyze these abnormal blood parameters and provide clinical insights:

Abnormal Parameters:
{param_text}

Summary:
- Total parameters: {summary.get('total_parameters', 'N/A')}
- Abnormal count: {summary.get('high', 0) + summary.get('low', 0)}
- Normal count: {summary.get('normal', 0)}

Provide actionable insights without diagnosing specific diseases."""

            # Call LLM (Groq via llm_provider)
            llm_response = await asyncio.to_thread(
                self.llm_provider.generate,
                prompt,
                system_prompt,
                0.1,  # temperature
                500,  # max_tokens
            )

            insights = [
                line.strip()
                for line in llm_response.split("\n")
                if line.strip() and not line.startswith("#")
            ][:3]

            return {
                "status": "completed",
                "insights": insights,
                "raw_response": llm_response,
                "model_provider": self.llm_provider._active_provider.value
                if hasattr(self.llm_provider, "_active_provider")
                else "unknown",
            }

        except Exception as e:
            logger.error(f"LLM insight generation failed: {e}")
            return {"status": "error", "error": str(e), "insights": []}

    async def _generate_recommendations(
        self, interpretation: Dict, risk_assessment: Dict, llm_insights: Dict
    ) -> List[str]:
        """Generate clinical recommendations based on analysis"""
        try:
            recommendations = []

            # Base recommendations from interpretation
            base_recs = interpretation.get("recommendations", [])
            recommendations.extend(base_recs[:2])

            # Risk-based recommendations
            risk_level = risk_assessment.get("risk_level", "unknown")
            if risk_level == "high":
                recommendations.append(
                    "⚠️ High risk profile detected. Urgent consultation with healthcare provider recommended."
                )
            elif risk_level == "medium":
                recommendations.append(
                    "Consider scheduling a consultation with your healthcare provider soon."
                )

            # LLM-based recommendations
            if llm_insights.get("status") == "completed":
                insights = llm_insights.get("insights", [])
                for insight in insights[:2]:
                    if insight and len(insight) < 150:  # Limit length
                        recommendations.append(f"📋 {insight}")

            # Add general recommendations
            recommendations.append(
                "Maintain healthy lifestyle: balanced diet, regular exercise, adequate sleep."
            )
            recommendations.append(
                "Follow up with lab work as recommended by your healthcare provider."
            )

            # Remove duplicates while preserving order
            seen = set()
            unique_recs = []
            for rec in recommendations:
                if rec not in seen:
                    seen.add(rec)
                    unique_recs.append(rec)

            return unique_recs[:8]  # Limit to 8 recommendations

        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return [
                "Consult with a healthcare provider to discuss your blood test results.",
                "Maintain a healthy lifestyle with regular exercise and balanced diet.",
            ]

    # ========================================================================
    # PRIVATE UTILITY METHODS
    # ========================================================================

    def _format_parameters(self, validated_params: Dict) -> Dict:
        """Format parameters for output"""
        formatted = {}

        for param_name, param_data in validated_params.items():
            formatted[param_name] = {
                "value": param_data.get("value"),
                "unit": param_data.get("unit", "N/A"),
                "status": param_data.get("status", "UNKNOWN"),
                "reference_range": param_data.get("reference_range", "N/A"),
            }

        return formatted

    @staticmethod
    def _get_disclaimer() -> str:
        """Return standard medical disclaimer"""
        return (
            "This analysis is for informational purposes only and does not constitute "
            "medical advice. Always consult with a qualified healthcare provider for "
            "personalized medical guidance. This system is not a substitute for professional "
            "medical diagnosis, treatment, or advice."
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


async def run_health_analysis(
    file_bytes: bytes,
    file_type: str,
    user_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Convenience function to run a complete health analysis.

    Usage:
        result = await run_health_analysis(
            file_bytes=pdf_content,
            file_type="pdf",
            user_context={"age": 45, "gender": "male"}
        )
    """
    orchestrator = HealthOrchestrator()
    return await orchestrator.run(file_bytes, file_type, user_context)
