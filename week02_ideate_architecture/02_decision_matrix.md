# 2. Decision Matrix

| Tiêu chí | Trọng số | A | B | C | Evidence/Basis |
|---|---:|---:|---:|---:|---|
| Giá trị cho người dùng | 30% | 5 | 3 | 5 | A và C giải quyết trực tiếp nhu cầu rảnh tay và truy vết; B vẫn yêu cầu thao tác thẻ/mã và không xác định chắc chắn người thực tế truy cập. |
| Khả thi kỹ thuật | 25% | 4 | 4 | 2 | Prototype hiện đã có camera, nhận diện, enroll, database và dashboard cho A; B dùng công nghệ quen thuộc nhưng chưa có phần cứng; C cần thêm luồng fallback, phân quyền và thiết bị điều khiển chưa triển khai. |
| Chi phí | 15% | 3 | 4 | 2 | A cần camera, máy chạy model và bảo vệ dữ liệu; B có thể dùng phần cứng phổ biến; C cộng thêm chi phí cho nhiều phương thức, phần cứng dự phòng và vận hành trực ban. |
| Thời gian | 15% | 4 | 4 | 2 | A có nền tảng phần mềm sẵn trong repository; B tương đối nhanh nhưng phải xây lại luồng xác thực; C có nhiều trường hợp ngoại lệ và tích hợp hơn. |
| Khả năng mở rộng | 15% | 4 | 3 | 5 | A mở rộng được số người và quản trị tập trung; B dễ mở rộng danh sách nhưng vẫn phụ thuộc vật dụng/mã; C mở rộng tốt cho nhiều chính sách và nhóm người dùng nếu có đủ quy trình vận hành. |

**Cách chấm:** 1 = thấp, 5 = cao. Điểm tổng = điểm từng tiêu chí nhân với trọng số; trọng số cộng lại bằng 100%.

| Phương án | Điểm có trọng số | Xếp hạng |
|---|---:|---:|
| A | 4,15 / 5 | 1 |
| B | 3,55 / 5 | 2 |
| C | 3,35 / 5 | 3 |

## Concept được chọn
- **Phương án A — Xác thực không chạm tại cửa bằng nhận diện sinh trắc học cục bộ.**

## Lý do
- A bám sát nhất với hai nhu cầu ưu tiên: không làm gián đoạn người đang mang thiết bị và giảm sự phụ thuộc vào thẻ/chìa khóa có thể bị mất hoặc chia sẻ.
- Đây là phương án phù hợp nhất với năng lực hiện có: repository đã có luồng camera → trích xuất embedding → so khớp → dashboard, cùng chức năng enroll, xóa người và quản trị tài khoản.
- A có thể phát triển theo từng bước: trước mắt kiểm chứng nhận diện và quản trị người dùng; sau đó mới tích hợp actuator, access log và cơ chế dự phòng. Việc chọn A không có nghĩa prototype hiện tại đã là khóa cửa production.
- Phương án C được giữ làm hướng nâng cấp sau MVP, đặc biệt cho fallback và tình huống khẩn cấp. Phương án B là phương án dự phòng nếu kết quả thử nghiệm nhận diện, quyền riêng tư hoặc mức chấp nhận người dùng không đạt yêu cầu.

## Rủi ro và điều kiện trước Scope Freeze

- Cần đo độ chính xác, false match/false reject và thời gian phản hồi bằng dữ liệu kiểm thử phù hợp; hiện repository chưa có kết quả benchmark người dùng thật.
- Cần thiết kế fallback an toàn cho khi camera, model hoặc nguồn điện gặp lỗi; nhận diện hiện tại chưa bao gồm liveness detection.
- Cần xác định cách lưu trữ, phân quyền và bảo vệ embedding; README đã nêu embedding không phải dữ liệu vô danh.
- Việc điều khiển servo, LCD và nút override chưa có trong code hiện tại, nên phải được kiểm thử riêng trước khi tuyên bố hoàn thành khóa cửa vật lý.
