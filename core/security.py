import os
from cryptography.fernet import Fernet

KEY_FILE = "secret.key"
DATA_FILE = "accounts.json"

def get_or_create_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    with open(KEY_FILE, "rb") as f:
        return f.read()

# Chắc chắn phải có dòng này ở cuối cùng:
cipher = Fernet(get_or_create_key())