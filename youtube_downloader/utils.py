"""Utility helpers for the YouTube Downloader application."""

from __future__ import annotations

import os
import re
from typing import Iterable


ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def clean_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return ANSI_ESCAPE.sub("", text)


def format_duration(seconds: int) -> str:
    """Format seconds into HH:MM:SS (or MM:SS when hours are zero)."""
    if not seconds:
        return "Không xác định"

    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def format_size(bytes_size: int) -> str:
    """Convert byte counts to a human-readable string."""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    if bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.2f} KB"
    if bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.2f} MB"
    return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"


def sanitize(filename: str) -> str:
    """Make a filename safe for most filesystems."""
    invalid_chars: Iterable[str] = r'<>:"/\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")

    if len(filename) > 200:
        filename = filename[:197] + "..."

    return filename
