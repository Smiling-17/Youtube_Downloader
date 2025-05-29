#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YouTube downloader Pro - Công cụ tải video/audio từ YouTube
Hỗ trợ tải video đơn lẻ và playlist với nhiều tùy chọn nâng cao
"""

import os
import re
import sys
import time
import json
import logging
import argparse
import threading
import traceback
import configparser
import urllib.request
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
import sys
import io
import copy


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


try:
    from yt_dlp import YoutubeDL
    from yt_dlp.version import __version__ as yt_dlp_version
except ImportError:
    print("Lỗi: Không thể import yt-dlp. Vui lòng cài đặt bằng lệnh: pip install yt-dlp")
    sys.exit(1)

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

def clean_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

# Thiết lập logging
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler("youtube_downloader.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("YouTubeDownloader")

# Các hằng số
VERSION = "2.0.0"
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".youtube_downloader_config.ini")
STATE_FILE = os.path.join(os.path.expanduser("~"), ".youtube_downloader_state.json")
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "YouTube")
YT_DLP_LATEST_VERSION_URL = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"

# Bảng màu cho giao diện
class ColorTheme:
    """Bảng màu chủ đạo cho ứng dụng"""
    # Màu chính
    PRIMARY_BLUE = "#87CEEB"      # Sky Blue - xanh da trời nhẹ
    PRIMARY_PINK = "#FFB6C1"      # Light Pink - hồng nhẹ  
    SECONDARY_BLUE = "#B0E0E6"    # Powder Blue - xanh nhạt hơn
    SECONDARY_PINK = "#FFCCCB"    # Light Coral - hồng san hô nhạt
    
    # Màu nền
    BACKGROUND = "#F8F9FA"        # Trắng kem nhẹ
    CARD_BACKGROUND = "#FFFFFF"   # Trắng tinh
    FRAME_BACKGROUND = "#F0F8FF"  # Alice Blue - xanh rất nhạt
    
    # Màu chữ
    TEXT_PRIMARY = "#2C3E50"      # Xám đen nhẹ
    TEXT_SECONDARY = "#5D6D7E"    # Xám xanh
    TEXT_SUCCESS = "#27AE60"      # Xanh lá thành công
    TEXT_ERROR = "#E74C3C"        # Đỏ lỗi
    TEXT_WARNING = "#F39C12"      # Cam cảnh báo
    
    # Màu nút
    BUTTON_PRIMARY = "#4A90E2"    # Xanh dương chính
    BUTTON_SUCCESS = "#5CB85C"    # Xanh lá thành công
    BUTTON_WARNING = "#F0AD4E"    # Cam cảnh báo
    BUTTON_DANGER = "#D9534F"     # Đỏ nguy hiểm
    BUTTON_HOVER = "#357ABD"      # Xanh đậm khi hover
    
    # Màu viền
    BORDER_LIGHT = "#E1E8ED"      # Viền nhẹ
    BORDER_MEDIUM = "#AAB8C2"     # Viền trung bình
    BORDER_FOCUS = "#4A90E2"      # Viền khi focus

class ModernStyle:
    """Tạo style hiện đại cho tkinter widgets"""
    
    @staticmethod
    def configure_ttk_style():
        """Cấu hình style cho ttk widgets"""
        style = ttk.Style()
        
        # Cấu hình style cho Frame
        style.configure("Modern.TFrame",
                       background=ColorTheme.FRAME_BACKGROUND,
                       relief="flat",
                       borderwidth=1)
        
        style.configure("Card.TFrame",
                       background=ColorTheme.CARD_BACKGROUND,
                       relief="solid",
                       borderwidth=1,
                       bordercolor=ColorTheme.BORDER_LIGHT)
        
        # Cấu hình style cho Label
        style.configure("Title.TLabel",
                       background=ColorTheme.FRAME_BACKGROUND,
                       foreground=ColorTheme.TEXT_PRIMARY,
                       font=("Segoe UI", 11, "bold"))
        
        style.configure("Modern.TLabel",
                       background=ColorTheme.FRAME_BACKGROUND,
                       foreground=ColorTheme.TEXT_SECONDARY,
                       font=("Segoe UI", 9))
        
        style.configure("Success.TLabel",
                       background=ColorTheme.FRAME_BACKGROUND,
                       foreground=ColorTheme.TEXT_SUCCESS,
                       font=("Segoe UI", 9))
        
        style.configure("Error.TLabel",
                       background=ColorTheme.FRAME_BACKGROUND,
                       foreground=ColorTheme.TEXT_ERROR,
                       font=("Segoe UI", 9))
        
        # Cấu hình style cho Button
        style.configure("Primary.TButton",
                       background=ColorTheme.BUTTON_PRIMARY,
                       foreground="#F2CB05",
                       font=("Segoe UI", 9, "bold"),
                       focuscolor="none",
                       borderwidth=0,
                       relief="flat",
                       padding=[12, 6])
        
        style.map("Primary.TButton",
                 background=[("active", ColorTheme.BUTTON_HOVER),
                           ("pressed", ColorTheme.BUTTON_HOVER)])
        
        style.configure("Success.TButton",
                       background=ColorTheme.BUTTON_SUCCESS,
                       foreground="#538C51",
                       font=("Segoe UI", 9, "bold"),
                       focuscolor="none",
                       borderwidth=0,
                       relief="flat",
                       padding=[12, 6])
        
        style.map("Success.TButton",
                 background=[("active", "#4cae4c"),
                           ("pressed", "#449d44")])
        
        style.configure("Warning.TButton",
                       background=ColorTheme.BUTTON_WARNING,
                       foreground="#F2CB05",
                       font=("Segoe UI", 9, "bold"),
                       focuscolor="none",
                       borderwidth=0,
                       relief="flat",
                       padding=[12, 6])
        
        style.map("Warning.TButton",
                 background=[("active", "#ec971f"),
                           ("pressed", "#d58512")])
        
        style.configure("Danger.TButton",
                       background=ColorTheme.BUTTON_DANGER,
                       foreground="#FA6E4F",
                       font=("Segoe UI", 9, "bold"),
                       focuscolor="none",
                       borderwidth=0,
                       relief="flat",
                       padding=[12, 6])
        
        style.map("Danger.TButton",
                 background=[("active", "#c9302c"),
                           ("pressed", "#ac2925")])
        
        # Cấu hình style cho Entry
        style.configure("Modern.TEntry",
                       fieldbackground="white",
                       bordercolor=ColorTheme.BORDER_LIGHT,
                       focuscolor=ColorTheme.BORDER_FOCUS,
                       borderwidth=2,
                       relief="solid",
                       font=("Segoe UI", 9))
        
        # Cấu hình style cho LabelFrame
        style.configure("Modern.TLabelframe",
                       background=ColorTheme.FRAME_BACKGROUND,
                       bordercolor=ColorTheme.BORDER_MEDIUM,
                       borderwidth=2,
                       relief="solid")
        
        style.configure("Modern.TLabelframe.Label",
                       background=ColorTheme.FRAME_BACKGROUND,
                       foreground=ColorTheme.TEXT_PRIMARY,
                       font=("Segoe UI", 10, "bold"))
        
        # Cấu hình style cho Radiobutton
        style.configure("Modern.TRadiobutton",
                       background=ColorTheme.FRAME_BACKGROUND,
                       foreground=ColorTheme.TEXT_SECONDARY,
                       font=("Segoe UI", 9),
                       focuscolor="none")
        
        # Cấu hình style cho Checkbutton
        style.configure("Modern.TCheckbutton",
                       background=ColorTheme.FRAME_BACKGROUND,
                       foreground=ColorTheme.TEXT_SECONDARY,
                       font=("Segoe UI", 9),
                       focuscolor="none")
        
        # Cấu hình style cho Treeview
        style.configure("Modern.Treeview",
                       background="white",
                       foreground=ColorTheme.TEXT_PRIMARY,
                       fieldbackground="white",
                       bordercolor=ColorTheme.BORDER_LIGHT,
                       borderwidth=1,
                       font=("Segoe UI", 9))
        
        style.configure("Modern.Treeview.Heading",
                       background=ColorTheme.PRIMARY_BLUE,
                       foreground="#F2A2B1",
                       font=("Segoe UI", 10, "bold"),
                       relief="flat")
        
        style.map("Modern.Treeview.Heading",
                 background=[("active", ColorTheme.BUTTON_HOVER)])
        
        style.map("Modern.Treeview",
                 background=[("selected", ColorTheme.SECONDARY_BLUE)])
        
        # Cấu hình style cho Notebook
        style.configure("Modern.TNotebook",
                       background=ColorTheme.FRAME_BACKGROUND,
                       borderwidth=0,
                       tabmargins=[0, 0, 0, 0])
        
        style.configure("Modern.TNotebook.Tab",
                       background=ColorTheme.SECONDARY_BLUE,
                       foreground=ColorTheme.TEXT_PRIMARY,
                       font=("Segoe UI", 9),
                       padding=[20, 10])
        
        style.map("Modern.TNotebook.Tab",
                 background=[("selected", ColorTheme.PRIMARY_BLUE),
                           ("active", ColorTheme.PRIMARY_PINK)])
        
        return style


# Các định nghĩa kiểu dữ liệu
@dataclass
class VideoFormat:
    format_id: str
    ext: str
    resolution: str = "N/A"
    fps: Union[int, str] = "N/A"
    filesize: int = 0
    has_audio: bool = False
    has_video: bool = False
    bitrate: float = 0
    
    def __str__(self) -> str:
        size_str = format_size(self.filesize) if self.filesize else "Không xác định"
        if self.has_video:
            return f"{self.format_id}: {self.resolution}, {self.fps} fps, {self.ext}, {size_str}, {'có audio' if self.has_audio else 'không audio'}"
        else:
            return f"{self.format_id}: audio {self.ext}, {self.bitrate} kbps, {size_str}"

@dataclass
class VideoInfo:
    video_id: str
    title: str
    uploader: str = "Không xác định"
    duration: int = 0
    view_count: int = 0
    upload_date: str = "Không xác định"
    formats: List[VideoFormat] = field(default_factory=list)
    thumbnail: str = ""
    description: str = ""
    url: str = ""
    
    @classmethod
    def from_yt_dlp_info(cls, info: Dict[str, Any]) -> 'VideoInfo':
        """Tạo đối tượng VideoInfo từ thông tin trả về bởi yt-dlp"""
        video_id = info.get('id', '')
        title = info.get('title', 'Không có tiêu đề')
        uploader = info.get('uploader', 'Không xác định')
        duration = info.get('duration', 0)
        view_count = info.get('view_count', 0)
        
        # Xử lý ngày tải lên
        upload_date = info.get('upload_date', '')
        if upload_date and len(upload_date) == 8:
            upload_date = f"{upload_date[6:8]}/{upload_date[4:6]}/{upload_date[0:4]}"
        else:
            upload_date = "Không xác định"
        
        # Xử lý formats
        formats = []
        for fmt in info.get('formats', []):
            has_video = fmt.get('vcodec', 'none') != 'none'
            has_audio = fmt.get('acodec', 'none') != 'none'
            
            format_obj = VideoFormat(
                format_id=fmt.get('format_id', ''),
                ext=fmt.get('ext', ''),
                resolution=f"{fmt.get('height', '?')}p" if fmt.get('height') else "N/A",
                fps=fmt.get('fps', 'N/A'),
                filesize=fmt.get('filesize', 0) or 0,
                has_audio=has_audio,
                has_video=has_video,
                bitrate=fmt.get('abr', 0) or fmt.get('tbr', 0) or 0
            )
            formats.append(format_obj)
        
        return cls(
            video_id=video_id,
            title=title,
            uploader=uploader,
            duration=duration,
            view_count=view_count,
            upload_date=upload_date,
            formats=formats,
            thumbnail=info.get('thumbnail', ''),
            description=info.get('description', ''),
            url=info.get('webpage_url', '') or info.get('url', '')
        )

@dataclass
class PlaylistInfo:
    playlist_id: str
    title: str
    uploader: str = "Không xác định"
    video_count: int = 0
    videos: List[VideoInfo] = field(default_factory=list)
    url: str = ""
    
    @classmethod
    def from_yt_dlp_info(cls, info: Dict[str, Any], include_videos: bool = False) -> 'PlaylistInfo':
        """Tạo đối tượng PlaylistInfo từ thông tin trả về bởi yt-dlp"""
        playlist_id = info.get('id', '')
        title = info.get('title', 'Không có tiêu đề')
        uploader = info.get('uploader', 'Không xác định')
        
        # Xác định số lượng video
        video_count = info.get('playlist_count', 0)
        if not video_count and 'entries' in info:
            video_count = len(list(info.get('entries') or []))
        
        # Tạo danh sách video nếu cần
        videos = []
        if include_videos and 'entries' in info:
            for entry in info.get('entries', []):
                if entry:
                    videos.append(VideoInfo.from_yt_dlp_info(entry))
        
        return cls(
            playlist_id=playlist_id,
            title=title,
            uploader=uploader,
            video_count=video_count,
            videos=videos,
            url=info.get('webpage_url', '') or info.get('url', '')
        )

@dataclass
class DownloadProgress:
    filename: str = ""
    percent: float = 0
    speed: str = ""
    eta: str = ""
    status: str = "waiting"  # waiting, downloading, finished, error
    error_message: str = ""
    bytes_downloaded: int = 0
    total_bytes: int = 0
    
    def __str__(self) -> str:
        if self.status == "waiting":
            return "Đang chờ..."
        elif self.status == "downloading":
            return f"{self.filename} | {self.percent:.1f}% | {self.speed} | ETA: {self.eta}"
        elif self.status == "finished":
            return f"{self.filename} | Hoàn thành"
        elif self.status == "error":
            return f"{self.filename} | Lỗi: {self.error_message}"
        return ""

@dataclass
class DownloadOptions:
    format_selector: str = "best"
    output_template: str = "%(title)s.%(ext)s"
    merge: bool = False
    merge_format: str = "mp4"
    convert_to_mp3: bool = False
    audio_quality: str = "192"
    download_dir: str = DEFAULT_DOWNLOAD_DIR
    max_downloads: int = 0  # 0 = không giới hạn
    rate_limit: str = ""  # Ví dụ: "50K"
    proxy: str = ""
    username: str = ""
    password: str = ""
    use_cookies: bool = False
    cookies_file: str = ""
    download_thumbnails: bool = False
    download_subtitles: bool = False
    subtitle_languages: List[str] = field(default_factory=lambda: ["vi", "en"])
    max_workers: int = 1  # Số luồng tải xuống song song
    retry_count: int = 10
    fragment_retries: int = 10
    skip_unavailable_fragments: bool = True
    continue_incomplete: bool = True
    sleep_interval: int = 3  # Thời gian chờ giữa các lần tải (giây)
    
    def to_yt_dlp_options(self, is_playlist: bool = False) -> Dict[str, Any]:
        """Chuyển đổi tùy chọn sang định dạng cho yt-dlp"""
        opts = {
            'format': self.format_selector,
            'outtmpl': self.output_template,
            'noplaylist': not is_playlist,
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [],  # Sẽ được thêm vào sau
            
            # Tùy chọn xử lý lỗi
            'retries': self.retry_count,
            'fragment_retries': self.fragment_retries,
            'skip_unavailable_fragments': self.skip_unavailable_fragments,
            'ignoreerrors': False,
            'continue': self.continue_incomplete,
            'socket_timeout': 30,
            
            # Giới hạn tốc độ nếu có
            'ratelimit': int(self.rate_limit.rstrip('K')) * 1024 if self.rate_limit and self.rate_limit.endswith('K') else None,
        }
        
        # Thêm tùy chọn proxy nếu có
        if self.proxy:
            opts['proxy'] = self.proxy
        
        # Thêm tùy chọn xác thực nếu có
        if self.username and self.password:
            opts['username'] = self.username
            opts['password'] = self.password
        
        # Thêm tùy chọn cookies nếu có
        if self.use_cookies and self.cookies_file and os.path.exists(self.cookies_file):
            opts['cookiefile'] = self.cookies_file
        
        # Thêm tùy chọn ghép file nếu cần
        if self.merge:
            opts['merge_output_format'] = self.merge_format
        
        # Thêm tùy chọn tải thumbnail nếu cần
        if self.download_thumbnails:
            opts['writethumbnail'] = True
            opts['postprocessors'] = opts.get('postprocessors', []) + [
                {'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'}
            ]
        
        # Thêm tùy chọn tải subtitle nếu cần
        if self.download_subtitles:
            opts['writesubtitles'] = True
            opts['writeautomaticsub'] = True
            opts['subtitleslangs'] = self.subtitle_languages
            opts['postprocessors'] = opts.get('postprocessors', []) + [
                {'key': 'FFmpegSubtitlesConvertor', 'format': 'srt'}
            ]
        
        # Thêm tùy chọn chuyển đổi sang MP3 nếu cần
        if self.convert_to_mp3:
            opts['postprocessors'] = opts.get('postprocessors', []) + [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': self.audio_quality,
            }]
        
        return opts

@dataclass
class DownloadTask:
    url: str
    options: DownloadOptions
    index: int = 0
    total: int = 0
    progress: DownloadProgress = field(default_factory=DownloadProgress)
    video_info: Optional[VideoInfo] = None
    is_playlist: bool = False
    playlist_info: Optional[PlaylistInfo] = None
    
    def get_display_name(self) -> str:
        """Trả về tên hiển thị của task"""
        if self.video_info:
            return self.video_info.title
        elif self.playlist_info:
            return f"Playlist: {self.playlist_info.title}"
        else:
            return self.url


class VersionChecker:
    """Kiểm tra phiên bản mới nhất của yt-dlp"""
    
    @staticmethod
    def check_for_updates() -> Tuple[bool, str]:
        """
        Kiểm tra xem có phiên bản mới của yt-dlp hay không
        Trả về: (có_phiên_bản_mới, phiên_bản_mới)
        """
        try:
            logger.info("Đang kiểm tra phiên bản mới của yt-dlp...")
            with urllib.request.urlopen(YT_DLP_LATEST_VERSION_URL, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest_version = data['tag_name'].lstrip('v')
                current_version = yt_dlp_version
                
                logger.info(f"Phiên bản hiện tại: {current_version}, Phiên bản mới nhất: {latest_version}")
                
                if latest_version > current_version:
                    return True, latest_version
                return False, current_version
        except Exception as e:
            logger.warning(f"Không thể kiểm tra phiên bản mới: {e}")
            return False, yt_dlp_version
    
    @staticmethod
    def update_yt_dlp() -> bool:
        """
        Cập nhật yt-dlp lên phiên bản mới nhất
        Trả về: Thành công hay không
        """
        try:
            import subprocess
            logger.info("Đang cập nhật yt-dlp...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], 
                                   capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Đã cập nhật yt-dlp thành công")
                return True
            else:
                logger.error(f"Lỗi khi cập nhật yt-dlp: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật yt-dlp: {e}")
            return False


class ConfigManager:
    """Quản lý cấu hình và trạng thái của ứng dụng"""
    
    def __init__(self, config_file: str = CONFIG_FILE, state_file: str = STATE_FILE):
        self.config_file = config_file
        self.state_file = state_file
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self) -> None:
        """Tải cấu hình từ file"""
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file)
                logger.info(f"Đã tải cấu hình từ {self.config_file}")
            except Exception as e:
                logger.error(f"Lỗi khi tải cấu hình: {e}")
                # Tạo cấu hình mặc định nếu có lỗi
                self.create_default_config()
        else:
            # Tạo file cấu hình mặc định nếu không tồn tại
            self.create_default_config()
    
    def create_default_config(self) -> None:
        """Tạo cấu hình mặc định"""
        self.config['general'] = {
            'download_dir': DEFAULT_DOWNLOAD_DIR,
            'max_workers': '1',
            'check_for_updates': 'true'
        }
        
        self.config['download'] = {
            'format_selector': 'best',
            'merge_format': 'mp4',
            'audio_quality': '192',
            'retry_count': '10',
            'sleep_interval': '3',
            'rate_limit': '',
            'download_thumbnails': 'false',
            'download_subtitles': 'false'
        }
        
        self.config['authentication'] = {
            'use_proxy': 'false',
            'proxy': '',
            'use_cookies': 'false',
            'cookies_file': ''
        }
        
        self.save_config()
    
    def save_config(self) -> None:
        """Lưu cấu hình vào file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                self.config.write(f)
            logger.info(f"Đã lưu cấu hình vào {self.config_file}")
        except Exception as e:
            logger.error(f"Lỗi khi lưu cấu hình: {e}")
    
    def get_download_options(self) -> DownloadOptions:
        """Tạo đối tượng DownloadOptions từ cấu hình"""
        options = DownloadOptions()
        
        if 'general' in self.config:
            options.download_dir = self.config.get('general', 'download_dir', fallback=DEFAULT_DOWNLOAD_DIR)
            options.max_workers = self.config.getint('general', 'max_workers', fallback=1)
        
        if 'download' in self.config:
            options.format_selector = self.config.get('download', 'format_selector', fallback='best')
            options.merge_format = self.config.get('download', 'merge_format', fallback='mp4')
            options.audio_quality = self.config.get('download', 'audio_quality', fallback='192')
            options.retry_count = self.config.getint('download', 'retry_count', fallback=10)
            options.sleep_interval = self.config.getint('download', 'sleep_interval', fallback=3)
            options.rate_limit = self.config.get('download', 'rate_limit', fallback='')
            options.download_thumbnails = self.config.getboolean('download', 'download_thumbnails', fallback=False)
            options.download_subtitles = self.config.getboolean('download', 'download_subtitles', fallback=False)
        
        if 'authentication' in self.config:
            if self.config.getboolean('authentication', 'use_proxy', fallback=False):
                options.proxy = self.config.get('authentication', 'proxy', fallback='')
            
            options.use_cookies = self.config.getboolean('authentication', 'use_cookies', fallback=False)
            options.cookies_file = self.config.get('authentication', 'cookies_file', fallback='')
        
        return options
    
    def update_from_options(self, options: DownloadOptions) -> None:
        """Cập nhật cấu hình từ đối tượng DownloadOptions"""
        if 'general' not in self.config:
            self.config['general'] = {}
        self.config['general']['download_dir'] = options.download_dir
        self.config['general']['max_workers'] = str(options.max_workers)
        
        if 'download' not in self.config:
            self.config['download'] = {}
        self.config['download']['format_selector'] = options.format_selector
        self.config['download']['merge_format'] = options.merge_format
        self.config['download']['audio_quality'] = options.audio_quality
        self.config['download']['retry_count'] = str(options.retry_count)
        self.config['download']['sleep_interval'] = str(options.sleep_interval)
        self.config['download']['rate_limit'] = options.rate_limit
        self.config['download']['download_thumbnails'] = str(options.download_thumbnails).lower()
        self.config['download']['download_subtitles'] = str(options.download_subtitles).lower()
        
        if 'authentication' not in self.config:
            self.config['authentication'] = {}
        self.config['authentication']['use_proxy'] = str(options.proxy != '').lower()
        self.config['authentication']['proxy'] = options.proxy
        self.config['authentication']['use_cookies'] = str(options.use_cookies).lower()
        self.config['authentication']['cookies_file'] = options.cookies_file
        
        self.save_config()
    
    def save_download_state(self, tasks: List[DownloadTask]) -> None:
        """Lưu trạng thái tải xuống vào file"""
        try:
            state = {
                'timestamp': datetime.now().isoformat(),
                'tasks': []
            }
            
            for task in tasks:
                # Chỉ lưu các task có URL và chưa hoàn thành
                if task.url and task.progress.status != 'finished':
                    task_data = {
                        'url': task.url,
                        'is_playlist': task.is_playlist,
                        'index': task.index,
                        'total': task.total,
                        'progress': task.progress.percent
                    }
                    state['tasks'].append(task_data)
            
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(state, f)
            
            logger.info(f"Đã lưu trạng thái tải xuống vào {self.state_file}")
        except Exception as e:
            logger.error(f"Lỗi khi lưu trạng thái tải xuống: {e}")
    
    def load_download_state(self) -> List[Dict[str, Any]]:
        """Tải trạng thái tải xuống từ file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                
                # Kiểm tra xem trạng thái có quá cũ không (> 7 ngày)
                timestamp = datetime.fromisoformat(state.get('timestamp', ''))
                if (datetime.now() - timestamp).days > 7:
                    logger.info("Trạng thái tải xuống quá cũ, không sử dụng")
                    return []
                
                logger.info(f"Đã tải trạng thái tải xuống từ {self.state_file}")
                return state.get('tasks', [])
            
            return []
        except Exception as e:
            logger.error(f"Lỗi khi tải trạng thái tải xuống: {e}")
            return []


class YouTubeDownloader:
    """Lớp chính để tải video từ YouTube"""
    
    def __init__(self, config_manager: ConfigManager = None):
        self.config_manager = config_manager or ConfigManager()
        self.default_options = self.config_manager.get_download_options()
        self.active_tasks: List[DownloadTask] = []
        self.completed_tasks: List[DownloadTask] = []
        self.failed_tasks: List[DownloadTask] = []
        self.progress_callbacks = []
        self.executor = None
    
    def add_progress_callback(self, callback) -> None:
        """Thêm callback để nhận thông báo tiến trình"""
        self.progress_callbacks.append(callback)
    
    def notify_progress(self, task: DownloadTask) -> None:
        """Thông báo tiến trình cho tất cả callbacks"""
        for callback in self.progress_callbacks:
            try:
                callback(task)
            except Exception as e:
                logger.error(f"Lỗi khi gọi callback tiến trình: {e}")
    
    def progress_hook(self, d: Dict[str, Any]) -> None:
        """Hook xử lý tiến trình từ yt-dlp"""
        # Tìm task tương ứng với filename
        filename = d.get('filename', '')
        task = next((t for t in self.active_tasks if filename.startswith(t.progress.filename)), None)
        
        if not task:
            # Nếu không tìm thấy task, có thể đây là file mới
            for t in self.active_tasks:
                if not t.progress.filename:
                    task = t
                    break
        
        if not task:
            logger.warning(f"Không tìm thấy task cho file: {filename}")
            return
        
        if d['status'] == 'downloading':
            task.progress.filename = os.path.basename(filename)
            task.progress.status = 'downloading'
            percent_str = d.get("_percent_str", "0")
            percent_str = clean_ansi(percent_str).replace('%', '').strip()
            task.progress.percent = float(percent_str) if '_percent_str' in d else 0
            task.progress.speed = d.get('_speed_str', 'N/A')
            task.progress.eta = d.get('_eta_str', 'N/A')
            task.progress.bytes_downloaded = d.get('downloaded_bytes', 0)
            task.progress.total_bytes = d.get('total_bytes', 0)
            
            self.notify_progress(task)
        
        elif d['status'] == 'finished':
            task.progress.filename = os.path.basename(filename)
            task.progress.status = 'finished'
            task.progress.percent = 100.0
            
            self.notify_progress(task)
            logger.info(f"Đã tải xong: {os.path.basename(filename)}")
        
        elif d['status'] == 'error':
            task.progress.status = 'error'
            task.progress.error_message = d.get('error', 'Lỗi không xác định')
            
            self.notify_progress(task)
            logger.error(f"Lỗi khi tải: {task.progress.error_message}")
    
    def extract_info(self, url: str, extract_formats: bool = True) -> Dict[str, Any]:
        """Trích xuất thông tin video/playlist từ URL"""
        opts = {
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': not extract_formats,
        }
        
        try:
            with YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            logger.error(f"Lỗi khi trích xuất thông tin: {e}")
            raise
    
    def is_playlist(self, url: str) -> bool:
        """Kiểm tra xem URL có phải là playlist không"""
        return 'playlist' in url or 'list=' in url
    
    def get_video_info(self, url: str) -> VideoInfo:
        """Lấy thông tin chi tiết về video"""
        try:
            info = self.extract_info(url)
            return VideoInfo.from_yt_dlp_info(info)
        except Exception as e:
            logger.error(f"Lỗi khi lấy thông tin video: {e}")
            raise
    
    def get_playlist_info(self, url: str, include_videos: bool = False) -> PlaylistInfo:
        """Lấy thông tin chi tiết về playlist"""
        try:
            # Trích xuất thông tin cơ bản của playlist
            info = self.extract_info(url, extract_formats=False)
            return PlaylistInfo.from_yt_dlp_info(info, include_videos)
        except Exception as e:
            logger.error(f"Lỗi khi lấy thông tin playlist: {e}")
            raise
    
    def get_all_video_urls_from_playlist(self, url: str) -> List[str]:
        """Lấy tất cả URL video từ playlist"""
        try:
            info = self.extract_info(url, extract_formats=False)
            
            video_urls = []
            for entry in info.get('entries', []):
                if entry:
                    if entry.get('url'):
                        video_urls.append(entry.get('url'))
                    elif entry.get('id'):
                        video_urls.append(f"https://www.youtube.com/watch?v={entry['id']}")
            
            return video_urls
        except Exception as e:
            logger.error(f"Lỗi khi lấy danh sách video từ playlist: {e}")
            raise
    
    def download_single_video(self, task: DownloadTask) -> bool:
        """Tải một video đơn lẻ"""
        if task.index > 0 and task.total > 0:
            logger.info(f"[{task.index}/{task.total}] Đang tải video: {task.url}")
        else:
            logger.info(f"Đang tải video: {task.url}")
        
        # Cập nhật trạng thái
        task.progress.status = 'downloading'
        self.notify_progress(task)
        
        # Tạo tùy chọn cho yt-dlp
        opts = task.options.to_yt_dlp_options()
        
        # Thêm hook tiến trình
        opts['progress_hooks'] = [self.progress_hook]
        
        try:
            with YoutubeDL(opts) as ydl:
                ydl.download([task.url])
            
            # Cập nhật trạng thái hoàn thành
            task.progress.status = 'finished'
            task.progress.percent = 100.0
            self.notify_progress(task)
            
            # Di chuyển task từ active sang completed
            if task in self.active_tasks:
                self.active_tasks.remove(task)
                self.completed_tasks.append(task)
            
            return True
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Lỗi khi tải video: {error_msg}")
            
            # Thử lại với format đơn giản hơn nếu lỗi format
            if "requested format is not available" in error_msg:
                logger.info("Định dạng yêu cầu không có sẵn. Đang thử lại với định dạng tốt nhất có sẵn...")
                opts['format'] = 'best'
                try:
                    with YoutubeDL(opts) as ydl:
                        ydl.download([task.url])
                    
                    # Cập nhật trạng thái hoàn thành
                    task.progress.status = 'finished'
                    task.progress.percent = 100.0
                    self.notify_progress(task)
                    
                    # Di chuyển task từ active sang completed
                    if task in self.active_tasks:
                        self.active_tasks.remove(task)
                        self.completed_tasks.append(task)
                    
                    return True
                except Exception as e2:
                    error_msg = str(e2)
                    logger.error(f"Vẫn không thể tải: {error_msg}")
            
            # Cập nhật trạng thái lỗi
            task.progress.status = 'error'
            task.progress.error_message = error_msg
            self.notify_progress(task)
            
            # Di chuyển task từ active sang failed
            if task in self.active_tasks:
                self.active_tasks.remove(task)
                self.failed_tasks.append(task)
            
            return False
    
    def download_playlist(self, url: str, options: DownloadOptions) -> bool:
        """Tải từng video trong playlist một cách riêng biệt"""
        try:
            # Lấy thông tin playlist
            playlist_info = self.get_playlist_info(url)
            logger.info(f"Đã tìm thấy playlist: {playlist_info.title} với {playlist_info.video_count} video")
            
            # Lấy tất cả URL video từ playlist
            video_urls = self.get_all_video_urls_from_playlist(url)
            
            if not video_urls:
                logger.error("Không tìm thấy video nào trong playlist hoặc có lỗi khi trích xuất")
                return False
            
            total_videos = len(video_urls)
            logger.info(f"Đã tìm thấy {total_videos} video trong playlist")
            
            # Tạo thư mục con cho playlist
            playlist_dir = os.path.join(options.download_dir, sanitize(playlist_info.title))
            os.makedirs(playlist_dir, exist_ok=True)
            
            # Cập nhật output template để bao gồm thư mục playlist
            playlist_options = copy_download_options(options)
            playlist_options.output_template = os.path.join(os.path.abspath(playlist_dir), '%(playlist_index)s - %(title)s.%(ext)s')
            
            # Tạo danh sách các task
            tasks = []
            for i, video_url in enumerate(video_urls):
                task = DownloadTask(
                    url=video_url,
                    options=playlist_options,
                    index=i+1,
                    total=total_videos,
                    is_playlist=True,
                    playlist_info=playlist_info
                )
                tasks.append(task)
            
            # Thêm vào danh sách active tasks
            self.active_tasks.extend(tasks)
            
            # Tải xuống các video
            if options.max_workers > 1:
                return self._download_parallel(tasks, options.max_workers, options.sleep_interval)
            else:
                return self._download_sequential(tasks, options.sleep_interval)
        except Exception as e:
            logger.error(f"Lỗi khi tải playlist: {e}")
            traceback.print_exc()
            return False
    
    def _download_sequential(self, tasks: List[DownloadTask], sleep_interval: int) -> bool:
        """Tải xuống các task một cách tuần tự"""
        success_count = 0
        
        for i, task in enumerate(tasks):
            # Thêm thời gian chờ giữa các lần tải để tránh bị chặn
            if i > 0:
                wait_time = min(sleep_interval, 1 + i // 20)  # Tăng thời gian chờ khi tải nhiều video
                logger.info(f"Chờ {wait_time} giây trước khi tải video tiếp theo...")
                time.sleep(wait_time)
            
            success = self.download_single_video(task)
            if success:
                success_count += 1
        
        logger.info(f"Đã tải thành công {success_count}/{len(tasks)} video")
        return success_count > 0
    
    def _download_parallel(self, tasks: List[DownloadTask], max_workers: int, sleep_interval: int) -> bool:
        """Tải xuống các task song song với số lượng worker giới hạn"""
        success_count = 0
        
        # Tạo executor nếu chưa có
        if self.executor is None or self.executor._shutdown:
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Chia nhỏ danh sách task thành các batch để tránh quá tải
        batch_size = min(max_workers, 10)  # Không tải quá 5 video cùng lúc
        task_batches = [tasks[i:i+batch_size] for i in range(0, len(tasks), batch_size)]
        
        for batch_index, batch in enumerate(task_batches):
            # Thêm thời gian chờ giữa các batch
            if batch_index > 0:
                logger.info(f"Chờ {sleep_interval} giây trước khi tải batch tiếp theo...")
                time.sleep(sleep_interval)
            
            # Tải song song các task trong batch
            futures = []
            for task in batch:
                future = self.executor.submit(self.download_single_video, task)
                futures.append(future)
            
            # Đợi tất cả các task trong batch hoàn thành
            for future in as_completed(futures):
                try:
                    if future.result():
                        success_count += 1
                except Exception as e:
                    logger.error(f"Lỗi khi tải song song: {e}")
        
        logger.info(f"Đã tải thành công {success_count}/{len(tasks)} video")
        return success_count > 0
    
    def download(self, url: str, options: Optional[DownloadOptions] = None) -> bool:
        """
        Tải video hoặc playlist từ URL
        Trả về: Thành công hay không
        """
        if options is None:
            options = self.default_options
        
        try:
            # Tạo thư mục lưu nếu chưa tồn tại
            os.makedirs(options.download_dir, exist_ok=True)
            
            # Kiểm tra xem URL có phải là playlist không
            if self.is_playlist(url):
                return self.download_playlist(url, options)
            else:
                # Tạo task cho video đơn lẻ
                try:
                    video_info = self.get_video_info(url)
                    task = DownloadTask(
                        url=url,
                        options=options,
                        video_info=video_info
                    )
                except Exception:
                    # Nếu không lấy được thông tin video, vẫn tạo task nhưng không có video_info
                    task = DownloadTask(url=url, options=options)
                
                # Thêm vào danh sách active tasks
                self.active_tasks.append(task)
                
                # Tải video
                return self.download_single_video(task)
        except Exception as e:
            logger.error(f"Lỗi khi tải: {e}")
            traceback.print_exc()
            return False
    
    def resume_downloads(self) -> bool:
        """Tiếp tục các tải xuống đã bị gián đoạn"""
        tasks_data = self.config_manager.load_download_state()
        if not tasks_data:
            logger.info("Không có tải xuống nào cần tiếp tục")
            return False
        
        options = self.default_options
        tasks = []
        
        for task_data in tasks_data:
            url = task_data.get('url')
            is_playlist = task_data.get('is_playlist', False)
            index = task_data.get('index', 0)
            total = task_data.get('total', 0)
            
            if not url:
                continue
            
            if is_playlist:
                # Nếu là playlist, tạo task mới với thông tin cơ bản
                try:
                    playlist_info = self.get_playlist_info(url)
                    task = DownloadTask(
                        url=url,
                        options=options,
                        index=index,
                        total=total,
                        is_playlist=True,
                        playlist_info=playlist_info
                    )
                except Exception:
                    # Nếu không lấy được thông tin playlist, vẫn tạo task
                    task = DownloadTask(
                        url=url,
                        options=options,
                        index=index,
                        total=total,
                        is_playlist=True
                    )
            else:
                # Nếu là video đơn lẻ
                try:
                    video_info = self.get_video_info(url)
                    task = DownloadTask(
                        url=url,
                        options=options,
                        video_info=video_info
                    )
                except Exception:
                    # Nếu không lấy được thông tin video, vẫn tạo task
                    task = DownloadTask(url=url, options=options)
            
            tasks.append(task)
        
        if not tasks:
            logger.info("Không có tải xuống hợp lệ để tiếp tục")
            return False
        
        logger.info(f"Tiếp tục {len(tasks)} tải xuống đã bị gián đoạn")
        
        # Thêm vào danh sách active tasks
        self.active_tasks.extend(tasks)
        
        # Tải xuống các task
        if options.max_workers > 1:
            return self._download_parallel(tasks, options.max_workers, options.sleep_interval)
        else:
            return self._download_sequential(tasks, options.sleep_interval)
    
    def cancel_all_downloads(self) -> None:
        """Hủy tất cả các tải xuống đang hoạt động"""
        # Lưu trạng thái trước khi hủy
        self.config_manager.save_download_state(self.active_tasks)
        
        # Đóng executor nếu đang chạy
        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None
        
        # Di chuyển tất cả task đang hoạt động sang failed
        for task in self.active_tasks:
            task.progress.status = 'error'
            task.progress.error_message = 'Đã hủy bởi người dùng'
            self.failed_tasks.append(task)
        
        self.active_tasks = []
        logger.info("Đã hủy tất cả các tải xuống")
    
    def cleanup(self) -> None:
        """Dọn dẹp tài nguyên"""
        if self.executor:
            self.executor.shutdown(wait=True)
            self.executor = None


class CommandLineInterface:
    """Giao diện dòng lệnh cho YouTube downloader"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.downloader = YouTubeDownloader(self.config_manager)
        self.downloader.add_progress_callback(self.update_progress)
        self.current_task = None
    
    def update_progress(self, task: DownloadTask) -> None:
        """Cập nhật và hiển thị tiến trình tải xuống"""
        self.current_task = task
        
        if task.progress.status == 'downloading':
            # Xóa dòng trước đó và in thông tin mới
            sys.stdout.write('\r\033[K')
            
            # Hiển thị thông tin task
            if task.index > 0 and task.total > 0:
                sys.stdout.write(f"[{task.index}/{task.total}] ")
            
            sys.stdout.write(f"{task.progress}")
            sys.stdout.flush()
        elif task.progress.status == 'finished':
            sys.stdout.write('\r\033[K')
            if task.index > 0 and task.total > 0:
                print(f"[{task.index}/{task.total}] Đã tải xong: {task.progress.filename}")
            else:
                print(f"Đã tải xong: {task.progress.filename}")
        elif task.progress.status == 'error':
            sys.stdout.write('\r\033[K')
            if task.index > 0 and task.total > 0:
                print(f"[{task.index}/{task.total}] Lỗi: {task.progress.error_message}")
            else:
                print(f"Lỗi: {task.progress.error_message}")
    
    def display_video_info(self, info: VideoInfo) -> None:
        """Hiển thị thông tin chi tiết về video"""
        print("\n=== THÔNG TIN VIDEO ===")
        print(f"Tiêu đề: {info.title}")
        print(f"Kênh: {info.uploader}")
        print(f"Thời lượng: {format_duration(info.duration)}")
        if info.view_count:
            print(f"Lượt xem: {info.view_count:,}".replace(',', '.'))
        print(f"Ngày đăng: {info.upload_date}")
    
    def display_playlist_info(self, info: PlaylistInfo) -> None:
        """Hiển thị thông tin chi tiết về playlist"""
        print("\n=== THÔNG TIN PLAYLIST ===")
        print(f"Tiêu đề: {info.title}")
        print(f"Kênh: {info.uploader}")
        print(f"Số lượng video: {info.video_count}")
        
        # Hiển thị thông tin về các video trong playlist
        if info.videos:
            print("\nCác video trong playlist:")
            for i, video in enumerate(info.videos[:5]):  # Chỉ hiển thị 5 video đầu tiên
                print(f" {i+1}. {video.title}")
            
            if len(info.videos) > 5:
                print(f" ... và {len(info.videos) - 5} video khác")
    
    def list_formats(self, info: VideoInfo, audio_only: bool = False) -> None:
        """Hiển thị danh sách format có sẵn"""
        if audio_only:
            # Lọc ra các format audio
            audio_formats = [f for f in info.formats if not f.has_video]
            audio_formats.sort(key=lambda f: f.bitrate, reverse=True)
            
            print("\nCác format audio tìm thấy:")
            for f in audio_formats:
                print(f" • {f}")
        else:
            # Lọc ra các format video
            video_formats = [f for f in info.formats if f.has_video]
            video_formats.sort(key=lambda f: int(f.resolution.replace('p', '')) if f.resolution.replace('p', '').isdigit() else 0, reverse=True)
            
            print("\nCác format video tìm thấy:")
            for f in video_formats:
                print(f" • {f}")
    
    def confirm_large_playlist(self, count: int) -> bool:
        """Xác nhận từ người dùng trước khi tải playlist lớn"""
        if count > 10:
            response = input(f"Playlist này có {count} video. Bạn có chắc muốn tải tất cả? (y/n): ").strip().lower()
            return response in ('y', 'yes', 'có', 'co')
        return True
    
    def setup_download_options(self, mode: str) -> DownloadOptions:
        """Thiết lập các tùy chọn tải xuống dựa trên chế độ đã chọn"""
        options = self.config_manager.get_download_options()
        
        # Thư mục gốc để lưu
        default_dir = options.download_dir
        base_outdir = input(f"Nhập thư mục lưu (Enter để dùng mặc định [{default_dir}]): ").strip()
        if base_outdir:
            options.download_dir = base_outdir
        
        # Tạo output template
        options.output_template = os.path.join(options.download_dir, '%(title)s.%(ext)s')
        
        # Thiết lập format và các tùy chọn tải dựa trên mode
        if mode == '1':  # Chỉ audio (MP3)
            # Chọn chất lượng MP3
            print("Chọn chất lượng MP3:")
            print("  1) Thấp (128 kbps)")
            print("  2) Trung bình (192 kbps)")
            print("  3) Cao (256 kbps)")
            print("  4) Rất cao (320 kbps)")
            quality_choice = input("Lựa chọn (1-4, mặc định: 2): ").strip() or "2"
            
            quality_map = {"1": "128", "2": "192", "3": "256", "4": "320"}
            options.audio_quality = quality_map.get(quality_choice, "192")
            
            print(f"→ Bắt đầu tải audio chất lượng cao nhất và chuyển đổi sang MP3 {options.audio_quality}kbps...")
            options.format_selector = 'bestaudio'
            options.convert_to_mp3 = True
        
        elif mode == '2':  # Chỉ video (không audio)
            print("→ Bắt đầu tải video MP4 (không audio)...")
            options.format_selector = 'bestvideo[ext=mp4]'
        
        elif mode == '3':  # Video + audio (MP4)
            print("→ Bắt đầu tải và ghép video+audio chất lượng cao nhất...")
            options.format_selector = 'bestvideo[ext=mp4]+bestaudio/best'
            options.merge = True
            options.merge_format = 'mp4'
        
        elif mode == '4':  # Chọn format cụ thể
            format_id = input("Nhập format_id bạn muốn tải: ").strip()
            print(f"→ Bắt đầu tải format {format_id}...")
            options.format_selector = format_id
            options.merge = '+' in format_id
            options.merge_format = 'mp4'
        
        # Hỏi về các tùy chọn nâng cao
        if input("Bạn có muốn cấu hình các tùy chọn nâng cao? (y/n, mặc định: n): ").strip().lower() in ('y', 'yes', 'có', 'co'):
            # Tải song song
            max_workers = input(f"Số luồng tải song song (1-10, mặc định: {options.max_workers}): ").strip()
            if max_workers and max_workers.isdigit() and 1 <= int(max_workers) <= 10:
                options.max_workers = int(max_workers)
            
            # Giới hạn tốc độ
            rate_limit = input(f"Giới hạn tốc độ tải (ví dụ: 500K, để trống nếu không giới hạn): ").strip()
            if rate_limit:
                options.rate_limit = rate_limit
            
            # Tải thumbnail
            download_thumbnails = input("Tải thumbnail? (y/n, mặc định: n): ").strip().lower()
            options.download_thumbnails = download_thumbnails in ('y', 'yes', 'có', 'co')
            
            # Tải subtitle
            download_subtitles = input("Tải subtitle? (y/n, mặc định: n): ").strip().lower()
            options.download_subtitles = download_subtitles in ('y', 'yes', 'có', 'co')
            
            if options.download_subtitles:
                subtitle_langs = input("Ngôn ngữ subtitle (ví dụ: vi,en, mặc định: vi,en): ").strip()
                if subtitle_langs:
                    options.subtitle_languages = subtitle_langs.split(',')
            
            # Proxy
            use_proxy = input("Sử dụng proxy? (y/n, mặc định: n): ").strip().lower()
            if use_proxy in ('y', 'yes', 'có', 'co'):
                proxy = input("Nhập địa chỉ proxy (ví dụ: socks5://127.0.0.1:1080): ").strip()
                if proxy:
                    options.proxy = proxy
            
            # Cookies
            use_cookies = input("Sử dụng cookies? (y/n, mặc định: n): ").strip().lower()
            if use_cookies in ('y', 'yes', 'có', 'co'):
                cookies_file = input("Nhập đường dẫn đến file cookies: ").strip()
                if cookies_file and os.path.exists(cookies_file):
                    options.use_cookies = True
                    options.cookies_file = cookies_file
        
        # Lưu cấu hình
        self.config_manager.update_from_options(options)
        
        return options
    
    def run(self) -> None:
        """Chạy giao diện dòng lệnh"""
        print("=== YOUTUBE downloadER PRO ===")
        print(f"Phiên bản: {VERSION}")
        print("Công cụ tải video/audio từ YouTube với nhiều tính năng nâng cao")
        print("Lưu ý: Cần cài đặt FFmpeg để chuyển đổi định dạng\n")
        
        # Kiểm tra phiên bản yt-dlp
        has_update, latest_version = VersionChecker.check_for_updates()
        if has_update:
            print(f"Có phiên bản mới của yt-dlp: {latest_version} (hiện tại: {yt_dlp_version})")
            if input("Bạn có muốn cập nhật ngay? (y/n): ").strip().lower() in ('y', 'yes', 'có', 'co'):
                if VersionChecker.update_yt_dlp():
                    print("Đã cập nhật yt-dlp thành công. Vui lòng khởi động lại ứng dụng.")
                    return
                else:
                    print("Không thể cập nhật yt-dlp. Tiếp tục với phiên bản hiện tại.")
        
        # Kiểm tra xem có tải xuống bị gián đoạn không
        tasks_data = self.config_manager.load_download_state()
        if tasks_data:
            if input(f"Tìm thấy {len(tasks_data)} tải xuống bị gián đoạn. Bạn có muốn tiếp tục? (y/n): ").strip().lower() in ('y', 'yes', 'có', 'co'):
                self.downloader.resume_downloads()
                print("\nHoàn tất! Tất cả các tải xuống đã được xử lý.")
                return
        
        # Nhập URL
        url = input("Nhập URL YouTube (video hoặc playlist): ").strip()
        if not url:
            print("URL không hợp lệ. Vui lòng thử lại.")
            return
        
        # Kiểm tra xem URL có phải là playlist không
        is_playlist = self.downloader.is_playlist(url)
        
        try:
            if is_playlist:
                print("→ Phát hiện: Playlist")
                # Lấy thông tin playlist
                playlist_info = self.downloader.get_playlist_info(url)
                self.display_playlist_info(playlist_info)
                
                # Xác nhận tải playlist lớn
                if not self.confirm_large_playlist(playlist_info.video_count):
                    print("Đã hủy tải xuống.")
                    return
            else:
                print("→ Phát hiện: Video đơn lẻ")
                # Lấy thông tin video
                video_info = self.downloader.get_video_info(url)
                self.display_video_info(video_info)
                
                # Hiển thị danh sách format
                self.list_formats(video_info)
            
            # Chọn chế độ tải
            print("""
Chọn chế độ tải:
  1) Chỉ audio (MP3)
  2) Chỉ video (không có audio)
  3) Video + audio (MP4)
  4) Chọn format cụ thể
""")
            mode = input("Lựa chọn (1/2/3/4): ").strip()
            if mode not in ('1', '2', '3', '4'):
                print("Lựa chọn không hợp lệ. Chạy lại và chọn 1, 2, 3 hoặc 4.")
                return
            
            # Thiết lập tùy chọn tải xuống
            options = self.setup_download_options(mode)
            
            # Thực hiện tải xuống
            try:
                success = self.downloader.download(url, options)
                if success:
                    print("\nHoàn tất! File đã được lưu tại:", os.path.abspath(options.download_dir))
                else:
                    print("\nTải xuống không thành công. Vui lòng kiểm tra log để biết thêm chi tiết.")
            except KeyboardInterrupt:
                print("\nĐã hủy tải xuống bởi người dùng.")
                # Lưu trạng thái để có thể tiếp tục sau
                self.downloader.cancel_all_downloads()
        except Exception as e:
            print(f"\nLỗi không mong muốn: {e}")
            traceback.print_exc()
        finally:
            # Dọn dẹp tài nguyên
            self.downloader.cleanup()


