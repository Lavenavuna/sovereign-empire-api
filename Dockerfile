FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway injects PORT at runtime. This line just documents it.
EXPOSE 8000

# Run FastAPI on Railway's PORT (or 8000 locally)
CMD ["sh", "-c", "python -c \"import os; print('PORT=', os.getenv('PORT')); print('DATABASE_URL set=', bool(os.getenv('DATABASE_URL')))\" && uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info"]
