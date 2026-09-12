# 1. Alternative Ideas

## Phương án A
- Mô tả: Xác thực không chạm tại cửa dựa trên đặc điểm sinh trắc học của người đã được cấp quyền. Người dùng tiếp cận cửa, hệ thống kiểm tra danh tính và chỉ cho phép mở khi phù hợp; nhân sự quản trị có thể đăng ký, cập nhật hoặc thu hồi quyền.
- Giá trị: Giảm thao tác bằng tay khi đang mang thiết bị, gắn quyền truy cập với người thực tế thay vì một vật có thể bị mượn, đồng thời tạo cơ sở để ghi nhận sự kiện ra vào rõ ràng hơn.
- Ưu điểm: Phù hợp trực tiếp với nhu cầu rảnh tay và truy vết danh tính; có thể vận hành cục bộ khi mạng không ổn định; mở rộng được quy trình quản trị người dùng.
- Nhược điểm: Cần xử lý các trường hợp ánh sáng, góc nhìn hoặc khuôn mặt không được nhận diện; dữ liệu sinh trắc học cần được bảo vệ; vẫn phải có phương án dự phòng khi hệ thống hoặc thiết bị gặp lỗi.

## Phương án B
- Mô tả: Cải tiến phương thức hiện tại bằng thẻ hoặc mã số cá nhân, kết hợp bảng điều khiển để cấp, thu hồi và theo dõi quyền truy cập. Có thể bổ sung cơ chế cấp quyền tạm thời cho khách hoặc đối tác.
- Giá trị: Giảm sự phụ thuộc vào log giấy và giúp quản lý quyền tập trung hơn, trong khi người dùng vẫn sử dụng một quy trình quen thuộc.
- Ưu điểm: Dễ giải thích và triển khai; chi phí phần cứng ban đầu có thể thấp; thuận tiện khi cần cấp quyền tạm thời hoặc thay đổi quyền nhanh.
- Nhược điểm: Chưa giải quyết triệt để việc người dùng phải dùng tay khi đang mang hàng; thẻ hoặc mã số vẫn có thể bị chia sẻ, mất hoặc lộ; khả năng xác định người thực tế truy cập còn hạn chế.

## Phương án C
- Mô tả: Mô hình hybrid nhiều lớp: xác thực tự động là luồng chính, còn nút hỗ trợ tại chỗ hoặc nhân viên trực ban xử lý ngoại lệ, khách chưa đăng ký và tình huống khẩn cấp. Mọi lần hỗ trợ hoặc từ chối đều được ghi nhận.
- Giá trị: Cân bằng giữa trải nghiệm ra vào nhanh, khả năng truy vết và tính liên tục của vận hành; người dùng không bị mắc kẹt chỉ vì một phương thức xác thực thất bại.
- Ưu điểm: Có đường lui rõ ràng cho lỗi thiết bị, người dùng mới và sự cố; phù hợp với khu vực cần kiểm soát chặt; có thể kết hợp nhiều phương thức mà không bắt buộc tất cả người dùng dùng cùng một cách.
- Nhược điểm: Quy trình và phân quyền phức tạp hơn; cần đào tạo người trực ban; nếu thiết kế không tốt, bước hỗ trợ thủ công có thể trở thành điểm yếu hoặc làm giảm lợi ích rảnh tay.

## So sánh sơ bộ

| Tiêu chí | Phương án A | Phương án B | Phương án C |
|---|---|---|---|
| Giải quyết nhu cầu rảnh tay | Cao | Thấp | Cao |
| Xác định người thực tế truy cập | Cao | Thấp đến trung bình | Cao |
| Khả năng xử lý ngoại lệ | Trung bình | Trung bình | Cao |
| Độ đơn giản khi vận hành | Trung bình | Cao | Thấp đến trung bình |
| Rủi ro cần kiểm chứng | Độ chính xác, quyền riêng tư, giả mạo | Mất/chia sẻ thẻ hoặc mã | Phức tạp quy trình và quyền hỗ trợ |

> Đây là so sánh định tính để chuẩn bị cho decision matrix; chưa phải kết luận chọn phương án. Các giả định về tốc độ, độ chính xác, mức chấp nhận của người dùng và chi phí cần được kiểm thử trước khi Scope Freeze.
