🧠 Multi-Model AI Agent for Automated Health Diagnostics

An AI-powered blood report analysis system that automatically extracts medical parameters, performs intelligent health risk assessment using multiple models, and generates personalized, explainable health recommendations through an end-to-end pipeline.

🔗 Live App:
https://health-diagnostics-ai-agent-sneqfjarlutprcqmxfcxwg.streamlit.app/

🔗 Project Resources (Drive):
https://drive.google.com/drive/folders/1QbfP3IH_mvhwTtLzHgj5jZa02lV2BGL6

📌 Overview

This project implements a Multi-Model AI Agent architecture to analyze blood test reports and deliver meaningful health insights. It supports multiple document formats, applies medical logic with AI reasoning, and produces professional diagnostic reports with appropriate medical disclaimers.

The system is designed for:

Healthcare AI research

Intelligent diagnostics automation

AI-assisted clinical decision support (non-diagnostic)

Academic & portfolio projects

🚀 Key Features
🔹 Milestone 1 & 2: Data Processing & Analysis

Multi-Format Input Support

PDF, DOCX, TXT, JSON

OCR fallback using EasyOCR for scanned reports

Intelligent Data Extraction

Robust parameter parsing

Unit normalization & validation

Model 1: Medical Classification Engine

Age & gender-aware classification

Labels: Low / Normal / High

Model 2: Health Pattern Recognition

Detects:

Anemia

Metabolic Syndrome

Cardiovascular risk indicators

Rule-based + pattern-driven logic

🔹 Milestone 3: Findings Synthesis & Recommendations

Cross-Model Result Aggregation

Combines outputs from all models

Produces coherent clinical summaries

AI-Powered Recommendations

Personalized:

Diet suggestions

Lifestyle improvements

Medical follow-ups

Uses:

LLMs (Ollama / Groq)

Rule-based fallback for reliability

🔹 Milestone 4: Integration & Reporting

End-to-End Orchestration

From report upload → analysis → recommendations

Professional Report Generation

Exportable Markdown reports

Clear sections: findings, risks, advice

Medical Safety Compliance

Explicit disclaimers

Encourages professional medical consultation

🧩 System Architecture (High-Level)
User Upload
   ↓
Document Parser + OCR
   ↓
Medical Parameter Extractor
   ↓
Multi-Model Analysis Engine
   ├── Classification Model
   ├── Pattern Recognition Model
   ↓
Findings Synthesizer
   ↓
AI Recommendation Engine
   ↓
Professional Health Report

🛠️ Tech Stack

Language: Python

Frontend: Streamlit

OCR: EasyOCR

AI / LLM: Ollama, Groq (optional)

Data Processing: Pandas, NumPy

Document Handling: PDF, DOCX, JSON parsers

⚙️ Installation & Setup
1️⃣ Install Dependencies
pip install -r requirements.txt

2️⃣ Run the Application
Windows
run.bat


or

py -m streamlit run app.py

Linux / macOS
chmod +x run.sh
./run.sh

3️⃣ Open in Browser
http://localhost:8501

📄 Output Report Includes

Extracted blood parameters

Normal / abnormal classifications

Detected health patterns

Risk assessment summary

Personalized recommendations

Medical disclaimer

⚠️ Medical Disclaimer

This application does not provide medical diagnoses.
All insights are for educational and informational purposes only.
Always consult a qualified healthcare professional for medical advice.

📂 Project Structure (Simplified)
├── app.py
├── models/
│   ├── classification_model.py
│   ├── pattern_model.py
├── ocr/
│   └── easyocr_handler.py
├── synthesis/
│   └── findings_aggregator.py
├── recommendations/
│   └── ai_recommender.py
├── reports/
│   └── report_generator.py
├── requirements.txt
├── run.bat
├── run.sh
└── README.md

🌟 Future Enhancements

Lab-specific reference range adaptation

Doctor-friendly PDF exports

Multi-language support

Integration with EHR systems

Continuous learning from anonymized data

👤 Author

Bhanu Satish Puvvala
AI | Data Science | Healthcare AI Enthusiast
