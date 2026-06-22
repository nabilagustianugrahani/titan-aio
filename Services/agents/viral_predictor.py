"""Viral Prediction Engine — score content virality before publishing."""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


# ── Input / Output Models ──────────────────────────────────────────


class ViralInput(BaseModel):
    """Content to evaluate for virality."""

    hook: str = Field(description="First line / hook of the content")
    script: str = Field(default="", description="Full script body")
    thumbnail_url: Optional[str] = Field(default=None, description="Thumbnail image URL")
    platform: str = Field(default="tiktok", description="Target platform")
    niche: str = Field(default="general", description="Content niche")
    target_audience: str = Field(default="general", description="Target audience description")


class ViralityScore(BaseModel):
    """Virality prediction result."""

    score: int = Field(ge=0, le=100, description="Overall virality score 0-100")
    predicted_reach: int = Field(description="Predicted impressions within 48h")
    predicted_engagement_rate: float = Field(description="Predicted engagement rate %")
    best_posting_time: str = Field(description="Recommended posting time (HH:MM UTC)")
    platform_scores: dict[str, int] = Field(description="Score per platform")
    optimization_tips: list[str] = Field(description="Actionable improvement tips")
    confidence: float = Field(ge=0.0, le=1.0, description="Prediction confidence")
    feature_breakdown: dict[str, float] = Field(description="Per-feature score contribution")


# ── Feature Lexicons ───────────────────────────────────────────────

EMOTIONAL_WORDS = frozenset(
    [
        "love", "hate", "amazing", "incredible", "terrible", "shocking",
        "insane", "crazy", "unbelievable", "mind-blowing", "heartbreaking",
        "urgent", "exclusive", "secret", "hidden", "forbidden", "mistake",
        "danger", "warning", "never", "always", "forever", "ruined",
        "destroyed", "banned", "banned", "scam", "trick", "hack",
        "reveal", "exposed", "truth", "lie", "myth", "reality",
        "free", "viral", "trending", "blowup", "explosive", "epic",
        "legendary", "massive", "tiny", "huge", "giant", "tiny",
        "beautiful", "gorgeous", "stunning", "ugly", "disgusting",
        "hilarious", "funny", "hilarious", "laugh", "cry", "scream",
        "whisper", "screaming", "crying", "laughing", "dying",
        # Indonesian
        "gratis", "gratis", "gila", "ajaib", "mengerikan", "menakjubkan",
        "rahasia", "tersembunyi", "dilarang", "salah", "bahaya",
        "amarah", "sedih", "tertarik", "kecanduan",
    ]
)

POWER_WORDS = frozenset(
    [
        "now", "today", "secret", "proven", "guaranteed", "instant",
        "easy", "simple", "fast", "quick", "results", "money",
        "save", "earn", "discover", "unlock", "transform", "boost",
        "skyrocket", "crush", "dominate", "win", "profit", "income",
        "success", "million", "billion", "first", "best", "top",
        "ultimate", "breakthrough", "revolutionary", "exclusive",
        "limited", "act", "join", "start", "stop", "watch",
        "try", "click", "follow", "share", "tag", "comment",
        # Indonesian
        "sekarang", "hari ini", "rahasia", "terbukti", "dijamin",
        "instan", "mudah", "cepat", "hasil", "uang", "hemat",
        "penghasilan", "sukses", "terbaik", "eksklusif", "terbatas",
    ]
)

CURIOUSITY_TRIGGERS = frozenset(
    [
        "what", "why", "how", "when", "where", "who",
        "did you know", "can you believe", "imagine if",
        "what if", "guess what", "you won't believe",
        "wait for it", "watch until the end", "stay tuned",
        "spoiler", "plot twist", "but then", "the truth is",
        "nobody tells you", "they don't want you to know",
        # Indonesian
        "apa", "mengapa", "bagaimana", "kapan", "dimana", "siapa",
        "tahukah kamu", "bisa kamu bayangkan", "tebak",
        "tonton sampai habis", "jangan skip", "yang terjadi selanjutnya",
    ]
)

