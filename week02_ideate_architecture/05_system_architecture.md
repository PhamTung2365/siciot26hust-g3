# 5. System Architecture

## 1. Kiến trúc tổng quan của hệ thống

Hệ thống khóa thông minh trong dự án được triển khai theo mô hình edge-to-cloud/local IoT, với các thành phần chính sau:

```text
Người dùng / Admin / Browser
          │
          ▼
   Flask Web App (Raspberry Pi)
   - xác thực người dùng
   - dashboard trạng thái
   - truy vấn camera / nhận diện
   - phát lệnh điều khiển cửa
          │
          │ HTTP / session / CSRF
          ▼
   Face Recognition Service
   - camera stream
   - InsightFace
   - database khuôn mặt
   - xác thực người / quyết định mở khóa
          │
          ▼
   MQTT Gateway / Broker
   - smartlock/{door_id}/command
   - smartlock/{door_id}/state
   - smartlock/{door_id}/event
          │
          ▼
   ESP32 Device (door controller)
   - nhận lệnh MQTT
   - điều khiển SG90 servo
   - hiển thị LCD 16x2
   - publish trạng thái cửa
          │
          ▼
   Physical Lock / Door Actuator
   - cánh cửa vật lý
   - chốt khóa cơ khí / servo
```

Trong mô hình này:

- Raspberry Pi là trung tâm xử lý nhận diện và điều phối nghiệp vụ.
- ESP32 là node thiết bị ở phía cánh cửa, trực tiếp thao tác với cơ cấu mở/khóa.
- MQTT là kênh giao tiếp chuẩn giữa backend và thiết bị đầu cuối.
- Web UI và dashboard cho phép người dùng theo dõi trạng thái, quản lý tài khoản và kiểm soát cửa từ xa.

---

## 2. Thành phần thực tế của hệ thống trong repo

### 2.1 Tầng cảm biến và nhận diện

- Camera USB hoặc camera laptop được sử dụng như đầu vào hình ảnh cho nhận diện khuôn mặt.
- Mô hình nhận dạng sử dụng InsightFace và các module như:
  - `src/pi_server/face_utils.py`
  - `src/pi_server/face_db.py`
  - `src/pi_server/web_stream_face.py`
- Các bước xử lý chính:
  1. Chụp frame từ camera.
  2. Phát hiện khuôn mặt.
  3. Trích xuất embedding vector.
  4. So sánh với dữ liệu đã lưu trong `faces_db/`.
  5. Nếu có người phù hợp và đạt ngưỡng xác thực, backend quyết định phát lệnh mở cửa.

### 2.2 Tầng backend và quản trị

- Backend nằm trong [src/pi_server](src/pi_server) và là trung tâm điều phối hệ thống.
- Nó chịu trách nhiệm:
  - cung cấp web UI cho admin/user
  - quản lý session và quyền truy cập
  - lưu trữ tài khoản người dùng trong SQLite
  - lưu trữ embedding khuôn mặt trong `faces_db/`
  - giao tiếp với broker MQTT qua `mqtt_gateway.py`
  - phát lệnh `open` hoặc `lock` tới thiết bị cửa

Các file quan trọng:

- [src/pi_server/web_stream_face.py](src/pi_server/web_stream_face.py)
- [src/pi_server/auth.py](src/pi_server/auth.py)
- [src/pi_server/mqtt_gateway.py](src/pi_server/mqtt_gateway.py)
- [src/pi_server/config.py](src/pi_server/config.py)

### 2.3 Tầng MQTT và điều khiển thiết bị

- Broker Mosquitto được sử dụng như sàn trung gian giao tiếp.
- Gateway thực hiện publish/subscribe với topic chuẩn:
  - `smartlock/{door_id}/command`
  - `smartlock/{door_id}/state`
  - `smartlock/{door_id}/event`
- Thiết bị ESP32 nhận lệnh, điều khiển servo SG90 để mở hay khóa cửa và gửi trạng thái lại cho backend.

Đây là phần nối trực tiếp giữa phần mềm nhận diện và phần cứng cửa vật lý.

### 2.4 Tầng thiết bị cổng cửa

- Module nằm trong [src/ESP32_SG90andLCD_control](src/ESP32_SG90andLCD_control)
- Thành phần cứng chính:
  - ESP32
  - Servo SG90
  - Màn hình LCD I2C 16x2
- Chức năng:
  - kết nối Wi‑Fi
  - kết nối MQTT
  - nhận lệnh `open` / `lock`
  - điều khiển servo ở góc 0° hoặc 180°
  - hiển thị trạng thái cửa
  - tự khóa sau thời gian quy định nếu cửa đang ở trạng thái mở

File chính:

