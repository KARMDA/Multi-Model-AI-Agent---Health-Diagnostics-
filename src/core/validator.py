"""
Unified Blood Report Validator - Validates blood parameters against reference ranges.

Features:
- Single class BloodReportValidator with validate() method
- Age/gender-adjusted reference ranges
- Confidence scoring: LOW, NORMAL, HIGH, BORDERLINE, CRITICAL
- Cross-parameter consistency checks
- Loads reference_ranges.json at init (not per call)
- Pure validation logic — no external API calls
"""

import json
import logging
import os
import re
from typing import Dict, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class BloodReportValidator:
    """
    Validates blood report parameters against reference ranges.
    
    Applies age/gender adjustments and performs cross-parameter consistency checks.
    Reference ranges loaded once at initialization.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize BloodReportValidator.
        
        Args:
            config_path: Path to reference_ranges.json (uses env var or default if None)
        """
        # Determine config path
        if config_path is None:
            config_path = os.getenv(
                "REFERENCE_RANGES_PATH",
                "config/reference_ranges.json"
            )
        
        # Load reference ranges at init
        self.reference_ranges = self._load_reference_ranges(config_path)
        self.config_path = config_path
        
        # Parameter name normalization mappings
        self.param_name_variations = {
            'hemoglobin': ['hemoglobin', 'hb', 'hgb'],
            'rbc': ['rbc', 'total rbc count', 'red blood cells', 'red blood cell'],
            'wbc': ['wbc', 'total wbc count', 'white blood cells', 'white blood cell'],
            'platelet': ['platelet', 'plt', 'platelets'],
            'pcv': ['pcv', 'hematocrit', 'hct', 'packed cell volume'],
            'mcv': ['mcv', 'mean corpuscular volume'],
            'mch': ['mch', 'mean corpuscular hemoglobin'],
            'mchc': ['mchc', 'mean corpuscular hemoglobin concentration'],
            'rdw': ['rdw', 'red cell distribution width'],
            'mpv': ['mpv', 'mean platelet volume'],
            'neutrophils': ['neutrophil'],
            'lymphocytes': ['lymphocyte'],
            'eosinophils': ['eosinophil'],
            'monocytes': ['monocyte'],
            'basophils': ['basophil'],
        }
        
        # Dynamic reference ranges with age/gender adjustments
        self.dynamic_ranges = self._build_dynamic_ranges()
    
    def validate(self, params: Dict[str, Any], age: Optional[int] = None, 
                 gender: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Validate blood parameters against reference ranges.
        
        Args:
            params: Dictionary of parameters {name: {value, unit}, ...}
            age: Patient age in years (optional)
            gender: Patient gender 'male' or 'female' (optional)
            
        Returns:
            Dictionary of validated parameters:
            {
                parameter: {
                    value: float,
                    unit: str,
                    status: str (LOW|NORMAL|HIGH|BORDERLINE|CRITICAL),
                    reference_range: str,
                    deviation: float (% above/below range)
                }
            }
        """
        validated = {}
        
        # Validate each parameter
        for param_name, param_data in params.items():
            if not isinstance(param_data, dict):
                continue
            
            value = param_data.get('value')
            unit = param_data.get('unit')
            
            if value is None:
                continue
            
            try:
                numeric_value = float(value)
            except (ValueError, TypeError):
                continue
            
            # Get normalized parameter name
            normalized_name = self._normalize_parameter_name(param_name)
            if not normalized_name:
                normalized_name = param_name  # fallback to original
            
            # Get reference range (with age/gender adjustment)
            ref_info = self._get_reference_range(normalized_name, age, gender)
            
            if not ref_info:
                # No reference range available
                validated[normalized_name] = {
                    'value': numeric_value,
                    'unit': unit or '',
                    'status': 'UNKNOWN',
                    'reference_range': 'N/A',
                    'deviation': 0
                }
                continue
            
            # Determine status and calculate deviation
            status, deviation = self._determine_status_and_deviation(
                numeric_value,
                ref_info['min'],
                ref_info['max']
            )
            
            validated[normalized_name] = {
                'value': numeric_value,
                'unit': ref_info.get('unit', unit or ''),
                'status': status,
                'reference_range': f"{ref_info['min']} - {ref_info['max']}",
                'deviation': round(deviation, 2)
            }
        
        # Apply cross-parameter consistency checks
        validated = self._apply_consistency_checks(validated)
        
        return validated
    
    def _load_reference_ranges(self, config_path: str) -> Dict[str, Any]:
        """Load reference ranges from JSON config file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                ranges = json.load(f)
                logger.info(f"Loaded {len(ranges)} reference ranges from {config_path}")
                return ranges
        except FileNotFoundError:
            logger.warning(f"Reference ranges file not found: {config_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {config_path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading reference ranges: {e}")
            return {}
    
    def _build_dynamic_ranges(self) -> Dict[str, Dict[str, Any]]:
        """
        Build dynamic reference ranges with age/gender adjustments.
        Complements the static ranges from JSON with computed adjustments.
        """
        return {
            'Hemoglobin': {
                'male': {
                    'child_0_12': {'min': 11.5, 'max': 15.5, 'unit': 'g/dL'},
                    'teen_13_17': {'min': 13.0, 'max': 16.0, 'unit': 'g/dL'},
                    'adult_18_49': {'min': 14.0, 'max': 18.0, 'unit': 'g/dL'},
                    'adult_50_64': {'min': 13.5, 'max': 17.5, 'unit': 'g/dL'},
                    'senior_65_plus': {'min': 12.5, 'max': 17.0, 'unit': 'g/dL'}
                },
                'female': {
                    'child_0_12': {'min': 11.5, 'max': 15.5, 'unit': 'g/dL'},
                    'teen_13_17': {'min': 12.0, 'max': 16.0, 'unit': 'g/dL'},
                    'adult_18_49': {'min': 12.0, 'max': 16.0, 'unit': 'g/dL'},
                    'adult_50_64': {'min': 11.5, 'max': 15.5, 'unit': 'g/dL'},
                    'senior_65_plus': {'min': 11.0, 'max': 15.0, 'unit': 'g/dL'}
                }
            },
            'RBC': {
                'male': {
                    'child_0_12': {'min': 4.0, 'max': 5.5, 'unit': 'mill/cumm'},
                    'adult_18_49': {'min': 4.7, 'max': 6.1, 'unit': 'mill/cumm'},
                    'senior_65_plus': {'min': 4.2, 'max': 5.7, 'unit': 'mill/cumm'}
                },
                'female': {
                    'child_0_12': {'min': 4.0, 'max': 5.5, 'unit': 'mill/cumm'},
                    'adult_18_49': {'min': 4.2, 'max': 5.4, 'unit': 'mill/cumm'},
                    'senior_65_plus': {'min': 3.8, 'max': 5.0, 'unit': 'mill/cumm'}
                }
            },
            'WBC': {
                'child_0_12': {'min': 5000, 'max': 15000, 'unit': '/cumm'},
                'adult_18_64': {'min': 4000, 'max': 11000, 'unit': '/cumm'},
                'senior_65_plus': {'min': 3500, 'max': 10500, 'unit': '/cumm'}
            },
            'Platelet': {
                'child_0_12': {'min': 150000, 'max': 450000, 'unit': '/cumm'},
                'adult_13_plus': {'min': 150000, 'max': 400000, 'unit': '/cumm'}
            },
            'PCV': {
                'male': {
                    'adult_18_49': {'min': 40, 'max': 54, 'unit': '%'},
                    'adult_50_plus': {'min': 38, 'max': 50, 'unit': '%'}
                },
                'female': {
                    'adult_18_49': {'min': 36, 'max': 48, 'unit': '%'},
                    'adult_50_plus': {'min': 34, 'max': 46, 'unit': '%'}
                }
            },
            'MCV': {
                'child_0_6': {'min': 70, 'max': 86, 'unit': 'fL'},
                'child_7_12': {'min': 77, 'max': 95, 'unit': 'fL'},
                'adult_13_plus': {'min': 80, 'max': 100, 'unit': 'fL'}
            },
            'MCH': {
                'child_0_12': {'min': 24, 'max': 30, 'unit': 'pg'},
                'adult_13_plus': {'min': 27, 'max': 32, 'unit': 'pg'}
            },
            'Glucose': {
                'child_0_12': {'min': 60, 'max': 100, 'unit': 'mg/dL'},
                'adult_13_64': {'min': 70, 'max': 100, 'unit': 'mg/dL'},
                'senior_65_plus': {'min': 70, 'max': 110, 'unit': 'mg/dL'}
            },
            'Creatinine': {
                'male': {
                    'adult_18_59': {'min': 0.7, 'max': 1.3, 'unit': 'mg/dL'},
                    'senior_60_plus': {'min': 0.8, 'max': 1.4, 'unit': 'mg/dL'}
                },
                'female': {
                    'adult_18_59': {'min': 0.6, 'max': 1.1, 'unit': 'mg/dL'},
                    'senior_60_plus': {'min': 0.6, 'max': 1.2, 'unit': 'mg/dL'}
                }
            },
            'HDL': {
                'male': {
                    'default': {'min': 40, 'max': 60, 'unit': 'mg/dL'}
                },
                'female': {
                    'default': {'min': 50, 'max': 70, 'unit': 'mg/dL'}
                }
            },
            'Uric_Acid': {
                'male': {
                    'default': {'min': 3.5, 'max': 7.2, 'unit': 'mg/dL'}
                },
                'female': {
                    'default': {'min': 2.5, 'max': 6.0, 'unit': 'mg/dL'}
                }
            }
        }
    
    def _normalize_parameter_name(self, name: str) -> Optional[str]:
        """
        Normalize parameter name to standard format.
        Returns None if not a recognized medical parameter.
        """
        if not name:
            return None
        
        name_lower = str(name).lower().strip()
        
        # Check direct variations
        for standard_name, variations in self.param_name_variations.items():
            for variation in variations:
                if variation in name_lower:
                    return standard_name.title()
        
        # Return original if recognized in reference ranges
        for ref_param in self.reference_ranges.keys():
            if name_lower == ref_param.lower():
                return ref_param
        
        return None
    
    def _get_age_category(self, age: Optional[int]) -> str:
        """Determine age category for range lookup."""
        if age is None:
            return 'adult'
        if age <= 6:
            return 'child_0_6'
        elif age <= 12:
            return 'child_0_12'
        elif age <= 17:
            return 'teen_13_17'
        elif age <= 49:
            return 'adult_18_49'
        elif age <= 59:
            return 'adult_18_59'
        elif age <= 64:
            return 'adult_50_64'
        else:
            return 'senior_65_plus'
    
    def _get_reference_range(self, param_name: str, age: Optional[int] = None, 
                            gender: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get reference range for parameter with age/gender adjustments.
        
        Returns:
            Dict with min, max, unit or None if not found
        """
        # Try dynamic ranges first (age/gender-adjusted)
        gender_lower = gender.lower() if gender else None
        age_cat = self._get_age_category(age)
        
        if param_name in self.dynamic_ranges:
            dyn_ranges = self.dynamic_ranges[param_name]
            
            # Try gender-specific with age adjustment
            if gender_lower and gender_lower in dyn_ranges:
                gender_ranges = dyn_ranges[gender_lower]
                
                # Try exact age category match
                if age_cat in gender_ranges:
                    return gender_ranges[age_cat]
                
                # Try to match age range pattern
                for key, value in gender_ranges.items():
                    if self._age_matches_key(age, key):
                        return value
            
            # Try age-specific ranges (non-gender-specific)
            for key, value in dyn_ranges.items():
                if key not in ['male', 'female', 'default']:
                    if age_cat in key or self._age_matches_key(age, key):
                        return value
        
        # Fall back to static reference ranges from JSON
        if param_name in self.reference_ranges:
            ref = self.reference_ranges[param_name]
            return {
                'min': ref.get('min'),
                'max': ref.get('max'),
                'unit': ref.get('unit', '')
            }
        
        # Try case-insensitive match
        param_lower = param_name.lower()
        for ref_param, ref_data in self.reference_ranges.items():
            if param_lower == ref_param.lower():
                return {
                    'min': ref_data.get('min'),
                    'max': ref_data.get('max'),
                    'unit': ref_data.get('unit', '')
                }
        
        return None
    
    def _age_matches_key(self, age: Optional[int], key: str) -> bool:
        """Check if age matches a range key pattern like 'adult_18_49' or 'senior_65_plus'."""
        if age is None:
            return False
        
        # Match patterns like "adult_18_49"
        match = re.search(r'(\d+)_(\d+)', key)
        if match:
            min_age, max_age = int(match.group(1)), int(match.group(2))
            return min_age <= age <= max_age
        
        # Match patterns like "senior_65_plus"
        match = re.search(r'(\d+)_plus', key)
        if match:
            min_age = int(match.group(1))
            return age >= min_age
        
        return False
    
    def _determine_status_and_deviation(self, value: float, min_val: float, 
                                       max_val: float) -> Tuple[str, float]:
        """
        Determine status (LOW|NORMAL|HIGH|BORDERLINE|CRITICAL) and deviation percentage.
        
        Deviation is negative for low values, positive for high values.
        """
        range_width = max_val - min_val
        mid_point = (min_val + max_val) / 2
        
        if min_val <= value <= max_val:
            # Within normal range
            deviation = 0
            # Check if borderline (close to limits)
            if value < min_val + (range_width * 0.1):
                status = 'BORDERLINE'
            elif value > max_val - (range_width * 0.1):
                status = 'BORDERLINE'
            else:
                status = 'NORMAL'
        
        elif value < min_val:
            # Below minimum
            deviation = ((value - min_val) / min_val) * 100 if min_val != 0 else -100
            percent_below = ((min_val - value) / range_width) * 100
            
            if percent_below > 50:
                status = 'CRITICAL'
            else:
                status = 'LOW'
        
        else:  # value > max_val
            # Above maximum
            deviation = ((value - max_val) / max_val) * 100
            percent_above = ((value - max_val) / range_width) * 100
            
            if percent_above > 50:
                status = 'CRITICAL'
            else:
                status = 'HIGH'
        
        return status, deviation
    
    def _apply_consistency_checks(self, validated: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Apply cross-parameter logical consistency checks.
        Adjusts status if inconsistencies detected.
        """
        # Check hemoglobin-related parameters
        if 'Hemoglobin' in validated and validated['Hemoglobin']['status'] == 'LOW':
            # If hemoglobin is low, RBC and/or hematocrit should also be affected
            rbc_status = validated.get('Rbc', {}).get('status')
            pcv_status = validated.get('Pcv', {}).get('status')
            
            # If hemoglobin is low but RBC/PCV are normal, could indicate anemia
            if rbc_status not in ['LOW', 'CRITICAL'] and pcv_status not in ['LOW', 'CRITICAL']:
                validated['Hemoglobin']['note'] = 'Low hemoglobin with normal RBC/PCV may indicate anemia'
        
        # Check WBC-related differential parameters
        if 'Wbc' in validated:
            wbc_status = validated['Wbc']['status']
            neutro_status = validated.get('Neutrophils', {}).get('status')
            lympho_status = validated.get('Lymphocytes', {}).get('status')
            
            # If WBC abnormal, differentials should also be abnormal
            if wbc_status in ['LOW', 'CRITICAL', 'HIGH']:
                if neutro_status == 'NORMAL' and lympho_status == 'NORMAL':
                    note = 'WBC abnormal but differentials normal - verify measurement'
                    validated['Wbc']['note'] = note
        
        # Check neutrophil-lymphocyte ratio (inversely correlated)
        neutro_pct = validated.get('Neutrophils', {}).get('value')
        lympho_pct = validated.get('Lymphocytes', {}).get('value')
        
        if neutro_pct and lympho_pct:
            # Neutrophils + Lymphocytes typically sum to 60-80%
            total_nl = neutro_pct + lympho_pct
            if total_nl > 95 or total_nl < 50:
                # Flag as non-physiological
                validated['Neutrophils']['note'] = f'Neutrophil+Lymphocyte sum={total_nl}% (typical: 50-95%)'
        
        # Check kidney function (Creatinine vs Urea/BUN)
        creat_status = validated.get('Creatinine', {}).get('status')
        urea_status = validated.get('Urea', {}).get('status')
        bun_status = validated.get('Bun', {}).get('status')
        
        if creat_status == 'HIGH':
            # If creatinine elevated, urea/BUN should also be elevated
            if urea_status == 'NORMAL' and bun_status == 'NORMAL':
                validated['Creatinine']['note'] = 'High creatinine with normal urea/BUN - verify results'
        
        # Check liver function (Albumin < Globulin indicates liver disease)
        albumin_val = validated.get('Albumin', {}).get('value')
        globulin_val = validated.get('Globulin', {}).get('value')
        
        if albumin_val and globulin_val:
            if albumin_val < globulin_val:
                validated['Albumin']['note'] = 'Albumin < Globulin - possible liver disease'
        
        # Check cholesterol-LDL relationship
        chol_val = validated.get('Cholesterol', {}).get('value')
        ldl_val = validated.get('Ldl', {}).get('value')
        
        if chol_val and ldl_val:
            # LDL should be roughly 60-70% of total cholesterol
            ldl_ratio = (ldl_val / chol_val) * 100 if chol_val > 0 else 0
            if ldl_ratio > 90:
                validated['Ldl']['note'] = 'LDL very high relative to total cholesterol'
        
        # Check glucose-HbA1c relationship (for diabetes monitoring)
        glucose_val = validated.get('Glucose', {}).get('value')
        hba1c_val = validated.get('Hba1c', {}).get('value')
        
        if glucose_val and hba1c_val:
            if glucose_val > 200 and hba1c_val < 6.0:
                validated['Glucose']['note'] = 'Very high glucose but normal HbA1c - verify fasting status'
        
        return validated
