FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything (includes templates/)
COPY . .

ENV PORT=8000
EXPOSE 8000

# IMPORTANT: don't run "python api.py" on Railway; run uvicorn
CMD ["sh", "-c", "python -c \"import os; print('PORT=', os.getenv('PORT')); print('DATABASE_URL set=', bool(os.getenv('DATABASE_URL')));\" && uvicorn api:app --host 0.0.0.0 --port ${PORT} --log-level info"]
