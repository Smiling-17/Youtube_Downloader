# YouTube Downloader Pro

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

Ứng dụng tải video/audio từ YouTube với cả giao diện đồ họa hiện đại (Tkinter) và dòng lệnh, xây dựng trên nền tảng `yt-dlp`. Dự án hỗ trợ playlist, tải song song, tiếp tục tải bị gián đoạn, proxy/cookies và tự kiểm tra cập nhật.

## 📦 Tính năng chính

- Tải video đơn lẻ hoặc toàn bộ playlist với nhiều định dạng (MP4, MP3, WebM…).
- Hỗ trợ kết hợp video + audio, chuyển đổi sang MP3 và tải thumbnail/phụ đề.
- Tải song song nhiều video với giới hạn tùy chọn, tiếp tục tải khi bị gián đoạn.
- Cấu hình proxy, cookies, giới hạn tốc độ ngay trong GUI hoặc CLI.
- Kiểm tra và cập nhật phiên bản `yt-dlp` trực tiếp từ ứng dụng.
- Ghi log chi tiết vào `youtube_downloader.log`.

## 🧱 Cấu trúc dự án

```
.
├── main.py                     # Điểm vào của ứng dụng (GUI hoặc CLI)
├── requirements.txt
├── RUN.bat
└── youtube_downloader/         # Mã nguồn chính
    ├── __init__.py             # Khởi tạo logging toàn cục
    ├── cli.py                  # Giao diện dòng lệnh
    ├── config.py               # Đọc/ghi cấu hình và trạng thái tải
    ├── constants.py            # Hằng số chung (đường dẫn, phiên bản…)
    ├── downloader.py           # Lớp lõi gọi yt-dlp, quản lý task tải
    ├── gui.py                  # Giao diện Tkinter
    ├── models.py               # Dataclass mô tả video/playlist/tùy chọn
    ├── theme.py                # Bảng màu và style của GUI
    ├── utils.py                # Hàm tiện ích (format thời gian/kích thước…)
    └── versioning.py           # Kiểm tra và cập nhật yt-dlp
```

## 🛠️ Yêu cầu hệ thống

- Python 3.8 trở lên
- Windows/macOS/Linux (GUI yêu cầu `tkinter`)
- FFmpeg (khuyến nghị để ghép/chuyển đổi định dạng)

## 🚀 Cài đặt

```bash
git clone https://github.com/Smiling-17/Youtube_Downloader.git
cd Youtube_Downloader
pip install -r requirements.txt
```

> Windows có thể chạy `RUN.bat` để kích hoạt môi trường ảo (nếu có), cài thư viện và khởi động ứng dụng.

## 💡 Sử dụng

### Giao diện đồ họa (GUI)

```bash
python main.py --gui          # Hoặc chỉ cần python main.py nếu có tkinter
```

1. Dán URL video/playlist và nhấn **Phân tích**.
2. Chọn chế độ tải (Audio, Video, Video+Audio hoặc format cụ thể).
3. Tùy chỉnh thư mục lưu, số luồng, thumbnail, subtitle… ngay trên giao diện.
4. Nhấn **Tải xuống** để bắt đầu; tiến trình hiển thị trong bảng và thanh trạng thái.

### Giao diện dòng lệnh (CLI)

```bash
# Khởi động chế độ CLI tương tác
python main.py --cli

# Tải trực tiếp từ tham số dòng lệnh
python main.py --url "https://youtu.be/VIDEO_ID" --output downloads --format best
python main.py --url "https://youtube.com/playlist?list=..." --max-workers 4
python main.py --url "https://youtu.be/VIDEO_ID" --audio-only
```

- Thêm `--format FORMAT_ID` để chọn format cụ thể (ví dụ `bestvideo[ext=mp4]+bestaudio/best`).
- Sử dụng `--max-workers` để điều chỉnh số luồng tải song song.

## ⚙️ Cấu hình & trạng thái

- Cấu hình người dùng được lưu tại:
  - Windows: `%USERPROFILE%\.youtube_downloader_config.ini`
  - macOS/Linux: `~/.youtube_downloader_config.ini`
- Trạng thái tải đang dang dở nằm trong `~/.youtube_downloader_state.json`; ứng dụng sẽ hỏi tiếp tục khi khởi động.
- Ghi log chi tiết vào `youtube_downloader.log` (cùng thư mục với `main.py`).

## 🧪 Kiểm thử nhanh

Sau khi cài đặt, có thể chạy:

```bash
python -m compileall youtube_downloader main.py
```

để đảm bảo mã nguồn hợp lệ trên môi trường hiện tại.

## 🤝 Đóng góp

1. Fork repository và tạo nhánh mới.
2. Thực hiện thay đổi có mô tả rõ ràng.
3. Đảm bảo code pass lint/test (nếu có).
4. Gửi Pull Request kèm mô tả thay đổi và ảnh chụp (nếu cập nhật UI).

## 📄 Giấy phép

Phát hành dưới giấy phép [MIT](LICENSE). Vui lòng tuân thủ điều khoản bản quyền nội dung khi tải từ YouTube.
