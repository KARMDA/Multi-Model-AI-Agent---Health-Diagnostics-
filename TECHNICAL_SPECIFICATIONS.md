# Technical Specifications & Architecture Document

## Project: Multi-Model AI Agent for Health Diagnostics

---

## 📋 Index

1. System Architecture
2. Module Specifications
3. Data Models & Structures
4. API Interfaces
5. Workflow & Processing Pipeline
6. Configuration & Environment
7. Performance Metrics
8. Error Handling & Validation
9. Testing Strategy
10. Deployment Architecture

---

## 1️⃣ System Architecture

### 1.1 High-Level Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                          │
│              Streamlit Web UI (src/ui/UI.py)                 │
│  • File Upload Interface                                     │
│  • Result Display                                            │
│  • Chat Interface                                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  APPLICATION LAYER                           │
│         Enhanced AI Agent (src/core/enhanced_ai_agent.py)    │
│  • Orchestration & Coordination                              │
│  • Workflow Management                                       │
│  • Decision Making                                           │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌─────────────────┐  ┌──────────────────┐  ┌──────────┐
│ EXTRACTION LAYER │ │ ANALYSIS LAYER   │ │ AI LAYER │
│ • OCR Engine     │ │ • Validator      │ │ • LLM    │
│ • Parser        │ │ • Interpreter    │ │ • Chat   │
│ • CSV Adapter   │ │ • Risk Calc      │ │ • Intent │
└─────────────────┘ │ • QA Assistant   │ └──────────┘
                    └──────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                 UTILITY LAYER                                │
│  • LLM Provider      • Unit Converter    • CSV Converter     │
│  • OCR Provider      • Context Manager   • Ollama Manager    │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│              EXTERNAL DATA & SERVICES                        │
│  • Config: reference_ranges.json                             │
│  • LLM: Ollama (Local) / HF Inference (Cloud)               │
│  • OCR: Tesseract (Local) / OCR.space (Cloud)               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Component Interaction Map

```
UI.py
├── enhanced_ai_agent.py
│   ├── goal_oriented_workflow_manager.py
│   │   ├── phase1_extractor.py (OCR + parsing)
│   │   ├── validator.py (Reference range check)
│   │   └── advanced_risk_calculator.py
│   │
│   ├── phase2_orchestrator.py
│   │   ├── advanced_pattern_analysis.py
│   │   └── phase2_integration_safe.py
│   │
│   ├── intent_inference_engine.py
│   ├── anticipatory_suggestion_system.py
│   ├── clarifying_question_generator.py
│   ├── comprehensive_report_generator.py
│   └── qa_assistant.py
│       └── llm_provider.py (Ollama / HF)
│
├── ocr_engine.py
│   ├── ocr_provider.py
│   └── [Tesseract / OpenCV / pdfplumber]
│
└── advanced_context_manager.py
```

---

## 2️⃣ Module Specifications

### 2.1 Core Modules (src/core/)

#### **ocr_engine.py** — Optical Character Recognition
```
Class: MedicalOCROrchestrator
Methods:
  - extract_text_from_pdf(file_path) → str
  - extract_text_from_image(file_path) → str
  - apply_preprocessing_strategy(image, strategy) → image
  - parse_extracted_text(text) → dict
  - validate_ocr_output(text) → bool

Features:
  - 6 preprocessing strategies (contrast, scale, rotate, blur, dilation, erosion)
  - Confidence scoring
  - API fallback (Tesseract → OCR.space)
  - Medical keyword detection
  - Pattern confidence threshold: 70%
```

