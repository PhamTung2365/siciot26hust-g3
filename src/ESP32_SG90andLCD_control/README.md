# ESP32 SG90 + LCD Control

## 1. Vai trò của module trong hệ thống khóa thông minh

Module này là một node thiết bị đầu cuối IoT nằm ở phía cánh cửa, có trách nhiệm trực tiếp điều khiển cơ cấu khóa và phản hồi trạng thái về hệ thống trung tâm. Trong kiến trúc của dự án, module ESP32 đóng vai trò là "đầu điều khiển cửa" giữa Raspberry Pi và cơ cấu vật lý:

- Nhận lệnh điều khiển từ backend hoặc server trung tâm qua giao thức MQTT.
- Điều khiển servo SG90 để mở hoặc khóa cửa.
- Theo dõi và báo trạng thái cửa lên broker MQTT để dashboard hoặc hệ thống backend cập nhật giao diện.
- Hiển thị trạng thái cửa lên màn hình LCD 16x2 để người dùng quan sát trực tiếp tại chỗ.

Về mặt chức năng, module này không thực hiện nhận diện khuôn mặt hay xác thực người dùng. Nó chỉ làm nhiệm vụ thực thi lệnh từ hệ thống, đảm bảo cánh cửa được mở/khóa đúng theo tín hiệu và phản hồi nhanh chóng, an toàn, ổn định.

---

## 2. Cấu trúc và thành phần phần cứng

Module này bao gồm các thành phần chính sau:

- ESP32 DevKit: board điều khiển trung tâm, có Wi-Fi và xử lý MQTT.
- Servo SG90: cơ cấu chốt cửa, dùng để quay từ vị trí khóa sang vị trí mở.
- Màn hình LCD I2C 16x2: hiển thị trạng thái cửa như "OPEN", "CLOSED" hoặc thông báo kết nối.
- Cáp nối và điện nguồn: cung cấp nguồn cho ESP32 và servo.

Cấu hình chân phần cứng trong code:

- Servo: GPIO 18
- I2C LCD: SDA = GPIO 21, SCL = GPIO 22
- Địa chỉ LCD: 0x27

---

## 3. Chức năng chính của module

### 3.1. Kết nối Wi‑Fi
Module khởi tạo kết nối tới mạng LAN nội bộ bằng SSID và mật khẩu đã cấu hình sẵn. Khi đã kết nối, ESP32 có thể hoạt động như một thiết bị IoT có thể truy cập vào broker MQTT của hệ thống.

### 3.2. Kết nối MQTT
ESP32 kết nối tới Raspberry Pi hoặc broker Mosquitto qua địa chỉ MQTT.

Các topic chính:

- Nguồn lệnh: `smartlock/front-door/command`
- Nguồn trạng thái: `smartlock/front-door/state`

ESP32 chủ động subscribe vào topic lệnh và publish trạng thái cửa ra topic trạng thái.

### 3.3. Nhận lệnh điều khiển cửa
Khi có payload JSON trên topic lệnh, ESP32 sẽ parse dữ liệu. Một lệnh hợp lệ phải chứa:

- `action`: `open` hoặc `lock`
- `request_id`: định danh yêu cầu để tránh xử lý trùng lặp

Ví dụ payload:

```json
{
  "action": "open",
  "request_id": "abc123",
  "open_seconds": 5
}
```

Lệnh `open` sẽ làm servo quay về góc mở; lệnh `lock` sẽ quay servo về góc khóa.

### 3.4. Chống lặp lệnh và xử lý trùng
Hệ thống có biến `last_request_id` để ngăn lặp lại cùng một yêu cầu. Nếu `request_id` trùng, ESP32 bỏ qua để tránh mở hoặc khóa lặp lại do mất gói MQTT hoặc điều kiện mạng.

### 3.5. Tự động khóa sau thời gian mở
Khi cửa mở, hệ thống đặt bộ hẹn giờ `auto_lock_at` theo thời gian `open_seconds`. Sau khi hết thời gian, servo sẽ tự động quay về vị trí khóa. Đây là cơ chế rất quan trọng để đảm bảo cửa không ở trạng thái mở quá lâu và giảm rủi ro cửa bị để hở.

### 3.6. Công bố trạng thái lên broker
Sau mỗi thay đổi trạng thái, ESP32 sẽ publish JSON chứa:

```json
{
  "status": "open",
  "online": true
}
```

hoặc

```json
{
  "status": "closed",
  "online": true
}
```

Thông tin này giúp backend hoặc dashboard biết trạng thái thực tế của cửa ngay thời điểm đó.

