# Database Setup Guide

## Quick Start (5 minutes)

### Step 1: Set Environment Variables

Create a `.env` file in the project root:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

Or set as system environment variables.

### Step 2: Install Supabase Client

```bash
pip install supabase
```

### Step 3: Run Database Migration

Open Supabase Web UI:
1. Go to SQL Editor
2. Create New Query
3. Copy-paste contents from `db/migrations/001_initial.sql`
4. Click Run

**Expected Output:**
```
✓ Tables created: users, reports, chat_history
✓ Indexes created: 9 indexes
✓ RLS policies enabled on all tables
✓ Timestamp triggers created
```

### Step 4: Update FastAPI Main

In `api/main.py`:

```python
from db.client import init_supabase, close_supabase

@app.on_event("startup")
async def startup():
    init_supabase()
    print("✓ Database initialized")

@app.on_event("shutdown")
async def shutdown():
    close_supabase()
```

### Step 5: Test Connection

```bash
python -c "from db.client import init_supabase; init_supabase(); print('✓ Connected')"
```

## Integration with API Routes

### Update `api/routes/analyze.py`

```python
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from supabase import Client
from db.client import get_db
from db.repository import ReportRepository

router = APIRouter(prefix="/api", tags=["Analysis"])

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_report(
    file: UploadFile = File(...),
    user_id: str = None,
    db: Client = Depends(get_db)
) -> AnalyzeResponse:
    report_id = str(uuid.uuid4())

    try:
        # ... existing file validation code ...
        
        # Perform analysis
        analysis = await _app_state.analysis_service.analyze_file(
            file_content, file_extension
        )

        # Save to database
        repo = ReportRepository(db)
        saved_id = await repo.save_report({
            "user_id": user_id,
            "parameters": {
                param: param_data.model_dump()
                for param, param_data in analysis.parameters.items()
            },
            "analysis": analysis.model_dump(),
            "risks": analysis.risk_assessment or [],
            "recommendations": analysis.recommendations,
            "summary": analysis.summary,
            "file_name": file.filename,
            "file_type": file_extension,
        })

        return AnalyzeResponse(
            report_id=saved_id,
            analysis=analysis,
            created_at=datetime.utcnow(),
            file_type=file_extension,
            file_name=file.filename,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Analysis failed: {str(e)}"
        )
```

### Update `api/routes/reports.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from supabase import Client
from db.client import get_db
from db.repository import ReportRepository

router = APIRouter(prefix="/api", tags=["Reports"])

@router.get("/report/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    db: Client = Depends(get_db)
) -> ReportResponse:
    repo = ReportRepository(db)
    report_meta = await repo.get_report(report_id)

    if not report_meta:
        raise HTTPException(status_code=404, detail=f"Report not found: {report_id}")

    chat_history = await repo.get_chat_history(report_id)

    return ReportResponse(
        report_id=report_id,
        analysis=report_meta.get("analysis"),
        created_at=report_meta.get("created_at"),
        file_name=report_meta.get("file_name"),
        chat_history=chat_history,
        chat_enabled=True,  # Assuming AI is enabled
    )

@router.get("/reports/user/{user_id}")
async def get_user_reports(
    user_id: str,
    db: Client = Depends(get_db)
) -> UserReportsResponse:
    repo = ReportRepository(db)
    reports = await repo.get_user_reports(user_id)

    return UserReportsResponse(
        user_id=user_id,
        reports=[
            {
                "report_id": r["id"],
                "file_name": r["file_name"],
                "created_at": r["created_at"],
                "abnormal_count": len(r.get("analysis", {}).get("abnormal_parameters", [])),
                "total_parameters": len(r.get("parameters", {})),
            }
            for r in reports
        ],
        total_count=len(reports),
    )
```

### Update `api/routes/chat.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from supabase import Client
from db.client import get_db
from db.repository import ReportRepository

router = APIRouter(prefix="/api", tags=["Chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatMessage,
    db: Client = Depends(get_db)
) -> ChatResponse:
    try:
        if not request.message or len(request.message.strip()) < 3:
            raise HTTPException(
                status_code=400, detail="Message must be at least 3 characters"
            )

        repo = ReportRepository(db)

        # Verify report exists
        report = await repo.get_report(request.report_id)
        if not report:
            raise ValueError(f"Report not found: {request.report_id}")

        # Get AI response (from existing service)
        response_text = await _app_state.chat_service.process_message(
            report_id=request.report_id,
            message=request.message,
            user_id=request.user_id,
        )

        # Save to database
        await repo.add_chat_message(
            report_id=request.report_id,
            role="user",
            content=request.message,
        )
        await repo.add_chat_message(
            report_id=request.report_id,
            role="assistant",
            content=response_text,
        )

        return ChatResponse(
            message=response_text,
            timestamp=datetime.utcnow(),
            report_id=request.report_id,
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")
```

## CLI Commands for Database Management

### Create User

```python
from db.client import get_supabase_client
from datetime import datetime

def create_user(email: str, full_name: str = None):
    db = get_supabase_client()
    result = db.table("users").insert({
        "email": email,
        "full_name": full_name,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
    }).execute()
    print(f"User created: {result.data}")
```

### List All Reports

```python
def list_all_reports():
    db = get_supabase_client()
    result = db.table("reports").select("*").order("created_at", desc=True).execute()
    for report in result.data:
        print(f"{report['id']} | {report['file_name']} | {report['status']}")
```

### Get Report Statistics

```python
from db.repository import ReportRepository

async def get_stats():
    from db.client import get_supabase_client
    db = get_supabase_client()
    repo = ReportRepository(db)
    stats = await repo.get_report_summary_stats()
    print(f"Total Reports: {stats['total_reports']}")
    print(f"Completed: {stats['completed']}")
    print(f"Processing: {stats['processing']}")
    print(f"Errors: {stats['error']}")
```

## Monitoring and Maintenance

### Check Database Usage

```sql
-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Row counts
SELECT 
    tablename,
    n_live_tup AS row_count
FROM pg_stat_user_tables
WHERE schemaname = 'public';
```

### Backup Data

```sql
-- Export reports as JSON
SELECT jsonb_pretty(jsonb_agg(to_jsonb(r))) 
FROM reports r;

-- Export specific user's data
SELECT jsonb_pretty(jsonb_agg(to_jsonb(r))) 
FROM reports r 
WHERE r.user_id = 'uuid-here';
```

### Clean Old Reports

```sql
-- Archive reports older than 30 days
UPDATE reports 
SET status = 'archived'
WHERE created_at < NOW() - INTERVAL '30 days';

-- Delete reports older than 90 days
DELETE FROM reports 
WHERE created_at < NOW() - INTERVAL '90 days';
```

## Troubleshooting

### Connection Issues

```bash
# Test Supabase URL accessibility
curl -I https://your-project.supabase.co

# Check Python package version
pip show supabase
```

### Migration Issues

```sql
-- Check if tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name IN ('users', 'reports', 'chat_history');

-- Check RLS status
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public';
```

### Performance Issues

```sql
-- Check slow queries
SELECT * FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

## Next Steps

1. ✅ Create `.env` file with credentials
2. ✅ Install supabase-py
3. ✅ Run migration script
4. ✅ Update API routes
5. ✅ Test endpoints with sample data
6. ✅ Set up monitoring/backups
7. ✅ Deploy to production

## Support Resources

- [Supabase Docs](https://supabase.com/docs)
- [Supabase Python Client](https://github.com/supabase/supabase-py)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Async Python Guide](https://docs.python.org/3/library/asyncio.html)
