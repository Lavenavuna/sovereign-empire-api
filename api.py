"""
Production API for Sovereign Empire Content Automation
Wraps your working create_content.py script
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import subprocess
import os
from datetime import datetime
import shutil

app = FastAPI(
    title="Sovereign Empire Content API",
    description="AI-powered content generation system",
    version="1.0.0"
)

# CORS - allows front-end to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request model
class ContentRequest(BaseModel):
    topic: str
    tenant_id: str

# Response model
class ContentResponse(BaseModel):
    success: bool
    job_id: str
    message: str
    blog_post: Optional[str] = None
    linkedin_post: Optional[str] = None
    twitter_thread: Optional[str] = None

@app.get("/")
def root():
    return {
        "service": "Sovereign Empire Content API",
        "version": "1.0.0",
        "status": "online"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "system": "operational"
    }

@app.post("/generate", response_model=ContentResponse)
async def generate_content(request: ContentRequest):
    """
    Generate content using your working create_content.py script
    """
    try:
        job_id = f"{request.tenant_id}_{int(datetime.now().timestamp())}"
        
        print(f"🚀 Generating content for: {request.topic}")
        print(f"👤 Tenant: {request.tenant_id}")
        
        # Run your actual working script
        result = subprocess.run(
            ["python", "create_content.py", request.topic],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes
            encoding='utf-8',
            errors='ignore'
        )
        
        if result.returncode != 0:
            print(f"❌ Script failed: {result.stderr}")
            raise Exception(f"Generation failed: {result.stderr}")
        
        print(f"✅ Script completed successfully")
        
        # Read the generated files
        content_folder = "my_first_content"
        
        # Read blog post
        blog_post = None
        blog_path = os.path.join(content_folder, "blog_post.md")
        if os.path.exists(blog_path):
            with open(blog_path, 'r', encoding='utf-8') as f:
                blog_post = f.read()
            print(f"📝 Blog post: {len(blog_post)} characters")
        
        # Read LinkedIn post
        linkedin_post = None
        linkedin_path = os.path.join(content_folder, "linkedin_post")
        if os.path.exists(linkedin_path):
            with open(linkedin_path, 'r', encoding='utf-8') as f:
                linkedin_post = f.read()
            print(f"💼 LinkedIn post: {len(linkedin_post)} characters")
        
        # Read Twitter thread
        twitter_thread = None
        twitter_path = os.path.join(content_folder, "twitter_thread")
        if os.path.exists(twitter_path):
            with open(twitter_path, 'r', encoding='utf-8') as f:
                twitter_thread = f.read()
            print(f"🐦 Twitter thread: {len(twitter_thread)} characters")
        
        # Archive this content (save with tenant_id and timestamp)
        archive_folder = f"content_archive/{request.tenant_id}/{job_id}"
        os.makedirs(archive_folder, exist_ok=True)
        
        # Copy files to archive
        if os.path.exists(blog_path):
            shutil.copy(blog_path, archive_folder)
        if os.path.exists(linkedin_path):
            shutil.copy(linkedin_path, archive_folder)
        if os.path.exists(twitter_path):
            shutil.copy(twitter_path, archive_folder)
        
        print(f"📦 Archived to: {archive_folder}")
        
        return ContentResponse(
            success=True,
            job_id=job_id,
            message=f"Content generated successfully for: {request.topic}",
            blog_post=blog_post,
            linkedin_post=linkedin_post,
            twitter_thread=twitter_thread
        )
        
    except subprocess.TimeoutExpired:
        print(f"⏱️ Timeout after 5 minutes")
        raise HTTPException(status_code=408, detail="Generation timed out after 5 minutes")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test")
async def test_api(request: ContentRequest):
    """
    Test endpoint - doesn't actually generate content
    Use this to verify API is working without using AI credits
    """
    return {
        "success": True,
        "message": f"API is working. Would generate content for: {request.topic}",
        "tenant_id": request.tenant_id,
        "note": "This is a test - no actual content generated"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Sovereign Empire API...")
    print("📍 API running at: http://localhost:8000")
    print("📚 API docs at: http://localhost:8000/docs")
    print("✨ Ready to generate content!")
    uvicorn.run(app, host="0.0.0.0", port=8000)
