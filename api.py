"""
api.py
FastAPI entrypoint (Railway runs: uvicorn api:app)
"""

import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from database import init_database

app = FastAPI(title="Sovereign Empire Content API")


@app.on_event("startup")
def on_startup():
    # Use Railway DATABASE_URL if present, otherwise fallback to SQLite for local dev
    db_url = os.getenv("DATABASE_URL", "sqlite:///./sovereign_empire.db")
    init_database(db_url)


@app.get("/")
def root():
    return {"ok": True, "service": "sovereign-empire-api"}


@app.get("/health")
def health():
    # Keep this endpoint SIMPLE so Railway never 502s from health checks
    return JSONResponse({"status": "ok"}, status_code=200)
