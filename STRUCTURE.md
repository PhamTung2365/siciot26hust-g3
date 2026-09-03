# Cấu trúc project

```text
config.py                    Cấu hình và tạo thư mục runtime
face_utils.py                Khởi tạo InsightFace, detect và lấy embedding
face_db.py                   Lưu pickle, cache, cosine matching và khóa dữ liệu
web_stream_face.py           Camera, Flask API, MJPEG và giao diện web
test_face_recognition.py     CLI ảnh tĩnh dùng chung core modules
test_face_db.py              Smoke test database/validation
requirements.txt             Python dependencies
setup.sh / run.sh            Cài đặt và chạy local
Dockerfile                   Container image
docker-compose.yml           Container + camera + volume dữ liệu
smartlock.service            Mẫu systemd cần chỉnh đường dẫn
faces_db/                    Embedding theo từng người
captures/                    Ảnh capture/debug
data/users.db                SQLite accounts (runtime, không commit)
```

## Luồng chính

```text
camera frame
  -> face_utils.get_face_embedding()
  -> face_db.recognize_face()
  -> web_stream_face CameraState
  -> MJPEG + /status
```

Enroll từ web và từ CLI đều gọi `face_db.add_face()`; xóa đều gọi
`face_db.delete_person()`. Camera được khóa tại `read_frame()` để các request
Flask không đọc đồng thời cùng thiết bị. Database dùng `RLock`, cache trong RAM
và thay file nguyên tử khi ghi.

Kiến trúc module hiện tại đã là separation of concerns phù hợp cho quy mô này.
Không cần thêm repository/service/factory pattern cho tới khi có storage hoặc
model implementation thứ hai.

## Định dạng database

```python
{
    "name": "Nguyen Van A",
    "embeddings": [[...], [...]],
    "created_at": 1724434824.5,
    "updated_at": 1724435012.3,
}
```

File pickle là dữ liệu tin cậy cục bộ, không import file `.pkl` từ nguồn lạ.
