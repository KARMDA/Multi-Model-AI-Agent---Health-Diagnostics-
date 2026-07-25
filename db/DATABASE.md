# Database Layer Documentation

## Overview

The database layer provides a complete Supabase integration for the Health Diagnostics API. It follows the repository pattern for clean separation of concerns and includes full async support for FastAPI.

## Architecture

```
db/
├── __init__.py          # Package exports
├── client.py            # Supabase client initialization & lifecycle
├── models.py            # Pydantic models matching Supabase schema
├── repository.py        # Repository pattern for data access
└── migrations/
    └── 001_initial.sql  # Database schema and RLS policies
```

## Environment Configuration

### Required Environment Variables

```bash
# .env file or system environment
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-public-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key  # Optional, defaults to SUPABASE_KEY
```

### Getting Supabase Credentials

1. Create project at https://supabase.com
2. Navigate to **Settings** → **API**
3. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon public key** → `SUPABASE_KEY`
   - **service_role key** → `SUPABASE_SERVICE_KEY`

## Database Schema

### Tables

#### `users`
```sql
- id (UUID, PK)
- email (VARCHAR, UNIQUE)
- full_name (VARCHAR)
- avatar_url (TEXT)
- is_active (BOOLEAN)
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ)
```

#### `reports`
```sql
- id (UUID, PK)
- user_id (UUID, FK → users)
- parameters (JSONB)
- analysis (JSONB)
- risks (JSONB)
- recommendations (TEXT[])
- summary (JSONB)
- status (VARCHAR: pending, processing, completed, error)
- file_name (VARCHAR)
- file_type (VARCHAR)
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ)
```

#### `chat_history`
```sql
- id (UUID, PK)
- report_id (UUID, FK → reports, UNIQUE)
- messages (JSONB)
- message_count (INTEGER)
- created_at (TIMESTAMPTZ)
- updated_at (TIMESTAMPTZ)
```

### Indexes

Performance-optimized indexes on:
- `users.email` - For user lookups
- `reports.user_id` - For user's reports query
- `reports.created_at` - For time-based sorting
- `reports.status` - For status filtering
- `reports(user_id, created_at)` - Composite for user reports list
- `chat_history.report_id` - For chat lookups

### Row Level Security (RLS)

All tables have RLS enabled with policies:

**Users:**
- View own profile or public users
- Update only own profile

**Reports:**
- View/insert/update/delete only own reports
- Anonymous reports (user_id = NULL) accessible to creator

**Chat History:**
- Access only for reports user owns

## Module Usage

### 1. Client Initialization (main.py)

```python
from fastapi import FastAPI
from db.client import init_supabase, close_supabase, get_db
from db.repository import ReportRepository

app = FastAPI()

@app.on_event("startup")
async def startup():
    init_supabase()
    print("✓ Database connected")

@app.on_event("shutdown")
async def shutdown():
    close_supabase()
    print("✓ Database disconnected")
```

### 2. Database Dependency (routes)

```python
from fastapi import APIRouter, Depends
from supabase import Client
from db.client import get_db
from db.repository import ReportRepository

router = APIRouter()

@router.post("/analyze")
async def analyze_report(db: Client = Depends(get_db)):
    repo = ReportRepository(db)
    report_id = await repo.save_report({
        "user_id": "some-uuid",
        "parameters": {...},
        "analysis": {...},
        "risks": [...],
        "recommendations": [...],
        "summary": {...},
        "file_name": "report.pdf",
        "file_type": "pdf",
    })
    return {"report_id": report_id}
```

### 3. ReportRepository Methods

#### Save Report
```python
repo = ReportRepository(db)
report_id = await repo.save_report({
    "user_id": "uuid",
    "parameters": {...},
    "analysis": {...},
    "risks": [...],
    "recommendations": [...],
    "summary": {...},
    "file_name": "report.pdf",
    "file_type": "pdf",
})
# Returns: "uuid-string"
```

#### Get Single Report
```python
report = await repo.get_report("report-uuid")
# Returns: {id, user_id, parameters, analysis, ...} or None
```

#### Get User Reports
```python
reports = await repo.get_user_reports("user-uuid")
# Returns: [{id, user_id, created_at, ...}, ...]
# Ordered by created_at DESC (newest first)
```

#### Update Report Status
```python
await repo.update_status("report-uuid", "completed")
# Status: pending, processing, completed, error
```

#### Add Chat Message
```python
await repo.add_chat_message(
    report_id="report-uuid",
    role="user",  # or "assistant"
    content="What do these results mean?"
)
```

