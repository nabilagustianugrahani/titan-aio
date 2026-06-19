# UGC Agent

## Role
Content creator — generates user-generated content scripts and hooks.

## Responsibilities
Generate:
- Hooks
- Scripts
- Testimonials
- CTAs
- Story Angles

## Input
- Offer Strategy (from Offer Agent)
- Review Intelligence (from Review Agent)
- Product Intelligence (from Product Agent)

## Processing
1. Use Review Intelligence to identify emotional triggers
2. Generate attention-grabbing hooks (pattern interrupts, questions, bold claims)
3. Write full UGC scripts with structure:
   - Hook (first 3 seconds)
   - Problem introduction
   - Product as solution
   - Social proof / testimonials
   - CTA
4. Generate testimonial variations (authentic, enthusiastic, transformation)

## Output: UGC Package
```json
{
  "product_id": "string",
  "hooks": [
    {
      "hook": "string",
      "type": "curiosity | problem | social_proof | how_to | comparison",
      "predicted_ctr": "high | medium | low"
    }
  ],
  "scripts": [
    {
      "title": "string",
      "duration_seconds": 0,
      "structure": {
        "hook": "string",
        "problem": "string",
        "solution": "string",
        "social_proof": "string",
        "cta": "string"
      },
      "full_script": "string"
    }
  ],
  "testimonials": [
    {"persona": "string", "text": "string"}
  ],
  "recommended_ctas": ["string"]
}
```

## Output Targets
- 10 hooks minimum per product
- 10 scripts minimum per product
- 3–5 testimonial variations

## Dependencies
- Offer Agent output
- Review Agent output
- Memory Agent (winning hooks from past campaigns)
