# Smart Lock Face Recognition

Ứng dụng thử nghiệm nhận diện khuôn mặt bằng InsightFace, OpenCV và Flask. Hệ
thống stream camera qua MJPEG, đăng ký nhiều embedding cho mỗi người và lưu dữ
liệu cục bộ trong `faces_db/`.

> Đây là prototype, chưa phải khóa cửa production: chưa có HTTPS hay chống giả
> mạo (liveness detection). Không mở trực tiếp ra Internet.

## Cài đặt và chạy

Tạo cấu hình admin trước lần chạy đầu:

```bash
cp .env.example .env
# sửa FLASK_SECRET_KEY, ADMIN_USERNAME và ADMIN_PASSWORD trong .env
```

```bash
cd /home/v005128/Vision_DL/CCD
bash setup.sh
bash run.sh
```

Mở <http://localhost:5000>. Lần chạy đầu InsightFace có thể tải model
`buffalo_l`, vì vậy cần mạng và dung lượng trống.

Nếu không có camera, server vẫn khởi động để xem trạng thái nhưng video, đăng ký
và chụp ảnh sẽ báo lỗi. Đổi camera và các thiết lập khác trong `config.py`.

Tài khoản admin trong `.env` chỉ được tạo khi database còn trống. Admin tạo tài
khoản `user`; user chỉ xem dashboard cơ bản và tự đổi mật khẩu.

## Tài khoản và quyền

- `admin`: quản lý khuôn mặt, chụp ảnh, tạo/list tài khoản user và đổi mật khẩu.
- `user`: xem video/trạng thái cơ bản và đổi mật khẩu của chính mình.
- Không có đăng ký công khai. Admin tạo user tại `/admin/users`.

Toàn bộ route cần đăng nhập; thao tác thay đổi dữ liệu yêu cầu CSRF token. Không
đặt `.env` hoặc `data/users.db` vào Git hay Docker image.

## Cấu hình

Các giá trị được dùng trực tiếp từ `config.py`:

- `MODEL_NAME`, `MODEL_CONTEXT`, `DETECTION_SIZE`
- `RECOGNITION_THRESHOLD`
- `CAMERA_DEVICE_ID`, độ phân giải và FPS camera
- chất lượng JPEG, chu kỳ tính FPS và hiển thị landmarks
- host, port, debug và threaded mode của Flask

`MODEL_CONTEXT=-1` dùng CPU; giá trị từ `0` trở lên yêu cầu
`CUDAExecutionProvider` tương ứng.

## Sử dụng

Web UI hỗ trợ:

1. Xem video và kết quả nhận diện.
2. Nhập tên rồi chọn **Enroll**; đăng ký nhiều lần để lưu nhiều góc mặt.
3. Xem hoặc xóa người đã đăng ký.
4. Chụp ảnh vào `captures/`.

Tên người dài 2-64 ký tự và chỉ gồm chữ Unicode, số, khoảng trắng, dấu chấm,
`_` hoặc `-`.

CLI ảnh tĩnh dùng cùng model, threshold và database với web:

```bash
source venv/bin/activate
python3 test_face_recognition.py
```

## API

| Method | Endpoint | Chức năng |
|---|---|---|
| GET | `/` | Web UI |
| GET | `/video_feed` | MJPEG stream |
| GET | `/status` | Trạng thái camera/nhận diện |
| GET | `/info` | Model, camera và thống kê |
| GET | `/get_people` | Danh sách và số embedding |
| POST | `/enroll_web` | JSON `{"name": "Nguyen Van A"}` |
| POST | `/delete_person` | JSON `{"name": "Nguyen Van A"}` |
| POST | `/capture` | Lưu frame hiện tại |

Route xác thực: `/login`, `/logout`, `/change-password`; route quản trị user:
`/admin/users` và `/api/admin/users`.

Các API thay đổi dữ liệu yêu cầu đăng nhập admin và CSRF token.

## Kiểm tra

```bash
source venv/bin/activate
python3 -m unittest -v test_face_db.py test_auth.py test_web_auth.py
python3 -m compileall -q config.py face_db.py face_utils.py web_stream_face.py test_face_recognition.py
```

Kiểm tra camera/model thật:

```bash
bash run.sh
curl http://localhost:5000/info
curl http://localhost:5000/status
```

## Dữ liệu

Mỗi người có một file pickle trong `faces_db/`. Pickle chỉ nên được đọc từ
nguồn tin cậy. Ảnh chụp và ảnh debug nằm trong `captures/`; embeddings không
thể xem như dữ liệu vô danh và cần được bảo vệ/backup phù hợp.

Xem [INSTALL.md](INSTALL.md) để cài đặt chi tiết và
[STRUCTURE.md](STRUCTURE.md) để hiểu cấu trúc.