#### Get Chat History
```python
messages = await repo.get_chat_history("report-uuid")
# Returns: [{role, content, timestamp}, ...]
```

#### Delete Report
```python
await repo.delete_report("report-uuid")
# Deletes report and associated chat history
```

#### Get Statistics
```python
stats = await repo.get_report_summary_stats(user_id="optional-uuid")
# Returns: {total_reports, completed, processing, error, user_id}
```

## Pydantic Models

### Input Models

**BloodParameter**
```python
{
    "value": 5.2,
    "unit": "g/dL",
    "status": "NORMAL",  # LOW, NORMAL, HIGH, UNKNOWN, CRITICAL
    "reference_range": "4.5-5.5",
    "reference_min": 4.5,
    "reference_max": 5.5
}
```

**AnalysisData**
```python
{
    "parameters": {...},
    "summary": {...},
    "abnormal_parameters": [...],
    "recommendations": [...]
}
```

**RiskAssessment**
```python
{
    "condition": "Anemia",
    "risk_level": "HIGH",  # LOW, MEDIUM, HIGH, CRITICAL
    "confidence": 0.85,
    "indicators": ["Low hemoglobin", "Low RBC"]
}
```

**ReportCreate**
```python
{
    "user_id": "optional-uuid",
    "parameters": {...},
    "analysis": {...},
    "risks": [...],
    "recommendations": [...],
    "summary": {...},
    "file_name": "report.pdf",
    "file_type": "pdf"
}
```

## Migration Setup

### Running Migrations

1. **Using Supabase Web UI:**
   - Navigate to **SQL Editor**
   - Click **New Query**
   - Copy contents of `db/migrations/001_initial.sql`
   - Click **Run**

2. **Using Supabase CLI:**
   ```bash
   supabase db push
   ```

3. **Using psql:**
   ```bash
   psql -h db.supabase.co -U postgres -d postgres -f db/migrations/001_initial.sql
   ```

### Verification

```sql
-- Check tables created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- Check indexes
SELECT indexname FROM pg_indexes WHERE schemaname = 'public';

-- Check RLS policies
SELECT schemaname, tablename, policyname FROM pg_policies;
```

## Error Handling

All repository methods raise `ValueError` on database errors:

```python
try:
    report_id = await repo.save_report(report_data)
except ValueError as e:
    print(f"Database error: {e}")
```

Errors are logged with context for debugging:
- `logger.info()` - Successful operations
- `logger.warning()` - Not found cases
- `logger.error()` - Failures with full error details

## Performance Considerations

1. **Indexes**: All query patterns have indexes
2. **JSONB**: Flexible schema stored efficiently
3. **Foreign Keys**: Referential integrity maintained
4. **Cascading Deletes**: Chat history auto-deleted with reports
5. **Auto-Timestamps**: `updated_at` auto-maintained by triggers

## Security

### Row Level Security

- Users can only access their own records
- Anonymous reports have limited access control
- Service role bypasses RLS (for admin operations)

### Sensitive Data

- Passwords: Not stored in this schema (handled by Supabase Auth)
- API Keys: Never stored in database
- PII: `email` and `full_name` only stored with consent

## Logging

All database operations are logged:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

Log levels:
- **INFO**: Successful operations
- **WARNING**: Not found, empty results
- **ERROR**: Failures, with exception details

## Testing

### Integration Tests

```python
import pytest
from db.client import init_supabase, get_supabase_client
from db.repository import ReportRepository

@pytest.fixture
async def db():
    init_supabase()
    return get_supabase_client()

@pytest.mark.asyncio
async def test_save_report(db):
    repo = ReportRepository(db)
    report_id = await repo.save_report({...})
    assert report_id is not None
    
    report = await repo.get_report(report_id)
    assert report["id"] == report_id
```

## Future Enhancements

- [ ] Bulk operations for batch inserts
- [ ] Soft deletes with archive table
- [ ] Audit trail tracking
- [ ] Full-text search on analysis
- [ ] Analytics queries
- [ ] Backup/restore procedures
- [ ] Migration versioning system

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "SUPABASE_URL not set" | Check `.env` file and environment variables |
| "RLS policy violation" | Ensure auth context is set or use service role |
| "Connection timeout" | Check SUPABASE_URL is correct and network allows connection |
| "JSON parse error" | Validate JSONB data structure before insert |
| "Unique constraint violation" | Check for duplicate email (users table) or report_id |

## Support

For issues:
1. Check logs with `logging.getLogger("db")`
2. Verify Supabase project is active
3. Check RLS policies are correct
4. Validate environment variables
5. Review SQL migration for syntax errors
