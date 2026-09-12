# 3. MVP Scope

## MUST HAVE
- [x] Nhận diện khuôn mặt cục bộ từ camera, so khớp với người đã đăng ký và trả về trạng thái nhận diện rõ ràng; khi không đạt ngưỡng thì giữ trạng thái từ chối. Đây là luồng cốt lõi của phương án A và đã có trong `face_utils.py`, `face_db.py` và `web_stream_face.py`.
- [x] Quy trình quản trị người dùng và dữ liệu khuôn mặt: admin đăng nhập, enroll nhiều embedding, xem/xóa người đã đăng ký; phân quyền admin/user và CSRF phải được giữ cho các thao tác thay đổi dữ liệu.
- [x] Dashboard/trạng thái tối thiểu để xem video, kết quả nhận diện, confidence, số người/embedding và tình trạng camera/model; hệ thống vẫn phải khởi động để chẩn đoán khi không có camera.

## SHOULD HAVE
- [ ] Tích hợp actuator khóa cửa và chu trình mở/khóa an toàn sau khi nhận diện thành công; cần kiểm thử riêng vì servo và giao thức điều khiển vật lý chưa có trong code hiện tại.
- [ ] Ghi nhận access event có thời gian, danh tính/kết quả từ chối và nguồn kích hoạt để hỗ trợ truy vết; hiện database mới lưu embedding và tài khoản, chưa phải access log.

## NICE TO HAVE
- [ ] Cơ chế fallback/override tại chỗ cho camera, model, nguồn điện hoặc người dùng chưa đăng ký; ưu tiên không làm người dùng bị mắc kẹt trong tình huống khẩn cấp.
- [ ] LCD hoặc giao diện tại cửa hiển thị thông báo dễ hiểu, cùng cảm biến trạng thái cửa để phát hiện cửa chưa khép kín.

## Out of Scope
- Xác thực hai yếu tố, liveness detection và các cơ chế chống giả mạo nâng cao.
- Ứng dụng mobile điều khiển từ xa hoặc yêu cầu internet luôn hoạt động.
- Triển khai production có HTTPS, mã hóa phức tạp, HA/monitoring doanh nghiệp hoặc mở hệ thống trực tiếp ra Internet.
- Camera hồng ngoại và các nâng cấp phần cứng chưa có BOM, wiring hoặc giao thức kiểm thử cụ thể.

## Ranh giới MVP

- MVP của milestone này là prototype phần mềm kiểm chứng nhận diện và quản trị truy cập; không được mô tả như một khóa cửa vật lý production.
- Các mục SHOULD HAVE/NICE TO HAVE chỉ được chuyển thành yêu cầu bắt buộc sau khi có thiết kế phần cứng, tiêu chí an toàn và kết quả kiểm thử tương ứng.
- Embedding và ảnh capture/debug là dữ liệu nhạy cảm; chỉ lưu cục bộ trong phạm vi prototype, giới hạn quyền truy cập và không đưa `.env`, database runtime hoặc dữ liệu khuôn mặt vào Git/image.

## Scope Freeze
Ngày: 2026-09-12
Người xác nhận: Nhóm 3 (đề xuất, chờ xác nhận chính thức)
