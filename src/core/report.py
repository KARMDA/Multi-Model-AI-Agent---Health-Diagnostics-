"""
Report Generator
Final report structure consolidating all analysis results
Creates unified report with structured data format and human-readable display
"""

import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates final structured medical analysis reports.
    Consolidates parameters, analysis, and synthesis into unified report format.
    """
    
    def __init__(self):
        """Initialize ReportGenerator"""
        self.report_templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, Any]:
        """Initialize default templates for empty fields"""
        return {
            'parameters': {},
            'analysis': {
                'parameter_flags': {},
                'risk_scores': {
                    'diabetes_risk': 0.0,
                    'cardio_risk': 0.0,
                    'anemia_risk': 0.0
                },
                'patterns': [],
                'severity': 'UNKNOWN'
            },
            'risks': {
                'diabetes_risk': 0.0,
                'cardio_risk': 0.0,
                'anemia_risk': 0.0
            },
            'recommendations': {
                'diet': [],
                'lifestyle': [],
                'medical_advice': []
            },
            'summary': '',
            'key_findings': [],
            'disclaimer': self._get_default_disclaimer()
        }
    
    def generate(self, parameters: Optional[Dict[str, Any]] = None,
                analysis: Optional[Dict[str, Any]] = None,
                synthesis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate final structured report from all analysis components.
        
        Args:
            parameters: Validated blood parameters dict
            analysis: Health analysis results (flags, risk_scores, patterns, severity)
            synthesis: Synthesis results (summary, recommendations, key_findings)
            
        Returns:
            Complete structured report with all fields present
        """
        # Initialize with templates
        report = {
            'report_id': str(uuid.uuid4()),
            'created_at': datetime.now().isoformat(),
        }
        
        # Extract and validate parameters
        report['parameters'] = self._extract_parameters(parameters)
        
        # Extract and validate analysis
        report['analysis'] = self._extract_analysis(analysis)
        
        # Extract risks (from analysis.risk_scores)
        report['risks'] = self._extract_risks(analysis)
        
        # Extract recommendations (from synthesis)
        report['recommendations'] = self._extract_recommendations(synthesis)
        
        # Extract summary and key findings
        report['summary'] = self._extract_summary(synthesis)
        report['key_findings'] = self._extract_key_findings(synthesis)
        
        # Extract disclaimer
        report['disclaimer'] = self._extract_disclaimer(synthesis)
        
        return report
    
    def _extract_parameters(self, parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract and validate parameters section"""
        if not parameters or not isinstance(parameters, dict):
            return {}
        
        extracted = {}
        for param_name, param_info in parameters.items():
            if isinstance(param_info, dict):
                extracted[param_name] = {
                    'value': param_info.get('value', 'N/A'),
                    'unit': param_info.get('unit', ''),
                    'status': param_info.get('status', 'UNKNOWN'),
                    'reference_range': param_info.get('reference_range', 'N/A')
                }
            else:
                # Handle scalar values
                extracted[param_name] = {
                    'value': param_info,
                    'unit': '',
                    'status': 'UNKNOWN',
                    'reference_range': 'N/A'
                }
        
        return extracted
    
    def _extract_analysis(self, analysis: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract and validate analysis section"""
        default_analysis = self.report_templates['analysis'].copy()
        
        if not analysis or not isinstance(analysis, dict):
            return default_analysis
        
        extracted = {
            'parameter_flags': {},
            'risk_scores': {},
            'patterns': [],
            'severity': 'UNKNOWN'
        }
        
        # Extract parameter flags
        if 'parameter_flags' in analysis and isinstance(analysis['parameter_flags'], dict):
            extracted['parameter_flags'] = analysis['parameter_flags']
        
        # Extract risk scores
        if 'risk_scores' in analysis and isinstance(analysis['risk_scores'], dict):
            risk_scores = analysis['risk_scores']
            extracted['risk_scores'] = {
                'diabetes_risk': float(risk_scores.get('diabetes_risk', 0.0)),
                'cardio_risk': float(risk_scores.get('cardio_risk', 0.0)),
                'anemia_risk': float(risk_scores.get('anemia_risk', 0.0))
            }
        else:
            extracted['risk_scores'] = default_analysis['risk_scores']
        
        # Extract patterns
        if 'patterns' in analysis and isinstance(analysis['patterns'], list):
            extracted['patterns'] = analysis['patterns'][:10]  # Limit to 10
        
        # Extract severity
        if 'severity' in analysis:
            severity = str(analysis['severity']).upper()
            if severity in ['LOW', 'MODERATE', 'HIGH', 'CRITICAL']:
                extracted['severity'] = severity
        
        return extracted
    
    def _extract_risks(self, analysis: Optional[Dict[str, Any]]) -> Dict[str, float]:
        """Extract risk scores specifically (duplicate from analysis)"""
        default_risks = self.report_templates['risks'].copy()
        
        if not analysis or not isinstance(analysis, dict):
            return default_risks
        
        if 'risk_scores' in analysis and isinstance(analysis['risk_scores'], dict):
            risk_scores = analysis['risk_scores']
            return {
                'diabetes_risk': float(risk_scores.get('diabetes_risk', 0.0)),
                'cardio_risk': float(risk_scores.get('cardio_risk', 0.0)),
                'anemia_risk': float(risk_scores.get('anemia_risk', 0.0))
            }
        
        return default_risks
    
    def _extract_recommendations(self, synthesis: Optional[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Extract and validate recommendations section"""
        default_recommendations = self.report_templates['recommendations'].copy()
        
        if not synthesis or not isinstance(synthesis, dict):
            return default_recommendations
        
        if 'recommendations' in synthesis and isinstance(synthesis['recommendations'], dict):
            recs = synthesis['recommendations']
            extracted = {
                'diet': self._extract_list(recs.get('diet', [])),
                'lifestyle': self._extract_list(recs.get('lifestyle', [])),
                'medical_advice': self._extract_list(recs.get('medical_advice', []))
            }
            return extracted
        
        return default_recommendations
    
    def _extract_summary(self, synthesis: Optional[Dict[str, Any]]) -> str:
        """Extract and validate summary"""
        if not synthesis or not isinstance(synthesis, dict):
            return ""
        
        summary = synthesis.get('summary', '')
        if isinstance(summary, str):
            return summary.strip()
        
        return str(summary) if summary else ""
    
    def _extract_key_findings(self, synthesis: Optional[Dict[str, Any]]) -> List[str]:
        """Extract and validate key findings"""
        if not synthesis or not isinstance(synthesis, dict):
            return []
        
        findings = synthesis.get('key_findings', [])
        if isinstance(findings, list):
            return [str(f).strip() for f in findings if f]
        
        return []
    
    def _extract_disclaimer(self, synthesis: Optional[Dict[str, Any]]) -> str:
        """Extract and validate disclaimer"""
        if not synthesis or not isinstance(synthesis, dict):
            return self._get_default_disclaimer()
        
        disclaimer = synthesis.get('disclaimer', '')
        if isinstance(disclaimer, str) and disclaimer.strip():
            return disclaimer.strip()
        
        return self._get_default_disclaimer()
    
    def _extract_list(self, items: Any) -> List[str]:
        """Extract and validate list field"""
        if not isinstance(items, list):
            return []
        
        return [str(item).strip() for item in items if item]
    
    def _get_default_disclaimer(self) -> str:
        """Get default disclaimer text"""
        return (
            "MEDICAL DISCLAIMER: This analysis is for informational purposes only and should not "
            "replace professional medical advice, diagnosis, or treatment. Blood test results must be "
            "interpreted in clinical context by qualified healthcare professionals. Always consult with "
            "a physician or healthcare provider for medical decisions. In case of emergency, seek "
            "immediate medical attention. The AI analysis may contain errors and should be verified by "
            "medical professionals before use in clinical decision-making."
        )
    
    def format_for_display(self, report: Dict[str, Any]) -> str:
        """
        Format structured report as human-readable markdown for Streamlit display.
        
        Args:
            report: Structured report dict from generate()
            
        Returns:
            Markdown-formatted string for display
        """
        lines = []
        
        # Header
        lines.extend([
            "# 🏥 Blood Report Analysis",
            "",
            f"**Report ID:** `{report.get('report_id', 'N/A')}`  ",
            f"**Generated:** {report.get('created_at', 'N/A')}",
            ""
        ])
        
        # Summary Section
        summary = report.get('summary', '')
        if summary:
            lines.extend([
                "## 📋 Summary",
                "",
                summary,
                ""
            ])
        
        # Key Findings Section
        key_findings = report.get('key_findings', [])
        if key_findings:
            lines.extend([
                "## 🔍 Key Findings",
                ""
            ])
            for i, finding in enumerate(key_findings, 1):
                lines.append(f"{i}. {finding}")
            lines.append("")
        
        # Parameters Section
        parameters = report.get('parameters', {})
        if parameters:
            lines.extend([
                "## 🔬 Measured Parameters",
                "",
                "| Parameter | Value | Unit | Status | Reference Range |",
                "|-----------|-------|------|--------|-----------------|"
            ])
            
            for param_name, param_info in parameters.items():
                value = param_info.get('value', 'N/A')
                unit = param_info.get('unit', '')
                status = param_info.get('status', 'UNKNOWN')
                ref_range = param_info.get('reference_range', 'N/A')
                
                # Add status emoji
                status_emoji = "⚠️" if status in ['LOW', 'HIGH', 'CRITICAL'] else "✅"
                
                lines.append(f"| {param_name} | {value} | {unit} | {status_emoji} {status} | {ref_range} |")
            
            lines.append("")
        
        # Analysis Section
        analysis = report.get('analysis', {})
        if analysis and any(analysis.values()):
            lines.append("## 📊 Analysis Results")
            lines.append("")
            
            severity = analysis.get('severity', 'UNKNOWN')
            lines.append(f"**Overall Severity:** {severity}")
            lines.append("")
            
            # Risk Scores
            risk_scores = analysis.get('risk_scores', {})
            if risk_scores:
                lines.append("### Risk Scores")
                for risk_type, score in risk_scores.items():
                    risk_name = risk_type.replace('_', ' ').title()
                    percentage = f"{score * 100:.1f}%" if isinstance(score, (int, float)) else "N/A"
                    
                    # Risk level indicator
                    if isinstance(score, (int, float)):
                        if score >= 0.8:
                            risk_indicator = "🔴 High"
                        elif score >= 0.5:
                            risk_indicator = "🟡 Moderate"
                        else:
                            risk_indicator = "🟢 Low"
                    else:
                        risk_indicator = "⚪ Unknown"
                    
                    lines.append(f"- **{risk_name}:** {percentage} ({risk_indicator})")
                lines.append("")
            
            # Patterns
            patterns = analysis.get('patterns', [])
            if patterns:
                lines.append("### Detected Patterns")
                for pattern in patterns[:5]:  # Show top 5
                    lines.append(f"- {pattern}")
                lines.append("")
        
        # Risks Section (duplicate for clarity)
        risks = report.get('risks', {})
        if risks and any(v for v in risks.values() if v):
            lines.extend([
                "## ⚠️ Health Risks",
                ""
            ])
            
            for risk_type, score in risks.items():
                risk_name = risk_type.replace('_', ' ').title()
                percentage = f"{score * 100:.1f}%" if isinstance(score, (int, float)) else "N/A"
                
                if isinstance(score, (int, float)):
                    if score >= 0.8:
                        icon = "🔴"
                    elif score >= 0.5:
                        icon = "🟡"
                    else:
                        icon = "🟢"
                else:
                    icon = "⚪"
                
                lines.append(f"{icon} **{risk_name}:** {percentage}")
            
            lines.append("")
        
        # Recommendations Section
        recommendations = report.get('recommendations', {})
        if recommendations and any(recommendations.values()):
            lines.append("## 💡 Recommendations")
            lines.append("")
            
            for category, items in recommendations.items():
                if items:
                    category_name = category.title()
                    lines.append(f"### {category_name}")
                    for i, item in enumerate(items[:5], 1):
                        lines.append(f"{i}. {item}")
                    lines.append("")
        
        # Disclaimer Section
        disclaimer = report.get('disclaimer', '')
        if disclaimer:
            lines.extend([
                "---",
                "",
                "## ⚖️ Disclaimer",
                "",
                f"> {disclaimer}",
                ""
            ])
        
        return "\n".join(lines)
    
    def format_as_json(self, report: Dict[str, Any]) -> str:
        """
        Format report as JSON string.
        
        Args:
            report: Structured report dict
            
        Returns:
            JSON-formatted string
        """
        import json
        return json.dumps(report, indent=2)
    
    def format_as_text(self, report: Dict[str, Any]) -> str:
        """
        Format report as plain text (simple format).
        
        Args:
            report: Structured report dict
            
        Returns:
            Plain text formatted string
        """
        lines = []
        
        # Header
        lines.extend([
            "=" * 80,
            "BLOOD REPORT ANALYSIS",
            "=" * 80,
            "",
            f"Report ID: {report.get('report_id', 'N/A')}",
            f"Generated: {report.get('created_at', 'N/A')}",
            ""
        ])
        
        # Summary
        summary = report.get('summary', '')
        if summary:
            lines.extend([
                "SUMMARY:",
                "-" * 40,
                summary,
                ""
            ])
        
        # Key Findings
        key_findings = report.get('key_findings', [])
        if key_findings:
            lines.extend([
                "KEY FINDINGS:",
                "-" * 40
            ])
            for finding in key_findings:
                lines.append(f"• {finding}")
            lines.append("")
        
        # Parameters
        parameters = report.get('parameters', {})
        if parameters:
            lines.extend([
                "MEASURED PARAMETERS:",
                "-" * 40
            ])
            for param_name, param_info in parameters.items():
                value = param_info.get('value', 'N/A')
                unit = param_info.get('unit', '')
                status = param_info.get('status', 'UNKNOWN')
                lines.append(f"{param_name}: {value} {unit} ({status})")
            lines.append("")
        
        # Analysis
        analysis = report.get('analysis', {})
        severity = analysis.get('severity', 'UNKNOWN')
        lines.extend([
            "ANALYSIS:",
            "-" * 40,
            f"Overall Severity: {severity}",
            ""
        ])
        
        # Risk Scores
        risk_scores = analysis.get('risk_scores', {})
        if risk_scores:
            lines.append("Risk Scores:")
            for risk_type, score in risk_scores.items():
                percentage = f"{score * 100:.1f}%" if isinstance(score, (int, float)) else "N/A"
                lines.append(f"  {risk_type}: {percentage}")
            lines.append("")
        
        # Patterns
        patterns = analysis.get('patterns', [])
        if patterns:
            lines.extend([
                "Patterns:",
                *[f"  • {p}" for p in patterns[:5]]
            ])
            lines.append("")
        
        # Recommendations
        recommendations = report.get('recommendations', {})
        if recommendations and any(recommendations.values()):
            lines.extend([
                "RECOMMENDATIONS:",
                "-" * 40
            ])
            for category, items in recommendations.items():
                if items:
                    lines.append(f"\n{category.upper()}:")
                    for item in items[:5]:
                        lines.append(f"  • {item}")
            lines.append("")
        
        # Disclaimer
        lines.extend([
            "=" * 80,
            "DISCLAIMER:",
            report.get('disclaimer', ''),
            "=" * 80
        ])
        
        return "\n".join(lines)
