"""Core package initialization for YouTube Downloader Pro."""

from __future__ import annotations

import logging

from .constants import LOG_FILE, LOG_FORMAT


def _configure_logging() -> None:
    """Configure application-wide logging only once."""
    if getattr(_configure_logging, "_configured", False):
        return

    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    _configure_logging._configured = True  # type: ignore[attr-defined]


_configure_logging()


__all__ = [
    "constants",
    "utils",
    "models",
    "config",
    "versioning",
    "downloader",
    "cli",
    "gui",
]
