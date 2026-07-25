"""
Context Model
Unified module merging advanced_context_manager, intent_inference_engine, and dynamic_reference_ranges
Enriches validated parameters with age/gender-adjusted ranges and lifestyle-based risk modifications
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class ContextModel:
    """
    Enriches validated blood parameters with contextual information including:
    - Age/gender-adjusted reference ranges
    - Lifestyle-based risk weight modifications
    - Medical history context tracking
    - User profile management
    """
    
    def __init__(self):
        """Initialize ContextModel with dynamic reference ranges and user profiles"""
        self.dynamic_ranges = self._load_dynamic_ranges()
        self.user_profiles = {}
        self.session_contexts = {}
        self.medical_history = {}
        
        # Lifestyle risk modifiers
        self.lifestyle_modifiers = {
            'smoker': {'risk_multiplier': 1.5, 'parameters': ['Cholesterol', 'HDL', 'LDL']},
            'diabetic': {'risk_multiplier': 1.3, 'parameters': ['Glucose', 'HbA1c']},
            'hypertensive': {'risk_multiplier': 1.4, 'parameters': ['Creatinine', 'Urea']},
            'sedentary': {'risk_multiplier': 1.2, 'parameters': ['Triglycerides', 'HDL']}
        }
    
    def _load_dynamic_ranges(self) -> Dict[str, Any]:
        """Load age and gender-adjusted reference ranges"""
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
                },
                'default': {'min': 12.0, 'max': 17.0, 'unit': 'g/dL'}
            },
            'RBC': {
                'male': {
                    'child_0_12': {'min': 4.0, 'max': 5.5, 'unit': 'mill/cumm'},
                    'teen_13_17': {'min': 4.5, 'max': 5.5, 'unit': 'mill/cumm'},
                    'adult_18_49': {'min': 4.7, 'max': 6.1, 'unit': 'mill/cumm'},
                    'adult_50_64': {'min': 4.5, 'max': 5.9, 'unit': 'mill/cumm'},
                    'senior_65_plus': {'min': 4.2, 'max': 5.7, 'unit': 'mill/cumm'}
                },
                'female': {
                    'child_0_12': {'min': 4.0, 'max': 5.5, 'unit': 'mill/cumm'},
                    'teen_13_17': {'min': 4.0, 'max': 5.0, 'unit': 'mill/cumm'},
                    'adult_18_49': {'min': 4.2, 'max': 5.4, 'unit': 'mill/cumm'},
                    'adult_50_64': {'min': 4.0, 'max': 5.2, 'unit': 'mill/cumm'},
                    'senior_65_plus': {'min': 3.8, 'max': 5.0, 'unit': 'mill/cumm'}
                },
                'default': {'min': 4.5, 'max': 5.5, 'unit': 'mill/cumm'}
            },
            'WBC': {
                'child_0_12': {'min': 5000, 'max': 15000, 'unit': '/cumm'},
                'teen_13_17': {'min': 4500, 'max': 13000, 'unit': '/cumm'},
                'adult_18_64': {'min': 4000, 'max': 11000, 'unit': '/cumm'},
                'senior_65_plus': {'min': 3500, 'max': 10500, 'unit': '/cumm'},
                'default': {'min': 4000, 'max': 11000, 'unit': '/cumm'}
            },
            'PCV': {
                'male': {
                    'child_0_12': {'min': 35, 'max': 45, 'unit': '%'},
                    'teen_13_17': {'min': 37, 'max': 49, 'unit': '%'},
                    'adult_18_49': {'min': 40, 'max': 54, 'unit': '%'},
                    'adult_50_plus': {'min': 38, 'max': 50, 'unit': '%'}
                },
                'female': {
                    'child_0_12': {'min': 35, 'max': 45, 'unit': '%'},
                    'teen_13_17': {'min': 36, 'max': 44, 'unit': '%'},
                    'adult_18_49': {'min': 36, 'max': 48, 'unit': '%'},
                    'adult_50_plus': {'min': 34, 'max': 46, 'unit': '%'}
                },
                'default': {'min': 36, 'max': 50, 'unit': '%'}
            },
            'MCV': {
                'child_0_6': {'min': 70, 'max': 86, 'unit': 'fL'},
                'child_7_12': {'min': 77, 'max': 95, 'unit': 'fL'},
                'adult_13_plus': {'min': 80, 'max': 100, 'unit': 'fL'},
                'default': {'min': 80, 'max': 100, 'unit': 'fL'}
            },
            'MCH': {
                'child_0_12': {'min': 24, 'max': 30, 'unit': 'pg'},
                'adult_13_plus': {'min': 27, 'max': 32, 'unit': 'pg'},
                'default': {'min': 27, 'max': 32, 'unit': 'pg'}
            },
            'MCHC': {
                'default': {'min': 32, 'max': 36, 'unit': 'g/dL'}
            },
            'Glucose': {
                'child_0_12': {'min': 60, 'max': 100, 'unit': 'mg/dL'},
                'adult_13_64': {'min': 70, 'max': 100, 'unit': 'mg/dL'},
                'senior_65_plus': {'min': 70, 'max': 110, 'unit': 'mg/dL'},
                'default': {'min': 70, 'max': 100, 'unit': 'mg/dL'}
            },
            'Cholesterol': {
                'child_0_17': {'min': 0, 'max': 170, 'unit': 'mg/dL'},
                'adult_18_plus': {'min': 0, 'max': 200, 'unit': 'mg/dL'},
                'default': {'min': 0, 'max': 200, 'unit': 'mg/dL'}
            },
            'HDL': {
                'male': {'default': {'min': 40, 'max': 60, 'unit': 'mg/dL'}},
                'female': {'default': {'min': 50, 'max': 70, 'unit': 'mg/dL'}},
                'default': {'min': 40, 'max': 60, 'unit': 'mg/dL'}
            },
            'LDL': {
                'optimal': {'min': 0, 'max': 100, 'unit': 'mg/dL'},
                'default': {'min': 0, 'max': 130, 'unit': 'mg/dL'}
            },
            'Triglycerides': {
                'child_0_9': {'min': 0, 'max': 75, 'unit': 'mg/dL'},
                'child_10_17': {'min': 0, 'max': 90, 'unit': 'mg/dL'},
                'adult_18_plus': {'min': 0, 'max': 150, 'unit': 'mg/dL'},
                'default': {'min': 0, 'max': 150, 'unit': 'mg/dL'}
            },
            'Creatinine': {
                'male': {
                    'child_0_12': {'min': 0.3, 'max': 0.7, 'unit': 'mg/dL'},
                    'teen_13_17': {'min': 0.5, 'max': 1.0, 'unit': 'mg/dL'},
                    'adult_18_59': {'min': 0.7, 'max': 1.3, 'unit': 'mg/dL'},
                    'senior_60_plus': {'min': 0.8, 'max': 1.4, 'unit': 'mg/dL'}
                },
                'female': {
                    'child_0_12': {'min': 0.3, 'max': 0.7, 'unit': 'mg/dL'},
                    'teen_13_17': {'min': 0.5, 'max': 0.9, 'unit': 'mg/dL'},
                    'adult_18_59': {'min': 0.6, 'max': 1.1, 'unit': 'mg/dL'},
                    'senior_60_plus': {'min': 0.6, 'max': 1.2, 'unit': 'mg/dL'}
                },
                'default': {'min': 0.6, 'max': 1.2, 'unit': 'mg/dL'}
            },
            'Urea': {
                'child_0_12': {'min': 5, 'max': 18, 'unit': 'mg/dL'},
                'adult_13_59': {'min': 7, 'max': 20, 'unit': 'mg/dL'},
                'senior_60_plus': {'min': 8, 'max': 23, 'unit': 'mg/dL'},
                'default': {'min': 7, 'max': 20, 'unit': 'mg/dL'}
            },
            'Uric_Acid': {
                'male': {'default': {'min': 3.5, 'max': 7.2, 'unit': 'mg/dL'}},
                'female': {
                    'premenopausal': {'min': 2.5, 'max': 6.0, 'unit': 'mg/dL'},
                    'postmenopausal': {'min': 3.0, 'max': 6.5, 'unit': 'mg/dL'}
                },
                'default': {'min': 3.0, 'max': 7.0, 'unit': 'mg/dL'}
            },
            'TSH': {
                'child_0_12': {'min': 0.7, 'max': 6.0, 'unit': 'mIU/L'},
                'adult_13_64': {'min': 0.4, 'max': 4.0, 'unit': 'mIU/L'},
                'senior_65_plus': {'min': 0.5, 'max': 5.0, 'unit': 'mIU/L'},
                'default': {'min': 0.4, 'max': 4.0, 'unit': 'mIU/L'}
            },
            'Ferritin': {
                'male': {'default': {'min': 30, 'max': 400, 'unit': 'ng/mL'}},
                'female': {
                    'premenopausal': {'min': 15, 'max': 150, 'unit': 'ng/mL'},
                    'postmenopausal': {'min': 30, 'max': 300, 'unit': 'ng/mL'}
                },
                'default': {'min': 20, 'max': 300, 'unit': 'ng/mL'}
            },
            'Iron': {
                'male': {'default': {'min': 65, 'max': 175, 'unit': 'mcg/dL'}},
                'female': {'default': {'min': 50, 'max': 170, 'unit': 'mcg/dL'}},
                'default': {'min': 60, 'max': 170, 'unit': 'mcg/dL'}
            },
            'Vitamin_D': {
                'default': {'min': 30, 'max': 100, 'unit': 'ng/mL'},
                'senior_65_plus': {'min': 30, 'max': 80, 'unit': 'ng/mL'}
            },
            'Vitamin_B12': {
                'default': {'min': 200, 'max': 900, 'unit': 'pg/mL'},
                'senior_65_plus': {'min': 300, 'max': 900, 'unit': 'pg/mL'}
            },
            'ESR': {
                'male': {
                    'adult_under_50': {'min': 0, 'max': 15, 'unit': 'mm/hr'},
                    'adult_50_plus': {'min': 0, 'max': 20, 'unit': 'mm/hr'}
                },
                'female': {
                    'adult_under_50': {'min': 0, 'max': 20, 'unit': 'mm/hr'},
                    'adult_50_plus': {'min': 0, 'max': 30, 'unit': 'mm/hr'}
                },
                'default': {'min': 0, 'max': 20, 'unit': 'mm/hr'}
            },
            'Platelet': {
                'child_0_12': {'min': 150000, 'max': 450000, 'unit': '/cumm'},
                'adult_13_plus': {'min': 150000, 'max': 400000, 'unit': '/cumm'},
                'default': {'min': 150000, 'max': 400000, 'unit': '/cumm'}
            },
            'Neutrophils': {'default': {'min': 40, 'max': 70, 'unit': '%'}},
            'Lymphocytes': {'default': {'min': 20, 'max': 40, 'unit': '%'}},
            'Monocytes': {'default': {'min': 2, 'max': 8, 'unit': '%'}},
            'Eosinophils': {'default': {'min': 1, 'max': 4, 'unit': '%'}},
            'Basophils': {'default': {'min': 0, 'max': 1, 'unit': '%'}}
        }
    
    def enrich(self, validated_params: Dict[str, Any], user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Enrich validated parameters with age/gender adjustments and lifestyle modifications.
        
        Args:
            validated_params: Blood parameters with current reference ranges
            user_context: User context {age: int, gender: str, lifestyle: str, medical_history: list}
            
        Returns:
            Enriched parameters with adjusted reference ranges and context flags
        """
        # Graceful handling of empty/None context
        if not user_context or not (user_context.get('age') or user_context.get('gender')):
            return validated_params.copy()
        
        enriched = validated_params.copy()
        age = user_context.get('age')
        gender = user_context.get('gender', '').lower()
        lifestyle = user_context.get('lifestyle', '').lower()
        medical_history = user_context.get('medical_history', [])
        
        # Apply age/gender-adjusted reference ranges
        for param_name in enriched:
            adjusted_range = self._get_reference_range(param_name, age, gender)
            
            if adjusted_range and isinstance(enriched[param_name], dict):
                if 'reference_range' not in enriched[param_name]:
                    enriched[param_name]['reference_range'] = f"{adjusted_range['min']} - {adjusted_range['max']}"
                else:
                    # Update if more specific
                    enriched[param_name]['reference_range'] = f"{adjusted_range['min']} - {adjusted_range['max']}"
                
                enriched[param_name]['adjusted_unit'] = adjusted_range.get('unit', '')
                enriched[param_name]['age_adjusted'] = True
        
        # Add context flags
        enriched['context_flags'] = self._generate_context_flags(
            validated_params, age, gender, lifestyle, medical_history
        )
        
        # Apply lifestyle-based risk modifications
        enriched['lifestyle_adjustments'] = self._apply_lifestyle_adjustments(
            validated_params, lifestyle, medical_history
        )
        
        return enriched
    
    def _get_age_category(self, age: Optional[int]) -> str:
        """Determine age category from numeric age"""
        if age is None:
            return 'adult'
        if age <= 6:
            return 'child_0_6'
        elif age <= 9:
            return 'child_0_9'
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
    
    def _age_matches_key(self, age: Optional[int], key: str) -> bool:
        """Check if age matches a range key"""
        if age is None:
            return False
        
        match = re.search(r'(\d+)_(\d+)', key)
        if match:
            min_age, max_age = int(match.group(1)), int(match.group(2))
            return min_age <= age <= max_age
        
        match = re.search(r'(\d+)_plus', key)
        if match:
            min_age = int(match.group(1))
            return age >= min_age
        
        match = re.search(r'under_(\d+)', key)
        if match:
            max_age = int(match.group(1))
            return age < max_age
        
        return False
    
    def _get_reference_range(self, parameter: str, age: Optional[int] = None,
                            gender: Optional[str] = None) -> Optional[Dict]:
        """Get reference range adjusted for age and gender"""
        param_ranges = self.dynamic_ranges.get(parameter)
        
        if not param_ranges:
            return None
        
        gender_lower = gender.lower() if gender else None
        age_cat = self._get_age_category(age)
        
        # Try gender-specific ranges first
        if gender_lower and gender_lower in param_ranges:
            gender_ranges = param_ranges[gender_lower]
            
            # Try age-specific within gender
            for key in gender_ranges:
                if age_cat in key or self._age_matches_key(age, key):
                    return gender_ranges[key]
            
            # Fall back to gender default
            if 'default' in gender_ranges:
                return gender_ranges['default']
        
        # Try age-specific ranges (non-gender-specific)
        for key in param_ranges:
            if key not in ['male', 'female', 'default']:
                if age_cat in key or self._age_matches_key(age, key):
                    return param_ranges[key]
        
        # Fall back to default
        return param_ranges.get('default')
    
    def _generate_context_flags(self, validated_params: Dict[str, Any], age: Optional[int],
                               gender: Optional[str], lifestyle: str,
                               medical_history: List[str]) -> Dict[str, Any]:
        """Generate context-aware flags for the patient"""
        flags = {}
        
        # Age-based flags
        if age:
            if age < 18:
                flags['pediatric'] = True
            elif age >= 65:
                flags['senior'] = True
            else:
                flags['adult'] = True
        
        # Gender-based flags
        if gender and gender.lower() == 'female':
            flags['female'] = True
            # Check for pregnancy-related concerns
            if 'glucose' in str(validated_params).lower():
                flags['glucose_monitoring_critical'] = True
        elif gender and gender.lower() == 'male':
            flags['male'] = True
        
        # Lifestyle flags
        if lifestyle:
            lifestyle_lower = lifestyle.lower()
            if 'smoke' in lifestyle_lower:
                flags['smoker'] = True
            if 'diabetes' in lifestyle_lower or 'diabetic' in lifestyle_lower:
                flags['known_diabetic'] = True
            if 'hypert' in lifestyle_lower:
                flags['known_hypertensive'] = True
            if 'sedentary' in lifestyle_lower or 'inactive' in lifestyle_lower:
                flags['sedentary_lifestyle'] = True
        
        # Medical history flags
        if medical_history:
            medical_lower = ' '.join([h.lower() for h in medical_history])
            if any(term in medical_lower for term in ['anemia', 'blood loss', 'iron deficiency']):
                flags['anemia_history'] = True
            if any(term in medical_lower for term in ['kidney', 'renal', 'nephro']):
                flags['kidney_disease_history'] = True
            if any(term in medical_lower for term in ['liver', 'hepatic', 'cirrhosis']):
                flags['liver_disease_history'] = True
            if any(term in medical_lower for term in ['cancer', 'malignancy', 'tumor']):
                flags['cancer_history'] = True
        
        return flags
    
    def _apply_lifestyle_adjustments(self, validated_params: Dict[str, Any],
                                    lifestyle: str, medical_history: List[str]) -> Dict[str, Any]:
        """Apply lifestyle-based risk weight modifications"""
        adjustments = {}
        
        if not lifestyle:
            return adjustments
        
        lifestyle_lower = lifestyle.lower()
        active_modifiers = []
        
        # Identify active lifestyle modifiers
        if any(term in lifestyle_lower for term in ['smoke', 'smoking', 'smoker']):
            active_modifiers.append('smoker')
        
        if any(term in lifestyle_lower for term in ['diabetes', 'diabetic']):
            active_modifiers.append('diabetic')
        
        if any(term in lifestyle_lower for term in ['hypert', 'high blood pressure', 'hypertension']):
            active_modifiers.append('hypertensive')
        
        if any(term in lifestyle_lower for term in ['sedentary', 'inactive', 'no exercise', 'no physical']):
            active_modifiers.append('sedentary')
        
        # Apply each active modifier
        for modifier in active_modifiers:
            if modifier in self.lifestyle_modifiers:
                mod_config = self.lifestyle_modifiers[modifier]
                adjustments[modifier] = {
                    'risk_multiplier': mod_config['risk_multiplier'],
                    'affected_parameters': mod_config['parameters'],
                    'clinical_implication': self._get_clinical_implication(modifier)
                }
        
        return adjustments
    
    def _get_clinical_implication(self, modifier: str) -> str:
        """Get clinical implication text for lifestyle modifier"""
        implications = {
            'smoker': 'Smoking increases cardiovascular and lipid disorder risk; recommend smoking cessation',
            'diabetic': 'Known diabetes; glucose and HbA1c control critical; adjust targets accordingly',
            'hypertensive': 'Known hypertension; monitor kidney function (creatinine, urea); renal protection important',
            'sedentary': 'Sedentary lifestyle increases metabolic risk; recommend regular physical activity'
        }
        return implications.get(modifier, '')
    
    def create_user_profile(self, user_id: str, age: int, gender: str,
                          lifestyle: str, medical_history: List[str]) -> Dict[str, Any]:
        """Create a user profile for context tracking"""
        profile = {
            'user_id': user_id,
            'age': age,
            'gender': gender,
            'lifestyle': lifestyle,
            'medical_history': medical_history,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        self.user_profiles[user_id] = profile
        return profile
    
    def add_medical_history_entry(self, user_id: str, entry: str) -> None:
        """Add medical history entry to user profile"""
        if user_id in self.user_profiles:
            if 'medical_history' not in self.user_profiles[user_id]:
                self.user_profiles[user_id]['medical_history'] = []
            self.user_profiles[user_id]['medical_history'].append(entry)
            self.user_profiles[user_id]['updated_at'] = datetime.now().isoformat()
    
    def get_all_adjusted_ranges(self, age: Optional[int] = None,
                               gender: Optional[str] = None) -> Dict[str, Dict]:
        """Get all reference ranges adjusted for given age and gender"""
        adjusted = {}
        
        for param in self.dynamic_ranges.keys():
            ref = self._get_reference_range(param, age, gender)
            if ref:
                adjusted[param] = ref
        
        return adjusted
    
    def log_context_enrichment(self, user_id: str, validated_params: Dict,
                               user_context: Dict, enriched_params: Dict) -> None:
        """Log context enrichment for audit trail"""
        log_entry = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'context_applied': user_context,
            'parameters_count': len(validated_params),
            'adjustments_made': 'age_gender_ranges' if user_context else 'none'
        }
        
        if user_id not in self.medical_history:
            self.medical_history[user_id] = []
        
        self.medical_history[user_id].append(log_entry)
        logger.debug(f"Context enrichment logged for user {user_id}")
