# Render Deployment Guide for Growixa API

## Quick Fix Summary

Your deployment failed due to two issues:

### 1. **Database Driver Mismatch** ❌ → ✅
- **Problem**: Render sets `DATABASE_URL` without a driver prefix (`postgresql://...`), which defaults to psycopg2
- **Solution**: Updated `src/growixa_api/db.py` to automatically normalize the URL to use `postgresql+asyncpg://`

### 2. **File Descriptor Exhaustion** ❌ → ✅
- **Problem**: Dockerfile enabled Uvicorn's `--reload` flag on production, causing "too many open files" error
- **Solution**: Updated Dockerfile to disable `--reload` in production (only enable if `RELOAD_ENABLED` env var is set)

---

## Deployment Steps

### Step 1: Push Changes to Repository
```bash
cd /path/to/growixa
git add .
git commit -m "Fix: Database driver and production Uvicorn configuration for Render deployment"
git push origin main  # or your main branch
```

### Step 2: Configure Environment Variables on Render

Go to your Render service dashboard and ensure these environment variables are set:

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `ENVIRONMENT` | ✅ | `production` | Disables debug mode, enables reload check |
| `DATABASE_URL` | ✅ | Provided by Render PostgreSQL | If using Render's managed DB, leave blank and connect via service binding |
| `REDIS_URL` | ✅ | `redis://...` | From Render Redis or external Redis |
| `RABBITMQ_URL` | ✅ | `amqp://...` | From external RabbitMQ service |
| `JWT_SIGNING_KEY` | ✅ | Generate a secure random string | **DO NOT USE DEFAULT** |
| `ENCRYPTION_KEY` | ✅ | Base64-encoded Fernet key | Generate via Python: `from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())` |
| `LOG_LEVEL` | ❌ | `info` | Optional; defaults to "info" |
| `RELOAD_ENABLED` | ❌ | (not set) | **DO NOT SET** — leaving it unset disables --reload in production |

### Step 3: Connect PostgreSQL Database

**Option A: Using Render's Managed PostgreSQL**
1. Create a new PostgreSQL database on Render
2. Add it as a dependency in `render.yaml` (uncomment the `databases` section)
3. Render will automatically inject `DATABASE_URL` as an environment variable

**Option B: Using External PostgreSQL**
1. Set `DATABASE_URL` manually: `postgresql+asyncpg://user:password@host:5432/dbname`

### Step 4: Run Database Migrations (First Deploy Only)

After the API service starts, run migrations via Render's SSH or a background job:

```bash
# Via Render shell (if available on your plan)
cd /app && alembic upgrade head
```

Or create a background job in `render.yaml` (see template below).

### Step 5: Deploy

Push a new commit or manually trigger a redeploy from the Render dashboard:
- Render will automatically detect `render.yaml` and use it for configuration
- Otherwise, update the service settings manually to match `render.yaml`

---

## Advanced: Using render.yaml

If you want fully declarative infrastructure (recommended):

1. Uncomment and customize the sections in `render.yaml`
2. Commit and push: `git push origin main`
3. Render will detect `render.yaml` and auto-configure services

To deploy via `render.yaml`:
```bash
# View what would be created (requires Render CLI)
render deploy --dry-run

# Actually deploy
render deploy
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'psycopg2'"
- ✅ Fixed by the database normalization in `db.py`
- Verify `DATABASE_URL` is now being normalized to `postgresql+asyncpg://`
- Check Render logs: `Logs` tab in the service dashboard

### "Too many open files (os error 24)"
- ✅ Fixed by removing `--reload` from production Dockerfile
- Confirm `RELOAD_ENABLED` env var is NOT set on Render
- Check Render logs for watchfiles errors

### Database connection fails
- Verify `DATABASE_URL` is set correctly in Render environment
- Test connection locally: `psql $DATABASE_URL`
- Check PostgreSQL service is running and accessible
- Ensure credentials and IP allowlisting are correct

### Import errors in uvicorn startup
- Check that all dependencies installed: `pip install -e ".[dev]"`
- Verify `src/growixa_api/` structure matches expectations
- Check PYTHONPATH includes `src/` (should be automatic with editable install)

### Migrations fail
- Run manually: `alembic upgrade head`
- Check database connectivity and permissions
- Review migration files in `apps/api/migrations/versions/`

---

## Environment Variable Security

⚠️ **NEVER commit `.env` files or actual secrets to git**

Generate secure values:
```python
# JWT_SIGNING_KEY (use a strong random value, not the default)
import secrets
print(secrets.token_urlsafe(32))

# ENCRYPTION_KEY (Fernet symmetric key)
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

Set these ONLY in Render's environment variable dashboard, not in code or `render.yaml`.

---

## Health Check Endpoint

Add a simple health check endpoint so Render can monitor your service:

```python
# In src/growixa_api/main.py

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}
```

Then update `render.yaml`:
```yaml
healthCheckPath: /health
```

---

## Performance Tuning for Production

The current Dockerfile runs with `WEB_CONCURRENCY=1` (Render default for limited CPU).

For better throughput on standard/pro plans, update the Uvicorn command:
```bash
# In render.yaml or manually:
# Render sets WEB_CONCURRENCY based on available CPUs; Uvicorn respects it automatically
uvicorn growixa_api.main:app --host 0.0.0.0 --port 8000 --workers $WEB_CONCURRENCY
```

---

## Next Steps

1. ✅ Commit the fixes: `git add . && git commit -m "..."`
2. ✅ Push to repository: `git push origin main`
3. ✅ Set environment variables in Render dashboard
4. ✅ Trigger redeploy and monitor logs
5. ✅ Test the API: `curl https://your-service.onrender.com/health`

---

## Additional Resources

- [Render Docs: Python/FastAPI](https://render.com/docs/deploy-fastapi)
- [Render Docs: render.yaml](https://render.com/docs/render-yaml)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Uvicorn Configuration](https://www.uvicorn.org/)