#### **enhanced_blood_parser.py** — Blood Parameter Parsing
```
Class: EnhancedBloodParameterParser
Methods:
  - extract_parameters(text: str) → dict[str, Parameter]
  - parse_parameter_value(text: str, param: str) → tuple(value, unit)
  - normalize_units(value: float, original_unit: str, target_unit: str) → float
  - detect_test_type(parameters: dict) → str

Supported Parameters (20+):
  CBC: WBC, RBC, Hemoglobin, Hematocrit, MCV, MCH, MCHC, RDW, Platelets
  Differential: Neutrophils, Lymphocytes, Monocytes, Eosinophils, Basophils
  Chemistry: Glucose, Electrolytes, Creatinine, BUN, Liver enzymes
  
Value Format Detection:
  - Decimal numbers (8.5, 12.3)
  - Fractions (not common)
  - Scientific notation (1.2e3)
  - Unit detection (mg/dL, g/dL, etc.)
```

#### **validator.py** — Reference Range Validation
```
Class: BloodParameterValidator
Methods:
  - validate_parameter(param: str, value: float, unit: str, age: int, gender: str) → Status
  - get_reference_range(param: str, age: int = None, gender: str = None) → tuple(min, max)
  - determine_status(value: float, min_range: float, max_range: float) → Status
  - validate_cross_parameter_logic(parameters: dict) → list[Warning]

Data Source:
  - config/reference_ranges.json
  
Status Enum:
  - LOW (value < min_range)
  - NORMAL (min_range ≤ value ≤ max_range)
  - HIGH (value > max_range)

Dynamic Ranges:
  - Age-based adjustments (pediatric, adult, geriatric)
  - Gender-based variations (male/female)
```

#### **enhanced_ai_agent.py** — Main AI Orchestrator
```
Class: EnhancedAIAgent
Properties:
  - workflow_manager: GoalOrientedWorkflowManager
  - intent_engine: IntentInferenceEngine
  - context_manager: AdvancedContextManager
  - suggestion_system: AnticipatorysuggestionSystem
  - report_generator: ComprehensiveReportGenerator

Methods:
  - process_blood_report(file_path: str) → Report
  - analyze_parameters(parameters: dict) → Analysis
  - generate_recommendations(analysis: Analysis) → list[Recommendation]
  - handle_user_question(question: str, context: dict) → str
  - compare_reports(reports: list[Report]) → Comparison

Workflow:
  1. File ingestion & OCR
  2. Parameter extraction
  3. Reference range validation
  4. Intent detection
  5. Risk calculation
  6. AI analysis & insights
  7. Recommendation generation
  8. Report formatting
```

#### **comprehensive_report_generator.py** — Report Generation
```
Class: ComprehensiveReportGenerator
Methods:
  - generate_text_report(analysis: Analysis) → str
  - generate_formatted_report(analysis: Analysis) → dict
  - create_summary_section(analysis: Analysis) → str
  - create_abnormalities_section(analysis: Analysis) → str
  - create_recommendations_section(analysis: Analysis) → str

Output Format:
  {
    "summary": str,
    "abnormalities": list[dict],
    "normal_parameters": list[str],
    "recommendations": list[str],
    "risk_level": str,
    "next_steps": list[str]
  }
```

#### **qa_assistant.py** — Chat & Q&A
```
Class: QAAssistant
Methods:
  - process_question(question: str, context: dict) → str
  - maintain_chat_history(question: str, answer: str) → None
  - generate_follow_up_questions(analysis: Analysis) → list[str]
  - clarify_user_intent(question: str) → Intent

Chat Context Maintained:
  - Extracted parameters
  - Validated results
  - Previous Q&A history
  - User preferences
  - Health concerns
```

#### **advanced_risk_calculator.py** — Risk Assessment
```
Class: AdvancedRiskCalculator
Methods:
  - calculate_overall_risk(parameters: dict) → float (0-1)
  - identify_risk_patterns(parameters: dict) → list[RiskPattern]
  - calculate_parameter_risk(param: str, value: float) → float
  - get_risk_level(risk_score: float) → str (LOW/MEDIUM/HIGH/CRITICAL)

Risk Factors:
  - Individual parameter deviation from normal
  - Parameter combinations indicating conditions
  - Trend analysis (if multiple reports)
  - Age-related risk adjustments
```

