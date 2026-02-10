def map_reddit_trust_landscape(business_niche):
    """
    1. Find where buyers ask "is this legit?"
    2. Identify key subreddits where decisions are made
    3. Map competitor presence (or absence)
    4. Document common objections
    """
    return {
        "trust_queries": [
            f"is {business_niche} legit?",
            f"{business_niche} scam?",
            f"reddit {business_niche} review",
            f"should I trust {business_niche}?"
        ],
        "decision_subreddits": [
            f"r/{business_niche}",
            f"r/smallbusiness",
            f"r/entrepreneur", 
            f"r/marketing",
            f"r/technology"
        ],
        "objection_map": {
            "price": "too expensive",
            "quality": "not good enough", 
            "trust": "scam concerns",
            "results": "doesn't work"
        }
    }
