"""Unified LLM service for TITAN AIO.
Uses Google AI (Gemini) API directly — no 9router proxy needed.
Works from anywhere: HF Space, VPS, local.
"""

from __future__ import annotations

import json
import logging
import os

import httpx

logger = logging.getLogger(__name__)

# Config — dual route: 9router proxy (local VPS) + Google AI API direct fallback
R9_BASE = "http://127.0.0.1:20128/v1/chat/completions"
R9_TOKEN = os.environ.get("ANTHROPIC_AUTH_TOKEN", os.environ.get("R9_AUTH_TOKEN", ""))
GA_API_KEY = os.environ.get("GOOGLE_AI_API_KEY", "")
GA_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Model mapping: 9router model → Google AI API model
# 2.5 Pro = smarter, closer to Opus 4.8 quality
MODEL_CREATIVE = "gc/gemini-2.5-pro"          # hooks, scripts, offers (~Opus 4.8 quality)
MODEL_FAST = "gc/gemini-2.5-flash"            # fast tasks
MODEL_FALLBACK = "gemini-2.5-pro"             # Google AI API fallback

DEFAULT_TIMEOUT = 60.0


async def _call_9router(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """Call LLM via local 9router proxy."""
    headers = {"Content-Type": "application/json"}
    if R9_TOKEN:
        headers["Authorization"] = f"Bearer {R9_TOKEN}"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.post(R9_BASE, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning("9router call failed (model=%s): %s", model, e)
        return ""


async def _call_google_ai(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """Call Google AI Gemini API directly as fallback."""
    if not GA_API_KEY:
        return ""
    # Convert gc/ model name to Google AI model name
    ga_model = model.replace("gc/gemini-2.5-pro", "gemini-2.5-pro").replace("gc/gemini-2.5-flash", "gemini-2.5-flash")
    url = f"{GA_BASE}/{ga_model}:generateContent?key={GA_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
        "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
    }
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            return candidates[0]["content"]["parts"][0].get("text", "").strip()
    except Exception as e:
        logger.warning("Google AI call failed (model=%s): %s", model, e)
        return ""


async def llm_call(
    system_prompt: str,
    user_prompt: str,
    model: str = MODEL_CREATIVE,
    temperature: float = 0.8,
    max_tokens: int = 2048,
) -> str:
    """Call LLM: try 9router first, fallback to Google AI API, return text."""
    text = await _call_9router(system_prompt, user_prompt, model, temperature, max_tokens)
    if text:
        return text
    text = await _call_google_ai(system_prompt, user_prompt, model, temperature, max_tokens)
    if text:
        return text
    logger.error("All LLM routes failed for model=%s", model)
    return ""


async def llm_json(
    system_prompt: str,
    user_prompt: str,
    model: str = MODEL_CREATIVE,
    temperature: float = 0.6,
) -> dict | list:
    """Call LLM and parse response as JSON."""
    text = await llm_call(
        system_prompt=system_prompt,
        user_prompt=user_prompt + "\n\nResponse dalam format JSON.",
        model=model,
        temperature=temperature,
        max_tokens=4096,
    )
    if not text:
        return {}
    # Find first [ or { in text
    start = text.find("[")
    if start == -1:
        start = text.find("{")
    if start != -1:
        text = text[start:]
    # Remove markdown fences if still present
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").removesuffix("```json").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("LLM JSON parse failed: %s", text[:200])
        return {}


# ── High-level generators ──────────────────────────────────────────

HOOK_SYSTEM = """Kamu adalah copywriter affiliate Indonesia expert untuk e-commerce. Buat hook penjualan yang clickbait, emosional, dan conversion-oriented dalam Bahasa Indonesia. Setiap hook maksimal 15 kata. Langsung output hook nya saja."""

async def generate_hooks(
    product_name: str, category: str, count: int = 10,
    pain_points: list[str] | None = None,
) -> list[str]:
    """Generate affiliate hooks for a product."""
    pain_text = "\n".join(f"- {p}" for p in (pain_points or []))
    prompt = f"""Produk: {product_name}\nKategori: {category}\nPain Points:\n{pain_text}\n\nBuat {count} hook penjualan. Format: JSON array: ["hook1", "hook2", ...]"""
    result = await llm_json(system_prompt=HOOK_SYSTEM, user_prompt=prompt, temperature=0.8)
    if isinstance(result, list):
        return [str(h) for h in result]
    if isinstance(result, dict):
        for key in ("hooks", "hook", "result", "data"):
            if key in result and isinstance(result[key], list):
                return [str(h) for h in result[key]]
    return []


SCRIPT_SYSTEM = """Kamu adalah creative director affiliate marketing Indonesia. Buat script video pendek (TikTok/Reels/Shorts) yang engaging. Format: [HOOK]-[PROBLEM]-[SOLUTION]-[SOCIAL_PROOF]-[CTA]. Gunakan Bahasa Indonesia casual."""

async def generate_scripts(
    product_name: str, category: str, hooks: list[str],
    offer_strategy: str, count: int = 5,
) -> list[dict]:
    """Generate video scripts based on hooks and offer strategy."""
    hooks_text = "\n".join(f"- {h}" for h in hooks[:3])
    prompt = f"""Produk: {product_name}\nKategori: {category}\nHook: {hooks_text}\nStrategi Offer: {offer_strategy}\n\nBuat {count} script video. Format: JSON array of {{title, hook_used, structure, full_script}}"""
    result = await llm_json(system_prompt=SCRIPT_SYSTEM, user_prompt=prompt, temperature=0.7)
    if isinstance(result, list):
        return [dict(s) for s in result if isinstance(s, dict)]
    if isinstance(result, dict):
        for key in ("scripts", "result", "data"):
            if key in result and isinstance(result[key], list):
                return [dict(s) for s in result[key] if isinstance(s, dict)]
    return []


OFFER_SYSTEM = """Kamu adalah strategist affiliate marketing Indonesia. Buat offer strategy lengkap untuk produk e-commerce. Fokus pada value proposition, target audience, emotional triggers, objection handling."""

async def generate_offer(
    product_name: str, category: str, price: float,
    pain_points: list[str], benefits: list[str],
) -> dict:
    """Generate offer strategy for a product."""
    pp_str = "\n".join(f"- {p}" for p in pain_points)
    ben_str = "\n".join(f"- {b}" for b in benefits)
    prompt = f"""Produk: {product_name}\nKategori: {category}\nHarga: Rp{price:,.0f}\nPain Points:\n{pp_str}\nBenefits:\n{ben_str}\n\nBuat offer strategy JSON dengan: primary_angle, value_proposition, positioning_statement, target_audience, emotional_triggers, key_benefits, objections_to_address, recommended_cta"""
    result = await llm_json(system_prompt=OFFER_SYSTEM, user_prompt=prompt, temperature=0.6)
    return result if isinstance(result, dict) else {}


async def analyze_reviews_llm(reviews_text: str, product_name: str) -> dict:
    """Analyze product reviews using LLM."""
    prompt = f"""Produk: {product_name}\nUlasan:\n{reviews_text[:3000]}\n\nAnalisis: {{
      "summary": "...", "sentiment": {{"positive": 0-1, "neutral": 0-1, "negative": 0-1}},
      "pain_points": [{{"point": "...", "frequency": 0-1, "severity": "high/medium/low"}}],
      "benefits": [{{"benefit": "...", "mention_rate": 0-1}}],
      "top_complaints": [], "recommendations": []
    }}"""
    return await llm_json(system_prompt="Kamu adalah analis ulasan produk e-commerce Indonesia.", user_prompt=prompt, temperature=0.4) or {}


async def analyze_competitors_llm(competitor_data: str, product_name: str, category: str) -> dict:
    """Analyze competitors using LLM."""
    prompt = f"""Produk: {product_name}\nKategori: {category}\nData Kompetitor:\n{competitor_data[:3000]}\n\nAnalisis: {{
      "market_overview": "", "competitors": [], "winning_hooks": [{{"hook": "", "why_works": ""}}],
      "gaps_identified": [], "recommended_differentiation": "", "common_angles": [], "predicted_trends": []
    }}"""
    return await llm_json(system_prompt="Kamu adalah analis kompetitor e-commerce Indonesia.", user_prompt=prompt, temperature=0.5) or {}
