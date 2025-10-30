#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Entry point for YouTube Downloader Pro."""

from __future__ import annotations

import argparse
import io
import os
import sys

from youtube_downloader.cli import CommandLineInterface
from youtube_downloader.config import ConfigManager
from youtube_downloader.constants import VERSION
from youtube_downloader.downloader import YouTubeDownloader
from youtube_downloader.gui import GUI_AVAILABLE, GraphicalUserInterface
from youtube_downloader.versioning import yt_dlp_version

# Force UTF-8 stdout/stderr to avoid encoding errors on Windows consoles.
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def _run_cli_with_url(args: argparse.Namespace) -> None:
    config_manager = ConfigManager()
    downloader = YouTubeDownloader(config_manager)

    options = config_manager.get_download_options()

    if args.output:
        options.download_dir = args.output

    if args.format:
        options.format_selector = args.format

    if args.audio_only:
        options.format_selector = "bestaudio"
        options.convert_to_mp3 = True

    if args.max_workers:
        options.max_workers = args.max_workers

    os.makedirs(options.download_dir, exist_ok=True)

    try:
        success = downloader.download(args.url, options)
        if success:
            print(
                "\nHoàn tất! File đã được lưu tại:",
                os.path.abspath(options.download_dir),
            )
        else:
            print("\nTải xuống không thành công. Vui lòng kiểm tra log để biết chi tiết.")
    except KeyboardInterrupt:
        print("\nĐã hủy tải xuống bởi người dùng.")
        downloader.cancel_all_downloads()
    finally:
        downloader.cleanup()


def main() -> None:
    parser = argparse.ArgumentParser(description=f"YouTube Downloader Pro {VERSION}")
    parser.add_argument("--cli", action="store_true", help="Sử dụng giao diện dòng lệnh")
    parser.add_argument("--gui", action="store_true", help="Sử dụng giao diện đồ họa")
    parser.add_argument("--url", help="URL video hoặc playlist để tải xuống")
    parser.add_argument("--output", help="Thư mục lưu file")
    parser.add_argument("--format", default="best", help="Format selector (mặc định: best)")
    parser.add_argument(
        "--audio-only",
        action="store_true",
        help="Chỉ tải audio và chuyển đổi sang MP3",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=1,
        help="Số luồng tải song song (mặc định: 1)",
    )

    args = parser.parse_args()

    if (not args.cli and not args.url) or args.gui:
        if GUI_AVAILABLE:
            try:
                app = GraphicalUserInterface()
                app.run()
                return
            except Exception as exc:
                print(f"Lỗi khi khởi tạo giao diện đồ họa: {exc}")
                print("Chuyển sang giao diện dòng lệnh...")
        else:
            print("Không thể tạo giao diện đồ họa. Vui lòng cài đặt tkinter.")
            print("Chuyển sang giao diện dòng lệnh...")

    if args.url:
        _run_cli_with_url(args)
    else:
        cli = CommandLineInterface()
        cli.run()


if __name__ == "__main__":
    main()