#### **goal_oriented_workflow_manager.py** — Workflow Control
```
Class: GoalOrientedWorkflowManager
Methods:
  - extract_user_goals(question: str) → list[Goal]
  - execute_workflow(file_path: str, goals: list[Goal]) → WorkflowResult
  - prioritize_analysis(parameters: dict, goals: list[Goal]) → OrderedAnalysis
  - track_goal_completion(analysis: Analysis, goals: list[Goal]) → Completion

Goals:
  - Get general health overview
  - Focus on specific organ system
  - Identify abnormalities
  - Track specific condition
```

#### **intent_inference_engine.py** — User Intent Detection
```
Class: IntentInferenceEngine
Methods:
  - infer_intent(question: str) → Intent
  - extract_keywords(question: str) → list[str]
  - detect_health_concerns(question: str) → list[HealthConcern]
  - identify_parameter_focus(question: str) → list[str]

Intent Types:
  - GENERAL_ANALYSIS (get overall health picture)
  - PARAMETER_FOCUS (ask about specific test)
  - TREND_ANALYSIS (compare multiple reports)
  - RISK_ASSESSMENT (understand health risks)
  - RECOMMENDATION_SEEKING (get advice)
```

#### **anticipatory_suggestion_system.py** — Proactive Suggestions
```
Class: AnticipatorysuggestionSystem
Methods:
  - generate_suggestions(analysis: Analysis) → list[Suggestion]
  - identify_potential_issues(parameters: dict) → list[PotentialIssue]
  - suggest_follow_up_tests(analysis: Analysis) → list[str]
  - recommend_lifestyle_changes(analysis: Analysis) → list[str]
```

#### **clarifying_question_generator.py** — Q&A Generation
```
Class: ClarifyingQuestionGenerator
Methods:
  - generate_questions(analysis: Analysis) → list[Question]
  - generate_follow_ups(user_answer: str, context: dict) → list[Question]
  - prioritize_questions(questions: list[Question]) → OrderedQuestions

Question Types:
  - Symptom clarification
  - Medical history
  - Lifestyle factors
  - Treatment history
  - Risk factor assessment
```

#### **dynamic_reference_ranges.py** — Dynamic Range Adjustment
```
Class: DynamicReferenceRanges
Methods:
  - get_age_adjusted_range(param: str, age: int) → tuple(min, max)
  - get_gender_adjusted_range(param: str, gender: str) → tuple(min, max)
  - get_demographic_adjusted_range(param: str, age: int, gender: str) → tuple(min, max)

Adjustments:
  - Pediatric (0-18): Different ranges for age groups
  - Adult (18-65): Standard reference ranges
  - Geriatric (65+): Age-adjusted values
  - Gender-specific: Male/Female variations
```

### 2.2 Phase 1 Modules (src/phase1/)

#### **phase1_extractor.py** — Basic Extraction
```
Class: Phase1Extractor
Methods:
  - extract_from_file(file_path: str) → ExtractionResult
  - validate_extraction_quality() → QualityScore
  
Responsibilities:
  - Handle file I/O
  - Coordinate OCR
  - Basic text cleaning
```

#### **table_extractor.py** — Table Extraction
```
Class: TableExtractor
Methods:
  - extract_tables_from_pdf(pdf_path: str) → list[DataFrame]
  - extract_tables_from_image(img_path: str) → list[DataFrame]
  - parse_table_structure(table: DataFrame) → ParsedTable
```

### 2.3 Phase 2 Modules (src/phase2/)

#### **phase2_orchestrator.py** — Advanced Analysis
```
Class: Phase2Orchestrator
Methods:
  - execute_phase2_analysis(extracted_data: dict) → AdvancedAnalysis
  - apply_pattern_analysis(parameters: dict) → PatternAnalysis
  - integrate_with_llm(analysis: dict) → EnhancedAnalysis
```

