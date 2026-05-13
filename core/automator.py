import os
import time
import psutil
import requests
import subprocess
import base64
import pyautogui
import win32gui
import win32con
import json
import traceback
from pathlib import Path
from datetime import datetime
from core.logger import logger

class RiotAutomator:
    # --- Đã thêm tham số status_callback ---
    def __init__(self, username, password, target_game, display_name="", status_callback=None):
        logger.info(f"═══ Khởi tạo RiotAutomator ═══")
        self.username = username
        self.password = password
        self.target_game = target_game
        self.display_name = display_name or ""
        self.status_callback = status_callback  # <--- Lưu hàm cập nhật giao diện
        
        self.riot_path = self._find_riot_client_path()
        self.assets_dir = Path("assets")
        self.image_assets = {
            "username_field": "username_field.png",
            "password_field": "password_field.png",
            "login_button_active": "login_button_active.png",
            "login_screen_marker": "login_screen_marker.png",
            "login_error": "login_error.png",
            "login_server_error": "login_server_error.png",
            "stay_signed_in_unchecked": "stay_signed_in_unchecked.png",
        }
        self.default_confidence = 0.88
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05
        self.launch_targets = {
            "LoL": ["--launch-product=league_of_legends", "--launch-patchline=live"],
            "Valorant": ["--launch-product=valorant", "--launch-patchline=live"],
        }

    def _update_status(self, key, progress):
        """Hàm gửi tín hiệu báo cáo tiến trình về cho giao diện"""
        if self.status_callback:
            self.status_callback(key, progress)

    def _find_riot_client_path(self):
        program_data = os.environ.get("ALLUSERSPROFILE", r"C:\ProgramData")
        riot_installs_path = os.path.join(program_data, "Riot Games", "RiotClientInstalls.json")
        if os.path.exists(riot_installs_path):
            try:
                with open(riot_installs_path, "r") as f:
                    data = json.load(f)
                    rc_path = data.get("rc_default")
                    if rc_path and os.path.exists(rc_path):
                        return os.path.normpath(rc_path)
            except Exception: pass
        for drive in ["C", "D", "E", "F", "G"]:
            guess = fr"{drive}:\Riot Games\Riot Client\RiotClientServices.exe"
            if os.path.exists(guess): return guess
        return r"C:\Riot Games\Riot Client\RiotClientServices.exe"

    def is_process_running(self, process_name):
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and process_name.lower() in proc.info['name'].lower(): return True
        return False

    def _hide_riot_window(self):
        handles = []
        def _enum(hwnd, _):
            if win32gui.GetWindowText(hwnd).strip().lower() == "riot client": handles.append(hwnd)
        win32gui.EnumWindows(_enum, None)
        for hwnd in handles:
            try: win32gui.ShowWindow(hwnd, 0)
            except Exception: pass

    def kill_process(self, process_name, wait_timeout=8):
        try: subprocess.run(["taskkill", "/F", "/IM", process_name, "/T"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception: pass
        try: self._wait_until(lambda: not self.is_process_running(process_name), timeout=wait_timeout, poll=0.2)
        except TimeoutError: pass
            
    def _asset_path(self, name): return self.assets_dir / self.image_assets[name]

    def _validate_required_assets(self):
        missing = [f"{name} -> {self.assets_dir / filename}" for name, filename in self.image_assets.items() if not (self.assets_dir / filename).exists()]
        if missing: raise FileNotFoundError("Thiếu ảnh template:\n" + "\n".join(missing))

    def _get_current_riot_id(self):
        username = os.environ.get("USERNAME", "")
        if not username: return ""
        lockfile_path = Path(f"C:/Users/{username}/AppData/Local/Riot Games/Riot Client/Config/lockfile")
        if not lockfile_path.exists(): return ""
        try:
            lockfile_content = lockfile_path.read_text(encoding="utf-8").strip()
            _, _, port, password, _ = lockfile_content.split(":")
            token_b64 = base64.b64encode(f"riot:{password}".encode("utf-8")).decode("utf-8")
            headers = {"Authorization": f"Basic {token_b64}", "Accept": "application/json"}
            import urllib3; urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(f"https://127.0.0.1:{port}/chat/v1/session", headers=headers, verify=False, timeout=3)
            if response.status_code != 200: return ""
            payload = response.json()
            return f"{payload.get('game_name', '')}#{payload.get('game_tag', '')}" if payload.get("game_tag") else payload.get("game_name", "")
        except Exception: return ""

    def _strip_riot_tag(self, riot_id: str) -> str:
        return riot_id.split("#")[0].strip().lower() if riot_id else ""

    def _wait_until(self, predicate, timeout, poll=0.25, error_message="Timeout"):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate(): return True
            time.sleep(poll)
        raise TimeoutError(error_message)

    def _locate_image(self, asset_name, confidence=None, region=None):
        if confidence is None: confidence = self.default_confidence
        try: return pyautogui.locateOnScreen(str(self._asset_path(asset_name)), confidence=confidence, region=region, grayscale=True)
        except Exception: return None

    def _find_riot_hwnd(self, timeout=30):
        result = {"hwnd": None}
        try: subprocess.Popen([self.riot_path])
        except Exception: pass
        def _probe():
            handles = []
            def _enum(hwnd, _):
                if win32gui.GetWindowText(hwnd).strip().lower() == "riot client":
                    rect = win32gui.GetWindowRect(hwnd)
                    if (rect[2] - rect[0]) > 100 and (rect[3] - rect[1]) > 100: handles.append(hwnd)
            win32gui.EnumWindows(_enum, None)
            if handles:
                for hwnd in handles:
                    if win32gui.IsWindowVisible(hwnd):
                        result["hwnd"] = hwnd; return True
                result["hwnd"] = handles[0]
                win32gui.ShowWindow(handles[0], 5)
                return True
            return False
        self._wait_until(_probe, timeout=timeout, poll=0.25)
        return result["hwnd"]

    def _activate_window(self, hwnd):
        try:
            if not win32gui.IsWindow(hwnd): return
            if win32gui.IsIconic(hwnd): win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
        except Exception: pass

    def _wait_center_on_screen(self, asset_name, timeout=30, confidence=0.8):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                center = pyautogui.locateCenterOnScreen(str(self._asset_path(asset_name)), confidence=confidence, grayscale=True)
                if center: return center
            except Exception: pass
            time.sleep(0.1)
        raise TimeoutError(f"Không tìm thấy ảnh {asset_name}")

    def _perform_login(self):
        self._update_status("status_login_open", 0.4)
        user_center = self._wait_center_on_screen("username_field", timeout=60, confidence=0.7)
        pyautogui.click(user_center.x, user_center.y)
        
        self._update_status("status_typing", 0.6)
        pyautogui.hotkey("ctrl", "a"); pyautogui.press("backspace")
        pyautogui.write(self.username); pyautogui.press("tab"); pyautogui.write(self.password)
        try:
            box = self._locate_image("stay_signed_in_unchecked", confidence=0.8)
            if box:
                pyautogui.click(pyautogui.center(box).x, pyautogui.center(box).y)
                time.sleep(0.1) 
        except Exception: pass
        login_center = self._wait_center_on_screen("login_button_active", timeout=10, confidence=0.8)
        pyautogui.click(login_center.x, login_center.y)

    def _verify_login_success(self):
        self._update_status("status_auth", 0.75)
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            if self._locate_image("login_server_error", confidence=0.8): raise ConnectionError("Lỗi kết nối từ máy chủ Riot.")
            if self._locate_image("login_error", confidence=0.8): raise ValueError("Sai tài khoản hoặc mật khẩu!")
            if self._locate_image("login_screen_marker", confidence=0.85) is None: return True
            time.sleep(0.5)
        raise TimeoutError(f"Quá thời gian xác thực Riot.")

    def _launch_game_via_cli(self):
        cli_args = self.launch_targets[self.target_game]
        try:
            subprocess.run(["taskkill", "/F", "/IM", "RiotClientUx.exe"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(1) 
        except Exception: pass
        try: subprocess.Popen([self.riot_path, *cli_args])
        except Exception as e: logger.error(f"Lỗi khởi chạy: {e}")

    def _start_and_login(self):
        self._launch_game_via_cli()
        self._activate_window(self._find_riot_hwnd(timeout=25))
        self._perform_login()
        self._verify_login_success()

    def _launch_game(self, trigger_launch=True):
        self._update_status("status_launching", 0.9)
        if trigger_launch:
            time.sleep(1)
            self._launch_game_via_cli()
        names = ["LeagueClient.exe", "League of Legends.exe"] if self.target_game == "LoL" else ["VALORANT.exe", "VALORANT-Win64-Shipping.exe"]
        self._wait_until(lambda: any(self.is_process_running(n) for n in names), timeout=60, poll=0.4)
        self._hide_riot_window()

    def execute_flow(self):
        try:
            self._update_status("status_prep", 0.1)
            self._validate_required_assets()
            lol_running = self.is_process_running("LeagueClient.exe") or self.is_process_running("League of Legends.exe")
            val_running = self.is_process_running("VALORANT.exe") or self.is_process_running("VALORANT-Win64-Shipping.exe")
            if not self.is_process_running("RiotClientServices.exe"):
                try: subprocess.Popen([self.riot_path])
                except Exception: pass

            self._update_status("status_check", 0.2)
            current_riot_id = ""
            is_correct_account = False
            for _ in range(6): 
                current_riot_id = self._get_current_riot_id()
                if current_riot_id:
                    if self._strip_riot_tag(current_riot_id) == self._strip_riot_tag(self.display_name) or self.display_name.strip().lower() in current_riot_id.lower():
                        is_correct_account = True
                    break
                time.sleep(2)

            need_to_trigger_launch = True
            if not is_correct_account:
                self._update_status("status_clean", 0.3)
                for proc in ["LeagueClient.exe", "League of Legends.exe", "VALORANT.exe", "VALORANT-Win64-Shipping.exe", "RiotClientUx.exe", "RiotClientServices.exe"]:
                    self.kill_process(proc, wait_timeout=2)
                import shutil
                try:
                    data_path = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Riot Games", "Riot Client", "Data")
                    if os.path.exists(os.path.join(data_path, "RiotGamesPrivateSettings.yaml")): os.remove(os.path.join(data_path, "RiotGamesPrivateSettings.yaml"))
                    if os.path.exists(os.path.join(data_path, "Sessions")): shutil.rmtree(os.path.join(data_path, "Sessions"), ignore_errors=True)
                except Exception: pass
                self._start_and_login()
                need_to_trigger_launch = False
            else:
                if (self.target_game == "LoL" and lol_running) or (self.target_game == "Valorant" and val_running):
                    need_to_trigger_launch = False
                    if self.target_game == "LoL" and val_running:
                        self.kill_process("VALORANT.exe", 2); self.kill_process("VALORANT-Win64-Shipping.exe", 2)
                    elif self.target_game == "Valorant" and lol_running:
                        self.kill_process("LeagueClient.exe", 2); self.kill_process("League of Legends.exe", 2)
                else:
                    if lol_running: self.kill_process("LeagueClient.exe", 2); self.kill_process("League of Legends.exe", 2)
                    if val_running: self.kill_process("VALORANT.exe", 2); self.kill_process("VALORANT-Win64-Shipping.exe", 2)
                    self.kill_process("RiotClientUx.exe", 2); self.kill_process("RiotClientServices.exe", 2)
                    time.sleep(1); need_to_trigger_launch = True

            self._launch_game(trigger_launch=need_to_trigger_launch)
            self._update_status("status_done", 1.0) # Báo cáo hoàn tất 100%

        except Exception as ex:
            logger.error(f"[AUTOMATION_ERROR] {ex}")
            logger.error(traceback.format_exc())
            raise ex # Bắn lỗi ra để giao diện bắt được