# YouTube Downloader Pro 🎥

Ứng dụng tải video YouTube với giao diện thân thiện và nhiều tính năng hữu ích.

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

## 🌟 Tính năng chính

- **Tải video đa dạng**:
  - Tải video đơn lẻ
  - Tải toàn bộ playlist
  - Hỗ trợ nhiều định dạng (MP4, MP3, WebM)
  - Tải thumbnail và phụ đề

- **Tùy chọn tải xuống**:
  - Chỉ tải audio (MP3)
  - Chỉ tải video (không audio)
  - Tải video + audio (MP4)
  - Format tùy chỉnh

- **Tính năng nâng cao**:
  - Tải song song với số luồng có thể cấu hình
  - Tiếp tục tải xuống bị gián đoạn
  - Hỗ trợ proxy và cookies
  - Cập nhật tự động yt-dlp

## 🚀 Cài đặt

### Yêu cầu hệ thống
- Python 3.8 trở lên
- Windows 10/11

### Cách cài đặt

1. **Tải xuống dự án**:
   ```bash
   git clone https://github.com/Smiling-17/Youtube_Downloader.git
   cd Youtube_Downloader
   ```

2. **Cài đặt các thư viện cần thiết**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Chạy chương trình**:
   - Double-click vào file `RUN.bat`
   - Hoặc chạy lệnh: `python main.py`

## 💻 Hướng dẫn sử dụng

### Giao diện đồ họa (GUI)

1. **Tải video đơn lẻ**:
   - Dán URL video vào ô nhập liệu
   - Chọn định dạng mong muốn
   - Nhấn "Tải xuống"

2. **Tải playlist**:
   - Dán URL playlist
   - Chọn thư mục lưu
   - Nhấn "Tải playlist"

3. **Tùy chỉnh cài đặt**:
   - Số luồng tải xuống
   - Thư mục lưu mặc định
   - Proxy và cookies
   - Các tùy chọn nâng cao

### Giao diện dòng lệnh (CLI)

```bash
# Tải video
python main.py -u "URL_VIDEO" -f mp4

# Tải playlist
python main.py -u "URL_PLAYLIST" -p

# Tải chỉ audio
python main.py -u "URL_VIDEO" -f mp3

# Tải với proxy
python main.py -u "URL_VIDEO" --proxy "http://proxy:port"
```

## ⚙️ Cấu hình

File cấu hình `config.json` cho phép tùy chỉnh:

```json
{
    "download_path": "downloads",
    "max_threads": 4,
    "proxy": "",
    "cookies": "",
    "format": "mp4"
}
```

## 🔧 Xử lý sự cố

1. **Lỗi không tải được video**:
   - Kiểm tra kết nối internet
   - Cập nhật yt-dlp: `pip install -U yt-dlp`
   - Kiểm tra URL video

2. **Lỗi proxy**:
   - Kiểm tra cấu hình proxy
   - Thử tắt proxy tạm thời

3. **Lỗi cài đặt**:
   - Đảm bảo Python 3.8+ đã được cài đặt
   - Chạy lại `pip install -r requirements.txt`

## 📝 Ghi chú

- Chương trình tự động cập nhật yt-dlp khi có phiên bản mới
- Có thể tải nhiều video cùng lúc
- Hỗ trợ tiếp tục tải xuống nếu bị gián đoạn

## 🤝 Đóng góp

Mọi đóng góp đều được hoan nghênh! Vui lòng:
1. Fork dự án
2. Tạo nhánh mới
3. Commit thay đổi
4. Push lên nhánh
5. Tạo Pull Request


Made with ❤️ by Smiling 😼
