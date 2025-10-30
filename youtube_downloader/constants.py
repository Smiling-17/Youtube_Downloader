"""Constant values shared across the YouTube Downloader application."""

from __future__ import annotations

import os

VERSION = "2.0.0"

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".youtube_downloader_config.ini")
STATE_FILE = os.path.join(os.path.expanduser("~"), ".youtube_downloader_state.json")
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "YouTube")

LOG_FILE = "youtube_downloader.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

YT_DLP_LATEST_VERSION_URL = (
    "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
)
