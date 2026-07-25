"""
Health Synthesizer
Unified module merging comprehensive_report_generator, interpreter, and llm_provider
Synthesizes health analysis into natural language summaries with recommendations
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class HealthSynthesizer:
    """
    Synthesizes health analysis results into comprehensive summaries and recommendations.
    Uses LLM for natural language synthesis with rule-based fallback.
    """
    
    def __init__(self):
        """Initialize HealthSynthesizer with recommendation templates"""
        self.llm_provider = None
        self._initialize_recommendations()
    
    def _initialize_recommendations(self) -> None:
        """Initialize rule-based recommendation templates"""
        self.recommendations_db = {
            # Diet recommendations by condition/parameter
            'diet': {
                'high_glucose': [
                    'Reduce refined carbohydrates and sugary foods',
                    'Increase fiber intake through whole grains and vegetables',
                    'Monitor portion sizes and eat at regular intervals',
                    'Limit beverages with added sugars'
                ],
                'high_cholesterol': [
                    'Reduce saturated fat intake (butter, red meat, full-fat dairy)',
                    'Increase soluble fiber foods (oats, beans, apples)',
                    'Include plant sterols/stanols (fortified foods)',
                    'Use healthier cooking oils (olive, canola)',
                    'Limit trans fats and processed foods'
                ],
                'high_triglycerides': [
                    'Reduce carbohydrate intake, especially refined sugars',
                    'Limit alcohol consumption',
                    'Increase omega-3 fatty acids (fish, flax seeds)',
                    'Reduce refined grains; choose whole grains',
                    'Limit high-calorie snacks'
                ],
                'low_hemoglobin': [
                    'Increase iron-rich foods (red meat, spinach, legumes)',
                    'Consume vitamin C with iron-rich meals (citrus, tomatoes)',
                    'Reduce excessive tea and coffee consumption',
                    'Include fortified cereals and grains',
                    'Consider iron supplementation if recommended'
                ],
                'high_bilirubin': [
                    'Reduce fatty and fried foods',
                    'Limit alcohol consumption',
                    'Increase antioxidant-rich foods (berries, leafy greens)',
                    'Stay well hydrated (water primarily)',
                    'Avoid processed and sugary foods'
                ],
                'high_creatinine': [
                    'Moderate protein intake (unless advised otherwise)',
                    'Limit salt and sodium intake',
                    'Reduce phosphorus-rich foods if advised',
                    'Stay well hydrated with appropriate fluid intake',
                    'Limit potassium-rich foods if advised'
                ],
                'default': [
                    'Maintain balanced diet with all food groups',
                    'Include plenty of vegetables and fruits',
                    'Choose whole grains over refined',
                    'Limit salt, sugar, and unhealthy fats',
                    'Stay adequately hydrated'
                ]
            },
            # Lifestyle recommendations by condition
            'lifestyle': {
                'general': [
                    'Engage in at least 150 minutes of moderate physical activity weekly',
                    'Maintain healthy body weight (BMI 18.5-24.9)',
                    'Ensure 7-9 hours of quality sleep nightly',
                    'Manage stress through relaxation techniques or meditation',
                    'Avoid smoking and limit alcohol consumption'
                ],
                'sedentary': [
                    'Gradually increase daily physical activity',
                    'Start with 30 minutes of moderate exercise 3-4 times weekly',
                    'Incorporate walking, swimming, cycling, or other preferred activities',
                    'Take breaks from sitting; aim for movement every hour',
                    'Build strength training exercises 2-3 times weekly'
                ],
                'smoker': [
                    'Develop a smoking cessation plan',
                    'Consult healthcare provider for nicotine replacement options',
                    'Consider behavioral support programs or counseling',
                    'Identify and avoid smoking triggers',
                    'Prepare strategies for high-risk situations'
                ],
                'overweight': [
                    'Gradual weight loss of 1-2 pounds per week is recommended',
                    'Combine dietary changes with regular physical activity',
                    'Track food intake and portion sizes mindfully',
                    'Consider consulting a nutritionist or weight management specialist',
                    'Focus on sustainable lifestyle changes rather than quick fixes'
                ],
                'high_stress': [
                    'Practice stress-reduction techniques (yoga, meditation, deep breathing)',
                    'Schedule regular relaxation and leisure activities',
                    'Maintain consistent sleep schedule',
                    'Consider counseling or mental health support',
                    'Build social connections and support networks'
                ]
            },
            # Medical advice by parameter/condition
            'medical_advice': {
                'abnormal_glucose': [
                    'Schedule appointment with endocrinologist or primary care physician',
                    'Monitor glucose levels regularly as per healthcare provider recommendation',
                    'Consider glucose meter for home monitoring if diabetic',
                    'Review current medications that might affect glucose',
                    'Explore diabetes prevention or management programs'
                ],
                'abnormal_lipids': [
                    'Discuss lipid management strategies with healthcare provider',
                    'Consider statin therapy if lifestyle changes insufficient',
                    'Regular lipid panel monitoring (every 1-2 years minimum)',
                    'Assess cardiovascular risk factors comprehensively',
                    'Review family history of cardiovascular disease'
                ],
                'abnormal_hemoglobin': [
                    'Consult hematologist or primary care physician',
                    'May require iron studies, B12, or folate testing',
                    'Discuss underlying causes and treatment options',
                    'Consider follow-up testing in 4-6 weeks',
                    'Review medications that might affect red blood cells'
                ],
                'abnormal_liver': [
                    'Schedule hepatology or primary care consultation',
                    'Undergo additional liver function tests and imaging if needed',
                    'Assess for viral hepatitis and alcohol-related liver disease',
                    'Avoid hepatotoxic drugs and excess alcohol',
                    'Monitor liver function regularly'
                ],
                'abnormal_kidney': [
                    'Consult nephrologist or primary care physician',
                    'Obtain kidney ultrasound or imaging if not recent',
                    'Monitor blood pressure closely (key risk factor)',
                    'Regular kidney function monitoring with annual testing',
                    'Review medications affecting kidney function'
                ],
                'abnormal_immune': [
                    'Consult immunologist or infectious disease specialist if needed',
                    'May require additional immune system evaluation',
                    'Assess for infections or immune disorders',
                    'Follow infection prevention protocols',
                    'Consider repeat testing after treatment'
                ],
                'default_abnormal': [
                    'Schedule follow-up appointment with primary care physician',
                    'Repeat testing may be recommended to confirm results',
                    'Discuss findings and next steps with healthcare provider',
                    'Keep detailed health records and medication list',
                    'Attend follow-up appointments as scheduled'
                ]
            }
        }
    
    async def synthesize(self, validated_params: Dict[str, Any],
                        analysis: Dict[str, Any],
                        context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Synthesize health analysis into comprehensive summary and recommendations.
        
        Args:
            validated_params: Validated blood parameters with status
            analysis: Health analysis results (risk scores, patterns, severity)
            context: Optional context (age, gender, medical_history, etc.)
            
        Returns:
            Dict with summary, key_findings, recommendations, disclaimer
        """
        # Extract key findings
        key_findings = self._extract_key_findings(validated_params, analysis, context)
        
        # Generate LLM summary with fallback
        summary = await self._generate_summary(validated_params, analysis, context, key_findings)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(validated_params, analysis, context, key_findings)
        
        # Hardcoded disclaimer (never LLM-generated)
        disclaimer = self._get_disclaimer()
        
        return {
            'summary': summary,
            'key_findings': key_findings,
            'recommendations': recommendations,
            'disclaimer': disclaimer,
            'synthesis_timestamp': datetime.now().isoformat(),
            'context_applied': bool(context),
            'analysis_completeness': self._assess_completeness(validated_params, analysis, context)
        }
    
    def _extract_key_findings(self, validated_params: Dict[str, Any],
                            analysis: Dict[str, Any],
                            context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Extract key findings from validated parameters and analysis"""
        findings = []
        
        # Critical abnormal parameters
        critical_params = []
        abnormal_params = []
        
        for param_name, param_info in validated_params.items():
            status = param_info.get('status', 'NORMAL')
            value = param_info.get('value')
            
            if status == 'CRITICAL':
                critical_params.append(f"{param_name}: {value} (CRITICAL)")
            elif status in ['LOW', 'HIGH']:
                abnormal_params.append(f"{param_name}: {value} ({status})")
        
        # Add critical findings first
        if critical_params:
            findings.append(f"⚠️ CRITICAL: {', '.join(critical_params[:2])}")
        
        # Add abnormal parameters summary
        if abnormal_params:
            finding_text = f"Abnormal values detected: {len(abnormal_params)} parameter(s)"
            findings.append(finding_text)
            # Add top 3 abnormal params as detail
            for param in abnormal_params[:3]:
                findings.append(f"  • {param}")
        else:
            findings.append("✅ All measured parameters within expected ranges")
        
        # Add risk scores from analysis
        if analysis and 'risk_scores' in analysis:
            risk_scores = analysis['risk_scores']
            for risk_type, score in risk_scores.items():
                if score > 0.6:
                    risk_name = risk_type.replace('_', ' ').title()
                    findings.append(f"⚠️ {risk_name}: {score:.1%} (Elevated)")
        
        # Add severity assessment
        if analysis and 'severity' in analysis:
            severity = analysis['severity']
            if severity in ['HIGH', 'CRITICAL']:
                findings.append(f"⚠️ Overall Health Assessment: {severity}")
            else:
                findings.append(f"✅ Overall Health Assessment: {severity}")
        
        # Add patterns if detected
        if analysis and 'patterns' in analysis and analysis['patterns']:
            patterns = analysis['patterns'][:2]  # Top 2 patterns
            for pattern in patterns:
                findings.append(f"🔍 Pattern detected: {pattern[:80]}")
        
        # Add context-specific findings
        if context:
            age = context.get('age')
            medical_history = context.get('medical_history', [])
            
            if age and age >= 65:
                findings.append("📌 Senior patient: Age-specific considerations applied")
            
            if medical_history:
                findings.append(f"📋 Medical history: {', '.join(medical_history[:2])}")
        
        return findings if findings else ["📊 Analysis complete - no critical abnormalities detected"]
    
    async def _generate_summary(self, validated_params: Dict[str, Any],
                               analysis: Dict[str, Any],
                               context: Optional[Dict[str, Any]],
                               key_findings: List[str]) -> str:
        """
        Generate natural language summary using LLM with rule-based fallback.
        Falls back silently if LLM unavailable.
        """
        try:
            # Lazy import to avoid circular dependency
            from src.utils.llm_provider import get_llm_provider
            
            # Build prompt for LLM
            prompt = self._build_summary_prompt(validated_params, analysis, context, key_findings)
            
            # Get LLM provider
            llm_provider = get_llm_provider()
            
            # Generate summary using LLM
            system_prompt = """You are a medical report synthesizer. Generate a concise, clear clinical summary 
            (2-3 sentences) of blood test results for a patient. Be factual and professional."""
            
            # Call LLM asynchronously
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                None,
                llm_provider.generate,
                prompt,
                system_prompt,
                0.3,  # temperature
                200   # max_tokens
            )
            
            # Verify summary quality
            if summary and len(summary.strip()) > 20 and not summary.startswith("Error"):
                return summary.strip()
            else:
                logger.debug("LLM summary generation failed or returned insufficient content; using fallback")
                return self._generate_summary_fallback(validated_params, analysis)
        
        except Exception as e:
            logger.debug(f"LLM summary generation encountered error: {e}; using fallback")
            return self._generate_summary_fallback(validated_params, analysis)
    
    def _build_summary_prompt(self, validated_params: Dict[str, Any],
                             analysis: Dict[str, Any],
                             context: Optional[Dict[str, Any]],
                             key_findings: List[str]) -> str:
        """Build prompt for LLM summary generation"""
        context_info = ""
        if context:
            age = context.get('age')
            gender = context.get('gender')
            if age:
                context_info += f"Patient age: {age} years. "
            if gender:
                context_info += f"Gender: {gender}. "
        
        abnormal_count = sum(1 for p in validated_params.values() if p.get('status') in ['LOW', 'HIGH', 'CRITICAL'])
        total_count = len(validated_params)
        
        severity = analysis.get('severity', 'UNKNOWN') if analysis else 'UNKNOWN'
        
        prompt = f"""Summarize these blood test results:
        {context_info}
        
        Test Results: {abnormal_count} abnormal of {total_count} parameters
        Key Findings: {'; '.join(key_findings[:3])}
        Overall Assessment: {severity}
        
        Provide a 2-3 sentence clinical summary."""
        
        return prompt
    
    def _generate_summary_fallback(self, validated_params: Dict[str, Any],
                                  analysis: Dict[str, Any]) -> str:
        """Generate rule-based summary fallback when LLM unavailable"""
        abnormal_count = sum(1 for p in validated_params.values() if p.get('status') in ['LOW', 'HIGH', 'CRITICAL'])
        critical_count = sum(1 for p in validated_params.values() if p.get('status') == 'CRITICAL')
        total_count = len(validated_params)
        
        severity = analysis.get('severity', 'UNKNOWN') if analysis else 'UNKNOWN'
        
        if critical_count > 0:
            summary = f"Blood test results show {critical_count} critically abnormal value(s) among {total_count} parameters measured. "
        elif abnormal_count > 0:
            summary = f"Blood test results show {abnormal_count} abnormal value(s) among {total_count} parameters measured. "
        else:
            summary = f"Blood test results show no abnormal values among {total_count} parameters measured. "
        
        if severity in ['HIGH', 'CRITICAL']:
            summary += "Overall health assessment indicates elevated concern requiring medical attention."
        elif severity == 'MODERATE':
            summary += "Some concerning findings warrant follow-up evaluation."
        else:
            summary += "Results are within generally acceptable ranges."
        
        return summary
    
    def _generate_recommendations(self, validated_params: Dict[str, Any],
                                 analysis: Dict[str, Any],
                                 context: Optional[Dict[str, Any]],
                                 key_findings: List[str]) -> Dict[str, List[str]]:
        """Generate rule-based recommendations organized by category"""
        recommendations = {
            'diet': [],
            'lifestyle': [],
            'medical_advice': []
        }
        
        # Identify abnormal parameters for targeting recommendations
        abnormal_params = {
            name: info for name, info in validated_params.items()
            if info.get('status') in ['LOW', 'HIGH', 'CRITICAL']
        }
        
        # Generate diet recommendations
        if 'Glucose' in abnormal_params:
            recommendations['diet'].extend(self.recommendations_db['diet'].get('high_glucose', []))
        
        if any(param in abnormal_params for param in ['Cholesterol', 'LDL']):
            recommendations['diet'].extend(self.recommendations_db['diet'].get('high_cholesterol', []))
        
        if 'Triglycerides' in abnormal_params:
            recommendations['diet'].extend(self.recommendations_db['diet'].get('high_triglycerides', []))
        
        if 'Hemoglobin' in abnormal_params and abnormal_params.get('Hemoglobin', {}).get('status') == 'LOW':
            recommendations['diet'].extend(self.recommendations_db['diet'].get('low_hemoglobin', []))
        
        if any(param in abnormal_params for param in ['Creatinine', 'Urea']):
            recommendations['diet'].extend(self.recommendations_db['diet'].get('high_creatinine', []))
        
        # Default diet if no specific triggers
        if not recommendations['diet']:
            recommendations['diet'] = self.recommendations_db['diet']['default']
        
        # Generate lifestyle recommendations
        recommendations['lifestyle'] = self.recommendations_db['lifestyle']['general'].copy()
        
        if context:
            lifestyle = context.get('lifestyle', '').lower()
            if 'sedentary' in lifestyle or 'inactive' in lifestyle:
                recommendations['lifestyle'].extend(self.recommendations_db['lifestyle'].get('sedentary', []))
            
            if 'smoke' in lifestyle:
                recommendations['lifestyle'].extend(self.recommendations_db['lifestyle'].get('smoker', []))
        
        if analysis and analysis.get('severity') in ['HIGH', 'CRITICAL']:
            recommendations['lifestyle'].insert(0, 'Consult healthcare provider before starting new exercise program')
        
        # Generate medical advice
        if abnormal_params:
            if any(param in abnormal_params for param in ['Glucose', 'HbA1c']):
                recommendations['medical_advice'].extend(self.recommendations_db['medical_advice'].get('abnormal_glucose', []))
            elif any(param in abnormal_params for param in ['Cholesterol', 'HDL', 'LDL', 'Triglycerides']):
                recommendations['medical_advice'].extend(self.recommendations_db['medical_advice'].get('abnormal_lipids', []))
            elif 'Hemoglobin' in abnormal_params:
                recommendations['medical_advice'].extend(self.recommendations_db['medical_advice'].get('abnormal_hemoglobin', []))
            elif any(param in abnormal_params for param in ['Creatinine', 'Urea']):
                recommendations['medical_advice'].extend(self.recommendations_db['medical_advice'].get('abnormal_kidney', []))
            else:
                recommendations['medical_advice'].extend(self.recommendations_db['medical_advice'].get('default_abnormal', []))
        else:
            recommendations['medical_advice'] = [
                'Continue regular health check-ups (annual or per medical provider recommendation)',
                'Maintain current healthy lifestyle practices',
                'Monitor for any new health concerns',
                'Schedule routine follow-ups as per healthcare provider guidelines'
            ]
        
        # Remove duplicates while preserving order
        for category in recommendations:
            seen = set()
            unique_recs = []
            for rec in recommendations[category]:
                if rec not in seen:
                    seen.add(rec)
                    unique_recs.append(rec)
            recommendations[category] = unique_recs[:5]  # Limit to 5 per category
        
        return recommendations
    
    def _get_disclaimer(self) -> str:
        """Return hardcoded medical disclaimer (never LLM-generated)"""
        return (
            "MEDICAL DISCLAIMER: This analysis is for informational purposes only and should not "
            "replace professional medical advice, diagnosis, or treatment. Blood test results must be "
            "interpreted in clinical context by qualified healthcare professionals. Always consult with "
            "a physician or healthcare provider for medical decisions. In case of emergency, seek "
            "immediate medical attention. The AI analysis may contain errors and should be verified by "
            "medical professionals before use in clinical decision-making."
        )
    
    def _assess_completeness(self, validated_params: Dict[str, Any],
                            analysis: Dict[str, Any],
                            context: Optional[Dict[str, Any]]) -> str:
        """Assess completeness of analysis for transparency"""
        completeness_score = 0
        
        if validated_params and len(validated_params) > 0:
            completeness_score += 33
        
        if analysis and any(k in analysis for k in ['risk_scores', 'patterns', 'severity']):
            completeness_score += 33
        
        if context and any(context.get(k) for k in ['age', 'gender', 'medical_history']):
            completeness_score += 34
        
        if completeness_score >= 90:
            return 'Comprehensive (>90%)'
        elif completeness_score >= 66:
            return 'Substantial (66-90%)'
        elif completeness_score >= 33:
            return 'Partial (33-66%)'
        else:
            return 'Minimal (<33%)'
