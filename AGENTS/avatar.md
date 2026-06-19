# Avatar Agent

## Role
Character designer — creates and maintains AI spokesperson identities.

## Responsibilities
Generate:
- AI spokesperson
- UGC avatars
- Character consistency

## Input
- Brand guidelines (if any)
- Product category
- Target audience profile
- Offer strategy

## Processing
1. Select or generate avatar persona based on audience
2. Generate consistent character across frames
3. Ensure lip-sync and expression compatibility
4. Maintain style consistency across campaign

## Output: Avatar Assets
```json
{
  "avatar_id": "string",
  "persona": {
    "name": "string",
    "age_range": "string",
    "style": "string",
    "vibe": "trustworthy | energetic | authoritative | friendly"
  },
  "character_sheet": {
    "base_look": "string",
    "expressions": ["neutral", "happy", "surprised", "serious"],
    "outfits": ["string"]
  },
  "generation_params": {
    "model": "string",
    "seed_consistency": true
  }
}
```

## Dependencies
- Video Agent (for rendering)
- Database (avatar_profiles table)
- Image Generation pipeline
