"""Locale utilities — adapted from MiroFish. Graceful fallback when locales not bundled."""

from __future__ import annotations

import json
import logging
import os
import threading

logger = logging.getLogger(__name__)

_thread_local = threading.local()

# Locales directory — may not exist in Titan AIO context
_locales_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "locales")

_translations: dict[str, dict] = {}
_languages: list[dict] = []

if os.path.isdir(_locales_dir):
    try:
        lang_file = os.path.join(_locales_dir, "languages.json")
        if os.path.isfile(lang_file):
            with open(lang_file, encoding="utf-8") as f:
                _languages = json.load(f)
        for filename in os.listdir(_locales_dir):
            if filename.endswith(".json") and filename != "languages.json":
                locale_name = filename[:-5]
                with open(os.path.join(_locales_dir, filename), encoding="utf-8") as f:
                    _translations[locale_name] = json.load(f)
    except Exception as exc:
        logger.debug("Locale files not loaded: %s", exc)
else:
    logger.debug("Locales directory not found: %s", _locales_dir)


def set_locale(locale: str) -> None:
    """Set locale for current thread."""
    _thread_local.locale = locale


def get_locale() -> str:
    """Get current locale, fallback to 'en'."""
    try:
        raw = os.environ.get("HTTP_ACCEPT_LANGUAGE", "en")
        if raw in _translations:
            return raw
    except Exception:
        pass
    return getattr(_thread_local, "locale", "en")


def t(key: str, **kwargs) -> str:
    """Translate a key, with optional format args."""
    locale = get_locale()
    table = _translations.get(locale, {})
    msg = table.get(key, key)
    if kwargs and isinstance(msg, str):
        try:
            return msg.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return msg


def get_language_instruction() -> str:
    """Get the language instruction for LLM prompts."""
    locale = get_locale()
    instructions = {
        "en": "You must output in English.",
        "zh": "你必须用中文输出。",
        "id": "Anda harus merespons dalam Bahasa Indonesia.",
    }
    return instructions.get(locale, instructions["en"])
