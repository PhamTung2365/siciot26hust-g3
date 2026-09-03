# Cài đặt

## Yêu cầu

- Python 3 có module `venv`
- Camera tương thích OpenCV
- Internet ở lần cài dependency và tải model đầu tiên
- Linux được khuyến nghị cho cấu hình camera/Docker hiện tại

## Cài trực tiếp

Trên thiết bị ARM64, project dùng `onnxruntime==1.19.2`, là bản có wheel
phù hợp với nhiều bản Python Linux ARM. Kiểm tra kiến trúc trước khi cài:

```bash
uname -m       # nên là aarch64 trên thiết bị ARM64
python3 --version
```

Nếu kết quả là `armv7l`/ARM32, pip thường không có wheel ONNX Runtime; cần
dùng hệ điều hành ARM64 hoặc tự build ONNX Runtime trước.

Chạy trong thư mục project, không phụ thuộc tên hay vị trí thư mục:

```bash
cp .env.example .env
# sửa FLASK_SECRET_KEY, ADMIN_USERNAME và ADMIN_PASSWORD
bash setup.sh
bash run.sh
```

`setup.sh` tạo `venv/`, `faces_db/`, `captures/` và cài
`requirements.txt`. `run.sh` luôn dùng Python trong `venv/`.

`.env` là bắt buộc, không được commit và không được dùng mật khẩu mẫu. Khi
database người dùng đã tồn tại, biến admin chỉ bootstrap tài khoản lần đầu để
không tự ghi đè mật khẩu đang dùng.

Cài thủ công tương đương:

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -r requirements.txt
python3 web_stream_face.py
```

## Docker

```bash
docker compose up --build
```

`docker-compose.yml` mặc định không mount camera nên vẫn chạy được trên máy
không có `/dev/video*`. Khi có webcam, thêm vào service `smartlock`:

```yaml
devices:
  - /dev/video0:/dev/video0
```

Nếu thiết bị có ID khác, sửa mapping trên và `CAMERA_DEVICE_ID` trong
`config.py`. Compose cũng mount cache model từ `${HOME}/.insightface/models`
để không tải lại khi recreate container, và mount CA bundle hệ thống read-only
cho HTTPS. Các thư mục dữ liệu được mount ra host.

## Systemd

`smartlock.service` là ví dụ và phải được sửa `User`, `WorkingDirectory`,
`Environment=PATH` và `ExecStart` cho đúng máy trước khi cài:

```bash
sudo cp smartlock.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now smartlock
sudo journalctl -u smartlock -f
```

## Xử lý lỗi

- Không có camera: kiểm tra `ls /dev/video*`, quyền thiết bị và
  `CAMERA_DEVICE_ID` trong `config.py`.
- Model không tải: kiểm tra mạng, dung lượng và thư mục
  `~/.insightface/models/`.
- Nếu HTTPS báo `CERTIFICATE_VERIFY_FAILED` trong mạng doanh nghiệp, trỏ
  `REQUESTS_CA_BUNDLE` tới CA bundle do hệ thống/quản trị viên cung cấp; không
  tắt xác minh TLS.
- Port bận: đổi `SERVER_PORT` trong `config.py`.
- Thiếu module: kích hoạt đúng `venv` rồi chạy
  `python3 -m pip install -r requirements.txt`.
- Chậm: giảm `DETECTION_SIZE`, chọn model nhỏ hơn hoặc giảm chất lượng JPEG.

Sau khi cài, chạy các lệnh kiểm tra trong [README.md](README.md#kiểm-tra).
