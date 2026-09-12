# 1. Problem & Context

## Bối cảnh

- **Vấn đề xảy ra ở đâu?**
    * Phòng máy chủ (Data Center) hoặc trung tâm dữ liệu lõi của doanh nghiệp.

    * Phòng thí nghiệm hóa học, y sinh hoặc công nghệ cao cần vô trùng/bảo mật.
    
    * Kho chứa thiết bị, linh kiện điện tử và tài sản cố định có giá trị cao.
    
    * Khu vực lưu trữ hồ sơ, tài liệu mật của ban giám đốc hoặc phòng nhân sự.


- **Ai gặp vấn đề?**
    * Đội ngũ chuyên viên kỹ thuật, kỹ sư bảo trì và nhân viên vận hành hệ thống.

    * Ban quản lý, giám đốc an ninh cần giám sát và truy vết luồng người ra vào.
    
    * Nhân viên kho, chuyên viên hậu cần thường xuyên phải vận chuyển hàng hóa.


- **Khi nào?**
    * Khi nhân viên đang mang vác máy móc nặng, cồng kềnh bằng cả hai tay và không thể rảnh tay thao tác mở cửa.
    
    * Khi có sự cố khẩn cấp (chập điện, lỗi server, hỏa hoạn) cần tốc độ tiếp cận hoặc sơ tán tính bằng giây.
    
    * Khi có sự luân chuyển ca trực với lưu lượng nhân sự lớn, đòi hỏi hệ thống xác thực nhanh chóng và liên tục.
    
    * Khi người có thẩm quyền bỏ quên thẻ từ, làm rơi chìa khóa cơ, hoặc thẻ bị hỏng do từ tính.


- **Hiện tại xử lý thế nào?**
    * Sử dụng thẻ từ (RFID), mã số (PIN), hoặc chìa khóa cơ vật lý truyền thống để cấp quyền ra vào.

    * Bố trí thêm nhân sự bảo vệ cầm chìa khóa tổng hoặc sử dụng sổ ghi chép logbook thủ công.


- **Bất tiện/rủi ro/chi phí là gì?**
    * Thẻ từ thiếu đi cơ chế định danh sinh trắc học độc bản; chúng dễ dàng bị đánh cắp, sao chép hoặc mượn tạm, tạo ra nguy cơ người ngoài lọt vào.

    * Hệ thống quản lý bị "mù" thông tin xác thực, không thể truy vết chính xác danh tính thực sự của người vừa mở cửa, gây khó khăn lớn khi cần điều tra sự cố thất thoát.

    * Sự bất tiện của các công cụ vật lý gây cản trở tiến độ công việc, làm giảm hiệu suất vận hành trong các tình huống cần thao tác nhanh hoặc khi nhân viên đang bê vác.

    * Phát sinh chi phí quản lý vận hành liên tục (mua thẻ mới, cấp lại thẻ mất, thay toàn bộ cụm khóa cơ định kỳ) và rủi ro thiệt hại tài chính nghiêm trọng nếu hệ thống an ninh bị vượt qua

## Consequence

- **Về trải nghiệm và hiệu suất làm việc?**
    * Nhân sự chưa được trải nghiệm sự tự do và tiện lợi tối đa khi di chuyển, đặc biệt lúc đang thao tác mang vác thiết bị.

    * Khả năng phản hồi của hệ thống chưa đạt mức lý tưởng trong các tình huống cần sự nhanh nhạy và kịp thời.

- **Về năng lực quản trị dữ liệu?**
    * Hệ thống dữ liệu hiện tại chưa phản ánh bức tranh định danh chính xác tuyệt đối, làm giảm khả năng theo dõi và hỗ trợ từ ban quản lý.
   
    * Thiếu đi một cơ chế truy vết luồng công việc thông minh và có tính xác thực cao.


- **Về tối ưu hóa nguồn lực?**
    * Tổ chức vẫn phải phân bổ ngân sách định kỳ cho việc cấp phát, quản lý và thay thế thẻ từ hoặc ổ khóa vật lý.
   
    * Bỏ lỡ cơ hội chuyển dịch nguồn lực sang các giải pháp công nghệ mang tính tương lai, thân thiện và bền vững hơn.



## Evidence

- **Bằng chứng từ các nghiên cứu quốc tế (Literature Review)?**
    * Báo cáo Access Control Research (2026) chỉ ra xu hướng chuyển dịch mạnh mẽ sang các giải pháp xác minh sự hiện diện thực tế của con người, nhằm tạo ra một môi trường an toàn và minh bạch tuyệt đối.
  
    * Nghiên cứu từ Đại học Tartu (2021) phân tích rằng thẻ RFID mang lại nhiều giá trị trong quá khứ nhưng hiện tạo ra không gian để nâng cấp lên các hệ thống sinh trắc học ưu việt hơn, giúp loại bỏ nguy cơ mượn hay sao chép thẻ.

| Nội dung | Trạng thái | Nguồn |
| --- | --- | --- |
| Chuyển đổi sang xác thực sinh trắc học | Target | Access Control Research (2026) |
| Không gian nâng cấp từ thẻ RFID truyền thống | Observed | Đại học Tartu (2021) |

## Scope sơ bộ

### In scope
* Xây dựng cơ chế nhận diện khuôn mặt offline (cục bộ) để mang lại độ trễ thấp và phản hồi tối ưu.

* Tích hợp điều khiển servo để tự động hóa thao tác mở/đóng khóa.

* Cung cấp màn hình LCD hiển thị trạng thái hoạt động trực quan và thân thiện.

* Thiết lập nút bấm override cơ học để đảm bảo sự linh hoạt tối đa trong mọi tình huống.

* Mở rộng khả năng lưu trữ thông qua quy trình đăng ký khuôn mặt mới (enroll).

* Ghi nhận log truy cập cơ bản để tạo nền tảng quản trị minh bạch.


### Out of scope
* Thiết lập cơ chế xác thực 2 yếu tố (2FA).

* Áp dụng các thuật toán chống giả mạo ảnh nâng cao (liveness detection).

* Yêu cầu kết nối internet bắt buộc để duy trì hệ thống.

* Xây dựng hệ sinh thái ứng dụng mobile điều khiển từ xa.

* Tích hợp các giao thức mã hóa dữ liệu truyền tải phức tạp.

* Đầu tư bổ sung hạ tầng camera hồng ngoại.