NEGATIVE_EMOTION = frozenset(
    [
        "hate", "terrible", "worst", "never", "don't", "stop",
        "banned", "scam", "danger", "warning", "mistake", "wrong",
        "ugly", "disgusting", "horrible", "awful", "pathetic",
        "ruined", "destroyed", "lost", "fail", "failure", "broke",
        "debts", "poor", "struggle", "pain", "hurt", "suffer",
    ]
)

# ── Platform configs ───────────────────────────────────────────────

PLATFORM_CONFIGS: dict[str, dict[str, float]] = {
    "tiktok": {
        "max_chars": 300,
        "optimal_hook_len": (15, 45),
        "ideal_video_len": (15, 60),
        "emoji_bonus": 1.08,
        "hashtag_bonus": 1.05,
        "avg_reach": 10000,
        "base_engagement": 5.2,
        "cta_weight": 0.9,
    },
    "instagram": {
        "max_chars": 2200,
        "optimal_hook_len": (10, 40),
        "ideal_video_len": (15, 90),
        "emoji_bonus": 1.12,
        "hashtag_bonus": 1.10,
        "avg_reach": 8000,
        "base_engagement": 3.8,
        "cta_weight": 1.0,
    },
    "facebook": {
        "max_chars": 63206,
        "optimal_hook_len": (15, 60),
        "ideal_video_len": (30, 180),
        "emoji_bonus": 1.04,
        "hashtag_bonus": 1.02,
        "avg_reach": 5000,
        "base_engagement": 2.5,
        "cta_weight": 1.1,
    },
    "youtube": {
        "max_chars": 5000,
        "optimal_hook_len": (20, 70),
        "ideal_video_len": (30, 300),
        "emoji_bonus": 1.02,
        "hashtag_bonus": 1.01,
        "avg_reach": 3000,
        "base_engagement": 4.0,
        "cta_weight": 1.2,
    },
    "twitter": {
        "max_chars": 280,
        "optimal_hook_len": (10, 40),
        "ideal_video_len": (15, 60),
        "emoji_bonus": 1.06,
        "hashtag_bonus": 1.04,
        "avg_reach": 6000,
        "base_engagement": 1.8,
        "cta_weight": 0.8,
    },
}

# Niche-specific multipliers
NICHE_MULTIPLIERS: dict[str, float] = {
    "electronics": 0.95,
    "fashion": 1.10,
    "beauty": 1.15,
    "food": 1.12,
    "fitness": 1.08,
    "tech": 1.05,
    "finance": 0.90,
    "education": 0.85,
    "entertainment": 1.20,
    "umum": 1.0,
    "general": 1.0,
}

# Audience age adjustments
AUDIENCE_MULTIPLIERS: dict[str, float] = {
    "gen_z": 1.15,
    "millennials": 1.05,
    "gen_x": 0.90,
    "boomers": 0.80,
    "general": 1.0,
}

# ── Scoring Weights ────────────────────────────────────────────────

FEATURE_WEIGHTS: dict[str, float] = {
    "hook_strength": 15.0,
    "emotional_impact": 12.0,
    "curiosity_gap": 12.0,
    "power_words": 8.0,
    "hook_length": 6.0,
    "question_marks": 5.0,
    "numbers_stats": 5.0,
    "emoji_usage": 4.0,
    "exclamation_energy": 3.0,
    "story_arc": 8.0,
    "cta_placement": 7.0,
    "hashtag_strategy": 4.0,
    "has_content_body": 5.0,
    "readability": 3.0,
    "urgency": 5.0,
    "social_proof": 3.0,
    "controversy_potential": 3.0,
    "length_optimization": 3.0,
    "niche_relevance": 3.0,
    "audience_match": 2.0,
    "first_person": 2.0,
    "punctuation_energy": 1.0,
}


# ── Feature Extraction ─────────────────────────────────────────────


