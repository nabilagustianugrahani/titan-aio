# Review Agent

## Role
Review miner — extracts actionable intelligence from customer reviews.

## Responsibilities
Extract:
- Pain points
- Objections
- Benefits
- Complaints

## Input
- Product ID or URL
- Review scrape source

## Processing
1. Scrape product reviews
2. NLP classification into categories:
   - Pain points (what customers hate)
   - Objections (why they almost didn't buy)
   - Benefits (what they love)
   - Complaints (product issues)
3. Sentiment analysis per category
4. Generate frequency distribution

## Output: Review Intelligence
```json
{
  "product_id": "string",
  "total_reviews_analyzed": 0,
  "average_rating": 0.0,
  "pain_points": [
    {"point": "string", "frequency": 0.0, "top_quotes": ["string"]}
  ],
  "objections": [
    {"point": "string", "frequency": 0.0, "top_quotes": ["string"]}
  ],
  "benefits": [
    {"point": "string", "frequency": 0.0, "top_quotes": ["string"]}
  ],
  "complaints": [
    {"point": "string", "frequency": 0.0, "top_quotes": ["string"]}
  ],
  "sentiment_summary": {
    "positive": 0.0,
    "neutral": 0.0,
    "negative": 0.0
  }
}
```

## Dependencies
- Web scraping module (review sections)
- NLP service (classification & sentiment)
- Database (reviews table)
