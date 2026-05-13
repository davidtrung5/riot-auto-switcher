# File: core/settings.py
import json
import os

CONFIG_FILE = "config.json"

def load_config():
    """Tải cài đặt, mặc định là Tiếng Việt nếu chưa có file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"language": "vi"}

def save_config(config_data):
    """Lưu cài đặt xuống file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f)