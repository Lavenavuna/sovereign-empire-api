FROM python:3.11-slim

WORKDIR /app

# Install deps first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire repo (includes templates/)
COPY . .

# Create any runtime folders you need
RUN mkdir -p my_first_content content_archive

# Railway provides PORT; default to 8000 for local
ENV PORT=8000

# Optional: Railway doesn't require EXPOSE, but it's fine
EXPOSE 8000

# Run with uvicorn (recommended)
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT}"]
