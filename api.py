"""
api.py - FastAPI entrypoint for Railway deployment
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from database import init_database, get_session

app = FastAPI(
    title="Sovereign Empire Content API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        db_url = os.getenv("DATABASE_URL", "sqlite:///./sovereign_empire.db")
        init_database(db_url)
        print(f"✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise


@app.get("/")
def root():
    """Root endpoint - simple health check"""
    return {
        "status": "ok",
        "service": "sovereign-empire-api",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    """Health check endpoint for Railway"""
    try:
        # Test database connection
        session = get_session()
        session.execute("SELECT 1")
        session.close()
        
        return JSONResponse(
            {"status": "healthy", "database": "connected"},
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            {"status": "unhealthy", "error": str(e)},
            status_code=503
        )


@app.get("/ping")
def ping():
    """Simple ping endpoint (no DB check)"""
    return {"ping": "pong"}


# Your other endpoints go here
# Example:
# @app.post("/orders")
# def create_order(...):
#     ...