#### **advanced_pattern_analysis.py** — Pattern Detection
```
Class: AdvancedPatternAnalyzer
Methods:
  - detect_patterns(parameters: dict) → list[Pattern]
  - identify_clinically_significant_combinations() → list[ClinicalPattern]
  - detect_anomalies(parameters: dict) → list[Anomaly]
```

---

## 3️⃣ Data Models & Structures

### 3.1 Core Data Models

```python
# Blood Parameter
class Parameter:
    name: str
    value: float
    unit: str
    reference_min: float
    reference_max: float
    status: Enum[LOW, NORMAL, HIGH]
    confidence: float  # 0-1
    source: str  # from OCR/JSON/CSV

# Analysis Result
class Analysis:
    parameters: dict[str, Parameter]
    abnormalities: list[Parameter]
    risk_score: float  # 0-1
    risk_level: str  # LOW/MEDIUM/HIGH/CRITICAL
    patterns: list[Pattern]
    recommendations: list[str]
    timestamp: datetime
    source_file: str

# Medical Report
class Report:
    analysis: Analysis
    test_date: date
    patient_age: int (optional)
    patient_gender: str (optional)
    test_type: str  # CBC, CMP, etc.
    generated_insights: str
    recommendations: list[str]

# Chat Message
class ChatMessage:
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    context: dict  # relevant extracted data

# Risk Pattern
class RiskPattern:
    name: str
    description: str
    parameters_involved: list[str]
    risk_level: str
    significance: float
```

### 3.2 Configuration Models

```json
{
  "reference_ranges": {
    "WBC": {
      "standard": { "min": 4.5, "max": 11.0, "unit": "K/uL" },
      "pediatric": {
        "0-1": { "min": 5.0, "max": 21.0 },
        "1-5": { "min": 5.0, "max": 15.0 },
        "5-12": { "min": 4.5, "max": 13.5 }
      },
      "geriatric": { "min": 3.5, "max": 11.0 }
    }
  }
}
```

---

## 4️⃣ API Interfaces

### 4.1 Main UI Interface (Streamlit)

```python
# File Upload Interface
uploaded_file = st.file_uploader("Upload blood report", 
                                 type=["pdf", "png", "jpg", "json", "csv"])

# Results Display
st.dataframe(extracted_parameters)
st.metric("Risk Level", risk_level, risk_score)
st.write(recommendations)

# Chat Interface
user_question = st.chat_input("Ask about your blood work...")
ai_response = qa_assistant.process_question(user_question, context)
```

### 4.2 LLM Provider Interface

```python
class LLMProvider:
    def generate_insight(prompt: str) -> str
    def generate_explanation(param: str, value: float) -> str
    def answer_question(question: str, context: dict) -> str

# Implementations
- OllamaLLMProvider  # Local Mistral 7B
- HuggingFaceLLMProvider  # Cloud HF Inference API
```

### 4.3 OCR Provider Interface

```python
class OCRProvider:
    def extract_text(file_path: str) -> str
    def extract_with_confidence(file_path: str) -> tuple(str, float)

# Implementations
- TesseractOCRProvider  # Local
- OcrSpaceProvider  # Cloud fallback
```

---

## 5️⃣ Workflow & Processing Pipeline

### 5.1 Complete Processing Workflow