- [src/ESP32_SG90andLCD_control/src/main.cpp](src/ESP32_SG90andLCD_control/src/main.cpp)
- [src/ESP32_SG90andLCD_control/README.md](src/ESP32_SG90andLCD_control/README.md)

---

## 3. Luồng hoạt động chính của hệ thống

### 3.1 Luồng nhận diện và mở cửa

```text
Camera → Face detection → Feature embedding → Match against face_db
                           │
                           ▼
                 Access decision (allowed/denied)
                           │
                           ▼
                 Backend publishes MQTT command
                           │
                           ▼
                 MQTT broker
                           │
                           ▼
                 ESP32 receives command
                           │
                           ▼
                 Servo rotates → door unlocks
                           │
                           ▼
                 State published back to broker
                           │
                           ▼
                 Dashboard updates status
```

### 3.2 Luồng người dùng từ web

```text
Admin/User login → web UI → session validation
                     │
                     ▼
           Request open or lock the door
                     │
                     ▼
         Flask backend validates role + CSRF
                     │
                     ▼
            MQTT gateway sends `command`
                     │
                     ▼
                ESP32 executes physical action
```

### 3.3 Luồng trạng thái và phản hồi

```text
ESP32 → publish state JSON → broker → backend → dashboard
```

Các trạng thái cửa có thể bao gồm:

- `unknown`
- `closed`
- `opening`
- `open`
- `closing`
- `error`

Theo thực tế hiện tại, trạng thái này được quản lý trên thiết bị và báo lên backend để hiển thị trên dashboard.

---

## 4. Mô hình module và phân trách nhiệm

| Layer | Thành phần | Vai trò chính |
|---|---|---|
| Sensing | Camera, OpenCV, InsightFace | Thu thập và xử lý khung hình, trích xuất vector khuôn mặt |
| Edge Intelligence | `face_utils.py`, `face_db.py`, `web_stream_face.py` | Nhận diện, đối chiếu embedding, quản lý camera state |
| Auth & UI | `auth.py`, Flask templates, dashboard JS | Đăng nhập, phân quyền, hiển thị trạng thái hệ thống |
| Control & Messaging | `mqtt_gateway.py`, Mosquitto broker | Gửi lệnh điều khiển, subscribe trạng thái, kết nối backend với thiết bị |
| Device Layer | ESP32 + SG90 + LCD | Thực thi lệnh mở/khóa cửa, phản hồi trạng thái tới broker |
| Storage | SQLite, `faces_db/`, `data/` | Lưu tài khoản, dữ liệu nhận dạng và các thông tin cấu hình |
| Physical Layer | Cửa, chốt cơ, servo | Tác động trực tiếp lên hệ thống vật lý |

---

## 5. Ranh giới kiến trúc hiện tại

### 5.1 Kiến trúc đã triển khai

- Xác thực người dùng bằng web login
- Giám sát camera và nhận diện khuôn mặt
- Tạo/xóa dữ liệu khuôn mặt
- Quản lý user/admin
- MQTT gateway gửi lệnh cửa
- ESP32 điều khiển servo và LCD
- Dashboard hiển thị trạng thái cửa

### 5.2 Vẫn là phần mở rộng hoặc cần bổ sung trong tương lai

- Cảm biến cửa vật lý để xác nhận cánh cửa đã đóng thật sự
- Liveness detection và chống giả mạo ảnh
- Audit log, event log bền vững
- MQTT TLS và bảo mật mạnh hơn
- OTA firmware cho ESP32
- Mạng nhiều cửa / nhiều site / cluster
- Chế độ backup offline hoặc nguy cơ mất kết nối hệ thống

---

## 6. Yêu cầu an ninh và vận hành

- Backend và gateway không được mở rộng trực tiếp trên Internet; nên chỉ sử dụng mạng LAN/VPN.
- `faces_db/` và dữ liệu biometric cần bảo vệ cẩn thận.
- Mỗi lệnh điều khiển nên có `request_id` để tránh xử lý trùng lặp.
- Cần có cơ chế timeout và auto-lock để tránh cửa ở trạng thái mở quá lâu.
- Quyền admin/user phải tách biệt rõ ràng theo vai trò.

---

## 7. Kết luận

Kiến trúc của hệ thống smart lock trong repo là một hệ thống end-to-end có ba lớp chính:

1. Layer nhận diện và điều phối nghiệp vụ trên Raspberry Pi
2. Layer truyền thông bằng MQTT giữa backend và thiết bị
3. Layer phần cứng cửa tại ESP32 với servo và màn hình LCD

Như vậy, không phải chỉ là một ứng dụng web nhận diện khuôn mặt đơn lẻ, mà là một hệ thống khóa thông minh hoàn chỉnh, với các thành phần phần cứng, phần mềm, mạng nội bộ và cơ chế điều khiển vật lý đang được tích hợp theo đúng hướng từ mục tiêu ban đầu của dự án.
