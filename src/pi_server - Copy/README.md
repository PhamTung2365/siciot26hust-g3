# Smart Lock Backend

Backend cho MVP **một khóa cửa chính**: nhận diện khuôn mặt, xác thực web,
điều khiển mở/khóa từ xa và giao tiếp thiết bị qua MQTT. Phần firmware ESP32
không nằm trong repository này; đội thiết bị chỉ cần tuân theo contract bên dưới.

## Kiến trúc

```text
Camera ──TCP/OpenCV──> Raspberry Pi
                       ├─ InsightFace + face database
Browser ──HTTPS/VPN──> ├─ Flask + session + RBAC + CSRF
                       └─ MQTT client (webapp)
                                │
                         Mosquitto broker
                                │
                       Thiết bị khóa (đội ESP32)
```

Dữ liệu tập trung trên Raspberry Pi:

- `data/users.db`: tài khoản và role.
- `faces_db/`: embedding khuôn mặt.
- `data/mqtt/password.txt`: credential đã hash của broker.

CSDL tập trung phù hợp với một khóa vì dễ backup, không có xung đột đồng bộ và
ESP32 không phải giữ dữ liệu sinh trắc học. Chỉ cân nhắc edge database phân tán
khi có nhiều site phải chạy độc lập lúc mất WAN.

## Phân quyền và UI

| Chức năng | user | admin |
|---|:---:|:---:|
| Đăng nhập, xem camera/trạng thái | ✓ | ✓ |
| Mở khóa/khóa từ xa | ✓ | ✓ |
| Đổi mật khẩu của mình | ✓ | ✓ |
| Đăng ký/xóa khuôn mặt | — | ✓ |
| Tạo/xem tài khoản | — | ✓ |

Không có đăng ký tài khoản công khai. Mọi lệnh cửa và thay đổi dữ liệu đều cần
session hợp lệ và CSRF token. Browser không nhận MQTT credential; Flask xác thực
người dùng rồi phát lệnh bằng service account `webapp`.

## MQTT contract cho đội ESP32

Kết nối tới host/port do triển khai cung cấp, MQTT v5 hoặc 3.1.1, QoS 1.
Đăng nhập bằng service account `esp32`. `door_id` mặc định là `front-door`.

### Nhận lệnh

Topic:

```text
smartlock/{door_id}/command
```

Payload mở khóa:

```json
{
  "action": "open",
  "request_id": "0f4c...",
  "actor": "alice",
  "source": "web",
  "open_seconds": 5,
  "sent_at": 1789063200
}
```

Payload khóa chủ động:

```json
{
  "action": "lock",
  "request_id": "a79e...",
  "actor": "alice",
  "source": "web",
  "sent_at": 1789063210
}
```

`source` có thể là `web` hoặc `face`. Command dùng QoS 1, **không retain**.
Thiết bị phải chống xử lý trùng theo `request_id`, giới hạn `open_seconds`
an toàn và tự khóa sau timer. Lệnh `lock` hủy timer và khóa ngay nếu phần cứng
cho phép an toàn.

### Gửi trạng thái

Topic, QoS 1, **retain**:

```text
smartlock/{door_id}/state
```

```json
{
  "status": "closed",
  "online": true,
  "updated_at": 1789063210
}
```

`status` chỉ nhận: `unknown`, `closed`, `opening`, `open`, `closing`,
`error`. Cấu hình Last Will retained với `online=false`.

### Gửi sự kiện

Topic, QoS 1, không retain:

```text
smartlock/{door_id}/event
```

```json
{
  "type": "exit_sensor",
  "occurred_at": 1789063220
}
```

Các `type` tối thiểu: `remote_open`, `remote_lock`, `face_open`,
`exit_sensor`, `auto_lock`, `error`.

ACL trong `mqtt/acl` quy định:

- `webapp`: ghi command, đọc state/event.
- `esp32`: đọc command, ghi state/event.
- anonymous access bị tắt.

## Use case MVP

1. Khuôn mặt hợp lệ → backend publish `action=open` → thiết bị mở rồi tự khóa.
2. User/admin đăng nhập → bấm **Mở khóa** hoặc **Khóa cửa** → Flask kiểm tra
   session + CSRF → publish MQTT.
