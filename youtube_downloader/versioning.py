"""Handle yt-dlp version checks and updates."""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import urllib.request
from typing import Tuple

from .constants import YT_DLP_LATEST_VERSION_URL

logger = logging.getLogger(__name__)


try:
    from yt_dlp.version import __version__ as yt_dlp_version  # type: ignore
except ImportError:  # pragma: no cover - handled elsewhere
    yt_dlp_version = "unknown"


class VersionChecker:
    """Check for available yt-dlp updates."""

    @staticmethod
    def check_for_updates() -> Tuple[bool, str]:
        try:
            logger.info("Đang kiểm tra phiên bản mới của yt-dlp...")
            with urllib.request.urlopen(YT_DLP_LATEST_VERSION_URL, timeout=5) as resp:
                data = json.loads(resp.read().decode())
            latest_version = data["tag_name"].lstrip("v")
            current_version = yt_dlp_version

            logger.info(
                "Phiên bản hiện tại: %s, phiên bản mới nhất: %s",
                current_version,
                latest_version,
            )

            if current_version == "unknown":
                return True, latest_version
            if latest_version > current_version:
                return True, latest_version
            return False, current_version
        except Exception as exc:
            logger.warning("Không thể kiểm tra phiên bản mới: %s", exc)
            return False, yt_dlp_version

    @staticmethod
    def update_yt_dlp() -> bool:
        try:
            logger.info("Đang cập nhật yt-dlp...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                logger.info("Đã cập nhật yt-dlp thành công.")
                return True

            logger.error("Lỗi khi cập nhật yt-dlp: %s", result.stderr)
            return False
        except Exception as exc:
            logger.error("Lỗi khi cập nhật yt-dlp: %s", exc)
            return False
