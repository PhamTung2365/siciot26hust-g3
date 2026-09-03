# Quick start

```bash
cd /home/v005128/Vision_DL/CCD
cp .env.example .env
# sửa secret, tên admin và mật khẩu admin trong .env
bash setup.sh       # chỉ cần ở lần đầu hoặc khi dependency thay đổi
bash run.sh
```

Mở <http://localhost:5000>, nhìn thẳng camera, nhập tên và chọn **Enroll**.
Đăng ký 3-5 góc/điều kiện sáng khác nhau cho mỗi người rồi thử nhận diện.

Kiểm tra nhanh:

```bash
curl http://localhost:5000/info
curl http://localhost:5000/status
```

Không có camera hoặc cần đổi port/threshold: sửa `config.py` rồi khởi động
lại. Xem [README.md](README.md) và [INSTALL.md](INSTALL.md) khi gặp lỗi.

Không expose dịch vụ ra Internet: đã có đăng nhập nhưng chưa có HTTPS và
liveness detection.
