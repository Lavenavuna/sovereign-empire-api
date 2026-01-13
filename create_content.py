"""
Sovereign Empire Content Generator
Creates SEO-optimized, engaging content with powerful hooks
"""

import sys
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_blog_post(topic):
    """Generate a compelling, SEO-optimized blog post"""
    
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

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert content writer who creates viral, SEO-optimized content that hooks readers from the first sentence."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    
    return response.choices[0].message.content


def generate_linkedin_post(blog_content, topic):
    """Generate an engaging LinkedIn post"""
    
    prompt = f"""Based on this blog post about '{topic}', create a LinkedIn post.

REQUIREMENTS:
- 150-200 words
- Start with a hook that stops the scroll
- Include 3 key insights from the blog
- Professional but conversational tone
- End with a thought-provoking question
- Use line breaks for readability
- NO hashtags (they look spammy)

Make it engaging enough that people comment and share.

Blog excerpt:
{blog_content[:500]}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a LinkedIn content expert who writes posts that generate high engagement."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )
    
    return response.choices[0].message.content


def generate_twitter_thread(blog_content, topic):
    """Generate a viral-worthy Twitter thread"""
    
    prompt = f"""Based on this blog post about '{topic}', create a Twitter thread.

REQUIREMENTS:
- 5-7 tweets (numbered 1/, 2/, etc.)
- First tweet: Attention-grabbing hook
- Middle tweets: Key insights (one per tweet)
- Last tweet: Call-to-action + "Follow for more"
- Each tweet under 280 characters
- Use simple, punchy language
- NO hashtags in every tweet (max 1-2 in last tweet)

Make it thread-worthy - something people want to retweet.

Blog excerpt:
{blog_content[:500]}"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a viral Twitter content creator who writes threads that get thousands of retweets."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    return response.choices[0].message.content


def save_content(blog_post, linkedin_post, twitter_thread):
    """Save all content to files"""
    
    # Create output folder if it doesn't exist
    os.makedirs("my_first_content", exist_ok=True)
    
    # Save blog post
    with open("my_first_content/blog_post.md", "w", encoding="utf-8") as f:
        f.write(blog_post)
    
    # Save LinkedIn post
    with open("my_first_content/linkedin_post", "w", encoding="utf-8") as f:
        f.write(linkedin_post)
    
    # Save Twitter thread
    with open("my_first_content/twitter_thread", "w", encoding="utf-8") as f:
        f.write(twitter_thread)
    
    print("Content saved successfully!")
    print(f"- Blog post: {len(blog_post)} characters")
    print(f"- LinkedIn post: {len(linkedin_post)} characters")
    print(f"- Twitter thread: {len(twitter_thread)} characters")


def main():
    """Main execution"""
    
    # Get topic from command line
    if len(sys.argv) < 2:
        print("Error: Please provide a topic")
        print("Usage: python create_content.py 'Your Topic Here'")
        sys.exit(1)
    
    topic = sys.argv[1]
    
    print(f"Generating content for: {topic}")
    print("This will take 30-60 seconds...")
    print()
    
    # Step 1: Generate blog post
    print("Step 1: Creating blog post...")
    blog_post = generate_blog_post(topic)
    print("Blog post created!")
    
    # Step 2: Generate LinkedIn post
    print("Step 2: Creating LinkedIn post...")
    linkedin_post = generate_linkedin_post(blog_post, topic)
    print("LinkedIn post created!")
    
    # Step 3: Generate Twitter thread
    print("Step 3: Creating Twitter thread...")
    twitter_thread = generate_twitter_thread(blog_post, topic)
    print("Twitter thread created!")
    
    # Step 4: Save everything
    print("Step 4: Saving content...")
    save_content(blog_post, linkedin_post, twitter_thread)
    
    print()
    print("Content generation complete!")
    print("Check the 'my_first_content' folder for your files.")


if __name__ == "__main__":
    main()
