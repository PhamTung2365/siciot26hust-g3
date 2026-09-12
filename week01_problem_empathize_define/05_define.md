# 5. Define

## Problem Statement
Mẫu: **[User] cần [Need] vì [Insight].**

**Nhân sự hậu cần và vận hành tại các khu vực bảo mật cần đi qua điểm kiểm soát một cách liền mạch khi đang mang thiết bị bằng cả hai tay, đồng thời vẫn cần được xác minh đúng quyền truy cập, vì thao tác với thẻ/chìa khóa hiện tại làm gián đoạn công việc còn cách ghi nhận thủ công không cung cấp định danh và lịch sử truy cập đủ tin cậy.**

> Trạng thái bằng chứng: `Assumed / Hypothesis to validate`. Persona, pain point và insight hiện được xây dựng từ quan sát bối cảnh và secondary research; chưa có interview hoặc contextual inquiry với người dùng thật.

## POV
- User: Nhân sự hậu cần, kỹ thuật và vận hành thường xuyên di chuyển thiết bị qua khu vực có kiểm soát; người quản lý an ninh là người chịu trách nhiệm theo dõi và xử lý truy cập.
- Need: Một trải nghiệm ra vào nhanh, dễ hiểu và ít làm gián đoạn công việc, đồng thời cung cấp thông tin đủ rõ để người có trách nhiệm xác nhận và truy vết quyền truy cập.
- Insight: Khi hai tay đang bận, người dùng phải dừng lại để xử lý phương tiện mở cửa; khi có sự cố, việc dựa vào thẻ, quan sát hoặc log thủ công khiến tổ chức khó biết chính xác ai đã truy cập và phản hồi kịp thời.

## HMW
1. How might we giúp người dùng đi qua điểm kiểm soát mà không phải làm gián đoạn việc mang, vận chuyển hoặc xử lý thiết bị?
2. How might we giúp người quản lý xác nhận quyền truy cập và truy vết sự kiện một cách rõ ràng, đáng tin cậy và không phụ thuộc quá nhiều vào ghi chép thủ công?
3. How might we thiết kế một quy trình ra vào vẫn dễ hiểu và an toàn khi người dùng quên phương tiện xác thực, hệ thống gặp sự cố hoặc tình huống cần phản hồi khẩn cấp?

## Kiểm tra
- [x] Không chứa sẵn giải pháp kỹ thuật. Nội dung mô tả hành vi, nhu cầu và kết quả mong muốn; chưa chọn camera, AI, RFID, servo hay nền tảng cụ thể.
- [x] Không chứa metric kỹ thuật quá sớm. Các chỉ số về độ trễ, độ chính xác và tỷ lệ hoàn thành sẽ được xác định sau khi chọn concept và thiết kế kế hoạch test.
- [x] Đủ mở để sinh ít nhất 3 phương án. Có thể khám phá các hướng xác thực không chạm, hỗ trợ vận hành, cải tiến quy trình hoặc kết hợp nhiều phương án trước khi quyết định kiến trúc.

## Giả định cần kiểm chứng

- Người dùng thực sự phải đặt thiết bị xuống hoặc mất thêm thời gian đáng kể khi mở cửa bằng thẻ/chìa khóa.
- Việc truy vết danh tính và sự kiện ra vào là nhu cầu ưu tiên của người quản lý, không chỉ là yêu cầu của nhóm phát triển.
- Người dùng chấp nhận một quy trình xác thực mới nếu phản hồi rõ ràng, không làm chậm công việc và vẫn có cách xử lý khi xảy ra sự cố.