class GraphicalUserInterface:
    """Giao diện đồ họa cho YouTube downloader"""
    
    def __init__(self):
        if not GUI_AVAILABLE:
            raise ImportError("Không thể tạo giao diện đồ họa. Vui lòng cài đặt tkinter.")
        
        self.config_manager = ConfigManager()
        self.downloader = YouTubeDownloader(self.config_manager)
        self.downloader.add_progress_callback(self.update_progress)
        
        self.root = tk.Tk()
        self.root.title(f"🎬 YouTube Downloader Pro {VERSION}")
        self.root.geometry("900x700")
        self.root.minsize(900, 700)
        
        # Thiết lập màu nền chính
        self.root.configure(bg=ColorTheme.BACKGROUND)
        
        # Cấu hình style hiện đại
        self.style = ModernStyle.configure_ttk_style()
        
        # Thiết lập icon (nếu có)
        try:
            # Bạn có thể thêm icon ở đây
            # self.root.iconbitmap("icon.ico")
            pass
        except:
            pass
        
        self.setup_ui()
        self.setup_styles()
        
        # Kiểm tra phiên bản khi khởi động
        self.root.after(1000, self.check_for_updates)

    def setup_styles(self):
        """Thiết lập các style cho ttk widgets"""
        style = ttk.Style()
        
        # Style cho Notebook
        style.configure("Modern.TNotebook", 
                    background=ColorTheme.BACKGROUND,
                    borderwidth=0)
        style.configure("Modern.TNotebook.Tab", 
                    padding=[20, 10],
                    font=("Segoe UI", 10))
        
        # Style cho Entry
        style.configure("Modern.TEntry",
                    fieldbackground="white",
                    borderwidth=1,
                    relief="solid")
        
        # Style cho Checkbutton
        style.configure("Modern.TCheckbutton",
                    background=ColorTheme.FRAME_BACKGROUND,
                    font=("Segoe UI", 10))
        
        # ===== SỬA LỖI: BUTTON STYLES VỚI PADDING VÀ MÀU SẮC CHÍNH XÁC =====
        
        # Button Success (màu xanh lá) (Tải xuống)
        style.configure("Success.TButton",
                    background="#28a745",      # Nền xanh lá
                    foreground="#538C51",        
                    font=("Segoe UI", 10, "bold"),
                    padding=[15, 8],
                    borderwidth=0,
                    relief="flat")
        style.map("Success.TButton",
                background=[('active', '#218838'),    # Hover đậm hơn
                            ('pressed', '#1e7e34'),    # Click đậm hơn
                            ('disabled', '#6c757d')],  # Disabled
                foreground=[('active', '#B9B7B3'),
                            ('pressed', '#B9B7B3'),
                            ('disabled', '#707070')])
        
        # Button Warning (màu cam) (Duyệt)
        style.configure("Warning.TButton",
                    background="#fd7e14",      # Nền cam
                    foreground="#F2D399",        
                    font=("Segoe UI", 10, "bold"),
                    padding=[15, 8],
                    borderwidth=0,
                    relief="flat")
        style.map("Warning.TButton",
                background=[('active', '#e8690b'),    # Hover đậm hơn
                            ('pressed', '#d35400'),    # Click đậm hơn
                            ('disabled', '#6c757d')],  # Disabled
                foreground=[('active', '#B9B7B3'),
                            ('pressed', '#B9B7B3'),
                            ('disabled', '#707070')])
        
        # Button Danger (màu đỏ) (Hủy)
        style.configure("Danger.TButton",
                    background="#dc3545",      # Nền đỏ
                    foreground="#F24444",        # Chữ trắng
                    font=("Segoe UI", 10, "bold"),
                    padding=[15, 8],
                    borderwidth=0,
                    relief="flat")
        style.map("Danger.TButton",
                background=[('active', '#c82333'),    # Hover đậm hơn
                            ('pressed', '#bd2130'),    # Click đậm hơn
                            ('disabled', '#6c757d')],  # Disabled
                foreground=[('active', '#B9B7B3'),
                            ('pressed', '#B9B7B3'),
                            ('disabled', '#707070')])
        
        # Button Primary (màu xanh dương) (Phân tích)
        style.configure("Primary.TButton",
                    background=ColorTheme.PRIMARY_BLUE,  # Nền xanh dương
                    foreground="#B16E4B",                   # Chữ trắng
                    font=("Segoe UI", 10, "bold"),
                    padding=[15, 8],
                    borderwidth=0,
                    relief="flat")
        style.map("Primary.TButton",
                background=[('active', '#0056b3'),     # Hover đậm hơn
                            ('pressed', '#004085'),     # Click đậm hơn
                            ('disabled', '#6c757d')],   # Disabled
                foreground=[('active', '#B9B7B3'),
                            ('pressed', '#B9B7B3'),
                            ('disabled', '#707070')])



    def add_hover_effect(self, widget, enter_color, leave_color):
        """Thêm hiệu ứng hover cho widget"""
        def on_enter(e):
            widget.configure(background=enter_color)
        
        def on_leave(e):
            widget.configure(background=leave_color)
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def create_menu(self) -> None:
        """Tạo menu cho ứng dụng"""
        menubar = tk.Menu(self.root)
        
        # Menu File
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Cài đặt", command=self.show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Thoát", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Menu Công cụ
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Kiểm tra cập nhật", command=self.check_for_updates)
        tools_menu.add_command(label="Tiếp tục tải xuống đã gián đoạn", command=self.resume_downloads)
        tools_menu.add_command(label="Xóa lịch sử tải xuống", command=self.clear_download_history)
        menubar.add_cascade(label="Công cụ", menu=tools_menu)
        
        # Menu Trợ giúp
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Hướng dẫn", command=self.show_help)
        help_menu.add_command(label="Giới thiệu", command=self.show_about)
        menubar.add_cascade(label="Trợ giúp", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def setup_ui(self) -> None:
        """Thiết lập giao diện người dùng hiện đại"""
        # Tạo menu
        self.create_menu()
        
        # Container chính với padding đẹp
        main_container = tk.Frame(self.root, bg=ColorTheme.BACKGROUND)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # === HEADER SECTION ===
        header_frame = ttk.Frame(main_container, style="Card.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Title với icon
        title_frame = tk.Frame(header_frame, bg=ColorTheme.CARD_BACKGROUND)
        title_frame.pack(fill=tk.X, padx=20, pady=15)
        
        title_label = tk.Label(title_frame, 
                            text="🎬 YouTube Downloader Pro",
                            font=("Segoe UI", 16, "bold"),
                            fg=ColorTheme.TEXT_PRIMARY,
                            bg=ColorTheme.CARD_BACKGROUND)
        title_label.pack(side=tk.LEFT)
        
        version_label = tk.Label(title_frame,
                            text=f"v{VERSION}",
                            font=("Segoe UI", 10),
                            fg=ColorTheme.TEXT_SECONDARY,
                            bg=ColorTheme.CARD_BACKGROUND)
        version_label.pack(side=tk.RIGHT)
        
        # === URL INPUT SECTION ===
        url_frame = ttk.LabelFrame(main_container, text="📎 Nhập URL YouTube", 
                                style="Modern.TLabelframe", padding=15)
        url_frame.pack(fill=tk.X, pady=(0, 15))
        
        url_input_frame = tk.Frame(url_frame, bg=ColorTheme.FRAME_BACKGROUND)
        url_input_frame.pack(fill=tk.X)
        
        tk.Label(url_input_frame, text="URL:", 
                font=("Segoe UI", 10, "bold"),
                fg=ColorTheme.TEXT_PRIMARY,
                bg=ColorTheme.FRAME_BACKGROUND).pack(side=tk.LEFT, padx=(0, 10))
        
        self.url_entry = ttk.Entry(url_input_frame, style="Modern.TEntry", font=("Segoe UI", 10))
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.analyze_button = ttk.Button(url_input_frame, text="🔍 Phân tích", 
                                    command=self.analyze_url, style="Primary.TButton")
        self.analyze_button.pack(side=tk.LEFT)
        
        # === INFO SECTION ===
        self.info_frame = ttk.LabelFrame(main_container, text="📋 Thông tin Video/Playlist", 
                                    style="Modern.TLabelframe", padding=15)
        self.info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Text widget với style đẹp
        text_frame = tk.Frame(self.info_frame, bg=ColorTheme.FRAME_BACKGROUND)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.info_text = scrolledtext.ScrolledText(text_frame, 
                                                wrap=tk.WORD, 
                                                height=8,
                                                font=("Consolas", 9),
                                                bg="white",
                                                fg=ColorTheme.TEXT_PRIMARY,
                                                selectbackground=ColorTheme.SECONDARY_BLUE,
                                                relief="solid",
                                                borderwidth=1)
        self.info_text.pack(fill=tk.BOTH, expand=True)
        self.info_text.insert(tk.END, "💡 Nhập URL YouTube và nhấn 'Phân tích' để bắt đầu.")
        self.info_text.config(state=tk.DISABLED)
        
        # === OPTIONS SECTION ===
        self.options_frame = ttk.LabelFrame(main_container, text="⚙️ Tùy chọn tải xuống", 
                                        style="Modern.TLabelframe", padding=15)
        self.options_frame.pack(fill=tk.X, pady=(0, 15))

        # Grid configuration
        self.options_frame.columnconfigure(1, weight=1)

        # Chế độ tải
        tk.Label(self.options_frame, text="📥 Chế độ tải:", 
                font=("Segoe UI", 10, "bold"),
                fg=ColorTheme.TEXT_PRIMARY,
                bg=ColorTheme.FRAME_BACKGROUND).grid(row=0, column=0, sticky=tk.W, pady=5)

        self.download_mode = tk.StringVar(value="3")
        modes = [
            ("🎵 Audio (MP3)", "1"),
            ("🎬 Video (không audio)", "2"), 
            ("🎥 Video + Audio (MP4)", "3"),
            ("🔧 Format cụ thể", "4")
        ]

        mode_frame = tk.Frame(self.options_frame, bg=ColorTheme.FRAME_BACKGROUND)
        mode_frame.grid(row=0, column=1, sticky=tk.W, pady=5)

        for i, (text, value) in enumerate(modes):
            ttk.Radiobutton(mode_frame, text=text, value=value, 
                        variable=self.download_mode, 
                        style="Modern.TRadiobutton").grid(row=0, column=i, padx=(0, 15), sticky=tk.W)

        # Format ID
        tk.Label(self.options_frame, text="🔧 Format ID:", 
                font=("Segoe UI", 10),
                fg=ColorTheme.TEXT_SECONDARY,
                bg=ColorTheme.FRAME_BACKGROUND).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.format_entry = ttk.Entry(self.options_frame, width=20, style="Modern.TEntry")
        self.format_entry.grid(row=1, column=1, sticky=tk.W, pady=5)

        # Thư mục lưu - label, entry, duyệt trên cùng một dòng
        tk.Label(self.options_frame, text="📁 Thư mục lưu:", 
                font=("Segoe UI", 10, "bold"),
                fg=ColorTheme.TEXT_PRIMARY,
                bg=ColorTheme.FRAME_BACKGROUND).grid(row=2, column=0, sticky=tk.W, pady=5, padx=(0, 8))

        self.save_dir_entry = ttk.Entry(self.options_frame, style="Modern.TEntry")
        self.save_dir_entry.grid(row=2, column=1, sticky="ew", pady=5)
        self.save_dir_entry.insert(0, self.config_manager.get_download_options().download_dir)

        self.browse_button = ttk.Button(self.options_frame, text="📂 Duyệt...", 
                                    command=self.browse_directory, style="Warning.TButton")
        self.browse_button.grid(row=2, column=2, sticky="e", padx=(8, 0), pady=5)
        self.options_frame.columnconfigure(1, weight=1)

        # Dòng dưới: các tùy chọn nâng cao + 2 nút tải xuống/hủy cùng hàng
        advanced_frame = tk.Frame(self.options_frame, bg=ColorTheme.FRAME_BACKGROUND)
        advanced_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        for i in range(6):
            advanced_frame.columnconfigure(i, weight=0)
        advanced_frame.columnconfigure(6, weight=1)  # Spacer
        advanced_frame.columnconfigure(7, weight=0)
        advanced_frame.columnconfigure(8, weight=0)

        self.download_thumbnail = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="🖼️ Tải thumbnail", 
                    variable=self.download_thumbnail, 
                    style="Modern.TCheckbutton").grid(row=0, column=0, padx=(0, 20), sticky="w")

        self.download_subtitle = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="📝 Tải subtitle", 
                    variable=self.download_subtitle, 
                    style="Modern.TCheckbutton").grid(row=0, column=1, padx=(0, 20), sticky="w")

        tk.Label(advanced_frame, text="⚡ Số luồng (khuyến nghị: 7, tối đa: 10):", 
                font=("Segoe UI", 9),
                fg=ColorTheme.TEXT_SECONDARY,
                bg=ColorTheme.FRAME_BACKGROUND).grid(row=0, column=2, padx=(0, 5), sticky="w")

        self.max_workers = tk.StringVar(value="1")
        worker_spinbox = ttk.Spinbox(advanced_frame, from_=1, to=10, width=5, 
                                textvariable=self.max_workers, font=("Segoe UI", 9))
        worker_spinbox.grid(row=0, column=3, sticky="w")

        # Spacer để đẩy nút sang phải
        spacer = tk.Label(advanced_frame, bg=ColorTheme.FRAME_BACKGROUND)
        spacer.grid(row=0, column=6, sticky="ew")

        self.download_button = ttk.Button(advanced_frame, text="⬇️ Tải xuống", 
                                        command=self.start_download, style="Success.TButton")
        self.download_button.grid(row=0, column=7, sticky="e", padx=(0, 8))

        self.cancel_button = ttk.Button(advanced_frame, text="❌ Hủy", 
                                    command=self.cancel_download, style="Danger.TButton", 
                                    state=tk.DISABLED)
        self.cancel_button.grid(row=0, column=8, sticky="e")

        
        # === PROGRESS SECTION ===
        self.progress_frame = ttk.LabelFrame(main_container, text="📊 Tiến trình tải xuống", 
                                        style="Modern.TLabelframe", padding=5)
        self.progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        columns = ('filename', 'status', 'progress', 'speed', 'eta')
        self.downloads_tree = ttk.Treeview(self.progress_frame, columns=columns, 
                                        show='headings', style="Modern.Treeview", height=10)

        headers = {
            'filename': '📄 Tên file',
            'status': '📊 Trạng thái', 
            'progress': '⏳ Tiến trình',
            'speed': '🚀 Tốc độ',
            'eta': '⏰ Thời gian còn lại'
        }
        for col, header in headers.items():
            self.downloads_tree.heading(col, text=header, anchor='center')
            self.downloads_tree.column(col, width=120, minwidth=80, stretch=True, anchor='center')

        # Đặt Treeview trực tiếp vào LabelFrame, không dùng frame phụ
        self.downloads_tree.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        scrollbar = ttk.Scrollbar(self.progress_frame, orient=tk.VERTICAL, command=self.downloads_tree.yview)
        self.downloads_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # === STATUS BAR ===
        self.status_var = tk.StringVar(value="✅ Sẵn sàng")
        status_bar = tk.Label(self.root, textvariable=self.status_var, 
                            relief=tk.SUNKEN, anchor=tk.W,
                            bg=ColorTheme.PRIMARY_BLUE, fg="white",
                            font=("Segoe UI", 9), height=1)  # Giảm height từ 2 xuống 1
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    
    def update_progress(self, task: DownloadTask) -> None:
        """Cập nhật tiến trình tải xuống trên giao diện"""
        # Tìm item trong treeview
        item_id = None
        for item in self.downloads_tree.get_children():
            if self.downloads_tree.item(item, 'values')[0] == task.progress.filename:
                item_id = item
                break
        
        # Nếu không tìm thấy, tạo mới
        if not item_id and task.progress.filename:
            item_id = self.downloads_tree.insert('', 'end', values=(
                task.progress.filename,
                'Đang tải',
                '0%',
                'N/A',
                'N/A'
            ))
        
        # Cập nhật thông tin
        if item_id:
            if task.progress.status == 'downloading':
                self.downloads_tree.item(item_id, values=(
                    task.progress.filename,
                    'Đang tải',
                    f"{task.progress.percent:.1f}%",
                    task.progress.speed,
                    task.progress.eta
                ))
            elif task.progress.status == 'finished':
                self.downloads_tree.item(item_id, values=(
                    task.progress.filename,
                    'Hoàn thành',
                    '100%',
                    '',
                    ''
                ))
            elif task.progress.status == 'error':
                self.downloads_tree.item(item_id, values=(
                    task.progress.filename,
                    'Lỗi',
                    '',
                    '',
                    task.progress.error_message
                ))
        
        # Cập nhật thanh trạng thái
        if task.progress.status == 'downloading':
            self.status_var.set(f"Đang tải: {task.progress.percent:.1f}% | {task.progress.speed} | ETA: {task.progress.eta}")
        elif task.progress.status == 'finished':
            self.status_var.set(f"Đã tải xong: {task.progress.filename}")
        elif task.progress.status == 'error':
            self.status_var.set(f"Lỗi: {task.progress.error_message}")
    
    def analyze_url(self) -> None:
        """Phân tích URL và hiển thị thông tin"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập URL YouTube.")
            return
        
        # Hiển thị thông báo đang phân tích
        self.status_var.set("Đang phân tích URL...")
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, "Đang phân tích URL, vui lòng đợi...")
        self.info_text.config(state=tk.DISABLED)
        self.root.update()
        
        try:
            # Kiểm tra xem URL có phải là playlist không
            is_playlist = self.downloader.is_playlist(url)
            
            if is_playlist:
                # Lấy thông tin playlist
                playlist_info = self.downloader.get_playlist_info(url)
                
                # Hiển thị thông tin
                self.info_text.config(state=tk.NORMAL)
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, f"=== THÔNG TIN PLAYLIST ===\n")
                self.info_text.insert(tk.END, f"Tiêu đề: {playlist_info.title}\n")
                self.info_text.insert(tk.END, f"Kênh: {playlist_info.uploader}\n")
                self.info_text.insert(tk.END, f"Số lượng video: {playlist_info.video_count}\n\n")
                
                # Hiển thị cảnh báo nếu playlist lớn
                if playlist_info.video_count > 10:
                    self.info_text.insert(tk.END, f"⚠️ Cảnh báo: Playlist này có {playlist_info.video_count} video. Tải xuống có thể mất nhiều thời gian.\n\n")
                
                self.info_text.config(state=tk.DISABLED)
                self.status_var.set(f"Đã phân tích playlist: {playlist_info.title}")
            else:
                # Lấy thông tin video
                video_info = self.downloader.get_video_info(url)
                
                # Hiển thị thông tin
                self.info_text.config(state=tk.NORMAL)
                self.info_text.delete(1.0, tk.END)
                self.info_text.insert(tk.END, f"=== THÔNG TIN VIDEO ===\n")
                self.info_text.insert(tk.END, f"Tiêu đề: {video_info.title}\n")
                self.info_text.insert(tk.END, f"Kênh: {video_info.uploader}\n")
                self.info_text.insert(tk.END, f"Thời lượng: {format_duration(video_info.duration)}\n")
                if video_info.view_count:
                    self.info_text.insert(tk.END, f"Lượt xem: {video_info.view_count:,}\n".replace(',', '.'))
                self.info_text.insert(tk.END, f"Ngày đăng: {video_info.upload_date}\n\n")
                
                # Hiển thị danh sách format
                self.info_text.insert(tk.END, "=== ĐỊNH DẠNG CÓ SẴN ===\n")
                
                # Format video
                video_formats = [f for f in video_info.formats if f.has_video]
                video_formats.sort(key=lambda f: int(f.resolution.replace('p', '')) if f.resolution.replace('p', '').isdigit() else 0, reverse=True)
                
                self.info_text.insert(tk.END, "Video:\n")
                for f in video_formats[:5]:  # Chỉ hiển thị 5 format đầu tiên
                    self.info_text.insert(tk.END, f" • {f}\n")
                
                if len(video_formats) > 5:
                    self.info_text.insert(tk.END, f" • ... và {len(video_formats) - 5} định dạng khác\n")
                
                # Format audio
                audio_formats = [f for f in video_info.formats if not f.has_video and f.has_audio]
                audio_formats.sort(key=lambda f: f.bitrate, reverse=True)
                
                self.info_text.insert(tk.END, "\nAudio:\n")
                for f in audio_formats[:3]:  # Chỉ hiển thị 3 format đầu tiên
                    self.info_text.insert(tk.END, f" • {f}\n")
                
                if len(audio_formats) > 3:
                    self.info_text.insert(tk.END, f" • ... và {len(audio_formats) - 3} định dạng khác\n")
                
                self.info_text.config(state=tk.DISABLED)
                self.status_var.set(f"Đã phân tích video: {video_info.title}")
        except Exception as e:
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, f"Lỗi khi phân tích URL:\n{str(e)}")
            self.info_text.config(state=tk.DISABLED)
            self.status_var.set("Lỗi khi phân tích URL")
            logger.error(f"Lỗi khi phân tích URL: {e}")
            traceback.print_exc()
    
    def browse_directory(self) -> None:
        """Mở hộp thoại chọn thư mục lưu"""
        directory = filedialog.askdirectory(initialdir=self.save_dir_entry.get())
        if directory:
            self.save_dir_entry.delete(0, tk.END)
            self.save_dir_entry.insert(0, directory)
    
    def get_download_options(self) -> DownloadOptions:
        """Lấy tùy chọn tải xuống từ giao diện"""
        options = self.config_manager.get_download_options()
        
        # Cập nhật từ giao diện
        options.download_dir = self.save_dir_entry.get()
        max_workers_value = int(self.max_workers.get())
        # ✅ THÊM VALIDATION
        if max_workers_value > 10:
            max_workers_value = 10
            messagebox.showwarning("Cảnh báo", "Số luồng tối đa là 10. Đã điều chỉnh về 10.")
        elif max_workers_value < 1:
            max_workers_value = 1
            messagebox.showwarning("Cảnh báo", "Số luồng tối thiểu là 1. Đã điều chỉnh về 1.")
        
        options.max_workers = max_workers_value
        options.download_thumbnails = self.download_thumbnail.get()
        options.download_subtitles = self.download_subtitle.get()
        options.output_template = os.path.join(options.download_dir, '%(title)s.%(ext)s')
        
        # Thiết lập format dựa trên chế độ tải
        mode = self.download_mode.get()
        if mode == "1":  # Chỉ audio (MP3)
            options.format_selector = 'bestaudio'
            options.convert_to_mp3 = True
            options.audio_quality = "192"
        elif mode == "2":  # Chỉ video (không audio)
            options.format_selector = 'bestvideo[ext=mp4]'
            options.convert_to_mp3 = False
        elif mode == "3":  # Video + audio (MP4)
            options.format_selector = 'bestvideo[ext=mp4]+bestaudio/best'
            options.merge = True
            options.merge_format = 'mp4'
            options.convert_to_mp3 = False
        elif mode == "4":  # Chọn format cụ thể
            format_id = self.format_entry.get().strip()
            if format_id:
                options.format_selector = format_id
                options.merge = '+' in format_id
                options.merge_format = 'mp4'
                options.convert_to_mp3 = False
        
        # Cập nhật cấu hình
        self.config_manager.update_from_options(options)
        
        return options
    
    def start_download(self) -> None:
        """Bắt đầu tải xuống"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập URL YouTube.")
            return
        
        # Lấy tùy chọn tải xuống
        options = self.get_download_options()

        try:
            os.makedirs(options.download_dir, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo thư mục: {options.download_dir}\nLỗi: {e}")
            return
        
        # Vô hiệu hóa nút tải xuống và phân tích
        self.download_button.config(state=tk.DISABLED)
        self.analyze_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        
        # Xóa danh sách tải xuống hiện tại
        for item in self.downloads_tree.get_children():
            self.downloads_tree.delete(item)
        
        # Cập nhật trạng thái
        self.status_var.set("Đang bắt đầu tải xuống...")
        
        # Tạo và bắt đầu thread tải xuống
        self.download_thread = threading.Thread(target=self._download_thread, args=(url, options))
        self.download_thread.daemon = True
        self.download_thread.start()
    
    def _download_thread(self, url: str, options: DownloadOptions) -> None:
        """Thread tải xuống"""
        try:
            success = self.downloader.download(url, options)
            
            # Cập nhật UI khi hoàn thành
            self.root.after(0, self._download_completed, success)
        except Exception as e:
            logger.error(f"Lỗi khi tải xuống: {e}")
            traceback.print_exc()
            
            # Cập nhật UI khi có lỗi
            self.root.after(0, self._download_error, str(e))
    
    def _download_completed(self, success: bool) -> None:
        """Xử lý khi tải xuống hoàn thành"""
        # Kích hoạt lại nút
        self.download_button.config(state=tk.NORMAL)
        self.analyze_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        
        if success:
            self.status_var.set("Tải xuống hoàn tất!")
            messagebox.showinfo("Thông báo", "Tải xuống hoàn tất!")
        else:
            self.status_var.set("Tải xuống không thành công. Xem log để biết thêm chi tiết.")
            messagebox.showerror("Lỗi", "Tải xuống không thành công. Xem log để biết thêm chi tiết.")
    
    def _download_error(self, error_message: str) -> None:
        """Xử lý khi có lỗi tải xuống"""
        # Kích hoạt lại nút
        self.download_button.config(state=tk.NORMAL)
        self.analyze_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        
        self.status_var.set(f"Lỗi: {error_message}")
        messagebox.showerror("Lỗi", f"Lỗi khi tải xuống: {error_message}")
    
    def cancel_download(self) -> None:
        """Hủy tải xuống đang chạy"""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn hủy tất cả các tải xuống đang chạy?"):
            self.downloader.cancel_all_downloads()
            self.status_var.set("Đã hủy tất cả các tải xuống.")
            
            # Kích hoạt lại nút
            self.download_button.config(state=tk.NORMAL)
            self.analyze_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)
    
    def check_for_updates(self) -> None:
        """Kiểm tra cập nhật cho yt-dlp"""
        try:
            has_update, latest_version = VersionChecker.check_for_updates()
            if has_update:
                if messagebox.askyesno("Cập nhật có sẵn", 
                                     f"Có phiên bản mới của yt-dlp: {latest_version} (hiện tại: {yt_dlp_version}).\n\nBạn có muốn cập nhật ngay?"):
                    self.status_var.set("Đang cập nhật yt-dlp...")
                    success = VersionChecker.update_yt_dlp()
                    
                    if success:
                        messagebox.showinfo("Cập nhật thành công", 
                                         "Đã cập nhật yt-dlp thành công. Vui lòng khởi động lại ứng dụng.")
                        self.root.quit()
                    else:
                        messagebox.showerror("Lỗi cập nhật", 
                                          "Không thể cập nhật yt-dlp. Vui lòng thử lại sau hoặc cập nhật thủ công.")
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra cập nhật: {e}")
    
    def resume_downloads(self) -> None:
        """Tiếp tục các tải xuống đã bị gián đoạn"""
        tasks_data = self.config_manager.load_download_state()
        if not tasks_data:
            messagebox.showinfo("Thông báo", "Không có tải xuống nào cần tiếp tục.")
            return
        
        if messagebox.askyesno("Tiếp tục tải xuống", 
                             f"Tìm thấy {len(tasks_data)} tải xuống bị gián đoạn. Bạn có muốn tiếp tục?"):
            # Xóa danh sách tải xuống hiện tại
            for item in self.downloads_tree.get_children():
                self.downloads_tree.delete(item)
            
            # Vô hiệu hóa nút tải xuống và phân tích
            self.download_button.config(state=tk.DISABLED)
            self.analyze_button.config(state=tk.DISABLED)
            self.cancel_button.config(state=tk.NORMAL)
            
            # Cập nhật trạng thái
            self.status_var.set("Đang tiếp tục tải xuống...")
            
            # Tạo và bắt đầu thread tải xuống
            self.download_thread = threading.Thread(target=self._resume_thread)
            self.download_thread.daemon = True
            self.download_thread.start()
    
    def _resume_thread(self) -> None:
        """Thread tiếp tục tải xuống"""
        try:
            success = self.downloader.resume_downloads()
            
            # Cập nhật UI khi hoàn thành
            self.root.after(0, self._download_completed, success)
        except Exception as e:
            logger.error(f"Lỗi khi tiếp tục tải xuống: {e}")
            traceback.print_exc()
            
            # Cập nhật UI khi có lỗi
            self.root.after(0, self._download_error, str(e))
    
    def clear_download_history(self) -> None:
        """Xóa lịch sử tải xuống"""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa lịch sử tải xuống?"):
            try:
                if os.path.exists(STATE_FILE):
                    os.remove(STATE_FILE)
                    messagebox.showinfo("Thông báo", "Đã xóa lịch sử tải xuống.")
                else:
                    messagebox.showinfo("Thông báo", "Không có lịch sử tải xuống.")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa lịch sử tải xuống: {e}")
    
    def show_settings(self) -> None:
        """Hiển thị cửa sổ cài đặt với style đẹp"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("⚙️ Cài đặt")
        settings_window.geometry("700x500")
        settings_window.minsize(700, 500)
        settings_window.configure(bg=ColorTheme.BACKGROUND)
        settings_window.grab_set()
        
        # Header đẹp
        header = tk.Frame(settings_window, bg=ColorTheme.PRIMARY_BLUE, height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="⚙️ Cài đặt ứng dụng", 
                font=("Segoe UI", 14, "bold"),
                fg="white", bg=ColorTheme.PRIMARY_BLUE).pack(expand=True)
        
        # Notebook với style
        notebook = ttk.Notebook(settings_window, style="Modern.TNotebook")
        notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # =================== TAB CHUNG ===================
        general_tab = tk.Frame(notebook, bg=ColorTheme.FRAME_BACKGROUND, padx=20, pady=20)
        notebook.add(general_tab, text="🏠 Chung")
        
        # Cài đặt thư mục lưu mặc định
        tk.Label(general_tab, text="📁 Thư mục lưu mặc định:", 
                font=("Segoe UI", 10, "bold"),
                fg=ColorTheme.TEXT_PRIMARY, 
                bg=ColorTheme.FRAME_BACKGROUND).grid(row=0, column=0, sticky=tk.W, pady=10)
        
        dir_frame = tk.Frame(general_tab, bg=ColorTheme.FRAME_BACKGROUND)
        dir_frame.grid(row=0, column=1, sticky=tk.W+tk.E, pady=10, padx=(10, 0))
        dir_frame.columnconfigure(0, weight=1)
        
        default_dir = self.config_manager.get_download_options().download_dir
        self.default_dir_entry = ttk.Entry(dir_frame, width=40, style="Modern.TEntry")
        self.default_dir_entry.grid(row=0, column=0, sticky=tk.W+tk.E, padx=(0, 10))
        self.default_dir_entry.insert(0, default_dir)
        
        browse_button = ttk.Button(dir_frame, text="📂 Duyệt...", 
                                command=self.browse_default_directory, 
                                style="Warning.TButton")
        browse_button.grid(row=0, column=1)
        
        # Cài đặt số luồng tải xuống
        tk.Label(general_tab, text="⚡ Số luồng tải xuống:", 
                font=("Segoe UI", 10, "bold"),
                fg=ColorTheme.TEXT_PRIMARY, 
                bg=ColorTheme.FRAME_BACKGROUND).grid(row=1, column=0, sticky=tk.W, pady=10)
        
        max_workers = self.config_manager.get_download_options().max_workers
        self.default_max_workers = tk.StringVar(value=str(max_workers))
        
        workers_frame = tk.Frame(general_tab, bg=ColorTheme.FRAME_BACKGROUND)
        workers_frame.grid(row=1, column=1, sticky=tk.W, pady=10, padx=(10, 0))
        
        ttk.Spinbox(workers_frame, from_=1, to=10, width=5, 
                textvariable=self.default_max_workers, 
                font=("Segoe UI", 10)).pack(side=tk.LEFT)
        
        tk.Label(workers_frame, text="(khuyến nghị: 7, tối đa: 10)", 
                font=("Segoe UI", 9),
                fg=ColorTheme.TEXT_SECONDARY, 
                bg=ColorTheme.FRAME_BACKGROUND).pack(side=tk.LEFT, padx=(10, 0))
        
        # Cài đặt kiểm tra cập nhật
        self.check_updates = tk.BooleanVar(value=self.config_manager.config.getboolean('general', 'check_for_updates', fallback=True))
        
        update_frame = tk.Frame(general_tab, bg=ColorTheme.FRAME_BACKGROUND)
        update_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        ttk.Checkbutton(update_frame, text="🔄 Tự động kiểm tra cập nhật khi khởi động", 
                    variable=self.check_updates, 
                    style="Modern.TCheckbutton").pack(side=tk.LEFT)
        
        # =================== TAB TẢI XUỐNG ===================
        download_tab = tk.Frame(notebook, bg=ColorTheme.FRAME_BACKGROUND, padx=20, pady=20)
        notebook.add(download_tab, text="📥 Tải xuống")
        
        # Số lần thử lại
        tk.Label(download_tab, text="🔄 Số lần thử lại:", 
                font=("Segoe UI", 10, "bold"),
                fg=ColorTheme.TEXT_PRIMARY, 
                bg=ColorTheme.FRAME_BACKGROUND).grid(row=0, column=0, sticky=tk.W, pady=10)
        
        retry_count = self.config_manager.get_download_options().retry_count
        self.retry_count = tk.StringVar(value=str(retry_count))
        
        retry_frame = tk.Frame(download_tab, bg=ColorTheme.FRAME_BACKGROUND)
        retry_frame.grid(row=0, column=1, sticky=tk.W, pady=10, padx=(10, 0))
        
        ttk.Spinbox(retry_frame, from_=1, to=20, width=5, 
                textvariable=self.retry_count, 
                font=("Segoe UI", 10)).pack(side=tk.LEFT)
        
        tk.Label(retry_frame, text="lần", 
                font=("Segoe UI", 9),
                fg=ColorTheme.TEXT_SECONDARY, 
                bg=ColorTheme.FRAME_BACKGROUND).pack(side=tk.LEFT, padx=(5, 0))
        
        # Thời gian chờ giữa các lần tải
        tk.Label(download_tab, text="⏰ Thời gian chờ giữa các lần tải:", 
                font=("Segoe UI", 10, "bold"),
                fg=ColorTheme.TEXT_PRIMARY, 
                bg=ColorTheme.FRAME_BACKGROUND).grid(row=1, column=0, sticky=tk.W, pady=10)
        
        sleep_interval = self.config_manager.get_download_options().sleep_interval
        self.sleep_interval = tk.StringVar(value=str(sleep_interval))
        
        sleep_frame = tk.Frame(download_tab, bg=ColorTheme.FRAME_BACKGROUND)
        sleep_frame.grid(row=1, column=1, sticky=tk.W, pady=10, padx=(10, 0))
        
        ttk.Spinbox(sleep_frame, from_=0, to=30, width=5, 
                textvariable=self.sleep_interval, 
                font=("Segoe UI", 10)).pack(side=tk.LEFT)
        
        tk.Label(sleep_frame, text="giây", 
                font=("Segoe UI", 9),
                fg=ColorTheme.TEXT_SECONDARY, 
                bg=ColorTheme.FRAME_BACKGROUND).pack(side=tk.LEFT, padx=(5, 0))
        
        # Giới hạn tốc độ
        tk.Label(download_tab, text="🚀 Giới hạn tốc độ:", 
                font=("Segoe UI", 10, "bold"),
                fg=ColorTheme.TEXT_PRIMARY, 
                bg=ColorTheme.FRAME_BACKGROUND).grid(row=2, column=0, sticky=tk.W, pady=10)
        
        rate_limit = self.config_manager.get_download_options().rate_limit
        self.rate_limit = tk.StringVar(value=rate_limit)
        
        rate_frame = tk.Frame(download_tab, bg=ColorTheme.FRAME_BACKGROUND)
        rate_frame.grid(row=2, column=1, sticky=tk.W, pady=10, padx=(10, 0))
        
        ttk.Entry(rate_frame, width=10, textvariable=self.rate_limit, 
                style="Modern.TEntry").pack(side=tk.LEFT)
        
        tk.Label(rate_frame, text="(ví dụ: 500K, 2M)", 
                font=("Segoe UI", 9),
                fg=ColorTheme.TEXT_SECONDARY, 
                bg=ColorTheme.FRAME_BACKGROUND).pack(side=tk.LEFT, padx=(10, 0))
        
        # Tải thumbnail mặc định
        self.default_download_thumbnail = tk.BooleanVar(value=self.config_manager.get_download_options().download_thumbnails)
        
        thumbnail_frame = tk.Frame(download_tab, bg=ColorTheme.FRAME_BACKGROUND)
        thumbnail_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        ttk.Checkbutton(thumbnail_frame, text="🖼️ Tải thumbnail theo mặc định", 
                    variable=self.default_download_thumbnail, 
                    style="Modern.TCheckbutton").pack(side=tk.LEFT)
        
        # Tải subtitle mặc định
        self.default_download_subtitle = tk.BooleanVar(value=self.config_manager.get_download_options().download_subtitles)
        
        subtitle_frame = tk.Frame(download_tab, bg=ColorTheme.FRAME_BACKGROUND)
        subtitle_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        ttk.Checkbutton(subtitle_frame, text="📝 Tải subtitle theo mặc định", 
                    variable=self.default_download_subtitle, 
                    style="Modern.TCheckbutton").pack(side=tk.LEFT)
        
        # Ngôn ngữ subtitle
        tk.Label(download_tab, text="🌐 Ngôn ngữ subtitle:", 
                font=("Segoe UI", 10, "bold"),
                fg=ColorTheme.TEXT_PRIMARY, 
                bg=ColorTheme.FRAME_BACKGROUND).grid(row=5, column=0, sticky=tk.W, pady=10)
        
        subtitle_langs = ','.join(self.config_manager.get_download_options().subtitle_languages)
        self.subtitle_langs = tk.StringVar(value=subtitle_langs)
        
        lang_frame = tk.Frame(download_tab, bg=ColorTheme.FRAME_BACKGROUND)
        lang_frame.grid(row=5, column=1, sticky=tk.W, pady=10, padx=(10, 0))
        
        ttk.Entry(lang_frame, width=20, textvariable=self.subtitle_langs, 
                style="Modern.TEntry").pack(side=tk.LEFT)
        
        tk.Label(lang_frame, text="(phân cách bằng dấu phẩy)", 
                font=("Segoe UI", 9),
                fg=ColorTheme.TEXT_SECONDARY, 
                bg=ColorTheme.FRAME_BACKGROUND).pack(side=tk.LEFT, padx=(10, 0))
        
        # =================== TAB XÁC THỰC ===================
        auth_tab = tk.Frame(notebook, bg=ColorTheme.FRAME_BACKGROUND, padx=20, pady=20)
        notebook.add(auth_tab, text="🔐 Xác thực")
        
        # Proxy
        self.use_proxy = tk.BooleanVar(value=bool(self.config_manager.get_download_options().proxy))
        
        proxy_check_frame = tk.Frame(auth_tab, bg=ColorTheme.FRAME_BACKGROUND)
        proxy_check_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        ttk.Checkbutton(proxy_check_frame, text="🌐 Sử dụng proxy", 
                    variable=self.use_proxy, command=self.toggle_proxy, 
                    style="Modern.TCheckbutton").pack(side=tk.LEFT)
        
        tk.Label(auth_tab, text="🔗 Địa chỉ proxy:", 
                font=("Segoe UI", 10, "bold"),
                fg=ColorTheme.TEXT_PRIMARY, 
                bg=ColorTheme.FRAME_BACKGROUND).grid(row=1, column=0, sticky=tk.W, pady=10)
        
        proxy = self.config_manager.get_download_options().proxy
        self.proxy = tk.StringVar(value=proxy)
        
        proxy_frame = tk.Frame(auth_tab, bg=ColorTheme.FRAME_BACKGROUND)
        proxy_frame.grid(row=1, column=1, sticky=tk.W+tk.E, pady=10, padx=(10, 0))
        proxy_frame.columnconfigure(0, weight=1)
        
        self.proxy_entry = ttk.Entry(proxy_frame, textvariable=self.proxy, 
                                    style="Modern.TEntry")
        self.proxy_entry.grid(row=0, column=0, sticky=tk.W+tk.E)
        
        if not self.use_proxy.get():
            self.proxy_entry.config(state=tk.DISABLED)
        
        tk.Label(proxy_frame, text="(ví dụ: socks5://127.0.0.1:1080)", 
                font=("Segoe UI", 9),
                fg=ColorTheme.TEXT_SECONDARY, 
                bg=ColorTheme.FRAME_BACKGROUND).grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Cookies
        self.use_cookies = tk.BooleanVar(value=self.config_manager.get_download_options().use_cookies)
        
        cookies_check_frame = tk.Frame(auth_tab, bg=ColorTheme.FRAME_BACKGROUND)
        cookies_check_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(20, 10))
        
        ttk.Checkbutton(cookies_check_frame, text="🍪 Sử dụng cookies", 
                    variable=self.use_cookies, command=self.toggle_cookies, 
                    style="Modern.TCheckbutton").pack(side=tk.LEFT)
        
        tk.Label(auth_tab, text="📄 File cookies:", 
                font=("Segoe UI", 10, "bold"),
                fg=ColorTheme.TEXT_PRIMARY, 
                bg=ColorTheme.FRAME_BACKGROUND).grid(row=3, column=0, sticky=tk.W, pady=10)
        
        cookies_frame = tk.Frame(auth_tab, bg=ColorTheme.FRAME_BACKGROUND)
        cookies_frame.grid(row=3, column=1, sticky=tk.W+tk.E, pady=10, padx=(10, 0))
        cookies_frame.columnconfigure(0, weight=1)
        
        cookies_file = self.config_manager.get_download_options().cookies_file
        self.cookies_file = tk.StringVar(value=cookies_file)
        
        self.cookies_entry = ttk.Entry(cookies_frame, textvariable=self.cookies_file, 
                                    style="Modern.TEntry")
        self.cookies_entry.grid(row=0, column=0, sticky=tk.W+tk.E, padx=(0, 10))
        
        if not self.use_cookies.get():
            self.cookies_entry.config(state=tk.DISABLED)
        
        cookies_browse = ttk.Button(cookies_frame, text="📂 Duyệt...", 
                                command=self.browse_cookies_file, 
                                style="Warning.TButton")
        cookies_browse.grid(row=0, column=1)
        
        if not self.use_cookies.get():
            cookies_browse.config(state=tk.DISABLED)
        self.cookies_browse = cookies_browse
        
        # =================== NÚT ĐIỀU KHIỂN ===================
        button_frame = tk.Frame(settings_window, bg=ColorTheme.BACKGROUND)
        button_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Nút với màu sắc đẹp
        ttk.Button(button_frame, text="💾 Lưu", 
                command=lambda: self.save_settings(settings_window), 
                style="Success.TButton").pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(button_frame, text="❌ Hủy", 
                command=settings_window.destroy, 
                style="Danger.TButton").pack(side=tk.RIGHT)
        
        # Cấu hình grid weights
        general_tab.columnconfigure(1, weight=1)
        download_tab.columnconfigure(1, weight=1)
        auth_tab.columnconfigure(1, weight=1)

    
    def browse_default_directory(self) -> None:
        """Mở hộp thoại chọn thư mục lưu mặc định"""
        directory = filedialog.askdirectory(initialdir=self.default_dir_entry.get())
        if directory:
            self.default_dir_entry.delete(0, tk.END)
            self.default_dir_entry.insert(0, directory)
    
    def browse_cookies_file(self) -> None:
        """Mở hộp thoại chọn file cookies"""
        file_path = filedialog.askopenfilename(
            title="Chọn file cookies",
            filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            self.cookies_file.set(file_path)
    
    def toggle_proxy(self) -> None:
        """Bật/tắt trạng thái nhập proxy"""
        if self.use_proxy.get():
            self.proxy_entry.config(state=tk.NORMAL)
        else:
            self.proxy_entry.config(state=tk.DISABLED)
    
    def toggle_cookies(self) -> None:
        """Bật/tắt trạng thái nhập cookies"""
        if self.use_cookies.get():
            self.cookies_entry.config(state=tk.NORMAL)
            self.cookies_browse.config(state=tk.NORMAL)
        else:
            self.cookies_entry.config(state=tk.DISABLED)
            self.cookies_browse.config(state=tk.DISABLED)
    
    def save_settings(self, window) -> None:
        """Lưu cài đặt và đóng cửa sổ"""
        try:
            # Cập nhật cấu hình
            if 'general' not in self.config_manager.config:
                self.config_manager.config['general'] = {}
            
            self.config_manager.config['general']['download_dir'] = self.default_dir_entry.get()
            self.config_manager.config['general']['max_workers'] = self.default_max_workers.get()
            self.config_manager.config['general']['check_for_updates'] = str(self.check_updates.get()).lower()
            
            if 'download' not in self.config_manager.config:
                self.config_manager.config['download'] = {}
            
            self.config_manager.config['download']['retry_count'] = self.retry_count.get()
            self.config_manager.config['download']['sleep_interval'] = self.sleep_interval.get()
            self.config_manager.config['download']['rate_limit'] = self.rate_limit.get()
            self.config_manager.config['download']['download_thumbnails'] = str(self.default_download_thumbnail.get()).lower()
            self.config_manager.config['download']['download_subtitles'] = str(self.default_download_subtitle.get()).lower()
            
            if 'authentication' not in self.config_manager.config:
                self.config_manager.config['authentication'] = {}
            
            self.config_manager.config['authentication']['use_proxy'] = str(self.use_proxy.get()).lower()
            self.config_manager.config['authentication']['proxy'] = self.proxy.get() if self.use_proxy.get() else ''
            self.config_manager.config['authentication']['use_cookies'] = str(self.use_cookies.get()).lower()
            self.config_manager.config['authentication']['cookies_file'] = self.cookies_file.get() if self.use_cookies.get() else ''
            
            # Lưu cấu hình
            self.config_manager.save_config()
            
            # Cập nhật tùy chọn tải xuống mặc định
            self.downloader.default_options = self.config_manager.get_download_options()
            
            # Cập nhật giao diện
            self.save_dir_entry.delete(0, tk.END)
            self.save_dir_entry.insert(0, self.default_dir_entry.get())
            self.max_workers.set(self.default_max_workers.get())
            self.download_thumbnail.set(self.default_download_thumbnail.get())
            self.download_subtitle.set(self.default_download_subtitle.get())
            
            # Đóng cửa sổ
            window.destroy()
            
            # Hiển thị thông báo
            self.status_var.set("Đã lưu cài đặt.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu cài đặt: {e}")
    
    def show_help(self) -> None:
        """Hiển thị hướng dẫn sử dụng"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Hướng dẫn sử dụng")
        help_window.geometry("700x500")
        help_window.minsize(700, 500)
        
        help_text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, padx=10, pady=10)
        help_text.pack(fill=tk.BOTH, expand=True)
        
        help_content = """# HƯỚNG DẪN SỬ DỤNG YOUTUBE downloadER PRO

## Giới thiệu
YouTube downloader Pro là công cụ tải video/audio từ YouTube với nhiều tính năng nâng cao. Ứng dụng hỗ trợ tải video đơn lẻ hoặc playlist với nhiều tùy chọn định dạng khác nhau.

## Các bước cơ bản
1. Nhập URL video hoặc playlist YouTube vào ô URL
2. Nhấn nút "Phân tích" để lấy thông tin
3. Chọn chế độ tải xuống phù hợp
4. Nhấn nút "Tải xuống" để bắt đầu tải

## Các chế độ tải xuống
- **Chỉ audio (MP3)**: Tải audio chất lượng cao nhất và chuyển đổi sang MP3
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
        """Hiển thị thông tin về ứng dụng"""
        about_window = tk.Toplevel(self.root)
        about_window.title("Giới thiệu")
        about_window.geometry("400x300")
        about_window.minsize(400, 300)
        about_window.resizable(False, False)
        
        # Logo (có thể thay bằng logo thực tế)
        logo_frame = ttk.Frame(about_window)
        logo_frame.pack(pady=(20, 10))
        
        ttk.Label(logo_frame, text="YouTube downloader Pro", font=("Helvetica", 16, "bold")).pack()
        
        # Thông tin
        info_frame = ttk.Frame(about_window)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        ttk.Label(info_frame, text=f"Phiên bản: {VERSION}").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"yt-dlp: {yt_dlp_version}").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text=f"Python: {sys.version.split()[0]}").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text="").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text="Tác giả: YouTube downloader Team").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text="Copyright © 2025").pack(anchor=tk.W, pady=2)
        
        # Nút đóng
        ttk.Button(about_window, text="Đóng", command=about_window.destroy).pack(pady=(0, 20))
    
    def run(self) -> None:
        """Khởi chạy giao diện đồ họa"""
        self.root.mainloop()


# Các hàm tiện ích
def format_duration(seconds: int) -> str:
    """Định dạng thời gian từ giây sang HH:MM:SS"""
    if not seconds:
        return "Không xác định"
    
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"

def format_size(bytes_size: int) -> str:
    """Định dạng kích thước file từ byte sang KB, MB, GB"""
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.2f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"

def sanitize(filename: str) -> str:
    """Loại bỏ các ký tự không hợp lệ trong tên file"""
    # Thay thế các ký tự không hợp lệ bằng dấu gạch dưới
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Giới hạn độ dài tên file
    if len(filename) > 200:
        filename = filename[:197] + '...'
    
    return filename

def copy_download_options(options: DownloadOptions) -> DownloadOptions:
    """Tạo bản sao của đối tượng DownloadOptions"""
    import copy
    return copy.deepcopy(options)


def main() -> None:
    """Hàm chính của ứng dụng"""
    parser = argparse.ArgumentParser(description=f"YouTube downloader Pro {VERSION}")
    parser.add_argument('--cli', action='store_true', help='Sử dụng giao diện dòng lệnh')
    parser.add_argument('--gui', action='store_true', help='Sử dụng giao diện đồ họa')
    parser.add_argument('--url', help='URL video hoặc playlist để tải xuống')
    parser.add_argument('--output', help='Thư mục lưu file')
    parser.add_argument('--format', default='best', help='Format selector (mặc định: best)')
    parser.add_argument('--audio-only', action='store_true', help='Chỉ tải audio và chuyển đổi sang MP3')
    parser.add_argument('--max-workers', type=int, default=1, help='Số luồng tải song song (mặc định: 1)')
    
    args = parser.parse_args()
    
    # Nếu không có tham số, hoặc có tham số --gui, sử dụng giao diện đồ họa nếu có thể
    if (not args.cli and not args.url) or args.gui:
        if GUI_AVAILABLE:
            try:
                app = GraphicalUserInterface()
                app.run()
                return
            except Exception as e:
                logger.error(f"Lỗi khi khởi tạo giao diện đồ họa: {e}")
                print(f"Lỗi khi khởi tạo giao diện đồ họa: {e}")
                print("Chuyển sang giao diện dòng lệnh...")
        else:
            print("Không thể tạo giao diện đồ họa. Vui lòng cài đặt tkinter.")
            print("Chuyển sang giao diện dòng lệnh...")
    
    # Sử dụng giao diện dòng lệnh
    if args.url:
        # Chế độ tải xuống trực tiếp từ tham số dòng lệnh
        config_manager = ConfigManager()
        downloader = YouTubeDownloader(config_manager)
        
        options = config_manager.get_download_options()
        
        if args.output:
            options.download_dir = args.output
        
        if args.format:
            options.format_selector = args.format
        
        if args.audio_only:
            options.format_selector = 'bestaudio'
            options.convert_to_mp3 = True
        
        if args.max_workers:
            options.max_workers = args.max_workers
        
        # Tạo thư mục lưu nếu chưa tồn tại
        os.makedirs(options.download_dir, exist_ok=True)
        
        # Tải xuống
        try:
            success = downloader.download(args.url, options)
            if success:
                print(f"\nHoàn tất! File đã được lưu tại: {os.path.abspath(options.download_dir)}")
            else:
                print("\nTải xuống không thành công. Vui lòng kiểm tra log để biết thêm chi tiết.")
        except KeyboardInterrupt:
            print("\nĐã hủy tải xuống bởi người dùng.")
            downloader.cancel_all_downloads()
        finally:
            downloader.cleanup()
    else:
        # Chế độ tương tác
        cli = CommandLineInterface()
        cli.run()


if __name__ == "__main__":
    main()
