# 5. System Architecture

## Kiến trúc end-to-end
```text
Physical World
      ↓
USB/Webcam (input)
      ↓
Local processing: InsightFace + face_utils.py
      ↓
Recognition/cache: face_db.py
      ↓
Flask app: web_stream_face.py
      ├── MJPEG video stream
      ├── JSON status/info API
      └── Authenticated admin/user routes
      ↓
HTTP on local network / localhost
      ↓
Browser dashboard + operator
```

### Phạm vi triển khai hiện tại

- Đây là kiến trúc prototype tập trung: camera, model nhận diện, database cục bộ và Flask backend có thể chạy trên cùng một máy.
- `face_utils.get_face_embedding()` phát hiện khuôn mặt và tạo embedding; `face_db.recognize_face()` so khớp cosine với dữ liệu đã đăng ký.
- `CameraState` giữ trạng thái tạm thời để dashboard đọc qua `/status`; video được phát qua MJPEG và thông tin hệ thống qua `/info`.
- Không có MQTT/broker, cloud platform hoặc database từ xa trong repository hiện tại. HTTP chỉ là kênh truy cập web/API, không phải một luồng telemetry IoT đã hoàn thiện.

## Nếu có điều khiển
```text
Face match / access rule
          ↓
  [planned command boundary]
          ↓
 Local GPIO or device controller
          ↓
 Planned servo/lock actuator
          ↓
 Physical door state
```

- Luồng điều khiển trên là kiến trúc mục tiêu, chưa phải implementation hiện tại. Code hiện chỉ cập nhật trạng thái nhận diện, chưa phát lệnh GPIO/servo và chưa có cảm biến xác nhận cửa đã đóng.
- Khi triển khai phần này cần định nghĩa trạng thái an toàn, timeout, hành vi khi camera/model mất, cơ chế override và kiểm thử không làm người dùng bị mắc kẹt. Không nên cho phép một kết quả nhận diện đơn lẻ tự động mở khóa production khi chưa có các kiểm soát đó.

## Thành phần
| Layer | Thành phần | Vai trò |
|---|---|---|
| Sensing | USB/webcam tương thích OpenCV | Cung cấp frame hình ảnh cho nhận diện; camera có thể không tồn tại, khi đó server vẫn khởi động nhưng video/enroll thất bại. |
| Edge | `face_utils.py`, InsightFace `buffalo_l`, `face_db.py`, `CameraState` | Xử lý cục bộ, tạo embedding, so khớp theo threshold cấu hình và giữ trạng thái nhận diện; `camera_lock` tránh đọc camera đồng thời. |
| Network | HTTP/Flask, MJPEG, JSON API trên host/port cấu hình | Truyền dashboard, video và trạng thái trong mạng cục bộ; không bắt buộc internet và hiện chưa có MQTT/broker. |
| Backend | `web_stream_face.py` + `auth.py` | Cung cấp route, session, role `admin`/`user`, CSRF, enroll/delete/capture và các endpoint `/status`, `/info`, `/get_people`. |
| Database | `faces_db/*.pkl` + SQLite `users.db` | Lưu embedding theo người và tài khoản/password hash; pickle là dữ liệu tin cậy cục bộ, không phải access log hoàn chỉnh. |
| Application | Templates Flask, dashboard web, browser operator | Hiển thị video, match/confidence, thống kê, trạng thái camera/model và các chức năng theo role. |

## Ranh giới và phụ thuộc

- MVP hiện tại kiểm chứng nhận diện và quản trị dữ liệu; actuator servo, LCD, cảm biến cửa, nút override và access-event store vẫn là phần mở rộng trong scope, chưa có BOM/wiring/protocol tương ứng.
- Embedding và ảnh capture/debug là dữ liệu nhạy cảm. Prototype chỉ nên chạy trong mạng tin cậy, không mở trực tiếp ra Internet; HTTPS, liveness detection và hardening production nằm ngoài kiến trúc hiện tại.
- Nếu sau này tách edge khỏi backend, cần bổ sung giao thức xác thực, định dạng message, retry/offline queue, đồng bộ thời gian và quyền điều khiển trước khi dùng sơ đồ IoT phân tán.