def _count_words(text: str) -> int:
    return len(text.split())


def _count_chars(text: str) -> int:
    return len(text)


def _count_sentences(text: str) -> int:
    parts = re.split(r"[.!?]+", text)
    return max(len([p for p in parts if p.strip()]), 1)


def _average_word_length(text: str) -> float:
    words = text.split()
    if not words:
        return 0.0
    return sum(len(w) for w in words) / len(words)


def _count_pattern(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, re.IGNORECASE))


def _contains_any(text: str, vocab: frozenset[str]) -> int:
    text_lower = text.lower()
    return sum(1 for w in vocab if w in text_lower)


def _extract_numbers(text: str) -> list[str]:
    return re.findall(r"\b\d[\d,\.]*%?\b", text)


def _has_story_markers(text: str) -> float:
    """Detect story-arc markers: transition words, before/after, etc."""
    markers = [
        "so ", "then ", "but ", "until ", "after ", "before ",
        "suddenly", "finally", "meanwhile", "next", "first",
        "later", "eventually", "last", "starting", "began",
        "jadi ", "lalu ", "tapi ", "sampai ", "setelah ", "sebelum ",
        "tiba-tiba", "akhirnya", "selanjutnya", "pertama",
    ]
    text_lower = text.lower()
    hits = sum(1 for m in markers if m in text_lower)
    return min(hits / 3.0, 1.0)


def _cta_score(text: str, platform_cfg: dict[str, float]) -> float:
    """Score call-to-action presence and placement."""
    cta_phrases = [
        "link in bio", "link di bio", "order sekarang", "buy now",
        "check it out", "click the link", "follow for more",
        "comment below", "share this", "tag someone", "send to",
        "shop now", "get yours", "swipe up", "tap the link",
        "join now", "sign up", "subscribe", "like and follow",
        "save this", "bookmark this", "send this to",
    ]
    text_lower = text.lower()
    hits = sum(1 for p in cta_phrases if p in text_lower)

    # Check CTA placement (end is better)
    words = text_lower.split()
    if len(words) > 5:
        last_20pct = " ".join(words[int(len(words) * 0.8) :])
        end_bonus = sum(0.3 for p in cta_phrases if p in last_20pct)
    else:
        end_bonus = 0.0

    raw = min((hits * 0.4 + end_bonus) * platform_cfg.get("cta_weight", 1.0), 1.0)
    return raw


def _readability_score(text: str) -> float:
    """Simple readability: shorter avg words + shorter sentences = more readable."""
    awl = _average_word_length(text)
    scount = _count_sentences(text)
    wcount = _count_words(text)
    if wcount == 0:
        return 0.0
    avg_sentence_len = wcount / scount

    # Sweet spot: avg word len 4-6, sentence len 8-20 words
    word_score = 1.0 - min(abs(awl - 5.0) / 4.0, 1.0)
    sent_score = 1.0 - min(abs(avg_sentence_len - 14.0) / 20.0, 1.0)
    return (word_score * 0.5 + sent_score * 0.5)


def _urgency_score(text: str) -> float:
    """Detect urgency: time-sensitive words, caps, exclamation."""
    urgency_words = [
        "now", "today", "limited", "hurry", "last chance", "ending soon",
        "only", "remaining", "final", "expire", "deadline",
        "sekarang", "hari ini", "terbatas", "buruan", "terakhir",
    ]
    text_lower = text.lower()
    hits = sum(1 for w in urgency_words if w in text_lower)
    excl_count = text.count("!")
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)

    score = min(hits * 0.25 + excl_count * 0.05 + caps_ratio * 0.5, 1.0)
    return score


def _social_proof_score(text: str) -> float:
    """Detect social proof: numbers, testimonials, ratings."""
    proof_patterns = [
        r"\d+\s*(rb|k|m|jt|million|billion|orang|people|users)",
        r"stars?|[★⭐]",
        r"review[s]?",
        r"testimonial",
        r"as seen",
        r"featured",
        r"viral",
        r"trending",
        r"\d+[\+]",  # e.g., 10k+
        r"sold\s+\d+",
        r"terjual\s+\d+",
    ]
    text_lower = text.lower()
    hits = sum(1 for p in proof_patterns if re.search(p, text_lower))
    return min(hits * 0.3, 1.0)


