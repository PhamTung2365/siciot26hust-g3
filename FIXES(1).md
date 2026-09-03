# Các điểm đã rà soát và sửa

## 2026-08-25

- Thêm đăng nhập/session/CSRF với SQLite và hai role `admin`/`user`; admin tạo
  user thường, còn user chỉ đổi mật khẩu của chính mình và xem dashboard cơ bản.

- CLI ảnh tĩnh trước đây dùng `faces.pkl`, threshold 0.70 và model config riêng;
  nay dùng chung `face_utils.py`, `face_db.py` và `config.py` với web.
- Chặn tên chứa path/ký tự nguy hiểm tại lớp database dùng chung, tránh ghi hoặc
  xóa file ngoài `faces_db/`.
- Ghi database qua file tạm rồi `os.replace` để giảm nguy cơ file pickle dở
  dang khi tiến trình bị ngắt.
- Áp dụng `CAMERA_DEVICE_ID`, độ phân giải, FPS, JPEG quality, chu kỳ FPS,
  landmarks và model info từ `config.py` thay vì hard-code.
- Khóa thao tác đọc camera dùng chung giữa stream, enroll và capture.
- Capture và ảnh debug được lưu đúng trong `captures/`.
- Trạng thái match/confidence được reset khi không còn khuôn mặt; trạng thái
  ready chỉ bật sau khi đọc được frame.
- Server không thoát toàn bộ khi thiếu camera, nhờ vậy API trạng thái vẫn dùng
  được để chẩn đoán.
- Bỏ refresh database thừa sau delete và bỏ nhánh “low-confidence name” không
  thể xảy ra theo contract của `recognize_face`.
- Viết lại tài liệu: bỏ URL/path mẫu giả, benchmark chưa kiểm chứng và tuyên bố
  “production-ready”; bổ sung giới hạn bảo mật và lệnh kiểm tra thật.
- Docker Compose không còn bắt buộc `/dev/video0`; máy không camera vẫn khởi
  động được, còn webcam được thêm bằng `devices` khi thiết bị thực sự tồn tại.
- Docker image thay OpenCV GUI bằng bản headless để chạy được trong image Python
  slim mà không kéo theo GL/X11.
- Compose giữ model cache trên host và dùng CA bundle hệ thống read-only, tránh
  tải lại model và không cần tắt xác minh TLS trong mạng doanh nghiệp.

## Chủ ý chưa thêm

- Authentication, HTTPS, liveness detection và điều khiển khóa vật lý chưa có
  yêu cầu/giao thức cụ thể; cần làm trước khi triển khai thực tế.
- Không thêm design-pattern boilerplate. Ba module config/model+database/web đã
  tách trách nhiệm đủ rõ cho quy mô hiện tại.