3. Admin đăng ký/xóa khuôn mặt và tạo user.
4. Thiết bị publish state → dashboard cập nhật trạng thái.
5. Cảm biến lối ra do firmware tự xử lý; backend chỉ nhận event.

MVP chưa gồm nhiều khóa/site, lịch quyền, audit log bền vững, mobile app,
liveness detection, MQTT TLS, OTA hoặc high availability.

## Chạy dự án

```bash
cd /home/nhom3/Desktop/Smart_lock/pi_server
cp env.example .env
# thay toàn bộ placeholder/secret trong .env

bash smartlock.sh setup
bash smartlock.sh mqtt-init
bash smartlock.sh start
```

Lệnh `mqtt-init` cần Docker Engine và Docker Compose plugin. Nếu máy chưa có
`docker`, hãy cài hai thành phần này trước khi chạy lệnh.

### Dùng camera laptop qua mạng

Camera laptop không truyền qua cáp USB trực tiếp vào Raspberry Pi. Hãy chạy
server trên Raspberry Pi trước, sau đó chạy file `laptop_camera_sender.py` trên
laptop. File này gửi JPEG qua TCP đến cổng `5001`, đúng giao thức mà backend
đang nhận từ ESP32-CAM.

Trên laptop, mở terminal tại thư mục `pi_server`, tạo môi trường riêng và cài
đúng dependencies của chương trình gửi camera:

```bash
python3 -m venv .venv-camera
source .venv-camera/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-laptop.txt
```

Trong VS Code, chọn đúng interpreter `.venv-camera/bin/python` bằng lệnh
`Python: Select Interpreter`. Cảnh báo `Import "cv2" could not be resolved`
thường xuất hiện khi VS Code đang chọn nhầm Python, dù OpenCV đã cài ở môi
trường khác.

Sau đó thay `192.168.1.102` bằng địa chỉ IP của Raspberry Pi:

```bash
python laptop_camera_sender.py --host 192.168.1.102
```

`--host` phải là IP hoặc hostname mà laptop phân giải được của Raspberry Pi.
Tên `pi3636` chỉ dùng được nếu laptop biết tên đó; nếu không, dùng địa chỉ IP,
ví dụ `192.168.1.50`.

Tuỳ chọn camera khác hoặc giảm chất lượng:

```bash
python3 laptop_camera_sender.py --host 192.168.1.102 --camera 1 --fps 10 --quality 70
```

Mở web tại `http://192.168.1.102:5000`. Nếu Raspberry Pi có firewall, cho phép
TCP port `5001` từ mạng LAN. Chỉ chạy một server backend trên Raspberry Pi để
tránh lỗi cổng `5000` và `5001` đã được sử dụng.

Các lệnh duy nhất:

```text
bash smartlock.sh setup       cài virtualenv/dependency
bash smartlock.sh mqtt-init   tạo password file Mosquitto
bash smartlock.sh start       chạy Flask local
bash smartlock.sh test        chạy toàn bộ test + compile
bash smartlock.sh docker      chạy backend + broker bằng Docker
```

Không forward port 5000 hoặc 1883 trực tiếp ra Internet. Dùng VPN riêng hoặc
reverse proxy HTTPS; broker chỉ nên ở LAN/VPN.

## API

| Method | Endpoint | Quyền |
|---|---|---|
| GET | `/`, `/video_feed`, `/status`, `/info` | user/admin |
| POST | `/api/door/command` với `open\|lock` | user/admin + CSRF |
| GET/POST | `/get_people`, `/enroll_web`, `/delete_person`, `/capture` | admin |
| GET/POST | `/admin/users`, `/api/admin/users` | admin |

## Cấu trúc

```text
auth.py                  account, session, RBAC và CSRF
face_db.py               embedding store và matching
face_utils.py            InsightFace inference
mqtt_gateway.py          MQTT contract, state và command
tcp_camera.py            camera TCP receiver
web_stream_face.py       Flask routes và recognition worker
templates/               HTML
static/                  neumorphism CSS và JavaScript
mqtt/                    Mosquitto config + ACL
tests/                   unit/integration tests
smartlock.sh             entrypoint duy nhất cho vận hành
```

Chạy kiểm tra:

```bash
bash smartlock.sh test
```

Embedding là dữ liệu sinh trắc học nhạy cảm: giới hạn quyền filesystem, backup
mã hóa và chỉ đọc pickle từ nguồn tin cậy.
