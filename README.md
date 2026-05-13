# Riot Auto Switcher

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
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
   ```bash
   git clone [https://github.com/your-username/riot-auto-switcher.git](https://github.com/your-username/riot-auto-switcher.git)
   cd riot-auto-switcher
3. Cài đặt các thư viện phụ thuộc:
   ```bash
   pip install -r requirements.txt
4. Khởi chạy ứng dụng:
   ```bash
   python main.py
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Riot Auto Switcher

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

Riot Auto Switcher is an open-source Python tool designed to simplify switching between Riot Games accounts (specifically League of Legends and Valorant). 

Instead of manually logging out, typing your username and password every time you want to switch accounts, this tool fully automates the process.

## Key Features

* **Automated Login:** Automatically terminates the current session, opens Riot Client, injects credentials, and launches the selected game.
* **Local Encryption:** Passwords are AES encrypted (Fernet) and stored strictly locally on your machine (`accounts.json`). No data is sent over the internet.
* **Modern UI:** Built with CustomTkinter featuring a Dark theme and intuitive Drag-and-Drop account sorting.
* **Multi-language:** Seamlessly switch between English and Vietnamese.
* **Progress Tracking:** Real-time status bar reporting the current execution step.

## How to run (For Developers)

Requires Python 3.10 or higher.

1. Clone the repository:
   ```bash
   git clone [https://github.com/your-username/riot-auto-switcher.git](https://github.com/your-username/riot-auto-switcher.git)
   cd riot-auto-switcher
2.
   ```bash
   pip install -r requirements.txt
3.
   ```bash
   python main.py
