"""
Sovereign Empire Content API - Production Version with Queue
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import json
from datetime import datetime
from inngest import Inngest
from inngest.fast_api import serve
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="Sovereign Empire Content API",
    description="AI-powered content generation with queue system",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Inngest client
inngest_client = Inngest(
    app_id="sovereign-empire",
    event_key=os.environ.get("INNGEST_EVENT_KEY", "local-dev-key"),
    signing_key=os.environ.get("INNGEST_SIGNING_KEY")
)

# Initialize OpenAI
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# In-memory job storage (will be replaced with database in Fix #7)
jobs_db = {}


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


# Content Generation Functions (from create_content.py)
def generate_blog_post(topic: str) -> str:
    """Generate blog post using OpenAI"""
    prompt = f"""Write a comprehensive, engaging blog post about: {topic}

REQUIREMENTS:
- 1000-1200 words
- Start with a POWERFUL hook that makes readers want to keep reading
- Use storytelling and real-world examples
- Include 5-7 actionable takeaways
- SEO-optimized with natural keyword usage
- Write in a conversational, engaging tone
- End with a strong call-to-action
- Use short paragraphs (2-3 sentences max)
- Include subheadings (## format)

Make it so good that readers can't stop reading and want to share it immediately."""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert content writer who creates viral, SEO-optimized content."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    return response.choices[0].message.content


def generate_linkedin_post(blog_content: str, topic: str) -> str:
    """Generate LinkedIn post"""
    prompt = f"""Based on this blog post about '{topic}', create a LinkedIn post.

REQUIREMENTS:
- 150-200 words
- Start with a hook that stops the scroll
- Include 3 key insights from the blog
- Professional but conversational tone
- End with a thought-provoking question
- Use line breaks for readability
- NO hashtags

Blog excerpt: {blog_content[:500]}"""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a LinkedIn content expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )
    return response.choices[0].message.content


def generate_twitter_thread(blog_content: str, topic: str) -> str:
    """Generate Twitter thread"""
    prompt = f"""Based on this blog post about '{topic}', create a Twitter thread.

REQUIREMENTS:
- 5-7 tweets (numbered 1/, 2/, etc.)
- First tweet: Attention-grabbing hook
- Middle tweets: Key insights (one per tweet)
- Last tweet: Call-to-action + "Follow for more"
- Each tweet under 280 characters
- Use simple, punchy language
- Max 1-2 hashtags in last tweet only

Blog excerpt: {blog_content[:500]}"""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a viral Twitter content creator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )
    return response.choices[0].message.content


# Inngest Function - The Worker
@inngest_client.create_function(
    fn_id="generate-content",
    trigger="content/generate",
    retries=2
)
async def generate_content_worker(ctx, step):
    """Background worker that generates content"""
    
    # Get event data
    job_id = ctx.event.data["job_id"]
    topic = ctx.event.data["topic"]
    tenant_id = ctx.event.data["tenant_id"]
    
    try:
        # Update status to processing
        jobs_db[job_id]["status"] = "processing"
        
        # Step 1: Generate blog post
        blog_post = await step.run("generate-blog", lambda: generate_blog_post(topic))
        
        # Step 2: Generate LinkedIn post
        linkedin_post = await step.run(
            "generate-linkedin",
            lambda: generate_linkedin_post(blog_post, topic)
        )
        
        # Step 3: Generate Twitter thread
        twitter_thread = await step.run(
            "generate-twitter",
            lambda: generate_twitter_thread(blog_post, topic)
        )
        
        # Update job with results
        jobs_db[job_id].update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "blog_post": blog_post,
            "linkedin_post": linkedin_post,
            "twitter_thread": twitter_thread
        })
        
        return {"success": True, "job_id": job_id}
        
    except Exception as e:
        # Update job with error
        jobs_db[job_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        })
        raise


# API Endpoints
@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "Sovereign Empire Content API",
        "version": "2.0.0",
        "status": "online",
        "queue": "inngest"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "queue": "inngest"}


@app.post("/generate", response_model=JobResponse)
async def generate_content(request: ContentRequest):
    """
    Queue content generation job
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
    
    # Send event to Inngest (triggers background worker)
    await inngest_client.send({
        "name": "content/generate",
        "data": {
            "job_id": job_id,
            "topic": request.topic,
            "tenant_id": request.tenant_id
        }
    })
    
    return JobResponse(
        success=True,
        job_id=job_id,
        message=f"Content generation queued for: {request.topic}",
        status="queued"
    )


@app.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """
    Check job status and get results
    """
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(**jobs_db[job_id])


@app.get("/jobs")
async def list_jobs():
    """
    List all jobs (for admin/debugging)
    """
    return {
        "total": len(jobs_db),
        "jobs": list(jobs_db.values())
    }


# Mount Inngest serve endpoint
app.mount("/api/inngest", serve(
    client=inngest_client,
    functions=[generate_content_worker]
))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
