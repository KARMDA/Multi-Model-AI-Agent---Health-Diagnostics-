"""
Unified Health Analyzer - Analyzes blood parameters for risk patterns and severity.

Consolidates:
- Parameter flagging (from interpreter.py)
- Pattern detection (from advanced_pattern_analysis.py)
- Risk scoring (from advanced_risk_calculator.py)

Features:
- Single HealthAnalyzer class with analyze() method
- Rule-based parameter flagging
- Risk scoring (diabetes, cardio, anemia) as 0.0-1.0 floats
- Pattern detection across parameter combinations
- Overall severity: LOW | MODERATE | HIGH | CRITICAL
"""

import logging
import math
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class HealthAnalyzer:
    """
    Analyzes blood parameters for risk patterns, abnormalities, and severity scores.
    
    Combines rule-based parameter flagging, pattern recognition, and risk scoring.
    """
    
    def __init__(self):
        """Initialize HealthAnalyzer with analysis rules and patterns."""
        
        # Parameter groups for pattern detection
        self.cbc_parameters = {
            'hemoglobin', 'hematocrit', 'rbc', 'mcv', 'mch', 'mchc', 'rdw',
            'wbc', 'neutrophils', 'lymphocytes', 'monocytes', 'eosinophils', 'basophils',
            'platelet', 'mpv'
        }
        
        self.lipid_parameters = {
            'cholesterol', 'hdl', 'ldl', 'triglycerides'
        }
        
        self.liver_parameters = {
            'alt', 'ast', 'alp', 'bilirubin', 'albumin', 'total_protein'
        }
        
        self.kidney_parameters = {
            'creatinine', 'bun', 'urea', 'egfr'
        }
        
        self.glucose_parameters = {
            'glucose', 'hba1c'
        }
        
        # Critical thresholds for severity escalation
        self.critical_thresholds = {
            'hemoglobin': (5.0, 20.0),
            'glucose': (30, 400),
            'potassium': (2.5, 6.5),
            'platelet': (20000, 1000000)
        }
    
    def analyze(self, validated_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze validated blood parameters for risk patterns and severity.
        
        Args:
            validated_params: Dictionary of validated parameters with format:
                {
                    param_name: {
                        'value': float,
                        'unit': str,
                        'status': str (LOW|NORMAL|HIGH|BORDERLINE|CRITICAL),
                        'reference_range': str,
                        'deviation': float
                    }
                }
        
        Returns:
            Dictionary with:
            {
                'parameter_flags': {param: status},
                'risk_scores': {diabetes_risk, cardio_risk, anemia_risk},
                'patterns': [detected_pattern_strings],
                'severity': str (LOW|MODERATE|HIGH|CRITICAL)
            }
        """
        
        # Step 1: Flag abnormal parameters
        parameter_flags = self._flag_parameters(validated_params)
        
        # Step 2: Calculate risk scores (0.0-1.0 range)
        risk_scores = self._calculate_risk_scores(validated_params, parameter_flags)
        
        # Step 3: Detect patterns across parameters
        patterns = self._detect_patterns(validated_params, parameter_flags)
        
        # Step 4: Determine overall severity
        severity = self._determine_severity(validated_params, parameter_flags, risk_scores, patterns)
        
        return {
            'parameter_flags': parameter_flags,
            'risk_scores': risk_scores,
            'patterns': patterns,
            'severity': severity
        }
    
    def _flag_parameters(self, validated_params: Dict[str, Any]) -> Dict[str, str]:
        """
        Flag abnormal parameters with binary status: NORMAL or ABNORMAL.
        """
        flags = {}
        
        for param_name, param_data in validated_params.items():
            if not isinstance(param_data, dict):
                continue
            
            status = param_data.get('status', 'UNKNOWN')
            
            if status in ['LOW', 'HIGH', 'BORDERLINE', 'CRITICAL']:
                flags[param_name] = 'ABNORMAL'
            else:
                flags[param_name] = 'NORMAL'
        
        return flags
    
    def _calculate_risk_scores(self, validated_params: Dict[str, Any], 
                              flags: Dict[str, str]) -> Dict[str, float]:
        """
        Calculate risk scores for diabetes, cardiovascular, and anemia (0.0-1.0 scale).
        """
        
        diabetes_risk = self._calculate_diabetes_risk(validated_params, flags)
        cardio_risk = self._calculate_cardio_risk(validated_params, flags)
        anemia_risk = self._calculate_anemia_risk(validated_params, flags)
        
        return {
            'diabetes_risk': round(diabetes_risk, 3),
            'cardio_risk': round(cardio_risk, 3),
            'anemia_risk': round(anemia_risk, 3)
        }
    
    def _calculate_diabetes_risk(self, params: Dict[str, Any], flags: Dict[str, str]) -> float:
        """Calculate diabetes risk score (0.0-1.0)."""
        
        score = 0.0
        
        # High glucose (fasting or random)
        glucose = params.get('Glucose', {}).get('value')
        if glucose:
            if glucose >= 200:
                score += 0.5
            elif glucose >= 126:
                score += 0.3
            elif glucose >= 100:
                score += 0.1
        
        # Elevated HbA1c indicates diabetes
        hba1c = params.get('Hba1c', {}).get('value')
        if hba1c:
            if hba1c >= 6.5:
                score += 0.4
            elif hba1c >= 5.7:
                score += 0.2
        
        # Elevated triglycerides (metabolic indicator)
        tg = params.get('Triglycerides', {}).get('value')
        if tg and tg > 150:
            score += 0.1
        
        # Low HDL (metabolic indicator)
        hdl = params.get('Hdl', {}).get('value')
        if hdl and hdl < 40:
            score += 0.1
        
        # Overweight indicators (if BMI available)
        bmi = params.get('Bmi', {}).get('value')
        if bmi and bmi >= 30:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_cardio_risk(self, params: Dict[str, Any], flags: Dict[str, str]) -> float:
        """Calculate cardiovascular risk score (0.0-1.0)."""
        
        score = 0.0
        
        # High Total Cholesterol
        tc = params.get('Cholesterol', {}).get('value')
        if tc:
            if tc >= 240:
                score += 0.3
            elif tc >= 200:
                score += 0.1
        
        # Low HDL (protective factor)
        hdl = params.get('Hdl', {}).get('value')
        if hdl:
            if hdl < 40:
                score += 0.3
            elif hdl < 50:
                score += 0.1
        
        # High LDL
        ldl = params.get('Ldl', {}).get('value')
        if ldl:
            if ldl >= 160:
                score += 0.25
            elif ldl >= 130:
                score += 0.1
        
        # High Triglycerides
        tg = params.get('Triglycerides', {}).get('value')
        if tg:
            if tg >= 200:
                score += 0.2
            elif tg >= 150:
                score += 0.1
        
        # Calculate lipid ratios
        if tc and hdl and hdl > 0:
            tc_hdl_ratio = tc / hdl
            if tc_hdl_ratio > 5.5:
                score += 0.15
            elif tc_hdl_ratio > 4.5:
                score += 0.05
        
        # High blood pressure (if available)
        if 'Hypertension' in params or flags.get('BloodPressure') == 'ABNORMAL':
            score += 0.15
        
        # Elevated glucose (metabolic risk)
        glucose = params.get('Glucose', {}).get('value')
        if glucose and glucose > 100:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_anemia_risk(self, params: Dict[str, Any], flags: Dict[str, str]) -> float:
        """Calculate anemia risk score (0.0-1.0)."""
        
        score = 0.0
        
        # Low Hemoglobin (primary anemia indicator)
        hb = params.get('Hemoglobin', {}).get('value')
        if hb:
            if hb < 7.0:
                score += 0.5  # Severe
            elif hb < 10.0:
                score += 0.4  # Moderate
            elif hb < 12.0:
                score += 0.2  # Mild
        
        # Low RBC
        rbc = params.get('Rbc', {}).get('value')
        if rbc:
            if rbc < 3.5:
                score += 0.2
        
        # Low Hematocrit (PCV)
        hct = params.get('Pcv', {}).get('value')
        if hct:
            if hct < 21:
                score += 0.2
        
        # Elevated RDW (red cell distribution abnormality)
        rdw = params.get('Rdw', {}).get('value')
        if rdw and rdw > 14.5:
            score += 0.1
        
        # Low Iron (if available)
        iron = params.get('Iron', {}).get('value')
        if iron and iron < 50:
            score += 0.15
        
        # Low Ferritin (iron store depletion)
        ferritin = params.get('Ferritin', {}).get('value')
        if ferritin and ferritin < 15:
            score += 0.15
        
        # Low B12 (pernicious anemia risk)
        b12 = params.get('Vitamin_B12', {}).get('value')
        if b12 and b12 < 200:
            score += 0.15
        
        return min(score, 1.0)
    
    def _detect_patterns(self, validated_params: Dict[str, Any], 
                        flags: Dict[str, str]) -> List[str]:
        """
        Detect clinically significant patterns across parameter combinations.
        Returns list of pattern descriptions.
        """
        patterns = []
        
        # CBC-related patterns
        patterns.extend(self._detect_cbc_patterns(validated_params, flags))
        
        # Lipid-related patterns
        patterns.extend(self._detect_lipid_patterns(validated_params, flags))
        
        # WBC distribution patterns
        patterns.extend(self._detect_wbc_patterns(validated_params, flags))
        
        # RBC index patterns
        patterns.extend(self._detect_rbc_patterns(validated_params, flags))
        
        # Kidney function patterns
        patterns.extend(self._detect_kidney_patterns(validated_params, flags))
        
        # Liver function patterns
        patterns.extend(self._detect_liver_patterns(validated_params, flags))
        
        # Cross-system patterns
        patterns.extend(self._detect_cross_system_patterns(validated_params, flags))
        
        return patterns
    
    def _detect_cbc_patterns(self, params: Dict[str, Any], flags: Dict[str, str]) -> List[str]:
        """Detect Complete Blood Count patterns."""
        patterns = []
        
        # Multiple CBC abnormalities
        cbc_abnormal = [p for p in flags if p.lower() in self.cbc_parameters and flags[p] == 'ABNORMAL']
        
        if len(cbc_abnormal) >= 5:
            patterns.append("Multiple severe CBC abnormalities detected across red cells, white cells, and platelets")
        elif len(cbc_abnormal) >= 3:
            patterns.append(f"Multiple CBC abnormalities in {len(cbc_abnormal)} parameters - investigate underlying cause")
        
        # Coordinated RBC abnormality
        rbc_abnormal = [p for p in ['Hemoglobin', 'Hematocrit', 'Rbc'] if p in flags and flags[p] == 'ABNORMAL']
        if len(rbc_abnormal) >= 2:
            hb_status = params.get('Hemoglobin', {}).get('status')
            if hb_status == 'LOW':
                patterns.append("Coordinated low hemoglobin and related indices suggest anemia")
        
        return patterns
    
    def _detect_lipid_patterns(self, params: Dict[str, Any], flags: Dict[str, str]) -> List[str]:
        """Detect lipid profile patterns."""
        patterns = []
        
        # Multiple lipid abnormalities
        lipid_abnormal = [p for p in flags if p.lower() in self.lipid_parameters and flags[p] == 'ABNORMAL']
        
        if len(lipid_abnormal) >= 3:
            patterns.append("Dyslipidemia: Multiple lipid abnormalities indicate elevated cardiovascular risk")
        elif len(lipid_abnormal) == 2:
            patterns.append("Lipid imbalance detected - may increase cardiovascular risk")
        
        # Cholesterol-HDL ratio analysis
        tc = params.get('Cholesterol', {}).get('value')
        hdl = params.get('Hdl', {}).get('value')
        
        if tc and hdl and hdl > 0:
            ratio = tc / hdl
            if ratio > 6.0:
                patterns.append(f"Very high TC/HDL ratio ({ratio:.1f}) - significant cardiovascular risk")
            elif ratio > 5.0:
                patterns.append(f"Elevated TC/HDL ratio ({ratio:.1f}) - increased cardiovascular risk")
        
        # TG/HDL ratio (insulin resistance marker)
        tg = params.get('Triglycerides', {}).get('value')
        if tg and hdl and hdl > 0:
            tg_hdl_ratio = tg / hdl
            if tg_hdl_ratio > 4.0:
                patterns.append(f"Elevated TG/HDL ratio ({tg_hdl_ratio:.1f}) - possible insulin resistance")
        
        return patterns
    
    def _detect_wbc_patterns(self, params: Dict[str, Any], flags: Dict[str, str]) -> List[str]:
        """Detect WBC distribution patterns."""
        patterns = []
        
        wbc_differential = ['Neutrophils', 'Lymphocytes', 'Monocytes', 'Eosinophils', 'Basophils']
        wbc_abnormal = [p for p in wbc_differential if p in flags and flags[p] == 'ABNORMAL']
        
        if len(wbc_abnormal) >= 3:
            # Check for opposing patterns
            low_count = sum(1 for p in wbc_abnormal if params.get(p, {}).get('status') == 'LOW')
            high_count = sum(1 for p in wbc_abnormal if params.get(p, {}).get('status') == 'HIGH')
            
            if low_count > 0 and high_count > 0:
                patterns.append("WBC distribution imbalance - lymphocytosis with neutropenia or similar")
            else:
                patterns.append(f"Multiple WBC differential abnormalities across {len(wbc_abnormal)} cell types")
        
        return patterns
    
    def _detect_rbc_patterns(self, params: Dict[str, Any], flags: Dict[str, str]) -> List[str]:
        """Detect RBC index patterns."""
        patterns = []
        
        rbc_indices = ['Mcv', 'Mch', 'Mchc', 'Rdw']
        rbc_abnormal = [p for p in rbc_indices if p in flags and flags[p] == 'ABNORMAL']
        
        if len(rbc_abnormal) >= 2:
            mcv = params.get('Mcv', {}).get('value')
            rdw = params.get('Rdw', {}).get('value')
            
            if mcv and mcv < 80:
                patterns.append("Microcytic anemia pattern - low MCV with abnormal RBC indices")
            elif mcv and mcv > 100:
                patterns.append("Macrocytic anemia pattern - high MCV with abnormal RBC indices")
            elif rdw:
                patterns.append("RBC morphology variation indicated by elevated RDW - suggests mixed anemia")
        
        return patterns
    
    def _detect_kidney_patterns(self, params: Dict[str, Any], flags: Dict[str, str]) -> List[str]:
        """Detect kidney function patterns."""
        patterns = []
        
        creat = params.get('Creatinine', {}).get('value')
        bun = params.get('Bun', {}).get('value')
        urea = params.get('Urea', {}).get('value')
        
        kidney_abnormal = sum(1 for p in ['Creatinine', 'Bun', 'Urea'] 
                            if p in flags and flags[p] == 'ABNORMAL')
        
        if kidney_abnormal >= 2:
            if creat and creat > 2.0:
                patterns.append("Severe renal dysfunction: markedly elevated creatinine with BUN abnormality")
            elif creat and creat > 1.5:
                patterns.append("Renal impairment pattern: elevated creatinine and urea/BUN suggest kidney dysfunction")
            else:
                patterns.append("Abnormal kidney function markers - consider GFR assessment")
        
        return patterns
    
    def _detect_liver_patterns(self, params: Dict[str, Any], flags: Dict[str, str]) -> List[str]:
        """Detect liver function patterns."""
        patterns = []
        
        alt = params.get('Alt', {}).get('value')
        ast = params.get('Ast', {}).get('value')
        bilirubin = params.get('Bilirubin_Total', {}).get('value')
        albumin = params.get('Albumin', {}).get('value')
        
        liver_abnormal = sum(1 for p in ['Alt', 'Ast', 'Bilirubin_Total', 'Albumin'] 
                           if p in flags and flags[p] == 'ABNORMAL')
        
        if liver_abnormal >= 2:
            if ast and alt and ast > alt * 2:
                patterns.append("AST > 2x ALT pattern suggests alcoholic or viral hepatitis")
            elif alt and alt > 100:
                patterns.append("Elevated ALT with abnormal liver tests - hepatocellular injury indicated")
            elif bilirubin and bilirubin > 2.0:
                patterns.append("Hyperbilirubinemia with abnormal LFTs - cholestasis or hemolysis possible")
            else:
                patterns.append("Liver function abnormality pattern - hepatic assessment recommended")
        
        if albumin and albumin < 3.5:
            if bilirubin and bilirubin > 1.2:
                patterns.append("Low albumin with elevated bilirubin suggests chronic liver disease")
        
        return patterns
    
    def _detect_cross_system_patterns(self, params: Dict[str, Any], 
                                     flags: Dict[str, str]) -> List[str]:
        """Detect patterns across multiple organ systems."""
        patterns = []
        
        # Count abnormalities by system
        cbc_abnormal = sum(1 for p in flags if p.lower() in self.cbc_parameters and flags[p] == 'ABNORMAL')
        kidney_abnormal = sum(1 for p in flags if p.lower() in self.kidney_parameters and flags[p] == 'ABNORMAL')
        liver_abnormal = sum(1 for p in flags if p.lower() in self.liver_parameters and flags[p] == 'ABNORMAL')
        lipid_abnormal = sum(1 for p in flags if p.lower() in self.lipid_parameters and flags[p] == 'ABNORMAL')
        
        affected_systems = sum(1 for count in [cbc_abnormal, kidney_abnormal, liver_abnormal, lipid_abnormal] if count > 0)
        
        if affected_systems >= 3:
            patterns.append(f"Multi-system involvement: abnormalities across {affected_systems} organ systems suggest systemic disease")
        
        # Metabolic syndrome pattern
        glucose = params.get('Glucose', {}).get('value')
        tg = params.get('Triglycerides', {}).get('value')
        hdl = params.get('Hdl', {}).get('value')
        
        metabolic_indicators = 0
        if glucose and glucose >= 100:
            metabolic_indicators += 1
        if tg and tg >= 150:
            metabolic_indicators += 1
        if hdl and hdl < 40:
            metabolic_indicators += 1
        
        if metabolic_indicators >= 3:
            patterns.append("Metabolic syndrome pattern: elevated glucose/TG with low HDL suggests metabolic disorder")
        
        return patterns
    
    def _determine_severity(self, params: Dict[str, Any], flags: Dict[str, str],
                           risk_scores: Dict[str, float], patterns: List[str]) -> str:
        """
        Determine overall severity level: LOW | MODERATE | HIGH | CRITICAL.
        """
        
        severity_score = 0
        
        # Critical status escalation
        for param_name, (min_crit, max_crit) in self.critical_thresholds.items():
            value = params.get(param_name, {}).get('value')
            if value and (value < min_crit or value > max_crit):
                return 'CRITICAL'
        
        # Count CRITICAL status parameters
        critical_count = sum(1 for p in params.values() 
                           if isinstance(p, dict) and p.get('status') == 'CRITICAL')
        if critical_count >= 3:
            return 'CRITICAL'
        elif critical_count >= 1:
            severity_score += 0.4
        
        # Count abnormal parameters
        abnormal_count = sum(1 for flag in flags.values() if flag == 'ABNORMAL')
        if abnormal_count > 15:
            severity_score += 0.6
        elif abnormal_count > 10:
            severity_score += 0.4
        elif abnormal_count > 5:
            severity_score += 0.2
        
        # Risk score contribution
        max_risk = max(risk_scores.values())
        if max_risk >= 0.8:
            severity_score += 0.4
        elif max_risk >= 0.6:
            severity_score += 0.3
        elif max_risk >= 0.4:
            severity_score += 0.2
        
        # Pattern severity
        high_severity_patterns = [p for p in patterns if any(
            keyword in p.lower() for keyword in ['severe', 'critical', 'multi-system', 'systemic']
        )]
        
        if len(high_severity_patterns) >= 2:
            severity_score += 0.5
        elif len(high_severity_patterns) >= 1:
            severity_score += 0.3
        elif len(patterns) >= 3:
            severity_score += 0.2
        
        # Determine final severity
        if severity_score >= 0.9:
            return 'CRITICAL'
        elif severity_score >= 0.6:
            return 'HIGH'
        elif severity_score >= 0.3:
            return 'MODERATE'
        else:
            return 'LOW'