```
START
  ↓
┌─────────────────────────────┐
│ 1. FILE UPLOAD & DETECTION  │
│ - MIME type check           │
│ - File validation           │
│ - Format selection (OCR/JSON/CSV)
└─────────────────────────────┘
  ↓
┌─────────────────────────────┐
│ 2. EXTRACTION PHASE         │
│ - OCR (if image/PDF)        │
│ - JSON/CSV parsing          │
│ - Text preprocessing        │
└─────────────────────────────┘
  ↓
┌─────────────────────────────┐
│ 3. PARSING PHASE            │
│ - Regex pattern matching    │
│ - Parameter extraction      │
│ - Value normalization       │
└─────────────────────────────┘
  ↓
┌─────────────────────────────┐
│ 4. VALIDATION PHASE         │
│ - Reference range lookup    │
│ - Status determination      │
│ - Quality checks            │
└─────────────────────────────┘
  ↓
┌─────────────────────────────┐
│ 5. ANALYSIS PHASE           │
│ - Risk calculation          │
│ - Pattern detection         │
│ - Abnormality flagging      │
└─────────────────────────────┘
  ↓
┌─────────────────────────────┐
│ 6. LLM ENHANCEMENT          │
│ - Mistral 7B processing     │
│ - Natural language insights │
│ - Recommendation generation │
└─────────────────────────────┘
  ↓
┌─────────────────────────────┐
│ 7. REPORT GENERATION        │
│ - Comprehensive report      │
│ - Formatted output          │
│ - Summary creation          │
└─────────────────────────────┘
  ↓
┌─────────────────────────────┐
│ 8. UI DISPLAY               │
│ - Result presentation       │
│ - Chat interface ready      │
│ - Context stored            │
└─────────────────────────────┘
  ↓
┌─────────────────────────────┐
│ 9. CHAT INTERACTION         │
│ - User questions            │
│ - AI responses              │
│ - Context maintenance       │
└─────────────────────────────┘
  ↓
END
```

### 5.2 Multi-Report Comparison Workflow

```
Report 1 → Parse → Validate → Analyze ─┐
                                        ├─→ Trend Analysis → Insights
Report 2 → Parse → Validate → Analyze ─┤
                                        │
Report 3 → Parse → Validate → Analyze ─┘
                                        
Result: Trends, improvements, concerns over time
```

---

## 6️⃣ Configuration & Environment

### 6.1 Environment Variables

```bash
# LLM Configuration
LLM_PROVIDER_PRIORITY=ollama_first      # "ollama_first" or "hf_only"
OLLAMA_HOST=http://localhost:11434      # Ollama endpoint
OLLAMA_MODEL=mistral:instruct           # Model name

# HuggingFace Configuration
HF_API_TOKEN=<token>                    # HF Inference API token
HF_MODEL_ID=mistralai/Mistral-7B-Instruct-v0.1

# OCR Configuration
OCR_SPACE_API_KEY=<key>                 # Optional OCR.space API
TESSERACT_PATH=/usr/bin/tesseract      # System tesseract path

# Application
STREAMLIT_SERVER_PORT=8501
LOG_LEVEL=INFO
```

### 6.2 Configuration File Structure

```
config/
└── reference_ranges.json
    ├── WBC
    ├── RBC
    ├── Hemoglobin
    ├── ... (20+ parameters)
    └── Dynamic adjustments by age/gender
```

---

## 7️⃣ Performance Metrics

### 7.1 Expected Performance

| Operation | Time | Resource |
|-----------|------|----------|
| OCR (page) | 2-5s | CPU bound |
| Parsing | <1s | RAM: 100MB |
| Validation | <0.5s | RAM: 50MB |
| LLM Analysis | 3-10s | CPU/GPU, 2GB memory |
| Report Gen | <1s | RAM: 50MB |
| Total (avg report) | 8-20s | Depends on LLM backend |

### 7.2 Scalability

- **Concurrent Users (HF Spaces)**: Auto-scaled
- **Concurrent Users (Local)**: 1-5 (Streamlit limitation)
- **Report Processing**: Sequential or queued
- **API Rate Limits**: HF Inference (free tier: reasonable limits)

---

## 8️⃣ Error Handling & Validation

### 8.1 Error Categories

```python
# Extraction Errors
- FileNotFoundError
- OCRExtractionError
- ParsingError (malformed JSON/CSV)
- UnsupportedFileFormat

# Parsing Errors
- ParameterNotFound
- InvalidUnitError
- ValueParsingError
- MissingReferenceRange

# Validation Errors
- OutOfRangeValue
- InvalidParameter
- InconsistentLogic
- QualityCheckFailed

# LLM Errors
- ModelNotAvailable
- APIConnectionError
- TokenLimitExceeded
- TimeoutError
```