def _controversy_score(text: str) -> float:
    """Detect controversy potential: polarizing language, hot takes."""
    controversy_triggers = [
        "unpopular opinion", "controversial", "hot take",
        "wrong about", "everyone is lying", "they don't want",
        "mainstream media", "wake up", "open your eyes",
        "truth they hid", "exposed", "scam",
        "pendapat kontroversial", "semua orang salah",
    ]
    text_lower = text.lower()
    hits = sum(1 for t in controversy_triggers if t in text_lower)

    neg_count = _contains_any(text, NEGATIVE_EMOTION)
    return min(hits * 0.3 + neg_count * 0.05, 1.0)


def _emoji_density(text: str) -> float:
    """Score emoji usage (0.5-2 per 100 chars is ideal)."""
    emoji_count = len(re.findall(r"[\U0001F300-\U0001F9FF☀-⛿✀-➿]", text))
    char_count = max(len(text), 1)
    density = (emoji_count / char_count) * 100
    # Ideal: 0.5-2 emojis per 100 chars
    if 0.3 <= density <= 3.0:
        return 1.0
    elif density < 0.3:
        return density / 0.3 * 0.6
    else:
        return max(1.0 - (density - 3.0) / 5.0, 0.2)


# ── Core Scoring ───────────────────────────────────────────────────


