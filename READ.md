# Sovereign Empire Content API - Railway Deployment Guide

## 🚀 Quick Deploy to Railway

### Step 1: Connect GitHub Repository
1. Go to [Railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect the Dockerfile

### Step 2: Add Postgres Database
1. In your Railway project, click "New" → "Database" → "Add PostgreSQL"
2. Railway automatically sets `DATABASE_URL` environment variable

### Step 3: Deploy
1. Railway will automatically build and deploy
2. Your app will be available at: `https://your-app.up.railway.app`

**That's it!** No custom configuration needed.

---

## 🏗️ Project Structure

```
.
├── api.py              # FastAPI application (main entry point)
├── database.py         # SQLAlchemy models and DB setup
├── Dockerfile          # Docker configuration (Railway-optimized)
├── requirements.txt    # Python dependencies
└── .env.example        # Environment variable template
```

---

## 🔧 How This Works (Railway-Specific)

### Port Handling
Railway assigns a random port via the `$PORT` environment variable. Our setup handles this automatically:

```dockerfile
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

- **Production (Railway)**: Uses `$PORT` from Railway
- **Local Dev**: Falls back to port 8000

### Database URL Normalization
Railway provides Postgres URLs as `postgres://...` but SQLAlchemy 2.x requires `postgresql://...`

Our code automatically converts this:
```python
def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url
```

---

## 🧪 Testing Locally

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up environment
```bash
cp .env.example .env
# Edit .env if needed
```

### 3. Run the server
```bash
uvicorn api:app --reload --port 8000
```

### 4. Test endpoints
- Root: http://localhost:8000/
- Health: http://localhost:8000/health
- API Docs: http://localhost:8000/docs

---

## 📊 Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint (simple health check) |
| `/health` | GET | Health check with database connection test |
| `/ping` | GET | Simple ping (no database check) |
| `/docs` | GET | Interactive API documentation |

---

## 🐛 Troubleshooting

### ❌ 502 Bad Gateway
**Cause**: Port mismatch between Railway and your app

**Solution**: This setup handles it automatically, but verify:
1. Dockerfile uses `${PORT:-8000}` (✅ included)
2. No custom start command in Railway settings (let Dockerfile handle it)
3. No hardcoded ports anywhere

**Quick Test**:
```bash
# Visit these URLs after deployment:
https://your-app.up.railway.app/ping
https://your-app.up.railway.app/health
```

### ❌ Database Connection Failed
**Cause**: `DATABASE_URL` not set or incorrect format

**Solution**:
1. Ensure Postgres database is added in Railway
2. Restart the service (Railway sets `DATABASE_URL` automatically)

**Manual Check** (in Railway logs):
```
✅ Database initialized successfully
```

### ❌ Build Failed
**Cause**: Missing dependencies or syntax errors

**Solution**:
1. Check Railway build logs for specific error
2. Test locally first: `docker build -t test .`
3. Ensure all files are committed to Git

---

## 📦 Dependencies Explained

```txt
fastapi==0.109.0           # Web framework
uvicorn[standard]==0.27.0  # ASGI server (production-ready)
SQLAlchemy==2.0.25         # ORM for database
psycopg2-binary==2.9.9     # PostgreSQL adapter
python-dotenv==1.0.0       # Environment variable management
pydantic==2.5.3            # Data validation (used by FastAPI)
```

---

## 🔐 Production Checklist

- [x] Uses Railway's `$PORT` environment variable
- [x] Handles Postgres URL normalization
- [x] Health check endpoint for monitoring
- [x] Connection pooling with `pool_pre_ping`
- [x] Non-root Docker user for security
- [x] Pinned dependency versions
- [x] Proper error handling in health checks

---

## 🎯 Next Steps

1. **Add your business logic** to `api.py`:
   ```python
   @app.post("/orders")
   def create_order(data: OrderData):
       # Your logic here
       pass
   ```

2. **Set up monitoring** in Railway:
   - Railway automatically monitors `/health` endpoint
   - Check "Metrics" tab for performance data

3. **Add environment variables** (if needed):
   - Go to Railway project → Variables
   - Add any API keys, secrets, etc.

---

## 📞 Support

- **Railway Issues**: Check [Railway Docs](https://docs.railway.app)
- **FastAPI Help**: [FastAPI Docs](https://fastapi.tiangolo.com)

---

## ✅ Why This Setup Works

1. **Port Flexibility**: Respects Railway's dynamic port assignment
2. **Database Compatibility**: Auto-converts Railway's Postgres URL format
3. **Health Monitoring**: Multiple health check endpoints for debugging
4. **Production-Ready**: Connection pooling, error handling, security best practices
5. **Zero Config**: Works out of the box on Railway with no custom settings

Deploy and forget! 🚀
