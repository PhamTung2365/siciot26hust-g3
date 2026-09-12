# 4. Use Cases

## UC01
- Actor: Người dùng đã được cấp quyền; hệ thống camera và mô-đun nhận diện.
- Trigger: Một người xuất hiện trước camera trong khi dashboard/video stream đang hoạt động.
- Main flow:
	1. Camera đọc frame và khóa thao tác đọc để tránh các request dùng camera đồng thời.
	2. Hệ thống phát hiện khuôn mặt, trích xuất embedding và so khớp với database cục bộ.
	3. Nếu confidence đạt `RECOGNITION_THRESHOLD`, hệ thống cập nhật tên và trạng thái `match`; nếu không đạt, trạng thái là `Unknown`/từ chối.
	4. Dashboard hiển thị kết quả, confidence, số khuôn mặt và trạng thái sẵn sàng qua video hoặc `/status`.
- Expected result: Danh tính được nhận diện hoặc bị từ chối một cách rõ ràng, không cần kết nối internet. Trong phạm vi MVP hiện tại chưa có bước điều khiển servo/mở cửa vật lý; đó là phần SHOULD HAVE cần tích hợp và kiểm thử riêng.

## UC02
- Actor: Admin quản trị hệ thống.
- Trigger: Cần thêm người mới, bổ sung góc mặt, hoặc thu hồi quyền của một người.
- Main flow:
	1. Admin đăng nhập và nhận CSRF token; user thường không được phép thực hiện thao tác quản trị.
	2. Với enroll, admin nhập tên, gửi yêu cầu `/enroll_web`, hệ thống đọc frame hiện tại và kiểm tra có khuôn mặt hợp lệ.
	3. Nếu hợp lệ, embedding được thêm vào file dữ liệu của người đó và cập nhật cache; nếu không có mặt hoặc dữ liệu không hợp lệ, hệ thống trả lỗi mà không ghi bản ghi mới.
	4. Với thu hồi, admin chọn người và gửi yêu cầu xóa; hệ thống kiểm tra tên an toàn, xóa dữ liệu tương ứng và cập nhật danh sách.
- Expected result: Danh sách người được cấp quyền phản ánh đúng thao tác của admin; mỗi người có thể có nhiều embedding, dữ liệu được ghi cục bộ và thao tác thay đổi bị giới hạn bởi role/CSRF.

## UC03
- Actor: User xem trạng thái hoặc admin/nhân sự vận hành giám sát hệ thống.
- Trigger: Người dùng mở dashboard, hoặc người vận hành cần kiểm tra camera, model, số người đã đăng ký và tình trạng nhận diện.
- Main flow:
	1. Người dùng đăng nhập; hệ thống kiểm tra session và role trước khi cho truy cập.
	2. Dashboard tải video stream, gọi `/status` định kỳ và có thể gọi `/info` để xem thông tin model, camera, threshold và thống kê.
	3. Admin có thêm quyền xem danh sách người, enroll, xóa người và capture; user chỉ xem trạng thái cơ bản và đổi mật khẩu của chính mình.
	4. Nếu không có camera hoặc camera bị ngắt, server vẫn giữ các endpoint trạng thái để chẩn đoán và đánh dấu hệ thống chưa sẵn sàng.
- Expected result: Người dùng nhìn thấy trạng thái và quyền phù hợp; admin có thể quản trị dữ liệu, user không thể thay đổi dữ liệu khuôn mặt, và lỗi camera được hiển thị/kiểm tra thay vì làm server dừng toàn bộ.

## Giới hạn use case

- Các use case này mô tả MVP prototype phần mềm hiện có. Access log, actuator servo, LCD, cảm biến cửa và nút override chưa có implementation hoặc giao thức kiểm thử trong repository.
- Việc nhận diện thành công không được hiểu là bảo đảm chống giả mạo: prototype chưa có liveness detection và không được dùng như hệ thống khóa cửa production.
