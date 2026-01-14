🩺 Multi-Model AI Agent for Automated Health Diagnostics

An intelligent AI-based health diagnostics system that automatically analyzes blood test reports, detects abnormalities and medical patterns, and generates clear, personalized health insights using a multi-model AI pipeline.

This project was developed as part of the Infosys Springboard Virtual Internship and demonstrates the application of agentic AI, rule-based medical reasoning, OCR, and Large Language Models (LLMs) in healthcare analytics.

🚀 Project Overview

Modern blood reports are often difficult for non-medical users to interpret.
This system acts as an AI diagnostic assistant that:

Reads blood reports (PDFs / scanned images)

Extracts parameters using OCR + regex

Applies medical reference ranges

Detects hidden patterns and health risks

Generates human-readable summaries and recommendations

⚠️ Note: This system is for educational and analytical purposes only and does not replace professional medical advice.

🧠 Key Innovations

✅ Multi-Model AI Architecture (3 cooperating models)
✅ Explainable Rule-Based Medical Reasoning
✅ OCR + Text-Based Hybrid Parsing
✅ Pattern Detection & Risk Scoring
✅ Context-Aware Personalization
✅ RAG-based Medical Chatbot (Groq API)

🧩 System Architecture
INPUT (PDF / Image)
        ↓
OCR + Text Extraction
        ↓
Parameter Classification
        ↓
Pattern Detection
        ↓
Contextual Adjustment
        ↓
Synthesis & Recommendation
        ↓
Final Report + Chatbot Response

🔁 Workflow (Step-by-Step)

User Uploads Report
PDF / scanned image
Optional context (age, gender, smoking history)
Extraction Phase
PyMuPDF for text-based PDFs
Tesseract OCR for scanned reports
Regex-based parameter parsing

Synthesis & Output

Structured medical-style summary
Personalized lifestyle recommendations
Interactive chatbot via Groq LLM

🧬 Three-Model AI Engine
🔹 Model 1 – Parameter Classification
Threshold-based medical rules
High accuracy and explainability

🔹 Model 2 – Pattern Recognition
Rule-based expert logic
Risk scoring using deviation calculations

🔹 Model 3 – Contextual Adjustment
Age, gender, lifestyle-based tuning
Produces personalized insights

🛠️ Tech Stack
Component	Technology
UI	Streamlit
Language	Python
OCR	Tesseract (pytesseract)
PDF Processing	PyMuPDF (fitz), PDFPlumber
Data Handling	Pandas
AI / LLM	Groq API
Architecture	Agentic, pipeline-based
Storage	Streamlit session_state
📁 Project Structure (Simplified)
├── app.py
├── data_processor.py
├── model2_pattern.py
├── model3_pattern.py
├── synthesizer.py
├── system_prompt.py
├── requirements.txt
├── .streamlit/
│   └── secrets.example.toml
└── README.md


📊 Output

The system generates:

✔ Highlighted abnormal parameters
✔ Detected medical patterns
✔ Risk-adjusted scores
✔ Personalized health recommendations
✔ AI-powered chatbot explanations

🏆 Key Achievements

Hybrid Rule-Based + Generative AI system
First-level explainable AI for blood report analysis
RAG-powered health chatbot
Modular, scalable, agent-based design
Ready for real-world extension

📌 Disclaimer

This project is for educational and research purposes only.
It does not provide medical diagnosis and should not be used as a substitute for professional healthcare advice.

👨‍💻 Author
Karthikeyan T
