"""Command line interface for the downloader."""

from __future__ import annotations

import logging
import os
import sys

from .config import ConfigManager
from .constants import VERSION
from .downloader import YouTubeDownloader
from .models import DownloadOptions, PlaylistInfo, VideoInfo
from .utils import format_duration
from .versioning import VersionChecker, yt_dlp_version

logger = logging.getLogger(__name__)


class CommandLineInterface:
    """Interactive console workflow."""

    def __init__(self) -> None:
        self.config_manager = ConfigManager()
        self.downloader = YouTubeDownloader(self.config_manager)
        self.downloader.add_progress_callback(self.update_progress)
        self.current_task = None

    def update_progress(self, task) -> None:
        self.current_task = task

        if task.progress.status == "downloading":
            sys.stdout.write("\r\033[K")
            if task.index > 0 and task.total > 0:
                sys.stdout.write(f"[{task.index}/{task.total}] ")
            sys.stdout.write(f"{task.progress}")
            sys.stdout.flush()
        elif task.progress.status == "finished":
            sys.stdout.write("\r\033[K")
            if task.index > 0 and task.total > 0:
                print(f"[{task.index}/{task.total}] Đã tải xong: {task.progress.filename}")
            else:
                print(f"Đã tải xong: {task.progress.filename}")
        elif task.progress.status == "error":
            sys.stdout.write("\r\033[K")
            if task.index > 0 and task.total > 0:
                print(f"[{task.index}/{task.total}] Lỗi: {task.progress.error_message}")
            else:
                print(f"Lỗi: {task.progress.error_message}")

    @staticmethod
    def display_video_info(info: VideoInfo) -> None:
        print("\n=== THÔNG TIN VIDEO ===")
        print(f"Tiêu đề: {info.title}")
        print(f"Kênh: {info.uploader}")
        print(f"Thời lượng: {format_duration(info.duration)}")
        if info.view_count:
            print(f"Lượt xem: {info.view_count:,}".replace(",", "."))
        print(f"Ngày đăng: {info.upload_date}")

    @staticmethod
    def display_playlist_info(info: PlaylistInfo) -> None:
        print("\n=== THÔNG TIN PLAYLIST ===")
        print(f"Tiêu đề: {info.title}")
        print(f"Kênh: {info.uploader}")
        print(f"Số lượng video: {info.video_count}")

        if info.videos:
            print("\nCác video trong playlist:")
            for idx, video in enumerate(info.videos[:5], 1):
                print(f" {idx}. {video.title}")
            if len(info.videos) > 5:
                print(f" ... và {len(info.videos) - 5} video khác")

    @staticmethod
    def list_formats(info: VideoInfo, audio_only: bool = False) -> None:
        if audio_only:
            audio_formats = [f for f in info.formats if not f.has_video]
            audio_formats.sort(key=lambda f: f.bitrate, reverse=True)

            print("\nCác format audio tìm thấy:")
            for fmt in audio_formats:
                print(f" • {fmt}")
            return

        video_formats = [f for f in info.formats if f.has_video]
        video_formats.sort(
            key=lambda f: int(f.resolution.replace("p", ""))
            if f.resolution.replace("p", "").isdigit()
            else 0,
            reverse=True,
        )

        print("\nCác format video tìm thấy:")
        for fmt in video_formats:
            print(f" • {fmt}")

    @staticmethod
    def confirm_large_playlist(count: int) -> bool:
        if count > 10:
            response = input(
                f"Playlist này có {count} video. Bạn có chắc muốn tải tất cả? (y/n): "
            ).strip().lower()
            return response in ("y", "yes", "có", "co")
        return True

    def setup_download_options(self, mode: str) -> DownloadOptions:
        options = self.config_manager.get_download_options()

        default_dir = options.download_dir
        base_outdir = input(
            f"Nhập thư mục lưu (Enter để dùng mặc định [{default_dir}]): "
        ).strip()
        if base_outdir:
            options.download_dir = base_outdir

        if options.download_dir:
            options.output_template = os.path.join(
                options.download_dir, "%(title)s.%(ext)s"
            )
        else:
            options.output_template = "%(title)s.%(ext)s"

        if mode == "1":
            print("Chọn chất lượng MP3:")
            print("  1) Thấp (128 kbps)")
            print("  2) Trung bình (192 kbps)")
            print("  3) Cao (256 kbps)")
            print("  4) Rất cao (320 kbps)")
            quality_choice = input("Lựa chọn (1-4, mặc định: 2): ").strip() or "2"
            quality_map = {"1": "128", "2": "192", "3": "256", "4": "320"}
            options.audio_quality = quality_map.get(quality_choice, "192")

            print(
                f"→ Bắt đầu tải audio chất lượng cao nhất và chuyển sang MP3 {options.audio_quality}kbps..."
            )
            options.format_selector = "bestaudio"
            options.convert_to_mp3 = True

        elif mode == "2":
            print("→ Bắt đầu tải video MP4 (không audio)...")
            options.format_selector = "bestvideo[ext=mp4]"

        elif mode == "3":
            print("→ Bắt đầu tải và ghép video+audio chất lượng cao nhất...")
            options.format_selector = "bestvideo[ext=mp4]+bestaudio/best"
            options.merge = True
            options.merge_format = "mp4"

        elif mode == "4":
            format_id = input("Nhập format_id bạn muốn tải: ").strip()
            print(f"→ Bắt đầu tải format {format_id}...")
            options.format_selector = format_id
            options.merge = "+" in format_id
            options.merge_format = "mp4"

        if (
            input("Bạn có muốn cấu hình các tùy chọn nâng cao? (y/n, mặc định: n): ")
            .strip()
            .lower()
            in ("y", "yes", "có", "co")
        ):
            max_workers = input(
                f"Số lượng tải song song (1-10, mặc định: {options.max_workers}): "
            ).strip()
            if max_workers.isdigit() and 1 <= int(max_workers) <= 10:
                options.max_workers = int(max_workers)

            rate_limit = input(
                "Giới hạn tốc độ tải (ví dụ: 500K, để trống nếu không giới hạn): "
            ).strip()
            if rate_limit:
                options.rate_limit = rate_limit

            download_thumbnails = (
                input("Tải thumbnail? (y/n, mặc định: n): ").strip().lower()
            )
            options.download_thumbnails = download_thumbnails in ("y", "yes", "có", "co")

            download_subtitles = (
                input("Tải subtitle? (y/n, mặc định: n): ").strip().lower()
            )
            options.download_subtitles = download_subtitles in ("y", "yes", "có", "co")

            if options.download_subtitles:
                subtitle_langs = input(
                    "Ngôn ngữ subtitle (ví dụ: vi,en, mặc định: vi,en): "
                ).strip()
                if subtitle_langs:
                    options.subtitle_languages = [
                        lang.strip() for lang in subtitle_langs.split(",") if lang.strip()
                    ]

            use_proxy = input("Sử dụng proxy? (y/n, mặc định: n): ").strip().lower()
            if use_proxy in ("y", "yes", "có", "co"):
                proxy = input("Nhập địa chỉ proxy (ví dụ: socks5://127.0.0.1:1080): ").strip()
                if proxy:
                    options.proxy = proxy

            use_cookies = input("Sử dụng cookies? (y/n, mặc định: n): ").strip().lower()
            if use_cookies in ("y", "yes", "có", "co"):
                cookies_file = input("Nhập đường dẫn đến file cookies: ").strip()
                if cookies_file:
                    options.use_cookies = True
                    options.cookies_file = cookies_file

        self.config_manager.update_from_options(options)
        return options

    def run(self) -> None:
        print("=== YOUTUBE DOWNLOADER PRO ===")
        print(f"Phiên bản: {VERSION}")
        print(f"yt-dlp: {yt_dlp_version}")
        print("Cảnh báo: Cần cài đặt FFmpeg để chuyển đổi định dạng\n")

        has_update, latest_version = VersionChecker.check_for_updates()
        if has_update:
            print(f"Có phiên bản mới của yt-dlp: {latest_version} (hiện tại: {yt_dlp_version})")
            if (
                input("Bạn có muốn cập nhật ngay? (y/n): ").strip().lower()
                in ("y", "yes", "có", "co")
            ):
                if VersionChecker.update_yt_dlp():
                    print(
                        "Đã cập nhật yt-dlp thành công. Vui lòng khởi động lại ứng dụng."
                    )
                    return
                print("Không thể cập nhật yt-dlp. Tiếp tục với phiên bản hiện tại.")

        tasks_data = self.config_manager.load_download_state()
        if tasks_data:
            if (
                input(
                    f"Tìm thấy {len(tasks_data)} tải xuống bị gián đoạn. Bạn có muốn tiếp tục? (y/n): "
                )
                .strip()
                .lower()
                in ("y", "yes", "có", "co")
            ):
                self.downloader.resume_downloads()
                print("\nHoàn tất! Tất cả các tải xuống đã được xử lý.")
                return

        url = input("Nhập URL YouTube (video hoặc playlist): ").strip()
        if not url:
            print("URL không hợp lệ. Vui lòng thử lại.")
            return

        is_playlist = self.downloader.is_playlist(url)

        try:
            if is_playlist:
                print("→ Phát hiện: Playlist")
                playlist_info = self.downloader.get_playlist_info(url)
                self.display_playlist_info(playlist_info)

                if not self.confirm_large_playlist(playlist_info.video_count):
                    print("Đã hủy tải xuống.")
                    return
            else:
                print("→ Phát hiện: Video đơn lẻ")
                video_info = self.downloader.get_video_info(url)
                self.display_video_info(video_info)
                self.list_formats(video_info)

            print(
                """
Chọn chế độ tải:
  1) Chỉ audio (MP3)
  2) Chỉ video (không có audio)
  3) Video + audio (MP4)
  4) Chọn format cụ thể
"""
            )
            mode = input("Lựa chọn (1/2/3/4): ").strip()
            if mode not in ("1", "2", "3", "4"):
                print("Lựa chọn không hợp lệ. Chạy lại và chọn 1, 2, 3 hoặc 4.")
                return

            options = self.setup_download_options(mode)

            try:
                success = self.downloader.download(url, options)
                if success:
                    print(
                        "\nHoàn tất! File đã được lưu tại:",
                        os.path.abspath(options.download_dir),
                    )
                else:
                    print(
                        "\nTải xuống không thành công. Vui lòng kiểm tra log để biết chi tiết."
                    )
            except KeyboardInterrupt:
                print("\nĐã hủy tải xuống bởi người dùng.")
                self.downloader.cancel_all_downloads()
        except Exception as exc:
            print(f"\nLỗi không mong muốn: {exc}")
            logger.exception("Lỗi CLI")
        finally:
            self.downloader.cleanup()
