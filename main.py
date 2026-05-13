import sys
import ctypes
from gui.app import App
from core.logger import logger

def configure_environment():
    """Thiết lập môi trường để chống mờ ảnh DPI trên Windows."""
    try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try: ctypes.windll.user32.SetProcessDPIAware()
        except Exception: pass

def main():
    configure_environment()
    logger.info("--- KHỞI ĐỘNG RIOT AUTO SWITCHER ---")
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        logger.critical(f"Lỗi hệ thống: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()