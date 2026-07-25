"""
Unified Blood Report Parser
Consolidates all parsing, extraction, and unit normalization logic.
Handles: JSON parsing, text extraction, table extraction, and unit conversion.
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple


class BloodReportParser:
    """
    Unified blood report parser supporting 20+ medical parameters.
    Handles multiple input formats: text, JSON, CSV, and tables.
    Returns structured JSON: {parameter_name: {value, unit, raw_string}}
    """

    def __init__(self):
        """Initialize parser with comprehensive parameter patterns"""
        
        # Standard units for each parameter
        self.standard_units = {
            'White Blood Cell (WBC)': 'K/mcL',
            'Red Blood Cell (RBC)': 'M/mcL',
            'Hemoglobin': 'g/dL',
            'Hematocrit': '%',
            'Mean Cell Volume (MCV)': 'fL',
            'Mean Cell Hemoglobin (MCH)': 'pg',
            'Mean Cell Hb Conc (MCHC)': 'g/dL',
            'Red Cell Dist Width (RDW)': '%',
            'Platelet Count': 'K/mcL',
            'Mean Platelet Volume': 'fL',
            'Neutrophil': '%',
            'Lymphocyte': '%',
            'Monocyte': '%',
            'Eosinophil': '%',
            'Basophil': '%',
            'Neutrophil, Absolute': 'K/mcL',
            'Lymphocyte, Absolute': 'K/mcL',
            'Monocyte, Absolute': 'K/mcL',
            'Eosinophil, Absolute': 'K/mcL',
            'Basophil, Absolute': 'K/mcL',
            'Glucose': 'mg/dL',
            'Cholesterol': 'mg/dL',
            'Creatinine': 'mg/dL',
            'BUN': 'mg/dL',
        }
        
        # Comprehensive parameter extraction patterns
        # Format: 'Canonical Name': {'patterns': [...regex...], 'aliases': [...]}
        self.parameter_patterns = {
            'White Blood Cell (WBC)': {
                'patterns': [
                    r'(?i)white\s+blood\s+cell.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)wbc\b.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)total\s+wbc.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)leucocyte.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                ],
                'aliases': ['WBC', 'White Blood Cell', 'Total WBC', 'Leucocyte'],
            },
            
            'Red Blood Cell (RBC)': {
                'patterns': [
                    r'(?i)red\s+blood\s+cell.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)rbc\b.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)erythrocyte.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                ],
                'aliases': ['RBC', 'Red Blood Cell', 'Erythrocyte'],
            },
            
            'Hemoglobin': {
                'patterns': [
                    r'(?i)hemoglobin\b.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]*)',
                    r'(?i)hb\s*[:/].*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)hgb\b.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)haemoglobin.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                ],
                'aliases': ['Hemoglobin', 'HB', 'Hgb', 'Haemoglobin'],
            },
            
            'Hematocrit': {
                'patterns': [
                    r'(?i)hematocrit.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)hct\b.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)packed\s+cell\s+volume.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)pcv\b.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                ],
                'aliases': ['Hematocrit', 'HCT', 'Packed Cell Volume', 'PCV'],
            },
            
            'Mean Cell Volume (MCV)': {
                'patterns': [
                    r'(?i)mean\s+cell\s+volume.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)mcv\b.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                ],
                'aliases': ['MCV', 'Mean Cell Volume', 'Mean Corpuscular Volume'],
            },
            
            'Mean Cell Hemoglobin (MCH)': {
                'patterns': [
                    r'(?i)mean\s+cell\s+hemoglobin\b.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)mch(?!\s*conc).*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                ],
                'aliases': ['MCH', 'Mean Cell Hemoglobin', 'Mean Corpuscular Hemoglobin'],
            },
            
            'Mean Cell Hb Conc (MCHC)': {
                'patterns': [
                    r'(?i)mean\s+cell\s+hb\s+conc.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)mchc\b.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                ],
                'aliases': ['MCHC', 'Mean Cell Hb Conc', 'Mean Cell Hemoglobin Concentration'],
            },
            
            'Red Cell Dist Width (RDW)': {
                'patterns': [
                    r'(?i)red\s+cell\s+dist\s+width.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)rdw\b.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)red\s+cell\s+distribution\s+width.*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                ],
                'aliases': ['RDW', 'Red Cell Dist Width', 'Red Cell Distribution Width'],
            },
            
            'Platelet Count': {
                'patterns': [
                    r'(?i)platelet\s+count.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)platelets\b.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)plt\b.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)thrombocyte.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                ],
                'aliases': ['Platelet Count', 'Platelets', 'PLT', 'Thrombocyte'],
            },
            
            'Mean Platelet Volume': {
                'patterns': [
                    r'(?i)mean\s+platelet\s+volume.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)mpv\b.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                ],
                'aliases': ['Mean Platelet Volume', 'MPV'],
            },
            
            'Neutrophil': {
                'patterns': [
                    r'(?i)neutrophil\b(?!\s*,).*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)neut\s*[:/].*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                ],
                'aliases': ['Neutrophil', 'Neutrophils', 'Neut'],
            },
            
            'Lymphocyte': {
                'patterns': [
                    r'(?i)lymphocyte\b(?!\s*,).*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)lymph\s*[:/].*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                ],
                'aliases': ['Lymphocyte', 'Lymphocytes', 'Lymph'],
            },
            
            'Monocyte': {
                'patterns': [
                    r'(?i)monocyte\b(?!\s*,).*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)mono\s*[:/].*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                ],
                'aliases': ['Monocyte', 'Monocytes', 'Mono'],
            },
            
            'Eosinophil': {
                'patterns': [
                    r'(?i)eosinophil\b(?!\s*,).*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)eos\s*[:/].*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                ],
                'aliases': ['Eosinophil', 'Eosinophils', 'Eos'],
            },
            
            'Basophil': {
                'patterns': [
                    r'(?i)basophil\b(?!\s*,).*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                    r'(?i)baso\s*[:/].*?(\d+\.?\d*)\s*([a-zA-Z%/µμ]*)',
                ],
                'aliases': ['Basophil', 'Basophils', 'Baso'],
            },
            
            'Neutrophil, Absolute': {
                'patterns': [
                    r'(?i)neutrophil,?\s+absolute.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)absolute\s+neutrophil.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)abs\s+neut.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                ],
                'aliases': ['Neutrophil Absolute', 'Absolute Neutrophil', 'Abs Neut'],
            },
            
            'Lymphocyte, Absolute': {
                'patterns': [
                    r'(?i)lymphocyte,?\s+absolute.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)absolute\s+lymphocyte.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)abs\s+lymph.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                ],
                'aliases': ['Lymphocyte Absolute', 'Absolute Lymphocyte', 'Abs Lymph'],
            },
            
            'Monocyte, Absolute': {
                'patterns': [
                    r'(?i)monocyte,?\s+absolute.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)absolute\s+monocyte.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)abs\s+mono.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                ],
                'aliases': ['Monocyte Absolute', 'Absolute Monocyte', 'Abs Mono'],
            },
            
            'Eosinophil, Absolute': {
                'patterns': [
                    r'(?i)eosinophil,?\s+absolute.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)absolute\s+eosinophil.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)abs\s+eos.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                ],
                'aliases': ['Eosinophil Absolute', 'Absolute Eosinophil', 'Abs Eos'],
            },
            
            'Basophil, Absolute': {
                'patterns': [
                    r'(?i)basophil,?\s+absolute.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)absolute\s+basophil.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)abs\s+baso.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                ],
                'aliases': ['Basophil Absolute', 'Absolute Basophil', 'Abs Baso'],
            },
            
            'Glucose': {
                'patterns': [
                    r'(?i)glucose\b.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)blood\s+sugar.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)fasting\s+glucose.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                ],
                'aliases': ['Glucose', 'Blood Sugar', 'Fasting Glucose', 'Random Glucose'],
            },
            
            'Cholesterol': {
                'patterns': [
                    r'(?i)total\s+cholesterol.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)cholesterol\b.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)chol\b.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                ],
                'aliases': ['Cholesterol', 'Total Cholesterol', 'CHOL'],
            },
            
            'Creatinine': {
                'patterns': [
                    r'(?i)creatinine\b.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)serum\s+creatinine.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)creat\b.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                ],
                'aliases': ['Creatinine', 'Serum Creatinine', 'CREAT'],
            },
            
            'BUN': {
                'patterns': [
                    r'(?i)bun\b.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)blood\s+urea\s+nitrogen.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                    r'(?i)urea\b.*?(\d+\.?\d*)\s*([a-zA-Z/µμ]+)',
                ],
                'aliases': ['BUN', 'Blood Urea Nitrogen', 'Urea'],
            },
        }
        
        # Unit normalization mapping
        self.unit_normalization = {
            'g/dl': 'g/dL',
            'g/l': 'g/L',
            'mg/dl': 'mg/dL',
            'mmol/l': 'mmol/L',
            'umol/l': 'umol/L',
            'meq/l': 'mEq/L',
            'miu/l': 'mIU/L',
            'uiu/ml': 'uIU/mL',
            'ng/ml': 'ng/mL',
            'pg/ml': 'pg/mL',
            'nmol/l': 'nmol/L',
            'pmol/l': 'pmol/L',
            'ug/l': 'ug/L',
            'mcg/dl': 'mcg/dL',
            'u/l': 'U/L',
            '/cumm': '/cumm',
            '/ul': '/uL',
            'k/mcl': 'K/mcL',
            'k/ul': 'K/uL',
            'm/mcl': 'M/mcL',
            'm/ul': 'M/uL',
            'fl': 'fL',
            'pg': 'pg',
            '%': '%',
            'mm/hr': 'mm/hr',
        }

    def parse(self, raw_text: str) -> Dict[str, Dict[str, Any]]:
        """
        Main parsing method - routes to best parser based on format.
        
        Returns:
            {parameter_name: {value, unit, raw_string}}
        """
        if not raw_text or len(raw_text.strip()) < 5:
            return {}
        
        # Try JSON parsing first
        json_result = self._parse_json(raw_text)
        if json_result:
            return json_result
        
        # Try table extraction
        table_result = self.extract_from_table(raw_text)
        if table_result:
            return table_result
        
        # Fall back to text parsing
        return self._parse_text(raw_text)

    def _parse_json(self, raw_text: str) -> Optional[Dict]:
        """Parse structured JSON blood report"""
        try:
            data = json.loads(raw_text)
            parameters = {}
            
            if isinstance(data, dict):
                # Handle 'parameters' key
                if 'parameters' in data:
                    for param in data['parameters']:
                        name = param.get('name', '')
                        if name:
                            parameters[name] = {
                                'value': self._safe_float(param.get('value')),
                                'unit': param.get('unit', ''),
                                'raw_string': f"{name}: {param.get('value')} {param.get('unit', '')}",
                            }
                # Handle direct key-value pairs
                else:
                    for key, value in data.items():
                        if isinstance(value, dict) and 'value' in value:
                            parameters[key] = {
                                'value': self._safe_float(value.get('value')),
                                'unit': value.get('unit', ''),
                                'raw_string': f"{key}: {value.get('value')}",
                            }
                        elif isinstance(value, (int, float)):
                            parameters[key] = {
                                'value': float(value),
                                'unit': 'N/A',
                                'raw_string': f"{key}: {value}",
                            }
            
            return parameters if parameters else None
        
        except (json.JSONDecodeError, ValueError, TypeError):
            return None

    def _parse_text(self, raw_text: str) -> Dict[str, Dict[str, Any]]:
        """Parse text-based blood report"""
        parameters = {}
        lines = raw_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Try each parameter pattern
            for param_name, param_config in self.parameter_patterns.items():
                if param_name in parameters:  # Skip if already found
                    continue
                
                for pattern in param_config['patterns']:
                    match = re.search(pattern, line)
                    if match:
                        try:
                            value = float(match.group(1))
                            unit = match.group(2) if len(match.groups()) > 1 else ''
                            
                            # Validate value is realistic
                            if 0.01 <= value <= 100000:
                                parameters[param_name] = {
                                    'value': value,
                                    'unit': self._normalize_unit(unit),
                                    'raw_string': line,
                                }
                                break
                        except (ValueError, IndexError):
                            continue
        
        return parameters

    def extract_from_table(self, raw_text: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract parameters from table-formatted text.
        Handles both plain text tables and CSV data.
        """
        parameters = {}
        
        # Try CSV parsing first
        csv_result = self._parse_csv(raw_text)
        if csv_result:
            return csv_result
        
        # Parse table rows (space/tab separated)
        lines = raw_text.split('\n')
        for line in lines:
            if not line.strip() or len(line) < 3:
                continue
            
            row_data = self._parse_table_row(line)
            if row_data:
                parameters.update(row_data)
        
        return parameters

    def _parse_csv(self, raw_text: str) -> Optional[Dict]:
        """Try to parse CSV formatted data"""
        try:
            import csv
            import io
            
            lines = raw_text.strip().split('\n')
            if len(lines) < 2:
                return None
            
            reader = csv.DictReader(io.StringIO(raw_text))
            parameters = {}
            
            for row in reader:
                for param_name in self.parameter_patterns.keys():
                    if param_name in parameters:
                        continue
                    
                    # Check each column for parameter
                    for col_val in row.values():
                        if not col_val:
                            continue
                        
                        for pattern in self.parameter_patterns[param_name]['patterns']:
                            match = re.search(pattern, col_val)
                            if match:
                                try:
                                    value = float(match.group(1))
                                    unit = match.group(2) if len(match.groups()) > 1 else ''
                                    
                                    if 0.01 <= value <= 100000:
                                        parameters[param_name] = {
                                            'value': value,
                                            'unit': self._normalize_unit(unit),
                                            'raw_string': col_val,
                                        }
                                        break
                                except (ValueError, IndexError):
                                    continue
            
            return parameters if parameters else None
        
        except (ImportError, ValueError):
            return None

    def _parse_table_row(self, row_text: str) -> Optional[Dict]:
        """Parse a single table row"""
        if not row_text or len(row_text) < 5:
            return None
        
        # Split by multiple spaces or tabs
        parts = re.split(r'\s{2,}|\t+', row_text.strip())
        if len(parts) < 2:
            return None
        
        parameters = {}
        
        # Look for patterns in the parts
        for param_name, param_config in self.parameter_patterns.items():
            for part in parts:
                for pattern in param_config['patterns']:
                    match = re.search(pattern, part)
                    if match:
                        try:
                            value = float(match.group(1))
                            unit = match.group(2) if len(match.groups()) > 1 else ''
                            
                            if 0.01 <= value <= 100000:
                                parameters[param_name] = {
                                    'value': value,
                                    'unit': self._normalize_unit(unit),
                                    'raw_string': row_text,
                                }
                        except (ValueError, IndexError):
                            pass
        
        return parameters if parameters else None

    def normalize_units(self, params: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Normalize units for all parameters.
        Preserves structure and returns modified copy.
        """
        normalized = {}
        
        for param_name, param_data in params.items():
            normalized[param_name] = {
                'value': param_data.get('value'),
                'unit': self._normalize_unit(param_data.get('unit', '')),
                'raw_string': param_data.get('raw_string', ''),
            }
        
        return normalized

    def _normalize_unit(self, unit: str) -> str:
        """Normalize unit string to standard form"""
        if not unit:
            return 'N/A'
        
        unit_lower = unit.lower().strip()
        return self.unit_normalization.get(unit_lower, unit)

    @staticmethod
    def _safe_float(value: Any) -> float:
        """Safely convert value to float"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
