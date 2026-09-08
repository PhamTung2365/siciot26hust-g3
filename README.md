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
## 3. PHẦN 1 — Problem & Context

### 3.1. Bối cảnh

Tại các không gian làm việc chuyên trách (như phòng máy chủ, phòng thí nghiệm, kho thiết bị giá trị cao), đội ngũ chuyên viên và nhà quản lý thường xuyên phải di chuyển ra vào để thực hiện các tác vụ công tác liên tục.

Hiện tại, quá trình kiểm soát an ninh vẫn phụ thuộc vào phương thức vật lý như thẻ từ hoặc chìa khóa cơ. Điều này tạo ra một rào cản đáng kể: nhân sự luôn phải rảnh tay để quẹt thẻ hoặc vặn tay nắm cửa. Trong những tình huống đang mang vác máy móc nặng, thiết bị nhạy cảm hoặc xử lý sự cố khẩn cấp, phương thức cũ bộc lộ sự bất tiện lớn, làm gián đoạn luồng công việc. Hơn thế nữa, thẻ từ thiếu đi cơ chế trong việc định danh sinh trắc học độc bản; chúng dễ dàng bị sao chép hoặc mượn tạm, tạo ra nguy cơ người ngoài lọt vào đánh cắp tài sản mà hệ thống quản lý không thể truy vết chính xác danh tính thực sự.

### 3.2. Mục tiêu ban đầu

Thể hiện một trong việc chuyển đổi số không gian làm việc, mục tiêu của dự án là xây dựng một hệ thống khóa cửa thông minh có khả năng chủ động nhận diện người dùng. Hệ thống hướng tới việc xóa bỏ hoàn toàn rào cản chạm vật lý trong khâu xác thực, mang lại trải nghiệm ra vào liền mạch để nhân sự tập trung tối đa vào chuyên môn. Đồng thời, giải pháp này phải thiết lập một phòng tuyến an ninh vững chắc, tự động hóa quá trình đóng/mở chốt khóa và ngăn chặn tuyệt đối mọi hành vi xâm nhập trái phép để bảo vệ tài sản.

### 3.3. Yêu cầu cần đạt

* **Yêu cầu 1 (Tối ưu hóa luồng công tác & Xác thực không chạm):**

- **User:** Nhân sự kỹ thuật, chuyên viên vận hành.

- **Problem:** Phải ngắt quãng công việc, tìm kiếm thẻ từ và thao tác mở khóa thủ công.

- **Context:** Khi đang thực hiện các chuỗi tác vụ chuyên môn đòi hỏi sự tập trung cao độ hoặc đang dùng cả hai tay để bưng bê thiết bị, máy móc.

- **Consequence:** Làm giảm hiệu suất làm việc, gây mệt mỏi và tiềm ẩn rủi ro rơi vỡ thiết bị trong quá trình xoay sở mở cửa.

*Giải pháp đề xuất:* Khai thác sức mạnh của công nghệ InsightFace, hệ thống tự động nhận diện khuôn mặt người dùng ngay khi họ tiến lại gần. Thuật toán nhanh chóng xác thực và truyền tín hiệu điều khiển servo quay 180° để mở khóa. Điều giúp người dùng chỉ việc đẩy nhẹ cửa bước vào mà không cần thay đổi tư thế tay.


* Yêu cầu 2 (Kiểm soát an ninh tuyệt đối & Ngăn chặn lấy cắp):

- **User:** Nhà quản lý an ninh, ban giám đốc.

- **Problem:** Không thể xác minh danh tính thực sự của người vừa mở cửa, dẫn đến lỗ hổng an ninh do mượn thẻ hoặc dùng thẻ giả mạo.

- **Context:** Môi trường lưu trữ thiết bị đắt tiền, dữ liệu bảo mật cần ngăn chặn tuyệt đối người lạ mặt hoặc nhân sự không có thẩm quyền.

- **Consequence:** Rủi ro mất cắp tài sản hiện hữu mà không có cơ sở dữ liệu chính xác để truy cứu trách nhiệm.

*Giải pháp đề xuất:* Ứng dụng mô hình ArcFace để trích xuất khuôn mặt thành vector 512 chiều độc bản. Mọi nỗ lực truy cập đều phải trải qua quá trình tính toán khoảng cách Cosine; nếu độ tin cậy không đạt ngưỡng yêu cầu (dưới 70%), hệ thống kiên quyết giữ nguyên trạng thái đóng và LCD hiển thị cảnh báo từ chối, tạo nên một lớp bảo vệ vững chắc cho tài sản nội bộ.



* Yêu cầu 3 (Kiểm soát trạng thái cửa vật lý & Rủi ro mở hé):

- **User:** Hệ thống quản trị vận hành.

- **Problem:** Cơ cấu chốt khóa điện tử (servo) tự động khóa lại, nhưng cánh cửa thực tế có thể vô tình bị khép hờ hoặc người dùng đi ra mà không kéo sát cửa vào khung.

- **Context:** Trong những thời điểm giao ca, hoặc khi nhân sự di chuyển ra ngoài vội vã.

- **Consequence:** Chốt khóa đã kích hoạt nhưng cánh cửa chưa đóng kín, tạo ra khe hở vật lý để kẻ gian lợi dụng lẻn vào.

*Giải pháp đề xuất:* Hệ thống được lập trình với một chu kỳ bảo vệ: sau 3 giây từ khi servo mở (180°), chốt khóa sẽ tự động quay về vị trí khóa (0°). Để giải quyết rủi ro cửa mở hé, hệ thống khóa tự động này cần được lắp đặt kết hợp cùng cơ cấu tay co thủy lực cơ học (tự động kéo khép cánh cửa vật lý) hoặc cảm biến từ, đảm bảo thao tác tự khóa của servo luôn đồng bộ với trạng thái đóng kín hoàn toàn của cánh cửa.



* **Yêu cầu 4 (Sự bền bỉ & Phương án dự phòng khẩn cấp):**

- **User:** Toàn bộ nhân sự trong không gian làm việc.

- **Problem:** Kẹt tại khu vực cửa do hệ thống mạng nội bộ gián đoạn hoặc phần mềm gặp sự cố đột xuất.

- **Context:** Trong các tình huống cần di chuyển khẩn cấp hoặc hệ thống WiFi tại cơ sở bị mất kết nối.

- **Consequence:** Gây cản trở công việc, tạo tâm lý hoang mang và mất an toàn cho nhân sự.

*Giải pháp đề xuất:* Hệ thống duy trì năng lực nhận diện hoàn toàn cục bộ (offline) trên Raspberry Pi. Đặc biệt, trang bị nút bấm cơ học tại chân GPIO23 mở khóa lập tức (override) mà không cần thông qua AI, đảm bảo lối ra vào luôn thông suốt và an toàn trong mọi kịch bản.

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
