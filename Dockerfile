FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE 8000

# Start with strong debug + compile check so errors show in Railway logs
CMD ["sh", "-c", "set -x && python -c \"import os; print('PORT=', os.getenv('PORT')); print('DATABASE_URL set=', bool(os.getenv('DATABASE_URL')));\" && python -m py_compile api.py database.py && uvicorn api:app --host 0.0.0.0 --port ${PORT} --log-level debug"]
