# 4. Pain Points & Insights

## Pain Points
1. **Phải dừng lại và dùng tay để mở cửa khi đang mang thiết bị cồng kềnh.** Người dùng phải đặt hàng xuống, tìm thẻ hoặc chìa khóa, thao tác mở cửa rồi mới tiếp tục di chuyển. Điều này làm gián đoạn công việc và có thể gây rơi, hỏng thiết bị.
2. **Thẻ từ hoặc chìa khóa có thể bị quên, mất, hỏng hoặc bị người khác mượn.** Cách xác thực hiện tại chứng minh quyền sở hữu của vật dụng hơn là danh tính thực sự của người đang mở cửa, nên tạo ra rủi ro truy cập trái phép.
3. **Khó truy vết chính xác ai đã ra vào.** Việc đối chiếu bằng mắt thường hoặc ghi chép thủ công không tạo ra thông tin định danh nhất quán, khiến người quản lý khó điều tra khi xảy ra mất mát hoặc sự cố.
4. **Quy trình hỗ trợ khi có sự cố còn phụ thuộc vào con người.** Khi quên thẻ, mất kết nối hoặc cần vào/ra khẩn cấp, nhân viên có thể phải gọi bảo vệ, chờ người có chìa khóa hoặc rời vị trí để xử lý, làm tăng thời gian phản hồi.
5. **Quản trị người dùng và quyền truy cập dễ trở nên nặng nề khi số người thay đổi.** Việc cấp, thu hồi, thay thế thẻ và cập nhật danh sách thủ công tạo ra chi phí lặp lại; đồng thời người trực ban cần một cách xem trạng thái rõ ràng, ít thao tác kỹ thuật.

## Evidence Mapping
| Pain Point | Evidence | Mức độ |
|---|---|---|
| 1. Thao tác mở cửa làm gián đoạn việc mang vác | Persona 1 mô tả phải đặt vật nặng xuống để tìm và quẹt thẻ | High |
| 2. Vật dụng xác thực có thể bị mất, mượn hoặc sao chép |**Secondary research**| High |
| 3. Thiếu truy vết định danh đáng tin cậy | Persona 2 cần thông tin lưu trữ minh bạch | High |


## Insights
### Insight 1
- Observation: Khi hai tay đang bận mang máy móc hoặc vật tư, người dùng phải ngắt công việc để tìm và thao tác với phương tiện mở cửa. Đây là quan sát/giả định được suy ra từ Persona 1 và cần được kiểm chứng bằng quan sát thực địa hoặc phỏng vấn.
- Why it matters: Điểm ngắt này làm chậm luồng vận chuyển, tăng nguy cơ làm rơi thiết bị và khiến người dùng phải lựa chọn giữa an toàn tài sản đang mang và việc mở cửa.
- User need: Một cách đi qua điểm kiểm soát nhanh, dễ hiểu và không buộc người dùng phải đặt hàng xuống hoặc thực hiện nhiều thao tác tay.

### Insight 2
- Observation: Người quản lý hiện phải dựa vào quan sát, danh sách giấy hoặc log thủ công để biết ai đã vào; trong khi thẻ hoặc chìa khóa có thể được dùng bởi người không phải chủ sở hữu. Đây là hypothesis vì bảng User Research chưa có người tham gia cụ thể.
- Why it matters: Khi xảy ra sự cố, dữ liệu không đủ tin cậy để phân biệt người được cấp quyền với người đang thực sự sử dụng phương tiện truy cập, làm tăng rủi ro an ninh và thời gian điều tra.
- User need: Một thông tin truy cập nhất quán, dễ xem và có thể liên kết với danh tính người dùng, kèm phản hồi rõ ràng khi truy cập được chấp nhận hoặc bị từ chối.

## Giả định và giới hạn bằng chứng

- Chưa có interview, questionnaire hoặc contextual inquiry; vì vậy các pain point về tần suất, thời gian chờ và mức độ thiệt hại chưa được định lượng.
- Các tên, tuổi, hành vi trong persona là dữ liệu giả định dùng để định hướng thiết kế, không phải dữ liệu người dùng thật.
- Prototype hiện có các luồng nhận diện khuôn mặt, enroll, quản trị tài khoản và trạng thái camera; chưa triển khai servo, LCD, nút override hoặc log ra/vào vật lý. Những thành phần đó được xem là nhu cầu/định hướng cần kiểm chứng ở các tuần sau, không phải bằng chứng đã triển khai.

## Câu hỏi cần kiểm chứng tiếp

1. Người dùng thường phải đặt vật xuống hoặc chờ bao lâu để mở cửa trong một lượt vận chuyển?
2. Tình huống quên, mất hoặc cho mượn thẻ xảy ra với tần suất và hậu quả như thế nào?
3. Khi có sự cố, ai là người xử lý, mất bao lâu và thông tin nào cần được ghi lại để điều tra?
4. Người trực ban cần xem những trường dữ liệu nào để xác nhận một lượt truy cập mà không phải đọc log thủ công?