### 3.7. Hiển thị trạng thái lên LCD
LCD 16x2 hiển thị các trạng thái sau:

- "Door Status: OPEN"
- "Door Status: CLOSED"
- "Connecting WiFi"
- "WiFi Connected"
- "MQTT Server: Connecting..."

Nhờ vậy, người dùng có thể quan sát trực tiếp trạng thái hoạt động của thiết bị ngay tại cửa mà không cần truy cập vào dashboard.

---

## 4. Nguyên lý hoạt động của hệ thống

### 4.1. Khởi động thiết bị
Khi `setup()` được gọi:

1. Khởi tạo Serial Monitor để debug.
2. Khởi tạo bus I2C cho LCD (`Wire.begin(21, 22)`).
3. Khởi động LCD và hiển thị logo/chuỗi thông báo ban đầu.
4. Cấu hình servo SG90 với tần số 50Hz.
5. Gắn servo vào chân GPIO 18 và đặt servo ở vị trí khóa.
6. Kết nối Wi‑Fi.
7. Gắn callback MQTT và cấu hình broker.

### 4.2. Xử lý lệnh MQTT
Trong `mqtt_callback()`, nếu topic bằng `smartlock/front-door/command`, code gọi `handle_command(payload, length)`. Hàm này:

- Parse JSON từ payload.
- Kiểm tra `action` phải là `open` hoặc `lock`.
- Kiểm tra `request_id` tồn tại và khác với yêu cầu vừa xử lý.
- Nếu là `open`, đặt servo ở góc `180°`, ghi nhận `door_open = true`, thiết lập `auto_lock_at` theo thời gian mở.
- Nếu là `lock`, đặt servo ở góc `0°`, hủy bộ hẹn giờ và báo trạng thái `closed`.

### 4.3. Máy trạng thái cửa
ESP32 duy trì biến `door_open` để biết trạng thái hiện tại. Giá trị trở về `true` khi cửa mở, và `false` khi cửa đóng.

Các góc servo:

- `locked_angle = 0`
- `open_angle = 180`

### 4.4. Vòng lặp chính (`loop`)
Trong `loop()`:

- Nếu mất kết nối broker, gọi `reconnect_mqtt()` để khôi phục kết nối.
- Gọi `mqtt_client.loop()` để duy trì giao tiếp MQTT.
- Nếu `door_open == true` và thời gian `auto_lock_at` đã hết, servo quay về trạng thái khóa và publish `closed`.

Đây là cơ chế điều khiển tự động, giúp cửa không bị mở quá lâu sau khi lệnh mở được gửi.

---

## 5. Luồng hoạt động mẫu

### Mô hình 1: Mở cửa từ xa
1. Backend phân tích quyền và xác thực người dùng.
2. Backend gửi lệnh MQTT tới topic `smartlock/front-door/command`.
3. ESP32 nhận lệnh `open`.
4. Servo quay đến góc 180°.
5. ESP32 publish trạng thái `open` lên topic `state`.
6. After time, servo tự động quay về góc 0° và publish `closed`.

### Mô hình 2: Khóa cửa thủ công hoặc tự động
1. Backend gửi lệnh `lock` hoặc timer tự động hết hạn.
2. Servo quay về `locked_angle`.
3. ESP32 publish trạng thái `closed`.
4. LCD hiển thị trạng thái cửa mới.

---

## 6. Đặc điểm kỹ thuật quan trọng

- Sử dụng MQTT QoS 1 cho việc gửi/nhận lệnh và trạng thái.
- Payload trạng thái có `retain`, nghĩa là trạng thái cuối cùng được giữ lại trên broker.
- Khi ESP32 mất kết nối MQTT, nó sẽ tự reconnect và gửi trạng thái lại nếu cần.
- `Last Will` được thiết lập với `online=false` để cảnh báo thiết bị mất kết nối.
- Hệ thống ưu tiên tính đơn giản, ổn định và giao tiếp theo mô hình publish/subscribe thay vì truyền trực tiếp qua API REST nội bộ.

---

## 7. Các tham số cần cập nhật khi triển khai thực tế

Trong file `main.cpp`, các tham số quan trọng cần điều chỉnh theo môi trường chạy thật:

- SSID Wi‑Fi của mạng nội bộ
- Mật khẩu Wi‑Fi
- Địa chỉ IP của broker MQTT (`mqtt_server`)
- Port MQTT (`mqtt_port`)
- Tên user và mật khẩu MQTT
- `state_topic` và `command_topic` nếu muốn tùy biến theo từng cửa

Đây là thông tin cần được cập nhật để module hoạt động đúng trên mạng triển khai của nhóm.

