"""Graphical user interface for the downloader."""

from __future__ import annotations

import logging
import os
import sys
import threading
import traceback
from typing import Dict, Optional

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk

    GUI_AVAILABLE = True
except ImportError:  # pragma: no cover - environments without tkinter
    tk = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]
    scrolledtext = None  # type: ignore[assignment]
    filedialog = None  # type: ignore[assignment]
    messagebox = None  # type: ignore[assignment]
    GUI_AVAILABLE = False

from .config import ConfigManager
from .constants import DEFAULT_DOWNLOAD_DIR, STATE_FILE, VERSION
from .downloader import YouTubeDownloader
from .models import DownloadOptions, DownloadTask
from .theme import ColorTheme, ModernStyle
from .utils import format_duration
from .versioning import VersionChecker, yt_dlp_version

logger = logging.getLogger(__name__)


class GraphicalUserInterface:
    """Tk GUI for YouTube Downloader Pro."""

    def __init__(self) -> None:
        if not GUI_AVAILABLE:
            raise ImportError("Không thể tạo giao diện đồ họa. Vui lòng cài đặt tkinter.")

        self.config_manager = ConfigManager()
        self.downloader = YouTubeDownloader(self.config_manager)
        self.downloader.add_progress_callback(self.update_progress)

        self.root = tk.Tk()
        self.root.title(f"🎬 YouTube Downloader Pro {VERSION}")
        self.root.geometry("900x700")
        self.root.minsize(900, 700)
        self.root.configure(bg=ColorTheme.BACKGROUND)

        self.style = ModernStyle.configure_ttk_style()

        try:
            # self.root.iconbitmap("icon.ico")
            pass
        except Exception:
            pass

        self.setup_ui()
        self.setup_styles()

        self.root.after(1000, self.check_for_updates)

    def setup_styles(self) -> None:
        style = ttk.Style()

        style.configure(
            "Modern.TNotebook",
            background=ColorTheme.BACKGROUND,
            borderwidth=0,
        )
        style.configure(
            "Modern.TNotebook.Tab",
            padding=[20, 10],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Modern.TEntry",
            fieldbackground="white",
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Modern.TCheckbutton",
            background=ColorTheme.FRAME_BACKGROUND,
            font=("Segoe UI", 10),
        )

        style.configure(
            "Success.TButton",
            background="#28a745",
            foreground="#538C51",
            font=("Segoe UI", 10, "bold"),
            padding=[15, 8],
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Success.TButton",
            background=[
                ("active", "#218838"),
                ("pressed", "#1e7e34"),
                ("disabled", "#6c757d"),
            ],
            foreground=[
                ("active", "#B9B7B3"),
                ("pressed", "#B9B7B3"),
                ("disabled", "#707070"),
            ],
        )

        style.configure(
            "Warning.TButton",
            background="#fd7e14",
            foreground="#F2D399",
            font=("Segoe UI", 10, "bold"),
            padding=[15, 8],
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Warning.TButton",
            background=[
                ("active", "#e8690b"),
                ("pressed", "#d35400"),
                ("disabled", "#6c757d"),
            ],
            foreground=[
                ("active", "#B9B7B3"),
                ("pressed", "#B9B7B3"),
                ("disabled", "#707070"),
            ],
        )

        style.configure(
            "Danger.TButton",
            background="#dc3545",
            foreground="#F24444",
            font=("Segoe UI", 10, "bold"),
            padding=[15, 8],
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Danger.TButton",
            background=[
                ("active", "#c82333"),
                ("pressed", "#bd2130"),
                ("disabled", "#6c757d"),
            ],
            foreground=[
                ("active", "#B9B7B3"),
                ("pressed", "#B9B7B3"),
                ("disabled", "#707070"),
            ],
        )

        style.configure(
            "Primary.TButton",
            background=ColorTheme.PRIMARY_BLUE,
            foreground="#B16E4B",
            font=("Segoe UI", 10, "bold"),
            padding=[15, 8],
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Primary.TButton",
            background=[
                ("active", "#0056b3"),
                ("pressed", "#004085"),
                ("disabled", "#6c757d"),
            ],
            foreground=[
                ("active", "#B9B7B3"),
                ("pressed", "#B9B7B3"),
                ("disabled", "#707070"),
            ],
        )

    def create_menu(self) -> None:
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Tải xuống", command=self.start_download)
        file_menu.add_command(label="Phân tích URL", command=self.analyze_url)
        file_menu.add_separator()
        file_menu.add_command(label="Tiếp tục tải xuống", command=self.resume_downloads)
        file_menu.add_command(label="Xóa lịch sử tải", command=self.clear_download_history)
        file_menu.add_separator()
        file_menu.add_command(label="Thoát", command=self.root.quit)
        menubar.add_cascade(label="Tệp", menu=file_menu)

        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Cài đặt", command=self.show_settings)
        menubar.add_cascade(label="Cài đặt", menu=settings_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Hướng dẫn sử dụng", command=self.show_help)
        help_menu.add_command(label="Giới thiệu", command=self.show_about)
        menubar.add_cascade(label="Trợ giúp", menu=help_menu)

        self.root.config(menu=menubar)

    def setup_ui(self) -> None:
        self.create_menu()

        main_container = tk.Frame(self.root, bg=ColorTheme.BACKGROUND)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        header_frame = ttk.Frame(main_container, style="Card.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 15))

        title_frame = tk.Frame(header_frame, bg=ColorTheme.CARD_BACKGROUND)
        title_frame.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(
            title_frame,
            text="🎬 YouTube Downloader Pro",
            font=("Segoe UI", 16, "bold"),
            fg=ColorTheme.TEXT_PRIMARY,
            bg=ColorTheme.CARD_BACKGROUND,
        ).pack(side=tk.LEFT)

        tk.Label(
            title_frame,
            text=f"v{VERSION}",
            font=("Segoe UI", 10),
            fg=ColorTheme.TEXT_SECONDARY,
            bg=ColorTheme.CARD_BACKGROUND,
        ).pack(side=tk.RIGHT)

        url_frame = ttk.LabelFrame(
            main_container,
            text="🔗 Nhập URL YouTube",
            style="Modern.TLabelframe",
            padding=15,
        )
        url_frame.pack(fill=tk.X, pady=(0, 15))

        url_input_frame = tk.Frame(url_frame, bg=ColorTheme.FRAME_BACKGROUND)
        url_input_frame.pack(fill=tk.X)

        tk.Label(
            url_input_frame,
            text="URL:",
            font=("Segoe UI", 10, "bold"),
            fg=ColorTheme.TEXT_PRIMARY,
            bg=ColorTheme.FRAME_BACKGROUND,
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.url_entry = ttk.Entry(
            url_input_frame, style="Modern.TEntry", font=("Segoe UI", 10)
        )
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.analyze_button = ttk.Button(
            url_input_frame,
            text="🔍 Phân tích",
            command=self.analyze_url,
            style="Primary.TButton",
        )
        self.analyze_button.pack(side=tk.LEFT)

        self.info_frame = ttk.LabelFrame(
            main_container,
            text="ℹ️ Thông tin Video/Playlist",
            style="Modern.TLabelframe",
            padding=15,
        )
        self.info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        text_frame = tk.Frame(self.info_frame, bg=ColorTheme.FRAME_BACKGROUND)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.info_text = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            height=8,
            font=("Consolas", 9),
            bg="white",
            fg=ColorTheme.TEXT_PRIMARY,
            selectbackground=ColorTheme.SECONDARY_BLUE,
            relief="solid",
            borderwidth=1,
        )
        self.info_text.pack(fill=tk.BOTH, expand=True)
        self.info_text.insert(
            tk.END, "🔔 Nhập URL YouTube và nhấn 'Phân tích' để bắt đầu."
        )
        self.info_text.config(state=tk.DISABLED)

        self.options_frame = ttk.LabelFrame(
            main_container,
            text="⚙️ Tùy chọn tải xuống",
            style="Modern.TLabelframe",
            padding=15,
        )
        self.options_frame.pack(fill=tk.X, pady=(0, 15))
        self.options_frame.columnconfigure(1, weight=1)

        tk.Label(
            self.options_frame,
            text="🎯 Chế độ tải:",
            font=("Segoe UI", 10, "bold"),
            fg=ColorTheme.TEXT_PRIMARY,
            bg=ColorTheme.FRAME_BACKGROUND,
        ).grid(row=0, column=0, sticky=tk.W, pady=5)

        self.download_mode = tk.StringVar(value="3")
        modes = [
            ("🎵 Audio (MP3)", "1"),
            ("🎥 Video (không audio)", "2"),
            ("🎞️ Video + Audio (MP4)", "3"),
            ("🧩 Format cụ thể", "4"),
        ]

        mode_frame = tk.Frame(self.options_frame, bg=ColorTheme.FRAME_BACKGROUND)
        mode_frame.grid(row=0, column=1, sticky=tk.W, pady=5)

        for idx, (text, value) in enumerate(modes):
            ttk.Radiobutton(
                mode_frame,
                text=text,
                value=value,
                variable=self.download_mode,
                style="Modern.TRadiobutton",
            ).grid(row=0, column=idx, padx=(0, 15), sticky=tk.W)

        tk.Label(
            self.options_frame,
            text="🧾 Format ID:",
            font=("Segoe UI", 10),
            fg=ColorTheme.TEXT_SECONDARY,
            bg=ColorTheme.FRAME_BACKGROUND,
        ).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.format_entry = ttk.Entry(self.options_frame, width=20, style="Modern.TEntry")
        self.format_entry.grid(row=1, column=1, sticky=tk.W, pady=5)

        tk.Label(
            self.options_frame,
            text="📁 Thư mục lưu:",
            font=("Segoe UI", 10, "bold"),
            fg=ColorTheme.TEXT_PRIMARY,
            bg=ColorTheme.FRAME_BACKGROUND,
        ).grid(row=2, column=0, sticky=tk.W, pady=5, padx=(0, 8))

        self.save_dir_entry = ttk.Entry(self.options_frame, style="Modern.TEntry")
        self.save_dir_entry.grid(row=2, column=1, sticky="ew", pady=5)
        self.save_dir_entry.insert(
            0, self.config_manager.get_download_options().download_dir
        )

        self.browse_button = ttk.Button(
            self.options_frame,
            text="📂 Duyệt...",
            command=self.browse_directory,
            style="Warning.TButton",
        )
        self.browse_button.grid(row=2, column=2, sticky="e", padx=(8, 0), pady=5)

        advanced_frame = tk.Frame(self.options_frame, bg=ColorTheme.FRAME_BACKGROUND)
        advanced_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        for idx in range(6):
            advanced_frame.columnconfigure(idx, weight=0)
        advanced_frame.columnconfigure(6, weight=1)

        self.download_thumbnail = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            advanced_frame,
            text="🖼️ Tải thumbnail",
            variable=self.download_thumbnail,
            style="Modern.TCheckbutton",
        ).grid(row=0, column=0, padx=(0, 20), sticky="w")

        self.download_subtitle = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            advanced_frame,
            text="📝 Tải subtitle",
            variable=self.download_subtitle,
            style="Modern.TCheckbutton",
        ).grid(row=0, column=1, padx=(0, 20), sticky="w")

        tk.Label(
            advanced_frame,
            text="⚡ Số luồng (khuyến nghị: 7, tối đa: 10):",
            font=("Segoe UI", 9),
            fg=ColorTheme.TEXT_SECONDARY,
            bg=ColorTheme.FRAME_BACKGROUND,
        ).grid(row=0, column=2, padx=(0, 5), sticky="w")

        self.max_workers = tk.StringVar(value="1")
        ttk.Spinbox(
            advanced_frame,
            from_=1,
            to=10,
            width=5,
            textvariable=self.max_workers,
            font=("Segoe UI", 9),
        ).grid(row=0, column=3, sticky="w")

        tk.Label(advanced_frame, bg=ColorTheme.FRAME_BACKGROUND).grid(
            row=0, column=6, sticky="ew"
        )

        self.download_button = ttk.Button(
            advanced_frame,
            text="⬇️ Tải xuống",
            command=self.start_download,
            style="Success.TButton",
        )
        self.download_button.grid(row=0, column=7, sticky="e", padx=(0, 8))

        self.cancel_button = ttk.Button(
            advanced_frame,
            text="🛑 Hủy",
            command=self.cancel_download,
            style="Danger.TButton",
            state=tk.DISABLED,
        )
        self.cancel_button.grid(row=0, column=8, sticky="e")

        self.progress_frame = ttk.LabelFrame(
            main_container,
            text="📊 Tiến trình tải xuống",
            style="Modern.TLabelframe",
            padding=5,
        )
        self.progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ("filename", "status", "progress", "speed", "eta")
        self.downloads_tree = ttk.Treeview(
            self.progress_frame,
            columns=columns,
            show="headings",
            style="Modern.Treeview",
            height=10,
        )

        headers = {
            "filename": "📄 Tên file",
            "status": "🚥 Trạng thái",
            "progress": "📈 Tiến trình",
            "speed": "⚡ Tốc độ",
            "eta": "⏳ Thời gian còn lại",
        }
        for col, header in headers.items():
            self.downloads_tree.heading(col, text=header, anchor="center")
            self.downloads_tree.column(
                col, width=120, minwidth=80, stretch=True, anchor="center"
            )

        self.downloads_tree.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        scrollbar = ttk.Scrollbar(
            self.progress_frame, orient=tk.VERTICAL, command=self.downloads_tree.yview
        )
        self.downloads_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.status_var = tk.StringVar(value="⏺️ Sẵn sàng")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg=ColorTheme.PRIMARY_BLUE,
            fg="white",
            font=("Segoe UI", 9),
            height=1,
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def update_progress(self, task: DownloadTask) -> None:
        payload = {
            "filename": task.progress.filename,
            "status": task.progress.status,
            "percent": f"{task.progress.percent:.1f}",
            "speed": task.progress.speed,
            "eta": task.progress.eta,
            "error": task.progress.error_message,
        }
        self.root.after(0, self._update_progress_ui, payload)

    def _update_progress_ui(self, payload: Dict[str, str]) -> None:
        filename = payload["filename"]
        if not filename:
            return

        item_id: Optional[str] = None
        for item in self.downloads_tree.get_children():
            values = self.downloads_tree.item(item, "values")
            if values and values[0] == filename:
                item_id = item
                break

        if item_id is None:
            item_id = self.downloads_tree.insert(
                "", "end", values=(filename, "Đang tải", "0%", "N/A", "N/A")
            )

        status = payload["status"]
        if status == "downloading":
            self.downloads_tree.item(
                item_id,
                values=(
                    filename,
                    "Đang tải",
                    f"{payload['percent']}%",
                    payload["speed"],
                    payload["eta"],
                ),
            )
            self.status_var.set(
                f"Đang tải: {payload['percent']}% | {payload['speed']} | ETA: {payload['eta']}"
            )
        elif status == "finished":
            self.downloads_tree.item(
                item_id, values=(filename, "Hoàn thành", "100%", "", "")
            )
            self.status_var.set(f"Đã tải xong: {filename}")
        elif status == "error":
            self.downloads_tree.item(
                item_id,
                values=(filename, "Lỗi", "", "", payload["error"]),
            )
            self.status_var.set(f"Lỗi: {payload['error']}")

    def analyze_url(self) -> None:
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập URL YouTube.")
            return

        self.status_var.set("Đang phân tích URL...")
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, "Đang phân tích URL, vui lòng đợi...")
        self.info_text.config(state=tk.DISABLED)
        self.root.update()

        try:
            is_playlist = self.downloader.is_playlist(url)

            if is_playlist:
                playlist_info = self.downloader.get_playlist_info(url)

                self.info_text.config(state=tk.NORMAL)
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, "=== THÔNG TIN PLAYLIST ===\n")
                self.info_text.insert(tk.END, f"Tiêu đề: {playlist_info.title}\n")
                self.info_text.insert(tk.END, f"Kênh: {playlist_info.uploader}\n")
                self.info_text.insert(
                    tk.END, f"Số lượng video: {playlist_info.video_count}\n\n"
                )

                if playlist_info.video_count > 10:
                    self.info_text.insert(
                        tk.END,
                        f"⚠️ Playlist này có {playlist_info.video_count} video. Tải xuống có thể mất nhiều thời gian.\n\n",
                    )

                self.info_text.config(state=tk.DISABLED)
                self.status_var.set(f"Đã phân tích playlist: {playlist_info.title}")
            else:
                video_info = self.downloader.get_video_info(url)

                self.info_text.config(state=tk.NORMAL)
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, "=== THÔNG TIN VIDEO ===\n")
                self.info_text.insert(tk.END, f"Tiêu đề: {video_info.title}\n")
                self.info_text.insert(tk.END, f"Kênh: {video_info.uploader}\n")
                self.info_text.insert(
                    tk.END, f"Thời lượng: {format_duration(video_info.duration)}\n"
                )
                if video_info.view_count:
                    self.info_text.insert(
                        tk.END, f"Lượt xem: {video_info.view_count:,}\n".replace(",", ".")
                    )
                self.info_text.insert(tk.END, f"Ngày đăng: {video_info.upload_date}\n\n")

                self.info_text.insert(tk.END, "=== ĐỊNH DẠNG CÓ SẴN ===\n")

                video_formats = [f for f in video_info.formats if f.has_video]
                video_formats.sort(
                    key=lambda f: int(f.resolution.replace("p", ""))
                    if f.resolution.replace("p", "").isdigit()
                    else 0,
                    reverse=True,
                )

                self.info_text.insert(tk.END, "Video:\n")
                for fmt in video_formats[:5]:
                    self.info_text.insert(tk.END, f" • {fmt}\n")
                if len(video_formats) > 5:
                    self.info_text.insert(
                        tk.END, f" • ... và {len(video_formats) - 5} định dạng khác\n"
                    )

                audio_formats = [
                    f for f in video_info.formats if not f.has_video and f.has_audio
                ]
                audio_formats.sort(key=lambda f: f.bitrate, reverse=True)

                self.info_text.insert(tk.END, "\nAudio:\n")
                for fmt in audio_formats[:3]:
                    self.info_text.insert(tk.END, f" • {fmt}\n")
                if len(audio_formats) > 3:
                    self.info_text.insert(
                        tk.END, f" • ... và {len(audio_formats) - 3} định dạng khác\n"
                    )

                self.info_text.config(state=tk.DISABLED)
                self.status_var.set(f"Đã phân tích video: {video_info.title}")
        except Exception as exc:
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, f"Lỗi khi phân tích URL:\n{exc}")
            self.info_text.config(state=tk.DISABLED)
            self.status_var.set("Lỗi khi phân tích URL")
            logger.error("Lỗi khi phân tích URL: %s", exc)
            traceback.print_exc()

    def browse_directory(self) -> None:
        directory = filedialog.askdirectory(initialdir=self.save_dir_entry.get())
        if directory:
            self.save_dir_entry.delete(0, tk.END)
            self.save_dir_entry.insert(0, directory)

    def get_download_options(self) -> DownloadOptions:
        options = self.config_manager.get_download_options()

        options.download_dir = self.save_dir_entry.get() or DEFAULT_DOWNLOAD_DIR
        try:
            max_workers_value = int(self.max_workers.get())
        except ValueError:
            max_workers_value = options.max_workers or 1
            messagebox.showwarning(
                "Cảnh báo", "Số luồng không hợp lệ. Đã sử dụng giá trị gần nhất."
            )

        if max_workers_value > 10:
            max_workers_value = 10
            messagebox.showwarning(
                "Cảnh báo", "Số luồng tối đa là 10. Đã điều chỉnh về 10."
            )
        elif max_workers_value < 1:
            max_workers_value = 1
            messagebox.showwarning(
                "Cảnh báo", "Số luồng tối thiểu là 1. Đã điều chỉnh về 1."
            )

        options.max_workers = max_workers_value
        options.download_thumbnails = self.download_thumbnail.get()
        options.download_subtitles = self.download_subtitle.get()
        options.output_template = os.path.join(
            options.download_dir, "%(title)s.%(ext)s"
        )

        mode = self.download_mode.get()
        if mode == "1":
            options.format_selector = "bestaudio"
            options.convert_to_mp3 = True
            options.audio_quality = "192"
            options.merge = False
        elif mode == "2":
            options.format_selector = "bestvideo[ext=mp4]"
            options.convert_to_mp3 = False
            options.merge = False
        elif mode == "3":
            options.format_selector = "bestvideo[ext=mp4]+bestaudio/best"
            options.merge = True
            options.merge_format = "mp4"
            options.convert_to_mp3 = False
        elif mode == "4":
            format_id = self.format_entry.get().strip()
            if format_id:
                options.format_selector = format_id
                options.merge = "+" in format_id
                options.merge_format = "mp4"
                options.convert_to_mp3 = False

        self.config_manager.update_from_options(options)
        return options

    def start_download(self) -> None:
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập URL YouTube.")
            return

        options = self.get_download_options()

        try:
            os.makedirs(options.download_dir, exist_ok=True)
        except Exception as exc:
            messagebox.showerror(
                "Lỗi",
                f"Không thể tạo thư mục: {options.download_dir}\nLỗi: {exc}",
            )
            return

        self.download_button.config(state=tk.DISABLED)
        self.analyze_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)

        for item in self.downloads_tree.get_children():
            self.downloads_tree.delete(item)

        self.status_var.set("Đang bắt đầu tải xuống...")

        self.download_thread = threading.Thread(
            target=self._download_thread, args=(url, options), daemon=True
        )
        self.download_thread.start()

    def _download_thread(self, url: str, options: DownloadOptions) -> None:
        try:
            success = self.downloader.download(url, options)
            self.root.after(0, self._download_completed, success)
        except Exception as exc:
            logger.error("Lỗi khi tải xuống: %s", exc)
            traceback.print_exc()
            self.root.after(0, self._download_error, str(exc))

    def _download_completed(self, success: bool) -> None:
        self.download_button.config(state=tk.NORMAL)
        self.analyze_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)

        if success:
            self.status_var.set("Tải xuống hoàn tất!")
            messagebox.showinfo("Thông báo", "Tải xuống hoàn tất!")
        else:
            self.status_var.set("Tải xuống không thành công. Xem log để biết chi tiết.")
            messagebox.showerror(
                "Lỗi", "Tải xuống không thành công. Xem log để biết chi tiết."
            )

    def _download_error(self, error_message: str) -> None:
        self.download_button.config(state=tk.NORMAL)
        self.analyze_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)

        self.status_var.set(f"Lỗi: {error_message}")
        messagebox.showerror("Lỗi", f"Lỗi khi tải xuống: {error_message}")

    def cancel_download(self) -> None:
        if messagebox.askyesno(
            "Xác nhận", "Bạn có chắc muốn hủy tất cả các tải xuống đang chạy?"
        ):
            self.downloader.cancel_all_downloads()
            self.status_var.set("Đã hủy tất cả các tải xuống.")
            self.download_button.config(state=tk.NORMAL)
            self.analyze_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)

    def check_for_updates(self) -> None:
        try:
            has_update, latest_version = VersionChecker.check_for_updates()
            if has_update:
                if messagebox.askyesno(
                    "Cập nhật có sẵn",
                    f"Có phiên bản mới của yt-dlp: {latest_version} (hiện tại: {yt_dlp_version}).\n\nBạn có muốn cập nhật ngay?",
                ):
                    self.status_var.set("Đang cập nhật yt-dlp...")
                    success = VersionChecker.update_yt_dlp()

                    if success:
                        messagebox.showinfo(
                            "Cập nhật thành công",
                            "Đã cập nhật yt-dlp thành công. Vui lòng khởi động lại ứng dụng.",
                        )
                        self.root.quit()
                    else:
                        messagebox.showerror(
                            "Lỗi cập nhật",
                            "Không thể cập nhật yt-dlp. Vui lòng thử lại sau hoặc cập nhật thủ công.",
                        )
        except Exception as exc:
            logger.error("Lỗi khi kiểm tra cập nhật: %s", exc)

    def resume_downloads(self) -> None:
        tasks_data = self.config_manager.load_download_state()
        if not tasks_data:
            messagebox.showinfo("Thông báo", "Không có tải xuống nào cần tiếp tục.")
            return

        if messagebox.askyesno(
            "Tiếp tục tải xuống",
            f"Tìm thấy {len(tasks_data)} tải xuống bị gián đoạn. Bạn có muốn tiếp tục?",
        ):
            for item in self.downloads_tree.get_children():
                self.downloads_tree.delete(item)

            self.download_button.config(state=tk.DISABLED)
            self.analyze_button.config(state=tk.DISABLED)
            self.cancel_button.config(state=tk.NORMAL)
            self.status_var.set("Đang tiếp tục tải xuống...")

            self.download_thread = threading.Thread(
                target=self._resume_thread, daemon=True
            )
            self.download_thread.start()

    def _resume_thread(self) -> None:
        try:
            success = self.downloader.resume_downloads()
            self.root.after(0, self._download_completed, success)
        except Exception as exc:
            logger.error("Lỗi khi tiếp tục tải xuống: %s", exc)
            traceback.print_exc()
            self.root.after(0, self._download_error, str(exc))

    def clear_download_history(self) -> None:
        if messagebox.askyesno(
            "Xác nhận", "Bạn có chắc muốn xóa lịch sử tải xuống?"
        ):
            try:
                if os.path.exists(STATE_FILE):
                    os.remove(STATE_FILE)
                    messagebox.showinfo("Thông báo", "Đã xóa lịch sử tải xuống.")
                else:
                    messagebox.showinfo("Thông báo", "Không có lịch sử tải xuống.")
            except Exception as exc:
                messagebox.showerror("Lỗi", f"Không thể xóa lịch sử tải xuống: {exc}")

    def show_settings(self) -> None:
        settings_window = tk.Toplevel(self.root)
        settings_window.title("⚙️ Cài đặt")
        settings_window.geometry("700x500")
        settings_window.minsize(700, 500)
        settings_window.configure(bg=ColorTheme.BACKGROUND)
        settings_window.grab_set()

        header = tk.Frame(settings_window, bg=ColorTheme.PRIMARY_BLUE, height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="⚙️ Cài đặt ứng dụng",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg=ColorTheme.PRIMARY_BLUE,
        ).pack(expand=True)

        notebook = ttk.Notebook(settings_window, style="Modern.TNotebook")
        notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        general_tab = tk.Frame(
            notebook, bg=ColorTheme.FRAME_BACKGROUND, padx=20, pady=20
        )
        notebook.add(general_tab, text="🏠 Chung")

        tk.Label(
            general_tab,
            text="📁 Thư mục lưu mặc định:",
            font=("Segoe UI", 10, "bold"),
            fg=ColorTheme.TEXT_PRIMARY,
            bg=ColorTheme.FRAME_BACKGROUND,
        ).grid(row=0, column=0, sticky=tk.W, pady=10)

        dir_frame = tk.Frame(general_tab, bg=ColorTheme.FRAME_BACKGROUND)
        dir_frame.grid(row=0, column=1, sticky=tk.W + tk.E, pady=10, padx=(10, 0))
        dir_frame.columnconfigure(0, weight=1)

        default_dir = self.config_manager.get_download_options().download_dir
        self.default_dir_entry = ttk.Entry(
            dir_frame, width=40, style="Modern.TEntry"
        )
        self.default_dir_entry.grid(row=0, column=0, sticky=tk.W + tk.E, padx=(0, 10))
        self.default_dir_entry.insert(0, default_dir)

        browse_button = ttk.Button(
            dir_frame,
            text="📂 Duyệt...",
            command=self.browse_default_directory,
            style="Warning.TButton",
        )
        browse_button.grid(row=0, column=1)

        tk.Label(
            general_tab,
            text="⚡ Số luồng tải xuống:",
            font=("Segoe UI", 10, "bold"),
            fg=ColorTheme.TEXT_PRIMARY,
            bg=ColorTheme.FRAME_BACKGROUND,
        ).grid(row=1, column=0, sticky=tk.W, pady=10)

        max_workers = self.config_manager.get_download_options().max_workers
        self.default_max_workers = tk.StringVar(value=str(max_workers))

        workers_frame = tk.Frame(general_tab, bg=ColorTheme.FRAME_BACKGROUND)
        workers_frame.grid(row=1, column=1, sticky=tk.W, pady=10, padx=(10, 0))

        ttk.Spinbox(
            workers_frame,
            from_=1,
            to=10,
            width=5,
            textvariable=self.default_max_workers,
            font=("Segoe UI", 10),
        ).pack(side=tk.LEFT)

        tk.Label(
            workers_frame,
            text="(khuyến nghị: 7, tối đa: 10)",
            font=("Segoe UI", 9),
            fg=ColorTheme.TEXT_SECONDARY,
            bg=ColorTheme.FRAME_BACKGROUND,
        ).pack(side=tk.LEFT, padx=(10, 0))

        self.check_updates = tk.BooleanVar(
            value=self.config_manager.config.getboolean(
                "general", "check_for_updates", fallback=True
            )
        )

        update_frame = tk.Frame(general_tab, bg=ColorTheme.FRAME_BACKGROUND)
        update_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=10)

        ttk.Checkbutton(
            update_frame,
            text="🔔 Tự động kiểm tra cập nhật yt-dlp",
            variable=self.check_updates,
            style="Modern.TCheckbutton",
        ).pack(side=tk.LEFT)

        download_tab = tk.Frame(
            notebook, bg=ColorTheme.FRAME_BACKGROUND, padx=20, pady=20
        )
        notebook.add(download_tab, text="⬇️ Tải xuống")

        tk.Label(
            download_tab,
            text="🔁 Số lần thử lại:",
            font=("Segoe UI", 10, "bold"),
            fg=ColorTheme.TEXT_PRIMARY,
            bg=ColorTheme.FRAME_BACKGROUND,
        ).grid(row=0, column=0, sticky=tk.W, pady=10)

        default_options = self.config_manager.get_download_options()
        self.retry_count = tk.StringVar(value=str(default_options.retry_count))
        ttk.Entry(
            download_tab, width=10, textvariable=self.retry_count, style="Modern.TEntry"
        ).grid(row=0, column=1, sticky=tk.W, pady=10, padx=(10, 0))

        tk.Label(
            download_tab,
            text="⏱️ Khoảng nghỉ giữa các lần tải (giây):",
            font=("Segoe UI", 10, "bold"),
            fg=ColorTheme.TEXT_PRIMARY,
            bg=ColorTheme.FRAME_BACKGROUND,
        ).grid(row=1, column=0, sticky=tk.W, pady=10)

        self.sleep_interval = tk.StringVar(value=str(default_options.sleep_interval))
        ttk.Entry(
            download_tab, width=10, textvariable=self.sleep_interval, style="Modern.TEntry"
        ).grid(row=1, column=1, sticky=tk.W, pady=10, padx=(10, 0))

        tk.Label(
            download_tab,
            text="🚀 Giới hạn tốc độ tải:",
            font=("Segoe UI", 10, "bold"),
            fg=ColorTheme.TEXT_PRIMARY,
            bg=ColorTheme.FRAME_BACKGROUND,
        ).grid(row=2, column=0, sticky=tk.W, pady=10)

        self.rate_limit = tk.StringVar(value=default_options.rate_limit)
        ttk.Entry(
            download_tab, width=20, textvariable=self.rate_limit, style="Modern.TEntry"
        ).grid(row=2, column=1, sticky=tk.W, pady=10, padx=(10, 0))

        self.default_download_thumbnail = tk.BooleanVar(
            value=default_options.download_thumbnails
        )
        ttk.Checkbutton(
            download_tab,
            text="🖼️ Tải thumbnail theo mặc định",
            variable=self.default_download_thumbnail,
            style="Modern.TCheckbutton",
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=10)

        self.default_download_subtitle = tk.BooleanVar(
            value=default_options.download_subtitles
        )
        ttk.Checkbutton(
            download_tab,
            text="📝 Tải subtitle theo mặc định",
            variable=self.default_download_subtitle,
            style="Modern.TCheckbutton",
        ).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=10)

        tk.Label(
            download_tab,
            text="🌐 Ngôn ngữ subtitle:",
            font=("Segoe UI", 10, "bold"),
            fg=ColorTheme.TEXT_PRIMARY,
            bg=ColorTheme.FRAME_BACKGROUND,
        ).grid(row=5, column=0, sticky=tk.W, pady=10)

        subtitle_langs = ",".join(default_options.subtitle_languages)
        self.subtitle_langs = tk.StringVar(value=subtitle_langs)

        lang_frame = tk.Frame(download_tab, bg=ColorTheme.FRAME_BACKGROUND)
        lang_frame.grid(row=5, column=1, sticky=tk.W, pady=10, padx=(10, 0))

        ttk.Entry(
            lang_frame, width=20, textvariable=self.subtitle_langs, style="Modern.TEntry"
        ).pack(side=tk.LEFT)

        tk.Label(
            lang_frame,
            text="(phân cách bằng dấu phẩy)",
            font=("Segoe UI", 9),
            fg=ColorTheme.TEXT_SECONDARY,
            bg=ColorTheme.FRAME_BACKGROUND,
        ).pack(side=tk.LEFT, padx=(10, 0))

        auth_tab = tk.Frame(notebook, bg=ColorTheme.FRAME_BACKGROUND, padx=20, pady=20)
        notebook.add(auth_tab, text="🔐 Xác thực")

        self.use_proxy = tk.BooleanVar(value=bool(default_options.proxy))

        proxy_check_frame = tk.Frame(auth_tab, bg=ColorTheme.FRAME_BACKGROUND)
        proxy_check_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=10)

        ttk.Checkbutton(
            proxy_check_frame,
            text="🌐 Sử dụng proxy",
            variable=self.use_proxy,
            command=self.toggle_proxy,
            style="Modern.TCheckbutton",
        ).pack(side=tk.LEFT)

        tk.Label(
            auth_tab,
            text="🔗 Địa chỉ proxy:",
            font=("Segoe UI", 10, "bold"),
            fg=ColorTheme.TEXT_PRIMARY,
            bg=ColorTheme.FRAME_BACKGROUND,
        ).grid(row=1, column=0, sticky=tk.W, pady=10)

        self.proxy = tk.StringVar(value=default_options.proxy)

        proxy_frame = tk.Frame(auth_tab, bg=ColorTheme.FRAME_BACKGROUND)
        proxy_frame.grid(row=1, column=1, sticky=tk.W + tk.E, pady=10, padx=(10, 0))
        proxy_frame.columnconfigure(0, weight=1)

        self.proxy_entry = ttk.Entry(
            proxy_frame, textvariable=self.proxy, style="Modern.TEntry"
        )
        self.proxy_entry.grid(row=0, column=0, sticky=tk.W + tk.E)

        if not self.use_proxy.get():
            self.proxy_entry.config(state=tk.DISABLED)

        tk.Label(
            proxy_frame,
            text="(ví dụ: socks5://127.0.0.1:1080)",
            font=("Segoe UI", 9),
            fg=ColorTheme.TEXT_SECONDARY,
            bg=ColorTheme.FRAME_BACKGROUND,
        ).grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

        self.use_cookies = tk.BooleanVar(value=default_options.use_cookies)

        cookies_check_frame = tk.Frame(auth_tab, bg=ColorTheme.FRAME_BACKGROUND)
        cookies_check_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(20, 10))

        ttk.Checkbutton(
            cookies_check_frame,
            text="🍪 Sử dụng cookies",
            variable=self.use_cookies,
            command=self.toggle_cookies,
            style="Modern.TCheckbutton",
        ).pack(side=tk.LEFT)

        tk.Label(
            auth_tab,
            text="📄 File cookies:",
            font=("Segoe UI", 10, "bold"),
            fg=ColorTheme.TEXT_PRIMARY,
            bg=ColorTheme.FRAME_BACKGROUND,
        ).grid(row=3, column=0, sticky=tk.W, pady=10)

        cookies_frame = tk.Frame(auth_tab, bg=ColorTheme.FRAME_BACKGROUND)
        cookies_frame.grid(row=3, column=1, sticky=tk.W + tk.E, pady=10, padx=(10, 0))
        cookies_frame.columnconfigure(0, weight=1)

        self.cookies_file = tk.StringVar(value=default_options.cookies_file)

        self.cookies_entry = ttk.Entry(
            cookies_frame, textvariable=self.cookies_file, style="Modern.TEntry"
        )
        self.cookies_entry.grid(row=0, column=0, sticky=tk.W + tk.E, padx=(0, 10))

        cookies_browse = ttk.Button(
            cookies_frame,
            text="📂 Duyệt...",
            command=self.browse_cookies_file,
            style="Warning.TButton",
        )
        cookies_browse.grid(row=0, column=1)

        if not self.use_cookies.get():
            self.cookies_entry.config(state=tk.DISABLED)
            cookies_browse.config(state=tk.DISABLED)
        self.cookies_browse = cookies_browse

        button_frame = tk.Frame(settings_window, bg=ColorTheme.BACKGROUND)
        button_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        ttk.Button(
            button_frame,
            text="💾 Lưu",
            command=lambda: self.save_settings(settings_window),
            style="Success.TButton",
        ).pack(side=tk.RIGHT, padx=(10, 0))

        ttk.Button(
            button_frame,
            text="🛑 Hủy",
            command=settings_window.destroy,
            style="Danger.TButton",
        ).pack(side=tk.RIGHT)

        general_tab.columnconfigure(1, weight=1)
        download_tab.columnconfigure(1, weight=1)
        auth_tab.columnconfigure(1, weight=1)

    def browse_default_directory(self) -> None:
        directory = filedialog.askdirectory(initialdir=self.default_dir_entry.get())
        if directory:
            self.default_dir_entry.delete(0, tk.END)
            self.default_dir_entry.insert(0, directory)

    def browse_cookies_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Chọn file cookies",
            filetypes=[
                ("Text files", "*.txt"),
                ("JSON files", "*.json"),
                ("All files", "*.*"),
            ],
        )
        if file_path:
            self.cookies_file.set(file_path)

    def toggle_proxy(self) -> None:
        if self.use_proxy.get():
            self.proxy_entry.config(state=tk.NORMAL)
        else:
            self.proxy_entry.config(state=tk.DISABLED)

    def toggle_cookies(self) -> None:
        if self.use_cookies.get():
            self.cookies_entry.config(state=tk.NORMAL)
            self.cookies_browse.config(state=tk.NORMAL)
        else:
            self.cookies_entry.config(state=tk.DISABLED)
            self.cookies_browse.config(state=tk.DISABLED)

    def save_settings(self, window: tk.Toplevel) -> None:
        try:
            self.config_manager.config.setdefault("general", {})
            self.config_manager.config["general"]["download_dir"] = (
                self.default_dir_entry.get()
            )
            self.config_manager.config["general"]["max_workers"] = (
                self.default_max_workers.get()
            )
            self.config_manager.config["general"]["check_for_updates"] = (
                str(self.check_updates.get()).lower()
            )

            self.config_manager.config.setdefault("download", {})
            self.config_manager.config["download"]["retry_count"] = self.retry_count.get()
            self.config_manager.config["download"]["sleep_interval"] = self.sleep_interval.get()
            self.config_manager.config["download"]["rate_limit"] = self.rate_limit.get()
            self.config_manager.config["download"]["download_thumbnails"] = str(
                self.default_download_thumbnail.get()
            ).lower()
            self.config_manager.config["download"]["download_subtitles"] = str(
                self.default_download_subtitle.get()
            ).lower()
            self.config_manager.config["download"]["subtitle_languages"] = (
                self.subtitle_langs.get()
            )

            self.config_manager.config.setdefault("authentication", {})
            self.config_manager.config["authentication"]["use_proxy"] = str(
                self.use_proxy.get()
            ).lower()
            self.config_manager.config["authentication"]["proxy"] = (
                self.proxy.get() if self.use_proxy.get() else ""
            )
            self.config_manager.config["authentication"]["use_cookies"] = str(
                self.use_cookies.get()
            ).lower()
            self.config_manager.config["authentication"]["cookies_file"] = (
                self.cookies_file.get() if self.use_cookies.get() else ""
            )

            self.config_manager.save_config()
            self.downloader.default_options = self.config_manager.get_download_options()

            self.save_dir_entry.delete(0, tk.END)
            self.save_dir_entry.insert(0, self.default_dir_entry.get())
            self.max_workers.set(self.default_max_workers.get())
            self.download_thumbnail.set(self.default_download_thumbnail.get())
            self.download_subtitle.set(self.default_download_subtitle.get())

            window.destroy()
            self.status_var.set("Đã lưu cài đặt.")
        except Exception as exc:
            messagebox.showerror("Lỗi", f"Không thể lưu cài đặt: {exc}")

    def show_help(self) -> None:
        help_window = tk.Toplevel(self.root)
        help_window.title("Hướng dẫn sử dụng")
        help_window.geometry("700x500")
        help_window.minsize(700, 500)

        help_text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, padx=10, pady=10)
        help_text.pack(fill=tk.BOTH, expand=True)

        help_content = """# HƯỚNG DẪN SỬ DỤNG YOUTUBE DOWNLOADER PRO

## Giới thiệu
YouTube downloader Pro là công cụ tải video/audio từ YouTube với nhiều tính năng nâng cao. Ứng dụng hỗ trợ tải video đơn lẻ hoặc playlist với nhiều tùy chọn định dạng khác nhau.

## Các bước cơ bản
1. Nhập URL video hoặc playlist YouTube vào ô URL
2. Nhấn nút "Phân tích" để lấy thông tin
3. Chọn chế độ tải xuống phù hợp
4. Nhấn nút "Tải xuống" để bắt đầu tải

## Các chế độ tải xuống
- **Chỉ audio (MP3)**: Tải audio chất lượng cao nhất và chuyển sang MP3
- **Chỉ video (không audio)**: Tải video MP4 không có âm thanh
- **Video + audio (MP4)**: Tải và ghép video+audio chất lượng cao nhất
- **Chọn format cụ thể**: Tải format cụ thể theo format ID

## Tùy chọn nâng cao
- **Tải thumbnail**: Tải hình thumbnail của video
- **Tải subtitle**: Tải phụ đề của video (nếu có)
- **Số luồng**: Số lượng video tải song song (đối với playlist)

## Cài đặt
Bạn có thể tùy chỉnh các cài đặt khác trong menu File > Cài đặt:
- Thư mục lưu mặc định
- Số luồng tải xuống
- Giới hạn tốc độ
- Proxy và cookies
- Và nhiều tùy chọn khác

## Yêu cầu hệ thống
- Python 3.6 trở lên
- FFmpeg (cần thiết để chuyển đổi định dạng)
- yt-dlp

## Lưu ý
- Việc tải xuống nội dung có bản quyền có thể vi phạm điều khoản dịch vụ của YouTube
- Chỉ sử dụng cho mục đích cá nhân và tuân thủ luật bản quyền
"""
        help_text.insert(tk.END, help_content)
        help_text.config(state=tk.DISABLED)

    def show_about(self) -> None:
        about_window = tk.Toplevel(self.root)
        about_window.title("Giới thiệu")
        about_window.geometry("400x300")
        about_window.minsize(400, 300)
        about_window.resizable(False, False)

        logo_frame = ttk.Frame(about_window)
        logo_frame.pack(pady=(20, 10))

        ttk.Label(
            logo_frame, text="YouTube downloader Pro", font=("Helvetica", 16, "bold")
        ).pack()

        info_frame = ttk.Frame(about_window)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        ttk.Label(info_frame, text=f"Phiên bản: {VERSION}").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"yt-dlp: {yt_dlp_version}").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Python: {sys.version.split()[0]}").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text="").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text="Tác giả: YouTube downloader Team").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text="Copyright © 2025").pack(anchor=tk.W, pady=2)

        ttk.Button(about_window, text="Đóng", command=about_window.destroy).pack(pady=(0, 20))

    def run(self) -> None:
        self.root.mainloop()
