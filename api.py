"""
Sovereign Empire Content API - BULLETPROOF VERSION
Uses direct HTTP calls to OpenAI - works everywhere, no proxy issues
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import os
from datetime import datetime
import json
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="Sovereign Empire Content API",
    description="AI-powered content generation - Bulletproof Edition",
    version="3.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")

# In-memory job storage
jobs_db: Dict = {}


# Request/Response Models
class ContentRequest(BaseModel):
    topic: str
    tenant_id: str = "default"


class JobResponse(BaseModel):
    success: bool
    job_id: str
    message: str
    status: str = "queued"


class JobStatus(BaseModel):
    job_id: str
    status: str
    topic: str
    tenant_id: str
    created_at: str
    completed_at: Optional[str] = None
    blog_post: Optional[str] = None
    linkedin_post: Optional[str] = None
    twitter_thread: Optional[str] = None
    error: Optional[str] = None


# Direct OpenAI API calls (no SDK)
def call_openai(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
    """
    Direct HTTP call to OpenAI API
    No SDK = no proxy issues, works everywhere
    """
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": max_tokens
    }
    
    # Use httpx with no proxy (force direct connection)
    with httpx.Client(timeout=120.0, proxies={}) as client:
        response = client.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]


# Content Generation Functions
def generate_blog_post(topic: str) -> str:
    """Generate blog post"""
    system = "You are an expert content writer who creates viral, SEO-optimized content."
    
    prompt = f"""Write a comprehensive, engaging blog post about: {topic}

REQUIREMENTS:
- 1000-1200 words
- Start with a POWERFUL hook
- Use storytelling and real-world examples
- Include 5-7 actionable takeaways
- SEO-optimized
- Conversational tone
- Strong call-to-action
- Short paragraphs (2-3 sentences max)
- Include subheadings (## format)

Make it so good readers can't stop reading."""
    
    return call_openai(system, prompt, max_tokens=2000)


def generate_linkedin_post(blog_content: str, topic: str) -> str:
    """Generate LinkedIn post"""
    system = "You are a LinkedIn content expert who writes engaging posts."
    
    prompt = f"""Based on this blog about '{topic}', create a LinkedIn post.

REQUIREMENTS:
- 150-200 words
- Scroll-stopping hook
- 3 key insights
- Professional but conversational
- Thought-provoking question
- NO hashtags

Blog excerpt: {blog_content[:500]}"""
    
    return call_openai(system, prompt, max_tokens=300)


def generate_twitter_thread(blog_content: str, topic: str) -> str:
    """Generate Twitter thread"""
    system = "You are a viral Twitter content creator."
    
    prompt = f"""Based on this blog about '{topic}', create a Twitter thread.

REQUIREMENTS:
- 5-7 tweets (numbered 1/, 2/, etc.)
- Attention-grabbing first tweet
- Key insights (one per tweet)
- Last tweet: CTA + "Follow for more"
- Under 280 chars each
- Punchy language
- Max 1-2 hashtags in last tweet

Blog excerpt: {blog_content[:500]}"""
    
    return call_openai(system, prompt, max_tokens=500)


# Background Worker
async def process_content_generation(job_id: str, topic: str, tenant_id: str):
    """Background worker that generates content"""
    
    try:
        # Update status
        jobs_db[job_id]["status"] = "processing"
        
        # Generate blog post
        blog_post = generate_blog_post(topic)
        
        # Generate LinkedIn post
        linkedin_post = generate_linkedin_post(blog_post, topic)
        
        # Generate Twitter thread
        twitter_thread = generate_twitter_thread(blog_post, topic)
        
        # Update job with results
        jobs_db[job_id].update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "blog_post": blog_post,
            "linkedin_post": linkedin_post,
            "twitter_thread": twitter_thread
        })
        
    except Exception as e:
        # Update job with error
        jobs_db[job_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        })


# API Endpoints
@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "Sovereign Empire Content API",
        "version": "3.0.0",
        "status": "online",
        "method": "direct-http"
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


@app.post("/generate", response_model=JobResponse)
async def generate_content(request: ContentRequest, background_tasks: BackgroundTasks):
    """
    Queue content generation
    Returns immediately with job_id
    """
    
    # Generate job ID
    job_id = f"{request.tenant_id}_{int(datetime.utcnow().timestamp())}"
    
    # Create job record
    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "topic": request.topic,
        "tenant_id": request.tenant_id,
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "blog_post": None,
        "linkedin_post": None,
        "twitter_thread": None,
        "error": None
    }
    
    # Add background task
    background_tasks.add_task(
        process_content_generation,
        job_id,
        request.topic,
        request.tenant_id
    )
    
    return JobResponse(
        success=True,
        job_id=job_id,
        message=f"Content generation queued for: {request.topic}",
        status="queued"
    )


@app.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Check job status and get results"""
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(**jobs_db[job_id])


@app.get("/jobs")
async def list_jobs():
    """List all jobs"""
    return {
        "total": len(jobs_db),
        "jobs": list(jobs_db.values())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