def _score_features(hook: str, script: str, platform: str, niche: str, target_audience: str) -> dict[str, float]:
    """Extract and score all features. Returns feature name -> raw score [0,1]."""
    full_text = f"{hook} {script}".strip()
    hook_lower = hook.lower()
    platform_cfg = PLATFORM_CONFIGS.get(platform, PLATFORM_CONFIGS["tiktok"])

    features: dict[str, float] = {}

    # 1. Hook strength: short, punchy, emotionally loaded
    hook_words = _count_words(hook)
    hook_min, hook_max = platform_cfg["optimal_hook_len"]
    if hook_min <= hook_words <= hook_max:
        features["hook_strength"] = 0.9 + (0.1 if hook_lower[0].isupper() else 0.0)
    elif hook_words < hook_min:
        features["hook_strength"] = max(0.3, hook_words / hook_min * 0.8)
    else:
        features["hook_strength"] = max(0.3, 1.0 - (hook_words - hook_max) / 30.0)

    # 2. Emotional impact
    emo_count = _contains_any(full_text, EMOTIONAL_WORDS)
    features["emotional_impact"] = min(emo_count * 0.2, 1.0)

    # 3. Curiosity gap
    curious_count = _contains_any(full_text, CURIOUSITY_TRIGGERS)
    features["curiosity_gap"] = min(curious_count * 0.25, 1.0)

    # 4. Power words
    pw_count = _contains_any(full_text, POWER_WORDS)
    features["power_words"] = min(pw_count * 0.15, 1.0)

    # 5. Hook length optimization
    hook_char_len = _count_chars(hook)
    if 40 <= hook_char_len <= 120:
        features["hook_length"] = 0.9
    elif hook_char_len < 40:
        features["hook_length"] = max(0.3, hook_char_len / 40.0 * 0.9)
    else:
        features["hook_length"] = max(0.2, 1.0 - (hook_char_len - 120) / 200.0)

    # 6. Question marks (hook with question = +engagement)
    q_count = hook.count("?")
    features["question_marks"] = min(q_count * 0.35, 1.0) if q_count > 0 else 0.0

    # 7. Numbers and statistics
    nums = _extract_numbers(full_text)
    features["numbers_stats"] = min(len(nums) * 0.25, 1.0)

    # 8. Emoji usage
    features["emoji_usage"] = _emoji_density(full_text)

    # 9. Exclamation energy
    excl = full_text.count("!")
    features["exclamation_energy"] = min(excl * 0.15, 1.0) if excl > 0 else 0.0

    # 10. Story arc
    features["story_arc"] = _has_story_markers(full_text)

    # 11. CTA placement
    features["cta_placement"] = _cta_score(full_text, platform_cfg)

    # 12. Hashtag strategy
    hashtags = re.findall(r"#\w+", full_text)
    if 3 <= len(hashtags) <= 8:
        features["hashtag_strategy"] = 0.9
    elif len(hashtags) > 0:
        features["hashtag_strategy"] = min(len(hashtags) / 5.0, 0.8)
    else:
        features["hashtag_strategy"] = 0.0

    # 13. Has content body (script present)
    features["has_content_body"] = 1.0 if len(script.strip()) > 20 else 0.0

    # 14. Readability
    features["readability"] = _readability_score(full_text)

    # 15. Urgency
    features["urgency"] = _urgency_score(full_text)

    # 16. Social proof
    features["social_proof"] = _social_proof_score(full_text)

    # 17. Controversy potential
    features["controversy_potential"] = _controversy_score(full_text)

    # 18. Length optimization (full content)
    word_count = _count_words(full_text)
    if 20 <= word_count <= 200:
        features["length_optimization"] = 0.85
    elif word_count < 20:
        features["length_optimization"] = max(0.2, word_count / 20.0 * 0.85)
    else:
        features["length_optimization"] = max(0.3, 1.0 - (word_count - 200) / 400.0)

    # 19. Niche relevance
    features["niche_relevance"] = NICHE_MULTIPLIERS.get(niche.lower(), 1.0)

    # 20. Audience match
    features["audience_match"] = AUDIENCE_MULTIPLIERS.get(target_audience.lower(), 1.0)

    # 21. First person pronouns (authenticity)
    first_person_patterns = r"\b(i |me |my |mine |i'm |i've |i'd |i'll |aku |gue |gw |gua |saya )\b"
    fp_count = len(re.findall(first_person_patterns, full_text.lower()))
    features["first_person"] = min(fp_count * 0.15, 1.0)

    # 22. Punctuation energy (variety of !?...)
    punct_variety = len(set(re.findall(r"[!?…\-]", full_text)))
    features["punctuation_energy"] = min(punct_variety * 0.2, 1.0)

    return features


def _weighted_score(features: dict[str, float]) -> float:
    """Compute weighted 0-100 score."""
    total_weight = 0.0
    weighted_sum = 0.0
    for feat, val in features.items():
        w = FEATURE_WEIGHTS.get(feat, 1.0)
        weighted_sum += val * w
        total_weight += w
    if total_weight == 0:
        return 0.0
    return (weighted_sum / total_weight) * 100.0


def _predict_reach(score: float, platform: str, niche: str, audience: str) -> int:
    """Predict 48h reach based on virality score."""
    cfg = PLATFORM_CONFIGS.get(platform, PLATFORM_CONFIGS["tiktok"])
    base = cfg["avg_reach"]

    # Score multiplier: 0→0.1x, 50→1x, 100→10x
    score_mult = 0.1 + (score / 100.0) ** 2 * 9.9

    niche_mult = NICHE_MULTIPLIERS.get(niche.lower(), 1.0)
    aud_mult = AUDIENCE_MULTIPLIERS.get(audience.lower(), 1.0)

    return int(base * score_mult * niche_mult * aud_mult)


def _predict_engagement_rate(score: float, platform: str) -> float:
    """Predict engagement rate % based on virality score."""
    cfg = PLATFORM_CONFIGS.get(platform, PLATFORM_CONFIGS["tiktok"])
    base = cfg["base_engagement"]

    # Higher score → exponentially higher engagement
    mult = 0.2 + (score / 100.0) ** 1.5 * 3.0
    return round(base * mult, 2)


