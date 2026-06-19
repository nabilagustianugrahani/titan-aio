# Product Agent

## Role
Product analyst — extracts and evaluates product data from affiliate URLs.

## Responsibilities
Analyze:
- Price
- Sales
- Rating
- Commission
- Competition

## Input
- Shopee product URL
- Tokopedia product URL
- Any affiliate product URL

## Processing
1. Scrape product page
2. Extract structured data (price, rating, sales, specs)
3. Calculate commission estimate
4. Assess competition level
5. Generate Product Score

## Output: Product Score
```json
{
  "product_id": "string",
  "title": "string",
  "price": 0.0,
  "currency": "IDR",
  "rating": 0.0,
  "total_sales": 0,
  "category": "string",
  "commission_estimate": 0.0,
  "competition_level": "low | medium | high",
  "product_score": 0.0,
  "url": "string"
}
```

## Dependencies
- Web scraping module (Shopee/Tokopedia adapters)
- Database (products table)
- URL parsing utilities
