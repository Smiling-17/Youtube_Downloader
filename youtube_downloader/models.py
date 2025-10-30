"""Domain models used throughout the downloader."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

from .constants import DEFAULT_DOWNLOAD_DIR
from .utils import format_size


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
            audio_state = "cả audio" if self.has_audio else "không audio"
            return (
                f"{self.format_id}: {self.resolution}, {self.fps} fps, "
                f"{self.ext}, {size_str}, {audio_state}"
            )
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
    def from_yt_dlp_info(cls, info: Dict[str, Any]) -> "VideoInfo":
        video_id = info.get("id", "")
        title = info.get("title", "Không có tiêu đề")
        uploader = info.get("uploader", "Không xác định")
        duration = info.get("duration", 0)
        view_count = info.get("view_count", 0)

        upload_date = info.get("upload_date", "")
        if upload_date and len(upload_date) == 8:
            upload_date = f"{upload_date[6:8]}/{upload_date[4:6]}/{upload_date[0:4]}"
        else:
            upload_date = "Không xác định"

        formats = []
        for fmt in info.get("formats", []):
            has_video = fmt.get("vcodec", "none") != "none"
            has_audio = fmt.get("acodec", "none") != "none"

            formats.append(
                VideoFormat(
                    format_id=fmt.get("format_id", ""),
                    ext=fmt.get("ext", ""),
                    resolution=f"{fmt.get('height', '?')}p"
                    if fmt.get("height")
                    else "N/A",
                    fps=fmt.get("fps", "N/A"),
                    filesize=fmt.get("filesize") or 0,
                    has_audio=has_audio,
                    has_video=has_video,
                    bitrate=fmt.get("abr", 0)
                    or fmt.get("tbr", 0)
                    or 0,
                )
            )

        return cls(
            video_id=video_id,
            title=title,
            uploader=uploader,
            duration=duration,
            view_count=view_count,
            upload_date=upload_date,
            formats=formats,
            thumbnail=info.get("thumbnail", ""),
            description=info.get("description", ""),
            url=info.get("webpage_url", "") or info.get("url", ""),
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
    def from_yt_dlp_info(
        cls, info: Dict[str, Any], include_videos: bool = False
    ) -> "PlaylistInfo":
        playlist_id = info.get("id", "")
        title = info.get("title", "Không có tiêu đề")
        uploader = info.get("uploader", "Không xác định")

        video_count = info.get("playlist_count", 0)
        if not video_count and "entries" in info:
            video_count = len(list(info.get("entries") or []))

        videos: List[VideoInfo] = []
        if include_videos and "entries" in info:
            for entry in info.get("entries", []):
                if entry:
                    videos.append(VideoInfo.from_yt_dlp_info(entry))

        return cls(
            playlist_id=playlist_id,
            title=title,
            uploader=uploader,
            video_count=video_count,
            videos=videos,
            url=info.get("webpage_url", "") or info.get("url", ""),
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
        if self.status == "downloading":
            return (
                f"{self.filename} | {self.percent:.1f}% | "
                f"{self.speed} | ETA: {self.eta}"
            )
        if self.status == "finished":
            return f"{self.filename} | Hoàn thành"
        if self.status == "error":
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
    max_downloads: int = 0
    rate_limit: str = ""
    proxy: str = ""
    username: str = ""
    password: str = ""
    use_cookies: bool = False
    cookies_file: str = ""
    download_thumbnails: bool = False
    download_subtitles: bool = False
    subtitle_languages: List[str] = field(default_factory=lambda: ["vi", "en"])
    max_workers: int = 1
    retry_count: int = 10
    fragment_retries: int = 10
    skip_unavailable_fragments: bool = True
    continue_incomplete: bool = True
    sleep_interval: int = 3

    def to_yt_dlp_options(self, is_playlist: bool = False) -> Dict[str, Any]:
        opts: Dict[str, Any] = {
            "format": self.format_selector,
            "outtmpl": self.output_template,
            "noplaylist": not is_playlist,
            "quiet": False,
            "no_warnings": False,
            "progress_hooks": [],
            "retries": self.retry_count,
            "fragment_retries": self.fragment_retries,
            "skip_unavailable_fragments": self.skip_unavailable_fragments,
            "ignoreerrors": False,
            "continue": self.continue_incomplete,
            "socket_timeout": 30,
            "ratelimit": int(self.rate_limit.rstrip("K")) * 1024
            if self.rate_limit and self.rate_limit.endswith("K")
            else None,
        }

        if self.proxy:
            opts["proxy"] = self.proxy

        if self.username and self.password:
            opts["username"] = self.username
            opts["password"] = self.password

        if self.use_cookies and self.cookies_file and os.path.exists(self.cookies_file):
            opts["cookiefile"] = self.cookies_file

        if self.merge:
            opts["merge_output_format"] = self.merge_format

        if self.download_thumbnails:
            opts.setdefault("postprocessors", []).append(
                {"key": "FFmpegThumbnailsConvertor", "format": "jpg"}
            )
            opts["writethumbnail"] = True

        if self.download_subtitles:
            opts.setdefault("postprocessors", []).append(
                {"key": "FFmpegSubtitlesConvertor", "format": "srt"}
            )
            opts["writesubtitles"] = True
            opts["writeautomaticsub"] = True
            opts["subtitleslangs"] = self.subtitle_languages

        if self.convert_to_mp3:
            opts.setdefault("postprocessors", []).append(
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": self.audio_quality,
                }
            )

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
        if self.video_info:
            return self.video_info.title
        if self.playlist_info:
            return f"Playlist: {self.playlist_info.title}"
        return self.url