def _compute_confidence(features: dict[str, float], hook: str, script: str) -> float:
    """Confidence based on data completeness and feature richness."""
    completeness = 0.0
    if len(hook.strip()) > 0:
        completeness += 0.3
    if len(script.strip()) > 20:
        completeness += 0.3
    active_features = sum(1 for v in features.values() if v > 0.1)
    feature_richness = min(active_features / len(FEATURE_WEIGHTS), 1.0) * 0.4
    return round(min(completeness + feature_richness, 1.0), 2)


# ── Optimal Posting Times ──────────────────────────────────────────

# Platform-specific peak hours (UTC)
PLATFORM_PEAK_HOURS: dict[str, list[int]] = {
    "tiktok": [7, 8, 12, 13, 19, 20, 21],
    "instagram": [6, 7, 12, 13, 17, 18, 19, 20],
    "facebook": [9, 10, 12, 13, 15, 16],
    "youtube": [12, 14, 15, 17, 18, 19, 20, 21],
    "twitter": [8, 9, 12, 13, 17, 18],
}


def _best_posting_time(platform: str, niche: str) -> str:
    """Return best posting time as HH:MM UTC string."""
    hours = PLATFORM_PEAK_HOURS.get(platform, PLATFORM_PEAK_HOURS["tiktok"])

    # Adjust by niche (entertainment peaks evening, finance peaks morning)
    niche_offsets = {
        "entertainment": 2,
        "food": 1,
        "fitness": -1,
        "finance": -2,
        "tech": 0,
        "beauty": 1,
        "fashion": 1,
    }
    offset = niche_offsets.get(niche.lower(), 0)

    adjusted = [(h + offset) % 24 for h in hours]
    peak_hour = max(set(adjusted), key=adjusted.count)

    # Pick minute to avoid exact-hour posting congestion
    minute = (hash(niche) % 4) * 15  # 0, 15, 30, 45
    return f"{peak_hour:02d}:{minute:02d}"


# ── Optimization Tips ──────────────────────────────────────────────


def _generate_tips(features: dict[str, float], platform: str, score: float) -> list[str]:
    """Generate actionable optimization tips based on weak features."""
    tips: list[str] = []

    if features.get("hook_strength", 0) < 0.5:
        tips.append("Shorten your hook to 15-45 words. Lead with a bold claim or question.")

    if features.get("emotional_impact", 0) < 0.3:
        tips.append("Add emotional power words (love, hate, shocking, insane, never).")

    if features.get("curiosity_gap", 0) < 0.3:
        tips.append("Create a curiosity gap: 'Wait until you see...' or 'Nobody talks about...'")

    if features.get("power_words", 0) < 0.3:
        tips.append("Include action words: now, secret, proven, free, instant, discover.")

    if features.get("question_marks", 0) < 0.1:
        tips.append("Add a question in your hook to boost engagement.")

    if features.get("numbers_stats", 0) < 0.2:
        tips.append("Add specific numbers: '3 reasons', '50% off', '1M+ sold'.")

    if features.get("emoji_usage", 0) < 0.4:
        tips.append("Add 2-3 relevant emojis for visual appeal (not too many).")

    if features.get("story_arc", 0) < 0.2 and len(features) > 0:
        tips.append("Add story elements: 'So I tried this...', 'But then...', 'And here's the twist...'")

    if features.get("cta_placement", 0) < 0.3:
        tips.append("Add a clear CTA at the end: 'Link in bio', 'Follow for more', 'Comment your answer'.")

    if features.get("hashtag_strategy", 0) < 0.2:
        tips.append("Add 3-5 relevant hashtags for discoverability.")

    if features.get("urgency", 0) < 0.2:
        tips.append("Add urgency: 'Limited time', 'Only today', 'Last chance'.")

    if features.get("social_proof", 0) < 0.2:
        tips.append("Add social proof: '10k+ sold', '5-star rated', 'As seen on...'.")

    if features.get("controversy_potential", 0) < 0.1 and score < 60:
        tips.append("Consider a controversial angle or hot take to spark discussion.")

    if features.get("first_person", 0) < 0.1:
        tips.append("Use first-person language ('I tried...', 'My experience') for authenticity.")

    if features.get("readability", 0) < 0.5:
        tips.append("Simplify language: shorter words, shorter sentences. Keep it scannable.")

    # Platform-specific tips
    if platform == "tiktok" and features.get("hook_strength", 0) < 0.6:
        tips.append("TikTok: Hook must land in first 1-2 seconds. Start mid-action or mid-sentence.")
    elif platform == "instagram" and features.get("emoji_usage", 0) < 0.3:
        tips.append("Instagram: Use line breaks and emojis for scannable captions.")
    elif platform == "facebook" and features.get("length_optimization", 0) < 0.4:
        tips.append("Facebook: Longer stories work. Build narrative before CTA.")
    elif platform == "youtube" and features.get("hook_strength", 0) < 0.5:
        tips.append("YouTube: Front-load the value. Say what they'll learn in first 5 seconds.")

    if score >= 80:
        tips.insert(0, "Strong viral potential. Consider scheduling for peak hours and cross-posting.")
    elif score >= 60:
        tips.insert(0, "Good potential. Apply tips below to push into viral range.")
    elif score >= 40:
        tips.insert(0, "Moderate potential. Significant improvements needed for viral reach.")
    else:
        tips.insert(0, "Low viral potential. Consider rewriting the hook completely.")

    return tips[:8]


