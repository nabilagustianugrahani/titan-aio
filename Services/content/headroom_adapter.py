"""Headroom Adapter — compress LLM token usage 60-95%.

Headroom (github.com/chopratejas/headroom) compresses tool outputs and RAG chunks
before they reach LLMs. Fewer tokens = faster responses + lower cost.

Zero API keys. Fully local ONNX model (downloaded once).

Install:
    pip install headroom

Usage:
    from Services.content.headroom_adapter import HeadroomCompressor
    compressor = HeadroomCompressor()
    compressed = compressor.compress(long_text)
"""

from __future__ import annotations

import subprocess


class HeadroomCompressor:
    """Compress text before sending to LLMs to save tokens."""

    def __init__(self, use_headroom: bool = False, target_ratio: float = 0.3):
        self.use_headroom = use_headroom
        self.target_ratio = target_ratio

    def compress(self, text: str, max_chars: int = 8000) -> dict:
        """Compress text using Headroom.

        Args:
            text: Text to compress
            max_chars: Max characters to process

        Returns:
            dict with compressed text, original length, compressed length

        """
        if not self.use_headroom or len(text) < 100:
            return {"text": text[:max_chars], "original": len(text), "compressed": len(text[:max_chars]), "ratio": 1.0}

        try:
            result = subprocess.run(
                ["headroom", "compress"],
                input=text[:max_chars],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                compressed = result.stdout.strip()
                ratio = len(compressed) / max(len(text[:max_chars]), 1)
                return {
                    "text": compressed,
                    "original": len(text[:max_chars]),
                    "compressed": len(compressed),
                    "ratio": round(ratio, 2),
                }
        except FileNotFoundError:
            pass
        except Exception:
            pass

        return {"text": text[:max_chars], "original": len(text[:max_chars]), "compressed": len(text[:max_chars]), "ratio": 1.0}

    @staticmethod
    def is_available() -> bool:
        try:
            r = subprocess.run(["headroom", "--version"], capture_output=True, timeout=5)
            return r.returncode == 0
        except FileNotFoundError:
            return False
