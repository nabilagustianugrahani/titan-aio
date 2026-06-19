"""
MarkItDown Adapter — convert anything to Markdown.

Microsoft MarkItDown (github.com/microsoft/markitdown) converts PDFs, DOCX,
PPTX, XLSX, images (via OCR), HTML, audio transcripts, and YouTube videos
into clean Markdown.

Zero API keys needed (unless using Azure Document Intelligence).
Pure local conversion.

Install:
    pip install 'markitdown[all]'

Then:
    from Services.content.markitdown_adapter import MarkItDownEngine
    engine = MarkItDownEngine()
    text = await engine.convert("review_screenshot.png")
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional


class MarkItDownEngine:
    """Convert files to Markdown using MarkItDown (Microsoft)."""

    def __init__(self, use_markitdown: bool = False):
        self.use_markitdown = use_markitdown

    def convert(self, file_path: str | Path) -> dict:
        """Convert a file to Markdown text.

        Supports: .pdf, .docx, .pptx, .xlsx, .png, .jpg, .html, .csv, .json, .xml
        """
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}", "text": ""}

        if not self.use_markitdown:
            return self._fallback(path)

        try:
            result = subprocess.run(
                ["markitdown", str(path)],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                return {
                    "text": result.stdout,
                    "source": str(path),
                    "characters": len(result.stdout),
                }
            return {"error": result.stderr[:300], "text": ""}
        except FileNotFoundError:
            return {"error": "MarkItDown not installed (pip install markitdown)", "text": ""}
        except Exception as e:
            return {"error": str(e), "text": ""}

    def _fallback(self, path: Path) -> dict:
        """Read text from simple files as fallback."""
        ext = path.suffix.lower()
        if ext in (".txt", ".md", ".csv", ".json", ".xml", ".html"):
            try:
                text = path.read_text(encoding="utf-8")
                return {"text": text[:5000], "source": str(path), "characters": len(text[:5000])}
            except Exception:
                pass
        return {"text": "", "note": "Install markitdown for full conversion support"}

    @staticmethod
    def is_available() -> bool:
        """Check if MarkItDown CLI is installed."""
        try:
            result = subprocess.run(["markitdown", "--help"], capture_output=True, timeout=5)
            return result.returncode == 0
        except FileNotFoundError:
            return False
