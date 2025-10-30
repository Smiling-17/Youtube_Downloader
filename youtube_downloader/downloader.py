"""Core download engine built around yt-dlp."""

from __future__ import annotations

import copy
import logging
import os
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

try:
    from yt_dlp import YoutubeDL  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Lỗi: Không thể import yt-dlp. "
        "Vui lòng cài đặt bằng lệnh: pip install yt-dlp"
    ) from exc

from .config import ConfigManager
from .models import (
    DownloadOptions,
    DownloadProgress,
    DownloadTask,
    PlaylistInfo,
    VideoInfo,
)
from .utils import clean_ansi, sanitize

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[DownloadTask], None]


def copy_download_options(options: DownloadOptions) -> DownloadOptions:
    """Deep-copy helper to duplicate download options safely."""
    return copy.deepcopy(options)


class YouTubeDownloader:
    """High-level downloader orchestrating yt-dlp operations."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()
        self.default_options = self.config_manager.get_download_options()
        self.active_tasks: List[DownloadTask] = []
        self.completed_tasks: List[DownloadTask] = []
        self.failed_tasks: List[DownloadTask] = []
        self.progress_callbacks: List[ProgressCallback] = []
        self.executor: Optional[ThreadPoolExecutor] = None
        self._tasks_lock = threading.Lock()

    def add_progress_callback(self, callback: ProgressCallback) -> None:
        self.progress_callbacks.append(callback)

    def notify_progress(self, task: DownloadTask) -> None:
        for callback in list(self.progress_callbacks):
            try:
                callback(task)
            except Exception as exc:
                logger.error("Lỗi khi gọi callback tiến trình: %s", exc)

    def progress_hook(self, data: Dict[str, Any]) -> None:
        filename = data.get("filename", "")
        basename = os.path.basename(filename)

        task: Optional[DownloadTask] = None
        info_dict = data.get("info_dict") or {}
        candidate_url = (
            info_dict.get("original_url")
            or info_dict.get("webpage_url")
            or info_dict.get("url")
        )

        with self._tasks_lock:
            if candidate_url:
                for candidate in self.active_tasks:
                    if candidate.url == candidate_url:
                        task = candidate
                        break

            if task is None:
                for candidate in self.active_tasks:
                    if candidate.progress.filename and candidate.progress.filename == basename:
                        task = candidate
                        break

            if task is None:
                for candidate in self.active_tasks:
                    if not candidate.progress.filename:
                        task = candidate
                        break

        if task is None:
            logger.warning("Không tìm thấy task cho file: %s", filename)
            return

        progress = task.progress

        status = data.get("status")
        if status == "downloading":
            progress.filename = basename
            progress.status = "downloading"
            percent_str = data.get("_percent_str", "0")
            percent_str = clean_ansi(percent_str).replace("%", "").strip()
            progress.percent = float(percent_str) if "_percent_str" in data else 0
            progress.speed = data.get("_speed_str", "N/A")
            progress.eta = data.get("_eta_str", "N/A")
            progress.bytes_downloaded = data.get("downloaded_bytes", 0)
            progress.total_bytes = data.get("total_bytes", 0)

            self.notify_progress(task)

        elif status == "finished":
            progress.filename = basename
            progress.status = "finished"
            progress.percent = 100.0
            self.notify_progress(task)
            logger.info("Đã tải xong: %s", basename)

        elif status == "error":
            progress.status = "error"
            progress.error_message = data.get("error", "Lỗi không xác định")
            self.notify_progress(task)
            logger.error("Lỗi khi tải: %s", progress.error_message)

    def extract_info(self, url: str, extract_formats: bool = True) -> Dict[str, Any]:
        options = {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "extract_flat": not extract_formats,
        }

        with YoutubeDL(options) as ydl:
            return ydl.extract_info(url, download=False)

    @staticmethod
    def is_playlist(url: str) -> bool:
        return "playlist" in url or "list=" in url

    def get_video_info(self, url: str) -> VideoInfo:
        try:
            info = self.extract_info(url)
            return VideoInfo.from_yt_dlp_info(info)
        except Exception as exc:
            logger.error("Lỗi khi lấy thông tin video: %s", exc)
            raise

    def get_playlist_info(self, url: str, include_videos: bool = False) -> PlaylistInfo:
        try:
            info = self.extract_info(url, extract_formats=False)
            return PlaylistInfo.from_yt_dlp_info(info, include_videos)
        except Exception as exc:
            logger.error("Lỗi khi lấy thông tin playlist: %s", exc)
            raise

    def get_all_video_urls_from_playlist(self, url: str) -> List[str]:
        try:
            info = self.extract_info(url, extract_formats=False)
            video_urls = []
            for entry in info.get("entries", []):
                if not entry:
                    continue
                if entry.get("url"):
                    video_urls.append(entry["url"])
                elif entry.get("id"):
                    video_urls.append(f"https://www.youtube.com/watch?v={entry['id']}")
            return video_urls
        except Exception as exc:
            logger.error("Lỗi khi lấy danh sách video từ playlist: %s", exc)
            raise

    def _finalize_success(self, task: DownloadTask) -> None:
        with self._tasks_lock:
            if task in self.active_tasks:
                self.active_tasks.remove(task)
            self.completed_tasks.append(task)

    def _finalize_failure(self, task: DownloadTask) -> None:
        with self._tasks_lock:
            if task in self.active_tasks:
                self.active_tasks.remove(task)
            self.failed_tasks.append(task)

    def download_single_video(self, task: DownloadTask) -> bool:
        if task.index > 0 and task.total > 0:
            logger.info("[%s/%s] Đang tải video: %s", task.index, task.total, task.url)
        else:
            logger.info("Đang tải video: %s", task.url)

        task.progress.status = "downloading"
        self.notify_progress(task)

        options = task.options.to_yt_dlp_options()
        options["progress_hooks"] = [self.progress_hook]

        try:
            with YoutubeDL(options) as ydl:
                ydl.download([task.url])

            task.progress.status = "finished"
            task.progress.percent = 100.0
            self.notify_progress(task)
            self._finalize_success(task)
            return True
        except Exception as exc:
            error_msg = str(exc)
            logger.error("Lỗi khi tải video: %s", error_msg)

            if "requested format is not available" in error_msg:
                logger.info(
                    "Định dạng yêu cầu không có sẵn. Thử lại với định dạng tốt nhất..."
                )
                options["format"] = "best"
                try:
                    with YoutubeDL(options) as ydl:
                        ydl.download([task.url])

                    task.progress.status = "finished"
                    task.progress.percent = 100.0
                    self.notify_progress(task)
                    self._finalize_success(task)
                    return True
                except Exception as retry_exc:
                    error_msg = str(retry_exc)
                    logger.error("Vẫn không thể tải: %s", error_msg)

            task.progress.status = "error"
            task.progress.error_message = error_msg
            self.notify_progress(task)
            self._finalize_failure(task)
            return False

    def download_playlist(self, url: str, options: DownloadOptions) -> bool:
        try:
            playlist_info = self.get_playlist_info(url)
            logger.info(
                "Đã tìm thấy playlist: %s với %s video",
                playlist_info.title,
                playlist_info.video_count,
            )

            video_urls = self.get_all_video_urls_from_playlist(url)

            if not video_urls:
                logger.error("Không tìm thấy video nào trong playlist.")
                return False

            playlist_dir = os.path.join(
                options.download_dir, sanitize(playlist_info.title)
            )
            os.makedirs(playlist_dir, exist_ok=True)

            playlist_options = copy_download_options(options)
            playlist_options.output_template = os.path.join(
                os.path.abspath(playlist_dir), "%(playlist_index)s - %(title)s.%(ext)s"
            )

            tasks = [
                DownloadTask(
                    url=video_url,
                    options=playlist_options,
                    index=i + 1,
                    total=len(video_urls),
                    is_playlist=True,
                    playlist_info=playlist_info,
                )
                for i, video_url in enumerate(video_urls)
            ]

            with self._tasks_lock:
                self.active_tasks.extend(tasks)

            if options.max_workers > 1:
                return self._download_parallel(tasks, options.max_workers, options.sleep_interval)

            return self._download_sequential(tasks, options.sleep_interval)
        except Exception as exc:
            logger.error("Lỗi khi tải playlist: %s", exc)
            traceback.print_exc()
            return False

    def _download_sequential(
        self, tasks: Iterable[DownloadTask], sleep_interval: int
    ) -> bool:
        tasks_list = list(tasks)
        success_count = 0

        for idx, task in enumerate(tasks_list):
            if idx > 0:
                wait_time = min(sleep_interval, 1 + idx // 20)
                logger.info("Chờ %s giây trước khi tải video tiếp theo...", wait_time)
                time.sleep(wait_time)

            if self.download_single_video(task):
                success_count += 1

        logger.info("Đã tải thành công %s/%s video", success_count, len(tasks_list))
        return success_count > 0

    def _download_parallel(
        self, tasks: List[DownloadTask], max_workers: int, sleep_interval: int
    ) -> bool:
        success_count = 0

        if self.executor is None or self.executor._shutdown:
            self.executor = ThreadPoolExecutor(max_workers=max_workers)

        batch_size = min(max_workers, 10)
        task_batches = [tasks[i : i + batch_size] for i in range(0, len(tasks), batch_size)]

        for batch_index, batch in enumerate(task_batches):
            if batch_index > 0:
                logger.info(
                    "Chờ %s giây trước khi tải batch tiếp theo...",
                    sleep_interval,
                )
                time.sleep(sleep_interval)

            futures = [self.executor.submit(self.download_single_video, task) for task in batch]

            for future in as_completed(futures):
                try:
                    if future.result():
                        success_count += 1
                except Exception as exc:
                    logger.error("Lỗi khi tải song song: %s", exc)

        logger.info("Đã tải thành công %s/%s video", success_count, len(tasks))
        return success_count > 0

    def download(self, url: str, options: Optional[DownloadOptions] = None) -> bool:
        options = options or self.default_options

        try:
            os.makedirs(options.download_dir, exist_ok=True)

            if self.is_playlist(url):
                return self.download_playlist(url, options)

            try:
                video_info = self.get_video_info(url)
                task = DownloadTask(url=url, options=options, video_info=video_info)
            except Exception:
                task = DownloadTask(url=url, options=options)

            with self._tasks_lock:
                self.active_tasks.append(task)

            return self.download_single_video(task)
        except Exception as exc:
            logger.error("Lỗi khi tải: %s", exc)
            traceback.print_exc()
            return False

    def resume_downloads(self) -> bool:
        tasks_data = self.config_manager.load_download_state()
        if not tasks_data:
            logger.info("Không có tải xuống nào cần tiếp tục.")
            return False

        options = self.default_options
        tasks: List[DownloadTask] = []

        for data in tasks_data:
            url = data.get("url")
            if not url:
                continue

            is_playlist = data.get("is_playlist", False)
            index = data.get("index", 0)
            total = data.get("total", 0)

            if is_playlist:
                try:
                    playlist_info = self.get_playlist_info(url)
                    task = DownloadTask(
                        url=url,
                        options=options,
                        index=index,
                        total=total,
                        is_playlist=True,
                        playlist_info=playlist_info,
                    )
                except Exception:
                    task = DownloadTask(
                        url=url,
                        options=options,
                        index=index,
                        total=total,
                        is_playlist=True,
                    )
            else:
                try:
                    video_info = self.get_video_info(url)
                    task = DownloadTask(
                        url=url,
                        options=options,
                        video_info=video_info,
                    )
                except Exception:
                    task = DownloadTask(url=url, options=options)

            tasks.append(task)

        if not tasks:
            logger.info("Không có tải xuống hợp lệ để tiếp tục.")
            return False

        logger.info("Tiếp tục %s tải xuống đã bị gián đoạn.", len(tasks))

        with self._tasks_lock:
            self.active_tasks.extend(tasks)

        if options.max_workers > 1:
            return self._download_parallel(tasks, options.max_workers, options.sleep_interval)

        return self._download_sequential(tasks, options.sleep_interval)

    def cancel_all_downloads(self) -> None:
        self.config_manager.save_download_state(self.active_tasks)

        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None

        with self._tasks_lock:
            for task in self.active_tasks:
                task.progress.status = "error"
                task.progress.error_message = "Đã hủy bởi người dùng"
                self.failed_tasks.append(task)

            self.active_tasks.clear()

        logger.info("Đã hủy tất cả các tải xuống.")

    def cleanup(self) -> None:
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None
