## 📖 Mô tả dự án

**FoodZone** là một ứng dụng web đặt đồ ăn trực tuyến được xây dựng bằng Django Framework. Ứng dụng cung cấp nền tảng kết nối giữa khách hàng, nhà hàng và người giao hàng, với các tính năng hiện đại như chatbot AI, thanh toán trực tuyến và theo dõi đơn hàng thời gian thực.

## ✨ Tính năng chính

### 🍽️ Dành cho khách hàng
- **Đặt đồ ăn**: Xem menu, đặt món và thanh toán trực tuyến
- **Quản lý tài khoản**: Đăng ký, đăng nhập, cập nhật thông tin cá nhân
- **Theo dõi đơn hàng**: Xem trạng thái đơn hàng và vị trí giao hàng
- **Quản lý địa chỉ**: Lưu trữ và quản lý địa chỉ giao hàng
- **Chatbot AI**: Hỗ trợ khách hàng 24/7 với AI chatbot

### 🏪 Dành cho nhà hàng
- **Quản lý menu**: Thêm, sửa, xóa món ăn và danh mục
- **Dashboard nhà hàng**: Theo dõi đơn hàng và doanh thu
- **Quản lý đơn hàng**: Xử lý và cập nhật trạng thái đơn hàng

### 🚚 Dành cho người giao hàng (Shipper)
- **Đăng ký shipper**: Đăng ký làm người giao hàng
- **Dashboard shipper**: Quản lý đơn hàng cần giao
- **Cập nhật vị trí**: Theo dõi vị trí giao hàng
- **Cập nhật trạng thái**: Cập nhật trạng thái giao hàng

### 💳 Hệ thống thanh toán
- **PayPal Integration**: Thanh toán an toàn qua PayPal
- **Quản lý giao dịch**: Theo dõi lịch sử thanh toán

## 🛠️ Công nghệ sử dụng

### Backend
- **Django 5.2** - Web framework chính
- **Python 3.8+** - Ngôn ngữ lập trình
- **SQLite** - Cơ sở dữ liệu (có thể thay đổi sang PostgreSQL/MySQL)

### Frontend
- **HTML5/CSS3** - Giao diện người dùng
- **JavaScript** - Tương tác động
- **Bootstrap** - Framework CSS responsive
- **jQuery** - Thư viện JavaScript

### AI & External Services
- **Google Generative AI** - Chatbot thông minh
- **PayPal API** - Xử lý thanh toán

### Development Tools
- **Virtual Environment** - Quản lý dependencies
- **Django Admin** - Giao diện quản trị

## 🚀 Cài đặt và chạy dự án

### Yêu cầu hệ thống
- Python 3.8 hoặc cao hơn
- pip (Python package manager)
- Git

### Bước 1: Clone dự án
```bash
git clone <repository-url>
cd foodzone
```

### Bước 2: Tạo môi trường ảo
```bash
# Windows
python -m venv .venv
.venv\Scripts\Activate.ps1

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Bước 3: Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Bước 4: Chạy migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Bước 5: Tạo superuser (tùy chọn)
```bash
python manage.py createsuperuser
```

### Bước 6: Chạy development server
```bash
python manage.py runserver
```

### Bước 7: Truy cập ứng dụng
- **Website**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/

## 📁 Cấu trúc dự án

```
foodzone/
├── foodzone/                 # Main project settings
│   ├── __init__.py
│   ├── settings.py          # Cấu hình Django
│   ├── urls.py              # URL routing chính
│   ├── wsgi.py              # WSGI configuration
│   └── asgi.py              # ASGI configuration
├── myapp/                    # Main application
│   ├── models.py            # Database models
│   ├── views.py             # Business logic
│   ├── urls.py              # App-specific URLs
│   ├── forms.py             # Form definitions
│   ├── admin.py             # Admin interface
│   └── migrations/          # Database migrations
├── static/                   # Static files (CSS, JS, images)
├── media/                    # User-uploaded files
├── template/                 # HTML templates
├── requirements.txt          # Python dependencies
├── manage.py                 # Django management script
└── db.sqlite3               # SQLite database
```

## 🗄️ Cấu trúc cơ sở dữ liệu

### Models chính
- **User/Profile**: Thông tin người dùng
- **Category**: Danh mục món ăn
- **Dish**: Thông tin món ăn
- **Restaurant**: Thông tin nhà hàng
- **Order**: Đơn hàng
- **Shipper**: Người giao hàng
- **Contact**: Liên hệ từ khách hàng

## 🔧 Cấu hình

### Environment Variables
Tạo file `.env` trong thư mục gốc:
```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-client-secret
PAYPAL_RECEIVER_EMAIL=your-paypal-email
```

### PayPal Configuration
- Cập nhật thông tin PayPal trong `settings.py`
- Sử dụng sandbox cho development
- Cập nhật production credentials khi deploy

## 🧪 Testing

```bash
# Chạy tất cả tests
python manage.py test

# Chạy test cho app cụ thể
python manage.py test myapp

# Chạy test với coverage
coverage run --source='.' manage.py test
coverage report
```

## 📦 Deployment

### Production Checklist
- [ ] Set `DEBUG = False`
- [ ] Update `ALLOWED_HOSTS`
- [ ] Configure production database
- [ ] Set up static file serving
- [ ] Configure HTTPS
- [ ] Update PayPal credentials
- [ ] Set up logging
- [ ] Configure backup strategy

### Docker (Tùy chọn)
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 🤝 Đóng góp

1. Fork dự án
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

## 📝 Changelog

### Version 1.0.0
- ✅ Hệ thống đăng ký/đăng nhập
- ✅ Quản lý món ăn và danh mục
- ✅ Hệ thống đặt hàng
- ✅ Chatbot AI
- ✅ Thanh toán PayPal
- ✅ Quản lý shipper
- ✅ Dashboard nhà hàng

## 📄 License

Dự án này được phân phối dưới giấy phép MIT. Xem file `LICENSE` để biết thêm chi tiết.

## 👥 Tác giả

**FoodZone Team** - Võ Đức Hòa - Nguyễn Anh Kiệt

## 🙏 Lời cảm ơn

- Django Community
- PayPal Developer Team
- Google AI Team
- Bootstrap Team

## 📞 Liên hệ

- **Email**: voduchoa4444@gmail.com
- **Website**: https://foodzone.com
- **GitHub**: https://github.com/foodzone

---

⭐ Nếu dự án này hữu ích, hãy cho chúng tôi một star trên GitHub!
