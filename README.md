# Smart Lock Face Recognition

## 1. Thông tin nhóm
Tên nhóm: Nhóm 3
Thành viên:
- Mạc Thanh Bình
- Phạm Tiến Đạt
- Phạm Mạc Thanh Tùng
- Lê Quang Hiếu

## 2. Giới thiệu

Ứng dụng thử nghiệm nhận diện khuôn mặt bằng InsightFace, OpenCV và Flask. Hệ
thống stream camera qua MJPEG, đăng ký nhiều embedding cho mỗi người và lưu dữ
liệu cục bộ trong `faces_db/`.

> Đây là prototype, chưa phải khóa cửa production: chưa có HTTPS hay chống giả
> mạo (liveness detection). Không mở trực tiếp ra Internet.

## 3. Problem & Context
### 3.1. Bối cảnh
Tại các phòng làm việc chuyên trách (như phòng máy chủ, phòng thí nghiệm hoặc kho thiết bị), nhân viên kỹ thuật và người quản lý thường xuyên phải ra vào liên tục trong giờ làm việc. Hiện tại, quá trình kiểm soát cửa ra vào ở những khu vực trên chủ yếu vẫn dựa vào chìa khóa cơ truyền thống hoặc thẻ từ nhận diện.

Việc duy trì phương pháp cũ này bộc lộ nhiều điểm bất tiện và rủi ro:

 • Bất tiện trong việc vận hành: Nhân viên thường xuyên gặp khó khăn trong việc quẹt thẻ hoặc tra chìa khóa vào ổ khi hai tay đang phải bưng bê thiết bị, máy móc hoặc tài liệu nặng.

 • Rủi ro gián đoạn công việc: Việc nhân viên để quên, làm rơi hoặc thất lạc thẻ/chìa khóa xảy ra thường xuyên, khiến họ không thể tiếp cận không gian làm việc ngay lập tức.

 • Lỗ hổng an ninh: Chìa khóa cơ và thẻ từ có thể dễ dàng bị sao chép, đánh cắp hoặc cho mượn trái phép. Người quản lý không thể xác định chính xác danh tính thực sự của người vừa mở cửa nếu chỉ dựa vào dữ liệu quẹt thẻ.

### 3.2. Mục tiêu ban đầu
Tạo ra một hệ thống khóa cửa thông minh, hoàn toàn tự động nhận diện chính xác danh tính người dùng ngay tại chỗ để tự động đóng hoặc  mở cửa mà không cần bất kỳ thao tác chạm vật lý nào. Hệ thống phải mang lại trải nghiệm ra vào liền mạch, có màn hình phản hồi thông tin trực quan cho người dùng. Đồng thời, hệ thống cung cấp cho người quản trị khả năng chủ động cấp quyền truy cập cho nhân viên mới và đảm bảo luôn có phương án dự phòng mở cửa khẩn cấp một cách linh hoạt, an toàn.

### 3.3. Yêu cầu cần đạt
Dựa trên sự phân tích giữa bài toán thực tế và nhu cầu sử dụng, hệ thống cần đáp ứng các yêu cầu sau:

 • Yêu cầu 1 (Khắc phục trở ngại vật lý): Người dùng cần ra vào không gian làm việc liên tục nhưng không rảnh tay để tìm và sử dụng chìa khóa/thẻ từ (Problem) trong lúc đang phải bưng bê thiết bị nặng (Context), dẫn đến nguy cơ rơi vỡ đồ đạc hoặc mất thời gian thao tác (Consequence).
 → Hệ thống cần có khả năng tự động nhận diện khuôn mặt và điều khiển cơ cấu cơ học để tự động mở khóa, giúp giải phóng hoàn toàn đôi tay của người dùng.

 • Yêu cầu 2 (Cải thiện giao tiếp người - máy): Người dùng không biết thiết bị có đang hoạt động hay đã nhận ra mình hay chưa (Problem) khi đứng chờ trước cửa phòng (Context), dẫn đến tâm lý bối rối hoặc rủi ro cố sức đẩy cửa làm hỏng khóa khi chốt chưa kịp mở (Consequence).
 → Hệ thống cần được trang bị màn hình hiển thị trực tiếp (LCD) để phản hồi trạng thái theo thời gian thực (ví dụ: chào tên người dùng, thông báo từ chối, hoặc báo cửa đang mở).

 • Yêu cầu 3 (Đảm bảo tính sẵn sàng & Xử lý sự cố): Người dùng cần vào phòng gấp nhưng hệ thống AI mất mạng internet hoặc gặp lỗi phần mềm (Problem) trong các tình huống khẩn cấp (Context), gây ra việc bị nhốt bên ngoài, làm đình trệ công việc và gây nguy hiểm (Consequence).
 → Hệ thống bắt buộc phải có khả năng xử lý nhận diện hoàn toàn cục bộ (offline) và phải tích hợp một nút bấm vật lý (override) để mở khóa khẩn cấp bỏ qua quá trình nhận diện.

 • Yêu cầu 4 (Kiểm soát an ninh cá nhân hóa): Người quản lý không thể kiểm soát được ai là người thực sự đã mở cửa phòng (Problem) khi nhân viên sử dụng thẻ từ dùng chung hoặc cho nhau mượn thẻ (Context), dẫn đến không thể truy cứu trách nhiệm nếu xảy ra mất mát tài sản (Consequence).
 → Do đó, hệ thống cần hỗ trợ tính năng đăng ký khuôn mặt cá nhân hóa (enroll) để liên kết chính xác sinh trắc học với định danh từng người, đồng thời lưu lại lịch sử truy cập cơ bản (log).

## 4. Cài đặt và chạy

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

## 5. Tài khoản và quyền

- `admin`: quản lý khuôn mặt, chụp ảnh, tạo/list tài khoản user và đổi mật khẩu.
- `user`: xem video/trạng thái cơ bản và đổi mật khẩu của chính mình.
- Không có đăng ký công khai. Admin tạo user tại `/admin/users`.

Toàn bộ route cần đăng nhập; thao tác thay đổi dữ liệu yêu cầu CSRF token. Không
đặt `.env` hoặc `data/users.db` vào Git hay Docker image.

## 6. Cấu hình

Các giá trị được dùng trực tiếp từ `config.py`:

- `MODEL_NAME`, `MODEL_CONTEXT`, `DETECTION_SIZE`
- `RECOGNITION_THRESHOLD`
- `CAMERA_DEVICE_ID`, độ phân giải và FPS camera
- chất lượng JPEG, chu kỳ tính FPS và hiển thị landmarks
- host, port, debug và threaded mode của Flask

`MODEL_CONTEXT=-1` dùng CPU; giá trị từ `0` trở lên yêu cầu
`CUDAExecutionProvider` tương ứng.

## 7. Sử dụng

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

## 9. API

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

## 10. Kiểm tra

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

## 11. Dữ liệu

Mỗi người có một file pickle trong `faces_db/`. Pickle chỉ nên được đọc từ
nguồn tin cậy. Ảnh chụp và ảnh debug nằm trong `captures/`; embeddings không
thể xem như dữ liệu vô danh và cần được bảo vệ/backup phù hợp.

Xem [INSTALL.md](INSTALL.md) để cài đặt chi tiết và
[STRUCTURE.md](STRUCTURE.md) để hiểu cấu trúc.