# ── Per-Platform Scores ────────────────────────────────────────────


def _platform_scores(features: dict[str, float], overall: float) -> dict[str, int]:
    """Generate per-platform virality scores."""
    result: dict[str, int] = {}
    for pname, pcfg in PLATFORM_CONFIGS.items():
        platform_adj = 1.0
        # Hooks are weighted differently per platform
        if pname == "tiktok":
            platform_adj *= (features.get("hook_strength", 0.5) * 1.3 + 0.7)
        elif pname == "instagram":
            platform_adj *= (features.get("emoji_usage", 0.5) * 1.2 + 0.8)
        elif pname == "facebook":
            platform_adj *= (features.get("story_arc", 0.5) * 1.2 + 0.8)
        elif pname == "youtube":
            platform_adj *= (features.get("readability", 0.5) * 1.1 + 0.9)
        elif pname == "twitter":
            platform_adj *= (features.get("hook_strength", 0.5) * 1.1 + features.get("controversy_potential", 0.3) * 0.5 + 0.5)

        result[pname] = min(max(int(overall * platform_adj), 0), 100)
    return result


# ── Main Entry Point ───────────────────────────────────────────────


class ViralPredictor:
    """Score content virality before publishing. No ML dependencies."""

    async def predict(self, input_data: ViralInput) -> ViralityScore:
        """Analyze content and return virality prediction."""
        features = _score_features(
            hook=input_data.hook,
            script=input_data.script,
            platform=input_data.platform,
            niche=input_data.niche,
            target_audience=input_data.target_audience,
        )

        overall = _weighted_score(features)
        score = min(max(int(overall), 0), 100)

        reach = _predict_reach(score, input_data.platform, input_data.niche, input_data.target_audience)
        eng_rate = _predict_engagement_rate(score, input_data.platform)
        best_time = _best_posting_time(input_data.platform, input_data.niche)
        p_scores = _platform_scores(features, overall)
        tips = _generate_tips(features, input_data.platform, score)
        confidence = _compute_confidence(features, input_data.hook, input_data.script)

        # Normalize feature breakdown to 0-1 scale for output
        feature_breakdown = {k: round(v, 3) for k, v in features.items()}

        return ViralityScore(
            score=score,
            predicted_reach=reach,
            predicted_engagement_rate=eng_rate,
            best_posting_time=best_time,
            platform_scores=p_scores,
            optimization_tips=tips,
            confidence=confidence,
            feature_breakdown=feature_breakdown,
        )
