# 🩺 Multi-Model AI Agent for Automated Health Diagnostics

This project implements a **Multi-Model AI Agent** that automatically analyzes **blood test reports (CBC)** and provides structured insights, risk assessment, summaries, recommendations, and an interactive chatbot for user queries.

The system is designed to assist users in **understanding medical reports** in a simple and user-friendly way, without replacing professional medical advice.

---

## 📌 Project Objectives

- Automatically extract lab values from blood reports
- Interpret individual parameters using reference ranges
- Detect clinical patterns using contextual information
- Generate concise clinical summaries and recommendations
- Provide an interactive chatbot for report-related questions
- Support multiple input formats (PDF, Image, JSON)

---

## 🏗️ System Architecture

The system follows a **multi-stage pipeline**:

1. **User Interface (Streamlit)**
2. **Data Ingestion & Preprocessing**
3. **Model 1 – Individual Parameter Analysis**
4. **Model 2 – Pattern Recognition & Risk Assessment**
5. **Model 3 – Summary & Recommendation Engine**
6. **Context-Aware Chatbot**
7. **Output & Visualization**

---

## 📂 Supported Input Formats

- **Text-based PDF** (recommended)
- **Scanned PDF / Image** (OCR-based)
- **JSON**

> ⚠️ For best reliability, **text-based PDFs** are preferred.  
> Scanned PDFs require OCR dependencies.

---

## ⚙️ Technologies & Libraries Used

| Library | Purpose |
|------|--------|
| **Python** | Core programming language |
| **Streamlit** | Interactive web application |
| **Pandas** | Data handling and tabular processing |
| **pdfplumber** | Text extraction from PDFs |
| **pytesseract** | OCR for scanned images |
| **Pillow (PIL)** | Image preprocessing |
| **Regex (re)** | Flexible lab value extraction |
| **Groq / LLM (Optional)** | AI-based summary generation |

---

## 🧠 Model Description

### 🔹 Model 1: Individual Parameter Analysis
- Compares each lab value with standard reference ranges
- Classifies parameters as:
  - Low
  - Normal
  - High
  - Borderline

### 🔹 Model 2: Pattern Recognition & Risk Assessment
- Uses patient context (age, gender)
- Identifies clinical patterns such as:
  - Mild anemia
  - Dehydration indicators
- Outputs overall risk level

### 🔹 Model 3: Summary & Recommendation Engine
- Synthesizes findings from previous models
- Generates:
  - Clinical summary
  - Lifestyle and follow-up recommendations
- Uses rule-based logic with optional AI enhancement

---

## 💬 Chatbot Module

- Allows users to ask questions about their uploaded report
- Provides:
  - Short
  - Context-aware
  - Non-diagnostic answers
- Designed for safety and clarity

---

## 🧪 Key Features

- ✔ Multi-format report upload
- ✔ Automatic lab data extraction
- ✔ Parameter-wise interpretation
- ✔ Pattern recognition with context
- ✔ Severity indication
- ✔ Personalized recommendations
- ✔ Interactive chatbot
- ✔ Clean and user-friendly UI

---

## ⚠️ Challenges Faced

- Handling scanned PDFs requiring OCR dependencies
- Inconsistent medical report formats
- LLM API quota and dependency limitations
- Overly verbose AI-generated responses

---

## ✅ Solutions Implemented

- Preferred text-based PDFs for reliability
- Regex-based flexible parsing
- Rule-based logic for clinical safety
- Concise chatbot and summary outputs
- Modular architecture for easy future upgrades

---

## 🚀 How to Run the Project

### 1️⃣ Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate
