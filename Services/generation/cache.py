"""Generation Cache — avoid regenerating same content.

Saves to GDrive or local filesystem.
Checks cache before calling Modal/HF.

Usage:
    from Services.generation.cache import get_cached, set_cached
    cached = await get_cached("image", "power bank product photo")
    if not cached:
        img = await generate_image(...)
        await set_cached("image", "power bank product photo", img)
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

# Local cache directory
CACHE_DIR = Path(os.environ.get("GENERATION_CACHE_DIR", "/tmp/titan-cache"))


def _cache_key(gen_type: str, prompt: str) -> str:
    """Generate cache key from type + prompt."""
    content = f"{gen_type}:{prompt}"
    return hashlib.md5(content.encode()).hexdigest()


def _cache_path(gen_type: str, prompt: str) -> Path:
    """Get cache file path."""
    key = _cache_key(gen_type, prompt)
    return CACHE_DIR / gen_type / f"{key}.bin"


async def get_cached(gen_type: str, prompt: str) -> bytes | None:
    """Check cache for generated content.

    Returns bytes if found, None if not.
    """
    path = _cache_path(gen_type, prompt)
    if path.exists():
        print(f"📦 Cache hit: {gen_type} ({path.stat().st_size // 1024} KB)")
        return path.read_bytes()
    return None


async def set_cached(gen_type: str, prompt: str, data: bytes) -> None:
    """Save generated content to cache."""
    path = _cache_path(gen_type, prompt)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    print(f"💾 Cached: {gen_type} ({len(data) // 1024} KB)")


async def generate_with_cache(
    gen_type: str,
    prompt: str,
    generator_fn,
    *args,
    **kwargs,
) -> bytes | None:
    """Generate with cache check.

    1. Check cache → return if found
    2. Call generator_fn
    3. Save to cache
    4. Return result
    """
    # Check cache
    cached = await get_cached(gen_type, prompt)
    if cached:
        return cached

    # Generate
    result = await generator_fn(prompt, *args, **kwargs)
    if result:
        await set_cached(gen_type, prompt, result)
    return result
