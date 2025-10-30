"""Configuration management for the downloader."""

from __future__ import annotations

import configparser
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

from .constants import CONFIG_FILE, DEFAULT_DOWNLOAD_DIR, STATE_FILE
from .models import DownloadOptions, DownloadTask

logger = logging.getLogger(__name__)


class ConfigManager:
    """Persist application preferences and download state."""

    def __init__(self, config_file: str = CONFIG_FILE, state_file: str = STATE_FILE):
        self.config_file = config_file
        self.state_file = state_file
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self) -> None:
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file)
                logger.info("Đã tải cấu hình từ %s", self.config_file)
            except Exception as exc:
                logger.error("Lỗi khi tải cấu hình: %s", exc)
                self.create_default_config()
        else:
            self.create_default_config()

    def create_default_config(self) -> None:
        self.config["general"] = {
            "download_dir": DEFAULT_DOWNLOAD_DIR,
            "max_workers": "1",
            "check_for_updates": "true",
        }

        self.config["download"] = {
            "format_selector": "best",
            "merge_format": "mp4",
            "audio_quality": "192",
            "retry_count": "10",
            "sleep_interval": "3",
            "rate_limit": "",
            "download_thumbnails": "false",
            "download_subtitles": "false",
            "subtitle_languages": "vi,en",
        }

        self.config["authentication"] = {
            "use_proxy": "false",
            "proxy": "",
            "use_cookies": "false",
            "cookies_file": "",
        }

        self.save_config()

    def save_config(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as config_file:
                self.config.write(config_file)
            logger.info("Đã lưu cấu hình vào %s", self.config_file)
        except Exception as exc:
            logger.error("Lỗi khi lưu cấu hình: %s", exc)

    def get_download_options(self) -> DownloadOptions:
        options = DownloadOptions()

        if "general" in self.config:
            options.download_dir = self.config.get(
                "general", "download_dir", fallback=DEFAULT_DOWNLOAD_DIR
            )
            options.max_workers = self.config.getint(
                "general", "max_workers", fallback=1
            )

        if "download" in self.config:
            download = self.config["download"]
            options.format_selector = download.get("format_selector", "best")
            options.merge_format = download.get("merge_format", "mp4")
            options.audio_quality = download.get("audio_quality", "192")
            options.retry_count = download.getint("retry_count", fallback=10)
            options.sleep_interval = download.getint("sleep_interval", fallback=3)
            options.rate_limit = download.get("rate_limit", "")
            options.download_thumbnails = download.getboolean(
                "download_thumbnails", fallback=False
            )
            options.download_subtitles = download.getboolean(
                "download_subtitles", fallback=False
            )
            subtitle_raw = download.get("subtitle_languages", "vi,en")
            options.subtitle_languages = [
                lang.strip() for lang in subtitle_raw.split(",") if lang.strip()
            ] or ["vi", "en"]

        if "authentication" in self.config:
            auth = self.config["authentication"]
            if auth.getboolean("use_proxy", fallback=False):
                options.proxy = auth.get("proxy", "")
            options.use_cookies = auth.getboolean("use_cookies", fallback=False)
            options.cookies_file = auth.get("cookies_file", "")

        return options

    def update_from_options(self, options: DownloadOptions) -> None:
        self.config.setdefault("general", {})
        self.config["general"]["download_dir"] = options.download_dir
        self.config["general"]["max_workers"] = str(options.max_workers)

        self.config.setdefault("download", {})
        self.config["download"]["format_selector"] = options.format_selector
        self.config["download"]["merge_format"] = options.merge_format
        self.config["download"]["audio_quality"] = options.audio_quality
        self.config["download"]["retry_count"] = str(options.retry_count)
        self.config["download"]["sleep_interval"] = str(options.sleep_interval)
        self.config["download"]["rate_limit"] = options.rate_limit
        self.config["download"]["download_thumbnails"] = str(
            options.download_thumbnails
        ).lower()
        self.config["download"]["download_subtitles"] = str(
            options.download_subtitles
        ).lower()
        self.config["download"]["subtitle_languages"] = ",".join(
            options.subtitle_languages
        )

        self.config.setdefault("authentication", {})
        self.config["authentication"]["use_proxy"] = str(bool(options.proxy)).lower()
        self.config["authentication"]["proxy"] = options.proxy
        self.config["authentication"]["use_cookies"] = str(
            options.use_cookies
        ).lower()
        self.config["authentication"]["cookies_file"] = options.cookies_file

        self.save_config()

    def save_download_state(self, tasks: List[DownloadTask]) -> None:
        try:
            state = {
                "timestamp": datetime.now().isoformat(),
                "tasks": [],
            }

            for task in tasks:
                if task.url and task.progress.status != "finished":
                    state["tasks"].append(
                        {
                            "url": task.url,
                            "is_playlist": task.is_playlist,
                            "index": task.index,
                            "total": task.total,
                            "progress": task.progress.percent,
                        }
                    )

            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, "w", encoding="utf-8") as state_file:
                json.dump(state, state_file)

            logger.info("Đã lưu trạng thái tải xuống vào %s", self.state_file)
        except Exception as exc:
            logger.error("Lỗi khi lưu trạng thái tải xuống: %s", exc)

    def load_download_state(self) -> List[Dict[str, Any]]:
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "r", encoding="utf-8") as state_file:
                    state = json.load(state_file)

                timestamp = datetime.fromisoformat(state.get("timestamp", ""))
                if (datetime.now() - timestamp).days > 7:
                    logger.info("Trạng thái tải xuống quá cũ, bỏ qua.")
                    return []

                logger.info("Đã tải trạng thái tải xuống từ %s", self.state_file)
                return state.get("tasks", [])
            return []
        except Exception as exc:
            logger.error("Lỗi khi tải trạng thái tải xuống: %s", exc)
            return []
