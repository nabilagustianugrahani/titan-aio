"""ML Content Scorer — ML-based content performance prediction."""

from __future__ import annotations

import hashlib
import math
from pydantic import BaseModel, Field


class ContentFeatures(BaseModel):
    hook_strength: float = 0.0
    emotional_impact: float = 0.0
    story_arc: float = 0.0
    cta_effectiveness: float = 0.0
    visual_appeal: float = 0.0
    timing_score: float = 0.0
    platform_fit: float = 0.0
    niche_relevance: float = 0.0


class MLScoreResult(BaseModel):
    score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    features: ContentFeatures
    predicted_ctr: float = 0.0
    predicted_reach: int = 0
    predicted_engagement: float = 0.0
    risk_factors: list[str] = []
    improvement_suggestions: list[str] = []


class MLContentScorer:
    """ML-inspired content scoring using weighted feature analysis."""

    def __init__(self):
        self.weights = {
            "hook_strength": 0.25,
            "emotional_impact": 0.20,
            "story_arc": 0.15,
            "cta_effectiveness": 0.12,
            "visual_appeal": 0.10,
            "timing_score": 0.08,
            "platform_fit": 0.05,
            "niche_relevance": 0.05,
        }
        self.history: list[dict] = []

    def _sigmoid(self, x: float) -> float:
        return 1 / (1 + math.exp(-x))

    async def score(self, content: str, platform: str = "tiktok", niche: str = "general") -> MLScoreResult:
        features = self._extract_features(content, platform, niche)
        weighted_sum = sum(getattr(features, k) * w for k, w in self.weights.items())
        raw_score = self._sigmoid(weighted_sum / 50) * 100
        score = max(0, min(100, int(raw_score)))
        confidence = min(1.0, 0.4 + len(content.split()) / 100)
        ctr = round(min(0.20, 0.01 + score / 500), 3)
        base_reach = {"tiktok": 5000, "instagram": 2000, "youtube": 1000, "twitter": 3000, "facebook": 1500}
        reach = int(base_reach.get(platform, 2000) * (score / 50))
        engagement = round(min(0.25, 0.02 + score / 400), 3)

        risk_factors = []
        if features.hook_strength < 3:
            risk_factors.append("Weak hook — low first-impression impact")
        if features.cta_effectiveness < 2:
            risk_factors.append("Missing or weak call-to-action")
        if features.emotional_impact < 3:
            risk_factors.append("Low emotional resonance")
        if len(content) > 500 and platform == "tiktok":
            risk_factors.append("Content too long for TikTok")

        suggestions = []
        if features.hook_strength < 5:
            suggestions.append("Start with a question or shocking statement")
        if features.cta_effectiveness < 5:
            suggestions.append("Add clear CTA: 'Link di bio!' or 'Check now!'")
        if features.story_arc < 3:
            suggestions.append("Add story structure: problem → solution → result")
        if features.emotional_impact < 5:
            suggestions.append("Use emotional trigger words (gila, amazing, rahasia)")

        result = MLScoreResult(
            score=score, confidence=confidence, features=features,
            predicted_ctr=ctr, predicted_reach=reach, predicted_engagement=engagement,
            risk_factors=risk_factors, improvement_suggestions=suggestions,
        )
        self.history.append({"content": content[:100], "score": score, "platform": platform})
        return result

    def _extract_features(self, content: str, platform: str, niche: str) -> ContentFeatures:
        lower = content.lower()
        words = content.split()
        word_count = len(words)
        hook = " ".join(words[:15]) if words else ""

        hook_score = 0.0
        if "?" in hook or "!" in hook: hook_score += 2
        if any(w in hook.lower() for w in ["you", "kamu", "this", "ini"]): hook_score += 1.5
        if any(w in hook.lower() for w in ["secret", "rahasia", "hack", "trick"]): hook_score += 2
        if any(c.isdigit() for c in hook): hook_score += 1.5
        if len(hook.split()) <= 8: hook_score += 1
        hook_score = min(10, hook_score)

        emotion_words = {"love", "hate", "amazing", "incredible", "shocking", "gila", "terbaik", "terburuk", "obsessed"}
        emotion_count = sum(1 for w in words if w.lower() in emotion_words)
        emotional = min(10, emotion_count * 2 + (2 if "😱" in content or "🔥" in content or "❤️" in content else 0))

        story = 3.0
        if word_count > 50: story += 2
        if any(w in lower for w in ["but then", "until i", "setelah itu", "plot twist"]): story += 3
        if any(w in lower for w in ["first", "then finally", "pertama", "akhirnya"]): story += 2
        story = min(10, story)

        cta = 0.0
        if any(w in lower for w in ["link", "bio", "click", "klik", "order", "beli", "check"]): cta += 5
        if any(w in lower for w in ["now", "sekarang", "today", "hari ini"]): cta += 2
        if "!" in content: cta += 1
        cta = min(10, cta)

        visual = 5.0
        if any(e in content for e in ["📸", "🎬", "🎥", "🖼️"]): visual += 2
        if platform in ("instagram", "tiktok"): visual += 1
        visual = min(10, visual)

        timing = 5.0
        if platform == "tiktok" and word_count <= 50: timing += 2
        if platform == "twitter" and word_count <= 30: timing += 2
        timing = min(10, timing)

        platform_fit = 5.0
        if platform == "tiktok" and word_count <= 60: platform_fit += 2
        if platform == "instagram" and word_count <= 200: platform_fit += 2
        platform_fit = min(10, platform_fit)

        niche_score = 5.0
        niche_words = {"electronics": ["phone", "gadget", "tech"], "fashion": ["style", "fashion", "ootd"], "beauty": ["skincare", "makeup", "beauty"], "food": ["recipe", "food", "cooking"]}
        if niche in niche_words and any(w in lower for w in niche_words[niche]): niche_score += 3
        niche_score = min(10, niche_score)

        return ContentFeatures(
            hook_strength=hook_score, emotional_impact=emotional, story_arc=story,
            cta_effectiveness=cta, visual_appeal=visual, timing_score=timing,
            platform_fit=platform_fit, niche_relevance=niche_score,
        )

    async def batch_score(self, contents: list[dict], platform: str = "tiktok", niche: str = "general") -> list[MLScoreResult]:
        results = []
        for item in contents:
            text = item.get("content", item.get("hook", ""))
            result = await self.score(content=text, platform=platform, niche=niche)
            results.append(result)
        return results
