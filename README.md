# Riot Auto Switcher

![Python](https://imgshields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

Riot Auto Switcher là một công cụ cá nhân được viết bằng Python, giúp đơn giản hóa việc chuyển đổi qua lại giữa các tài khoản Riot Games (Liên Minh Huyền Thoại và Valorant). 

Thay vì phải đăng xuất, gõ lại username và password mỗi khi muốn đổi tài khoản khác nhau, tool sẽ tự động hóa toàn bộ quá trình này.

## Các tính năng chính

* **Tự động hóa đăng nhập:** Tự động tắt phiên làm việc cũ, mở Riot Client, điền thông tin và khởi chạy game được chọn.
* **Mã hóa cục bộ:** Thông tin mật khẩu được mã hóa AES (Fernet) và chỉ lưu trữ trên ổ cứng của người dùng (file accounts.json), không gửi dữ liệu qua mạng.
* **Giao diện quản lý:** Sử dụng CustomTkinter với Dark theme, hỗ trợ thao tác kéo-thả để sắp xếp thứ tự tài khoản.
* **Đa ngôn ngữ:** Hỗ trợ Tiếng Việt và Tiếng Anh.
* **Theo dõi tiến trình:** Có thanh trạng thái báo cáo chi tiết các bước tool đang thực thi.

## Hướng dẫn chạy code 

Yêu cầu máy tính đã cài đặt Python 3.10 trở lên.

1. Clone repository:
   git clone [https://github.com/your-username/riot-auto-switcher.git](https://github.com/your-username/riot-auto-switcher.git)
   cd riot-auto-switcher
2. Cài đặt các thư viện phụ thuộc:
   pip install -r requirements.txt
3. Khởi chạy ứng dụng:
   python main.py
