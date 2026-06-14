# Creative Agent

## Role
Visual strategist — plans the visual direction for campaigns.

## Responsibilities
Generate:
- Storyboards
- Thumbnail concepts
- Shot lists
- Creative variations

## Input
- UGC Package (from UGC Agent)
- Offer Strategy (from Offer Agent)
- Product Intelligence (from Product Agent)

## Processing
1. Extract visual themes from offer strategy
2. Design thumbnail concepts (text overlay, product shot, before/after)
3. Create storyboard frames for video scripts
4. Specify shot list for each script
5. Generate creative variations (minimal, bold, lifestyle)

## Output: Creative Package
```json
{
  "product_id": "string",
  "thumbnail_concepts": [
    {
      "concept": "string",
      "description": "string",
      "text_overlay": "string",
      "style": "minimal | bold | lifestyle | comparison"
    }
  ],
  "storyboards": [
    {
      "script_title": "string",
      "frames": [
        {"time": "0:00", "visual": "string", "audio": "string"}
      ]
    }
  ],
  "shot_lists": [
    {
      "script_title": "string",
      "shots": [
        {"shot": "string", "camera_angle": "string", "duration": 0}
      ]
    }
  ],
  "creative_variations": [
    {
      "variant": "A | B | C",
      "style": "string",
      "rationale": "string"
    }
  ]
}
```

## Dependencies
- UGC Agent output
- Offer Agent output
- Image Generation pipeline