### 8.2 Validation Strategies

1. **Input Validation**
   - File type checking
   - Size validation
   - MIME type verification

2. **Data Validation**
   - Parameter existence check
   - Value range check
   - Unit compatibility check

3. **Logic Validation**
   - Cross-parameter relationships
   - Medical reasonableness
   - Consistency checks

4. **Output Validation**
   - Report completeness
   - Recommendation feasibility
   - AI response quality

---

## 9️⃣ Testing Strategy

### 9.1 Test Coverage

```
Unit Tests
├── test_ocr_engine.py
├── test_blood_parser.py
├── test_validator.py
├── test_interpreter.py
└── test_unit_converter.py

Integration Tests
├── test_full_pipeline.py
├── test_phase1_phase2_integration.py
└── test_llm_integration.py

End-to-End Tests
├── test_pdf_workflow.py
├── test_image_workflow.py
└── test_json_workflow.py

Test Data
├── sample_reports/
│   ├── normal_report.pdf
│   ├── abnormal_report.json
│   └── edge_cases/
```

### 9.2 Test Types

- Unit: Individual module testing
- Integration: Module interaction testing
- Functional: Feature/workflow testing
- Performance: Speed and resource testing
- Security: Input sanitization testing

---

## 🔟 Deployment Architecture

### 10.1 Local Deployment

```
[User Machine]
    ├── Python 3.8+
    │   ├── Streamlit server (localhost:8501)
    │   ├── Python runtime
    │   └── Dependencies (pip)
    │
    ├── System Services
    │   ├── Tesseract OCR
    │   ├── Ollama (optional, for local LLM)
    │   └── OpenCV
    │
    └── Data
        ├── config/reference_ranges.json
        └── Session files (temporary)
```

### 10.2 Cloud Deployment (HF Spaces)

```
[HF Spaces Infrastructure]
    ├── Streamlit Application Container
    │   ├── Python runtime
    │   ├── Application code (src/)
    │   └── Configuration
    │
    ├── External Services
    │   ├── HF Inference API (Mistral 7B)
    │   └── OCR.space (backup OCR)
    │
    └── Persistent Storage
        └── config/reference_ranges.json
```

### 10.3 Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy application
COPY . /app

# Install Python dependencies
RUN pip install -r requirements.txt

# Run application
CMD ["streamlit", "run", "src/ui/UI.py"]
```

### 10.4 API Load Path (Cloud)

```
User Request
    ↓
[CDN/Load Balancer]
    ↓
[HF Spaces App Server]
    ↓
Local Processing (OCR, parsing, validation)
    ↓
API Calls to External Services:
├─ HF Inference API (LLM)
└─ OCR.space (Optional)
    ↓
Response to User
```

---

## 📊 Database/Config Module Reference

### reference_ranges.json Structure

```json
{
  "WBC": {
    "display_name": "White Blood Cell Count",
    "unit": "K/uL",
    "standard_range": {
      "min": 4.5,
      "max": 11.0
    },
    "special_populations": {
      "pediatric": {...},
      "geriatric": {...},
      "male": {...},
      "female": {...}
    }
  },
  // ... 19+ more parameters
}
```

---

## 🔐 Security Considerations

1. **Input Sanitization**: All user inputs sanitized before LLM
2. **Data Privacy**: No data stored externally by default
3. **API Key Management**: Environment variable based
4. **Error Messages**: Non-technical user-friendly messages
5. **Rate Limiting**: Respect API rate limits

---

## 📈 Monitoring & Logging

```python
# Logging Strategy
- File: logs/application.log
- Console: INFO and above
- Format: {timestamp} | {level} | {module} | {message}

# Metrics
- OCR success rate
- Parsing accuracy
- API response times
- LLM processing time
- User session duration
```

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Status**: Complete  

For implementation details, refer to individual module documentation.

