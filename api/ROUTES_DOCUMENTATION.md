# API Routes Refactoring - Completed ✓

This document describes the refactored modular API structure.

## Overview

The API has been refactored from a monolithic `main.py` to a modular route-based architecture with clear separation of concerns.

## Directory Structure

```
api/
├── main.py                 # FastAPI app initialization, middleware, state management
├── routes/
│   ├── __init__.py        # Route package exports
│   ├── analyze.py         # Blood report analysis endpoint
│   ├── reports.py         # Report retrieval and management endpoints
│   └── chat.py            # Interactive chat endpoint
```

## Routes Breakdown

### 1. **analyze.py** - Analysis Endpoint
**Location:** `POST /api/analyze`

**Purpose:** Handles blood report file uploads and analysis

**Supported Formats:**
- PDF (scanned or digital)
- PNG, JPG, JPEG (images)
- JSON (structured data)
- CSV (tabular data)

**Request:**
```json
{
  "file": "<binary_file>",
  "user_id": "optional_user_id"
}
```

**Response:**
```json
{
  "report_id": "uuid-string",
  "analysis": {
    "parameters": { ... },
    "summary": { ... },
    "abnormal_parameters": [ ... ],
    "recommendations": [ ... ]
  },
  "created_at": "ISO-8601-datetime",
  "file_type": "pdf|png|jpg|json|csv",
  "file_name": "filename.ext"
}
```

### 2. **reports.py** - Report Management Endpoints
**Locations:**
- `GET /api/report/{report_id}` - Retrieve specific report
- `GET /api/reports/user/{user_id}` - List user's reports

**Purpose:** Retrieve previously analyzed reports and chat history

**Response (GET /report/{report_id}):**
```json
{
  "report_id": "uuid-string",
  "analysis": { ... },
  "created_at": "ISO-8601-datetime",
  "file_name": "report.pdf",
  "chat_history": [
    { "role": "user", "content": "...", "timestamp": "..." },
    { "role": "assistant", "content": "...", "timestamp": "..." }
  ],
  "chat_enabled": true
}
```

**Response (GET /reports/user/{user_id}):**
```json
{
  "user_id": "user-id",
  "reports": [
    {
      "report_id": "uuid-string",
      "file_name": "report.pdf",
      "created_at": "ISO-8601-datetime",
      "abnormal_count": 3,
      "total_parameters": 20
    }
  ],
  "total_count": 1
}
```

### 3. **chat.py** - Interactive Chat Endpoint
**Location:** `POST /api/chat`

**Purpose:** Ask AI-powered questions about blood reports

**Request:**
```json
{
  "report_id": "uuid-string",
  "message": "What do my results mean?",
  "user_id": "optional_user_id"
}
```

**Response:**
```json
{
  "message": "AI-generated response...",
  "timestamp": "ISO-8601-datetime",
  "report_id": "uuid-string"
}
```

## Core Application (main.py)

**Responsibilities:**
- FastAPI app initialization
- CORS middleware configuration
- Global exception handlers
- Application state management (_app_state)
- Lifespan events (startup/shutdown)
- Health check endpoint
- System stats endpoint
- Report deletion endpoint

**Key Components:**
- `_app_state`: Global state container with:
  - `store`: Report storage (ReportStore)
  - `analysis_service`: File analysis service
  - `chat_service`: Chat message processing service

## Models

**Shared Models (in main.py):**
- `BloodParameter` - Blood test parameter
- `AnalysisResult` - Complete analysis output
- `ReportMetadata` - Report storage metadata

**Route-Specific Models:**
- **analyze.py**: `AnalyzeResponse`
- **reports.py**: `ReportResponse`, `UserReportsResponse`
- **chat.py**: `ChatMessage`, `ChatResponse`

## Route Registration

Routes are registered in `main.py`:

```python
from routes import analyze_router, reports_router, chat_router

app.include_router(analyze_router)
app.include_router(reports_router)
app.include_router(chat_router)
```

## Benefits of This Structure

1. **Modularity**: Each route group in its own file
2. **Scalability**: Easy to add new endpoints
3. **Maintainability**: Clear separation of concerns
4. **Testability**: Each route module can be tested independently
5. **Organization**: Related endpoints grouped together
6. **Documentation**: Self-documenting structure

## API Documentation

Auto-generated OpenAPI documentation available at:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

## Future Enhancements

- [ ] Add authentication/authorization
- [ ] Integrate Supabase for persistent storage
- [ ] Add more specialized analysis endpoints
- [ ] Implement webhooks for async processing
- [ ] Add request/response validation middleware
- [ ] Implement caching layer
- [ ] Add rate limiting
