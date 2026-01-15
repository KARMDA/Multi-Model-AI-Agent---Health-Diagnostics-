"""
Advanced Risk Calculator Module
Implements:
1. Framingham Cardiovascular Risk Score
2. Lipid Panel Ratio Calculations
3. Metabolic Syndrome Detection
"""

import math
from typing import Dict, Optional, Tuple, List


class AdvancedRiskCalculator:
    """
    Advanced medical risk calculations based on blood parameters and patient context.
    """
    
    def __init__(self):
        # Framingham coefficients for 10-year CVD risk
        # Based on published Framingham Heart Study data
        self.framingham_coefficients = {
            'male': {
                'age': 0.04826,
                'total_cholesterol': 0.0,  # Varies by age
                'hdl': -0.0,  # Varies by age
                'sbp_treated': 0.0,
                'sbp_untreated': 0.0,
                'smoker': 0.0,
                'diabetes': 0.0,
                'baseline': -29.799
            },
            'female': {
                'age': 0.0,
                'total_cholesterol': 0.0,
                'hdl': -0.0,
                'sbp_treated': 0.0,
                'sbp_untreated': 0.0,
                'smoker': 0.0,
                'diabetes': 0.0,
                'baseline': -29.18
            }
        }

    def calculate_lipid_ratios(self, report_data: Dict) -> Dict:
        """
        Calculate Lipid Panel Ratios:
        1. Total Cholesterol / HDL Ratio
        2. LDL / HDL Ratio
        3. Triglyceride / HDL Ratio
        4. Non-HDL Cholesterol
        5. Atherogenic Index of Plasma (AIP)
        """
        
        def get_value(param_name):
            for key in report_data:
                if param_name.lower() in key.lower():
                    try:
                        return float(report_data[key].get('value', 0))
                    except:
                        return None
            return None
        
        total_chol = get_value('cholesterol') or get_value('total cholesterol')
        hdl = get_value('hdl')
        ldl = get_value('ldl')
        triglycerides = get_value('triglyceride')
        
        ratios = {
            'available': False,
            'total_cholesterol': total_chol,
            'hdl': hdl,
            'ldl': ldl,
            'triglycerides': triglycerides,
            'ratios': {},
            'interpretations': [],
            'risk_level': 'Unknown'
        }
        
        risk_points = 0
        
        # 1. Total Cholesterol / HDL Ratio (Cardiac Risk Ratio)
        if total_chol and hdl and hdl > 0:
            ratios['available'] = True
            tc_hdl_ratio = round(total_chol / hdl, 2)
            ratios['ratios']['tc_hdl_ratio'] = {
                'value': tc_hdl_ratio,
                'name': 'Total Cholesterol / HDL Ratio',
                'optimal': '< 4.0',
                'status': 'Optimal' if tc_hdl_ratio < 4.0 else 'Borderline' if tc_hdl_ratio < 5.0 else 'High Risk'
            }
            if tc_hdl_ratio >= 5.0:
                ratios['interpretations'].append(f"⚠️ TC/HDL Ratio ({tc_hdl_ratio}) is HIGH - Increased cardiovascular risk")
                risk_points += 2
            elif tc_hdl_ratio >= 4.0:
                ratios['interpretations'].append(f"⚡ TC/HDL Ratio ({tc_hdl_ratio}) is BORDERLINE - Monitor closely")
                risk_points += 1
            else:
                ratios['interpretations'].append(f"✅ TC/HDL Ratio ({tc_hdl_ratio}) is OPTIMAL")
        
        # 2. LDL / HDL Ratio
        if ldl and hdl and hdl > 0:
            ratios['available'] = True
            ldl_hdl_ratio = round(ldl / hdl, 2)
            ratios['ratios']['ldl_hdl_ratio'] = {
                'value': ldl_hdl_ratio,
                'name': 'LDL / HDL Ratio',
                'optimal': '< 2.5 (Men), < 2.0 (Women)',
                'status': 'Optimal' if ldl_hdl_ratio < 2.5 else 'Borderline' if ldl_hdl_ratio < 3.5 else 'High Risk'
            }
            if ldl_hdl_ratio >= 3.5:
                ratios['interpretations'].append(f"⚠️ LDL/HDL Ratio ({ldl_hdl_ratio}) is HIGH - Atherogenic risk elevated")
                risk_points += 2
            elif ldl_hdl_ratio >= 2.5:
                ratios['interpretations'].append(f"⚡ LDL/HDL Ratio ({ldl_hdl_ratio}) is BORDERLINE")
                risk_points += 1
            else:
                ratios['interpretations'].append(f"✅ LDL/HDL Ratio ({ldl_hdl_ratio}) is OPTIMAL")
        
        # 3. Triglyceride / HDL Ratio (Insulin Resistance Marker)
        if triglycerides and hdl and hdl > 0:
            ratios['available'] = True
            tg_hdl_ratio = round(triglycerides / hdl, 2)
            ratios['ratios']['tg_hdl_ratio'] = {
                'value': tg_hdl_ratio,
                'name': 'Triglyceride / HDL Ratio',
                'optimal': '< 2.0',
                'status': 'Optimal' if tg_hdl_ratio < 2.0 else 'Borderline' if tg_hdl_ratio < 4.0 else 'High Risk'
            }
            if tg_hdl_ratio >= 4.0:
                ratios['interpretations'].append(f"⚠️ TG/HDL Ratio ({tg_hdl_ratio}) is HIGH - Insulin resistance likely")
                risk_points += 2
            elif tg_hdl_ratio >= 2.0:
                ratios['interpretations'].append(f"⚡ TG/HDL Ratio ({tg_hdl_ratio}) is BORDERLINE - Pre-diabetic indicator")
                risk_points += 1
            else:
                ratios['interpretations'].append(f"✅ TG/HDL Ratio ({tg_hdl_ratio}) is OPTIMAL - Good insulin sensitivity")
        
        # 4. Non-HDL Cholesterol
        if total_chol and hdl:
            ratios['available'] = True
            non_hdl = round(total_chol - hdl, 1)
            ratios['ratios']['non_hdl_cholesterol'] = {
                'value': non_hdl,
                'name': 'Non-HDL Cholesterol',
                'optimal': '< 130 mg/dL',
                'status': 'Optimal' if non_hdl < 130 else 'Borderline' if non_hdl < 160 else 'High Risk'
            }
            if non_hdl >= 160:
                ratios['interpretations'].append(f"⚠️ Non-HDL Cholesterol ({non_hdl} mg/dL) is HIGH")
                risk_points += 2
            elif non_hdl >= 130:
                ratios['interpretations'].append(f"⚡ Non-HDL Cholesterol ({non_hdl} mg/dL) is BORDERLINE")
                risk_points += 1
            else:
                ratios['interpretations'].append(f"✅ Non-HDL Cholesterol ({non_hdl} mg/dL) is OPTIMAL")
        
        # 5. Atherogenic Index of Plasma (AIP) = log10(TG/HDL)
        if triglycerides and hdl and hdl > 0 and triglycerides > 0:
            # Convert to mmol/L for AIP calculation (TG: mg/dL * 0.0113, HDL: mg/dL * 0.0259)
            tg_mmol = triglycerides * 0.0113
            hdl_mmol = hdl * 0.0259
            if tg_mmol > 0 and hdl_mmol > 0:
                aip = round(math.log10(tg_mmol / hdl_mmol), 3)
                ratios['ratios']['aip'] = {
                    'value': aip,
                    'name': 'Atherogenic Index of Plasma (AIP)',
                    'optimal': '< 0.11',
                    'status': 'Low Risk' if aip < 0.11 else 'Intermediate' if aip < 0.21 else 'High Risk'
                }
                if aip >= 0.21:
                    ratios['interpretations'].append(f"⚠️ AIP ({aip}) indicates HIGH cardiovascular risk")
                    risk_points += 2
                elif aip >= 0.11:
                    ratios['interpretations'].append(f"⚡ AIP ({aip}) indicates INTERMEDIATE risk")
                    risk_points += 1
                else:
                    ratios['interpretations'].append(f"✅ AIP ({aip}) indicates LOW cardiovascular risk")
        
        # Overall lipid risk level
        if risk_points >= 6:
            ratios['risk_level'] = 'High'
        elif risk_points >= 3:
            ratios['risk_level'] = 'Moderate'
        elif risk_points >= 1:
            ratios['risk_level'] = 'Low-Moderate'
        else:
            ratios['risk_level'] = 'Low'
        
        ratios['risk_points'] = risk_points
        
        return ratios

    def calculate_framingham_risk(self, report_data: Dict, user_context: Dict) -> Dict:
        """
        Calculate Framingham 10-Year Cardiovascular Risk Score.
        
        Required inputs:
        - Age (30-79 years)
        - Gender (Male/Female)
        - Total Cholesterol
        - HDL Cholesterol
        - Systolic Blood Pressure (optional, uses default if not available)
        - Smoking status
        - Diabetes status
        - BP treatment status
        """
        
        def get_value(param_name):
            for key in report_data:
                if param_name.lower() in key.lower():
                    try:
                        return float(report_data[key].get('value', 0))
                    except:
                        return None
            return None
        
        age = user_context.get('age')
        gender = user_context.get('gender', '').lower()
        total_chol = get_value('cholesterol') or get_value('total cholesterol')
        hdl = get_value('hdl')
        
        # Get from context
        medical_history = user_context.get('medical_history', [])
        lifestyle = user_context.get('lifestyle', {})
        
        is_diabetic = 'Diabetes' in medical_history
        is_smoker = lifestyle.get('smoker', False)
        is_bp_treated = 'Hypertension' in medical_history  # Assume treated if has hypertension
        
        # Default SBP if not in report (use average normal)
        sbp = get_value('systolic') or get_value('blood pressure') or 120
        
        result = {
            'available': False,
            'risk_percentage': None,
            'risk_category': 'Unknown',
            'inputs_used': {},
            'missing_inputs': [],
            'interpretation': '',
            'recommendations': []
        }
        
        # Check required inputs
        if not age or age < 30 or age > 79:
            result['missing_inputs'].append('Age (must be 30-79 years)')
        if not gender or gender not in ['male', 'female']:
            result['missing_inputs'].append('Gender')
        if not total_chol:
            result['missing_inputs'].append('Total Cholesterol')
        if not hdl:
            result['missing_inputs'].append('HDL Cholesterol')
        
        if result['missing_inputs']:
            result['interpretation'] = f"Cannot calculate Framingham Risk. Missing: {', '.join(result['missing_inputs'])}"
            return result
        
        result['available'] = True
        result['inputs_used'] = {
            'age': age,
            'gender': gender.capitalize(),
            'total_cholesterol': total_chol,
            'hdl': hdl,
            'systolic_bp': sbp,
            'bp_treated': is_bp_treated,
            'smoker': is_smoker,
            'diabetic': is_diabetic
        }
        
        # Framingham Risk Score Calculation (Simplified Point System)
        # Based on ATP III guidelines
        
        points = 0
        point_breakdown = []
        
        if gender == 'male':
            # Age points (Male)
            if age < 35:
                points += -9
                point_breakdown.append(f"Age {age}: -9 points")
            elif age < 40:
                points += -4
                point_breakdown.append(f"Age {age}: -4 points")
            elif age < 45:
                points += 0
                point_breakdown.append(f"Age {age}: 0 points")
            elif age < 50:
                points += 3
                point_breakdown.append(f"Age {age}: +3 points")
            elif age < 55:
                points += 6
                point_breakdown.append(f"Age {age}: +6 points")
            elif age < 60:
                points += 8
                point_breakdown.append(f"Age {age}: +8 points")
            elif age < 65:
                points += 10
                point_breakdown.append(f"Age {age}: +10 points")
            elif age < 70:
                points += 11
                point_breakdown.append(f"Age {age}: +11 points")
            else:
                points += 12
                point_breakdown.append(f"Age {age}: +12 points")
            
            # Total Cholesterol points (Male)
            if total_chol < 160:
                points += 0
                point_breakdown.append(f"Total Cholesterol {total_chol}: 0 points")
            elif total_chol < 200:
                points += 1
                point_breakdown.append(f"Total Cholesterol {total_chol}: +1 point")
            elif total_chol < 240:
                points += 2
                point_breakdown.append(f"Total Cholesterol {total_chol}: +2 points")
            elif total_chol < 280:
                points += 3
                point_breakdown.append(f"Total Cholesterol {total_chol}: +3 points")
            else:
                points += 4
                point_breakdown.append(f"Total Cholesterol {total_chol}: +4 points")
            
            # HDL points (Male)
            if hdl >= 60:
                points += -1
                point_breakdown.append(f"HDL {hdl}: -1 point (protective)")
            elif hdl >= 50:
                points += 0
                point_breakdown.append(f"HDL {hdl}: 0 points")
            elif hdl >= 40:
                points += 1
                point_breakdown.append(f"HDL {hdl}: +1 point")
            else:
                points += 2
                point_breakdown.append(f"HDL {hdl}: +2 points (low)")
            
            # SBP points (Male)
            if is_bp_treated:
                if sbp < 120:
                    points += 0
                elif sbp < 130:
                    points += 1
                elif sbp < 140:
                    points += 2
                elif sbp < 160:
                    points += 2
                else:
                    points += 3
                point_breakdown.append(f"SBP {sbp} (treated): +{points} points")
            else:
                if sbp < 120:
                    points += 0
                elif sbp < 130:
                    points += 0
                elif sbp < 140:
                    points += 1
                elif sbp < 160:
                    points += 1
                else:
                    points += 2
                point_breakdown.append(f"SBP {sbp} (untreated): points added")
            
            # Smoking (Male)
            if is_smoker:
                points += 3
                point_breakdown.append("Smoker: +3 points")
            
            # Diabetes (Male)
            if is_diabetic:
                points += 2
                point_breakdown.append("Diabetic: +2 points")
            
            # Convert points to 10-year risk (Male)
            risk_table = {
                -1: 1, 0: 1, 1: 1, 2: 1, 3: 1, 4: 1,
                5: 2, 6: 2, 7: 3, 8: 4, 9: 5, 10: 6,
                11: 8, 12: 10, 13: 12, 14: 16, 15: 20, 16: 25
            }
            
        else:  # Female
            # Age points (Female)
            if age < 35:
                points += -7
                point_breakdown.append(f"Age {age}: -7 points")
            elif age < 40:
                points += -3
                point_breakdown.append(f"Age {age}: -3 points")
            elif age < 45:
                points += 0
                point_breakdown.append(f"Age {age}: 0 points")
            elif age < 50:
                points += 3
                point_breakdown.append(f"Age {age}: +3 points")
            elif age < 55:
                points += 6
                point_breakdown.append(f"Age {age}: +6 points")
            elif age < 60:
                points += 8
                point_breakdown.append(f"Age {age}: +8 points")
            elif age < 65:
                points += 10
                point_breakdown.append(f"Age {age}: +10 points")
            elif age < 70:
                points += 12
                point_breakdown.append(f"Age {age}: +12 points")
            else:
                points += 14
                point_breakdown.append(f"Age {age}: +14 points")
            
            # Total Cholesterol points (Female)
            if total_chol < 160:
                points += 0
            elif total_chol < 200:
                points += 1
            elif total_chol < 240:
                points += 2
            elif total_chol < 280:
                points += 3
            else:
                points += 4
            point_breakdown.append(f"Total Cholesterol {total_chol}: points added")
            
            # HDL points (Female)
            if hdl >= 60:
                points += -1
            elif hdl >= 50:
                points += 0
            elif hdl >= 40:
                points += 1
            else:
                points += 2
            point_breakdown.append(f"HDL {hdl}: points added")
            
            # SBP points (Female) - similar to male
            if is_bp_treated:
                if sbp < 120:
                    points += 0
                elif sbp < 130:
                    points += 1
                elif sbp < 140:
                    points += 2
                elif sbp < 160:
                    points += 3
                else:
                    points += 4
            else:
                if sbp < 120:
                    points += 0
                elif sbp < 130:
                    points += 0
                elif sbp < 140:
                    points += 1
                elif sbp < 160:
                    points += 2
                else:
                    points += 3
            point_breakdown.append(f"SBP {sbp}: points added")
            
            # Smoking (Female)
            if is_smoker:
                points += 4
                point_breakdown.append("Smoker: +4 points")
            
            # Diabetes (Female)
            if is_diabetic:
                points += 4
                point_breakdown.append("Diabetic: +4 points")
            
            # Convert points to 10-year risk (Female)
            risk_table = {
                -2: 1, -1: 1, 0: 1, 1: 1, 2: 1, 3: 1, 4: 1,
                5: 2, 6: 2, 7: 3, 8: 4, 9: 5, 10: 6,
                11: 8, 12: 10, 13: 12, 14: 16, 15: 20, 16: 25, 17: 30
            }
        
        # Get risk percentage
        if points < min(risk_table.keys()):
            risk_pct = 1
        elif points > max(risk_table.keys()):
            risk_pct = 30
        else:
            risk_pct = risk_table.get(points, 30)
        
        result['total_points'] = points
        result['point_breakdown'] = point_breakdown
        result['risk_percentage'] = risk_pct
        
        # Categorize risk
        if risk_pct < 10:
            result['risk_category'] = 'Low'
            result['interpretation'] = f"Your 10-year cardiovascular risk is {risk_pct}% (LOW). Continue healthy lifestyle."
        elif risk_pct < 20:
            result['risk_category'] = 'Moderate'
            result['interpretation'] = f"Your 10-year cardiovascular risk is {risk_pct}% (MODERATE). Lifestyle modifications recommended."
        else:
            result['risk_category'] = 'High'
            result['interpretation'] = f"Your 10-year cardiovascular risk is {risk_pct}% (HIGH). Medical intervention may be needed."
        
        # Generate recommendations
        if risk_pct >= 10:
            result['recommendations'].append("Consider statin therapy discussion with doctor")
        if is_smoker:
            result['recommendations'].append("Smoking cessation is critical - reduces risk by 50% in 1 year")
        if total_chol > 200:
            result['recommendations'].append("Reduce saturated fat intake, increase fiber")
        if hdl < 40:
            result['recommendations'].append("Increase HDL through exercise and omega-3 fatty acids")
        if is_diabetic:
            result['recommendations'].append("Strict blood sugar control reduces cardiovascular risk")
        if sbp > 140:
            result['recommendations'].append("Blood pressure control is essential")
        
        return result

    def detect_metabolic_syndrome(self, report_data: Dict, user_context: Dict) -> Dict:
        """
        Detect Metabolic Syndrome based on NCEP ATP III criteria.
        
        Metabolic Syndrome is diagnosed when 3 or more of the following 5 criteria are met:
        1. Waist circumference: >102 cm (men), >88 cm (women) - OR use BMI proxy
        2. Triglycerides: ≥150 mg/dL
        3. HDL Cholesterol: <40 mg/dL (men), <50 mg/dL (women)
        4. Blood Pressure: ≥130/85 mmHg or on treatment
        5. Fasting Glucose: ≥100 mg/dL or on treatment
        """
        
        def get_value(param_name):
            for key in report_data:
                if param_name.lower() in key.lower():
                    try:
                        return float(report_data[key].get('value', 0))
                    except:
                        return None
            return None
        
        age = user_context.get('age')
        gender = user_context.get('gender', '').lower()
        medical_history = user_context.get('medical_history', [])
        
        # Get values from report
        triglycerides = get_value('triglyceride')
        hdl = get_value('hdl')
        glucose = get_value('glucose') or get_value('fasting glucose') or get_value('blood sugar')
        sbp = get_value('systolic') or get_value('blood pressure')
        
        result = {
            'available': False,
            'criteria_met': 0,
            'criteria_details': [],
            'has_metabolic_syndrome': False,
            'risk_level': 'Unknown',
            'interpretation': '',
            'recommendations': [],
            'missing_data': []
        }
        
        criteria_count = 0
        criteria_details = []
        
        # Criterion 1: Abdominal Obesity (using proxy - check if diabetic/hypertensive as indicator)
        # Since we don't have waist circumference, we use medical history as proxy
        has_obesity_indicator = 'Diabetes' in medical_history or 'Hypertension' in medical_history
        if has_obesity_indicator:
            criteria_count += 1
            criteria_details.append({
                'criterion': 'Abdominal Obesity (Proxy)',
                'met': True,
                'value': 'Inferred from medical history',
                'threshold': 'Diabetes/Hypertension present',
                'note': 'Waist circumference not available - using medical history as proxy'
            })
        else:
            criteria_details.append({
                'criterion': 'Abdominal Obesity',
                'met': False,
                'value': 'Not assessed',
                'threshold': '>102cm (M) / >88cm (F)',
                'note': 'Waist circumference not in blood report'
            })
            result['missing_data'].append('Waist circumference')
        
        # Criterion 2: Elevated Triglycerides
        if triglycerides is not None:
            result['available'] = True
            tg_met = triglycerides >= 150
            if tg_met:
                criteria_count += 1
            criteria_details.append({
                'criterion': 'Elevated Triglycerides',
                'met': tg_met,
                'value': f"{triglycerides} mg/dL",
                'threshold': '≥150 mg/dL',
                'status': '⚠️ HIGH' if tg_met else '✅ Normal'
            })
        else:
            result['missing_data'].append('Triglycerides')
            criteria_details.append({
                'criterion': 'Elevated Triglycerides',
                'met': False,
                'value': 'Not available',
                'threshold': '≥150 mg/dL',
                'status': '❓ Unknown'
            })
        
        # Criterion 3: Low HDL Cholesterol
        if hdl is not None:
            result['available'] = True
            if gender == 'male':
                hdl_met = hdl < 40
                threshold = '<40 mg/dL (Male)'
            else:
                hdl_met = hdl < 50
                threshold = '<50 mg/dL (Female)'
            
            if hdl_met:
                criteria_count += 1
            criteria_details.append({
                'criterion': 'Low HDL Cholesterol',
                'met': hdl_met,
                'value': f"{hdl} mg/dL",
                'threshold': threshold,
                'status': '⚠️ LOW' if hdl_met else '✅ Normal'
            })
        else:
            result['missing_data'].append('HDL Cholesterol')
            criteria_details.append({
                'criterion': 'Low HDL Cholesterol',
                'met': False,
                'value': 'Not available',
                'threshold': '<40 (M) / <50 (F) mg/dL',
                'status': '❓ Unknown'
            })
        
        # Criterion 4: Elevated Blood Pressure
        has_hypertension = 'Hypertension' in medical_history
        if sbp is not None:
            result['available'] = True
            bp_met = sbp >= 130 or has_hypertension
            if bp_met:
                criteria_count += 1
            criteria_details.append({
                'criterion': 'Elevated Blood Pressure',
                'met': bp_met,
                'value': f"{sbp} mmHg" + (" (on treatment)" if has_hypertension else ""),
                'threshold': '≥130/85 mmHg or on treatment',
                'status': '⚠️ HIGH' if bp_met else '✅ Normal'
            })
        elif has_hypertension:
            result['available'] = True
            criteria_count += 1
            criteria_details.append({
                'criterion': 'Elevated Blood Pressure',
                'met': True,
                'value': 'On treatment (Hypertension history)',
                'threshold': '≥130/85 mmHg or on treatment',
                'status': '⚠️ On Treatment'
            })
        else:
            result['missing_data'].append('Blood Pressure')
            criteria_details.append({
                'criterion': 'Elevated Blood Pressure',
                'met': False,
                'value': 'Not available',
                'threshold': '≥130/85 mmHg',
                'status': '❓ Unknown'
            })
        
        # Criterion 5: Elevated Fasting Glucose
        has_diabetes = 'Diabetes' in medical_history
        if glucose is not None:
            result['available'] = True
            glucose_met = glucose >= 100 or has_diabetes
            if glucose_met:
                criteria_count += 1
            criteria_details.append({
                'criterion': 'Elevated Fasting Glucose',
                'met': glucose_met,
                'value': f"{glucose} mg/dL" + (" (Diabetic)" if has_diabetes else ""),
                'threshold': '≥100 mg/dL or on treatment',
                'status': '⚠️ HIGH' if glucose_met else '✅ Normal'
            })
        elif has_diabetes:
            result['available'] = True
            criteria_count += 1
            criteria_details.append({
                'criterion': 'Elevated Fasting Glucose',
                'met': True,
                'value': 'On treatment (Diabetes history)',
                'threshold': '≥100 mg/dL or on treatment',
                'status': '⚠️ Diabetic'
            })
        else:
            result['missing_data'].append('Fasting Glucose')
            criteria_details.append({
                'criterion': 'Elevated Fasting Glucose',
                'met': False,
                'value': 'Not available',
                'threshold': '≥100 mg/dL',
                'status': '❓ Unknown'
            })
        
        result['criteria_met'] = criteria_count
        result['criteria_details'] = criteria_details
        result['has_metabolic_syndrome'] = criteria_count >= 3
        
        # Risk level
        if criteria_count >= 4:
            result['risk_level'] = 'Very High'
        elif criteria_count >= 3:
            result['risk_level'] = 'High'
        elif criteria_count >= 2:
            result['risk_level'] = 'Moderate'
        elif criteria_count >= 1:
            result['risk_level'] = 'Low-Moderate'
        else:
            result['risk_level'] = 'Low'
        
        # Interpretation
        if result['has_metabolic_syndrome']:
            result['interpretation'] = f"⚠️ METABOLIC SYNDROME DETECTED ({criteria_count}/5 criteria met). This significantly increases risk of Type 2 Diabetes, Heart Disease, and Stroke."
        elif criteria_count >= 2:
            result['interpretation'] = f"⚡ PRE-METABOLIC SYNDROME ({criteria_count}/5 criteria met). At risk - lifestyle intervention recommended."
        else:
            result['interpretation'] = f"✅ No Metabolic Syndrome ({criteria_count}/5 criteria met)."
        
        # Recommendations
        if result['has_metabolic_syndrome'] or criteria_count >= 2:
            result['recommendations'] = [
                "Weight loss of 7-10% body weight significantly reduces risk",
                "150 minutes/week of moderate exercise",
                "Mediterranean or DASH diet recommended",
                "Reduce refined carbohydrates and sugars",
                "Regular monitoring of blood pressure and glucose",
                "Consider consultation with endocrinologist"
            ]
            
            if triglycerides and triglycerides >= 150:
                result['recommendations'].append("Reduce triglycerides: limit alcohol, sugars, and refined carbs")
            if hdl and ((gender == 'male' and hdl < 40) or (gender == 'female' and hdl < 50)):
                result['recommendations'].append("Increase HDL: aerobic exercise, omega-3 fatty acids, quit smoking")
            if glucose and glucose >= 100:
                result['recommendations'].append("Blood sugar control: low glycemic index foods, regular meals")
        
        return result


def calculate_all_advanced_risks(report_data: Dict, user_context: Dict) -> Dict:
    """
    Calculate all advanced risk metrics.
    Returns combined results for Lipid Ratios, Framingham Risk, and Metabolic Syndrome.
    """
    calculator = AdvancedRiskCalculator()
    
    return {
        'lipid_ratios': calculator.calculate_lipid_ratios(report_data),
        'framingham_risk': calculator.calculate_framingham_risk(report_data, user_context),
        'metabolic_syndrome': calculator.detect_metabolic_syndrome(report_data, user_context)
    }
