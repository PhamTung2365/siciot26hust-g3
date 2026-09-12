# 3. Persona

## Persona 1 — Primary User
- **Tên giả định**: Trần Bảo Long

- **Tuổi**: 32

- **Vai trò**: Chuyên viên Hậu cần & Vận hành thiết bị phòng máy chủ.

- **Bối cảnh**: Anh Long thường xuyên phải luân chuyển máy chủ, vật tư và thiết bị cồng kềnh giữa kho và phòng trung tâm dữ liệu. Đôi tay của anh hầu như luôn trong trạng thái bận rộn để nâng đỡ hàng hóa giá trị cao.

- **Mục tiêu**: Duy trì nhịp độ công việc liền mạch, trơn tru nhất có thể; di chuyển qua các điểm kiểm soát an ninh mà không cần phải dừng lại hay đặt thiết bị xuống đất.

- **Hành vi**: Hiện tại, anh thường phải tạm ngưng bước chân, đặt vật nặng xuống sàn, tìm kiếm thẻ từ trong túi áo bảo hộ, quẹt thẻ mở cửa, rồi mới tiếp tục nâng hàng lên để bước vào. 

- **Kinh nghiệm**: Sở hữu thâm niên nhiều năm trong việc quản lý vật tư vật lý và nắm rõ các quy định an ninh tại khu vực lưu trữ trọng yếu.

- **Mức độ dùng công nghệ**: Anh sử dụng thành thạo điện thoại thông minh và các phần mềm quản lý kho cơ bản, nhưng không đi sâu vào việc thiết lập hay cấu hình các hệ thống phần mềm phức tạp.

- **Khó khăn**: Đang đứng trước cơ hội lớn để tối ưu hóa thời gian di chuyển. Việc phụ thuộc vào thẻ từ vật lý tạo ra một điểm nghẽn trong luồng vận hành, mở ra dư địa để tìm kiếm một phương thức nhận diện tự động giúp giải phóng hoàn toàn đôi tay.

- **Nhu cầu**: Một trải nghiệm bước qua cửa hoàn toàn rảnh tay và liền mạch, hệ thống tự động xác minh danh tính của anh một cách tự nhiên, nhanh chóng.

## Persona 2 — Secondary User
- **Tên giả định**: Lê Thị Mai

- **Tuổi**: 45

- **Vai trò**: Giám sát viên An ninh trực ban.

- **Mức độ dùng công nghệ**: Cô Mai quen với các thao tác ghi chép thủ công trên sổ sách hoặc sử dụng các công cụ cơ học, rất ngại phải làm quen với các giao diện phần mềm hiển thị nhiều thông số kỹ thuật đan xen.

- **Mục tiêu**: Đảm bảo không gian khu vực luôn an toàn, minh bạch; đồng thời có khả năng chủ động hỗ trợ chào đón, mở cửa từ xa cho nhân sự nội bộ hoặc đối tác được cấp phép một cách thuận tiện nhất.

- **Hành vi**: Thường xuyên quan sát người ra vào, đối chiếu danh tính bằng mắt thường với danh sách đã đăng ký trên giấy; đôi khi phải rời vị trí để dùng chìa khóa mở cửa cho nhân viên quên thẻ.

- **Khó khăn**: Quá trình ghi chép và đối chiếu thủ công đòi hỏi sự tập trung cao độ và tiêu tốn nhiều năng lượng. Cô đang mong mỏi một công cụ hỗ trợ trực quan, thân thiện để quán xuyến việc nhận diện và ghi nhận thông tin lưu thông nhẹ nhàng hơn.

- **Nhu cầu**: Một hệ thống có khả năng tự động lưu trữ thông tin minh bạch, kèm theo một cơ chế phản hồi cực kỳ dễ hiểu (ví dụ: màn hình nhỏ hiển thị bằng ngôn ngữ tiếng Việt).

## Checklist

- [x] Persona mô tả người dùng, không mô tả giải pháp (Không nhắc đến camera, AI, thẻ RFID nâng cao hay kiến trúc server; chỉ tập trung vào trải nghiệm "rảnh tay", "nút bấm cơ học đơn giản", "màn hình hiển thị thân thiện").

- [x] Không khóa trước camera/Raspberry Pi/MQTT/AI nếu chưa có lý do (Khảo sát thuần túy dựa trên hành vi bê vác và nhu cầu quản lý).

- [x] Phân biệt dữ liệu thực và giả định (Các thông tin về tên, tuổi và hành vi cụ thể được giả định dựa trên việc phân tích môi trường phòng máy chủ/kho hàng).
