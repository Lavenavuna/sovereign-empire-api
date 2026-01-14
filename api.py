from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {
        "service": "Sovereign Empire API",
        "status": "online"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
