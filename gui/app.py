import customtkinter as ctk
import tkinter.messagebox as messagebox
import json
import os
import threading
import sys
from PIL import Image

from core.security import cipher, DATA_FILE
from core.automator import RiotAutomator
from core.logger import logger
from core.locales import translations
from core.settings import load_config, save_config

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def get_resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.abspath("."), relative_path)
    def __init__(self):
        super().__init__()
        self.title("Riot Auto Switcher - Account Manager")
        
        try: self.iconbitmap(self.get_resource_path("assets/app_icon.ico"))
        except Exception: pass
        
        window_width, window_height = 1100, 650
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{window_width}x{window_height}+{int((screen_w/2)-(window_width/2))}+{int((screen_h/2)-(window_height/2))}")
        self.minsize(800, 500)

        self.bg_color = "#0f172a"      
        self.card_color = "#1e293b"    
        self.border_color = "#334155"  
        self.text_muted = "#94a3b8"    
        self.configure(fg_color=self.bg_color) 

        self.app_config = load_config()
        self.lang = self.app_config.get("language", "vi")

        self.accounts = self.load_accounts()
        self.automation_thread = None
        self.automation_just_completed = False  
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # Thanh trạng thái (Tạo 1 lần duy nhất)
        self.status_frame = ctk.CTkFrame(self, height=45, fg_color="#0b1121", corner_radius=0)
        self.status_frame.pack(side="bottom", fill="x")
        self.status_label = ctk.CTkLabel(self.status_frame, text="", font=("Arial", 13, "bold"), text_color="#10b981")
        self.status_label.pack(side="left", padx=30, pady=10)
        self.progress_bar = ctk.CTkProgressBar(self.status_frame, width=300, height=8, fg_color=self.card_color, progress_color="#3b82f6")
        self.progress_bar.pack(side="right", padx=30, pady=10)
        self.progress_bar.set(0) # Mặc định 0%
        
        self._build_main_ui()

    def t(self, key, **kwargs):
        text = translations.get(self.lang, translations["en"]).get(key, key)
        return text.format(**kwargs) if kwargs else text

    def change_language(self, choice):
        new_lang = "vi" if choice == "Tiếng Việt" else "en"
        if self.lang != new_lang:
            self.lang = new_lang
            self.app_config["language"] = self.lang
            save_config(self.app_config)
            self._build_main_ui()

    def set_status(self, key, progress=0.0, **kwargs):
        """Hàm cập nhật Thanh trạng thái an toàn (Thread-safe)"""
        def update_ui():
            self.status_label.configure(text=self.t(key, **kwargs))
            self.progress_bar.set(progress)
            if progress == 0.0 or progress == 1.0:
                self.progress_bar.configure(progress_color="#10b981") # Xanh lá khi rảnh/xong
            else:
                self.progress_bar.configure(progress_color="#3b82f6") # Xanh dương khi đang chạy
                
        self.after(0, update_ui) # Đẩy lệnh cập nhật vào luồng chính của UI

    def _build_main_ui(self):
        # Không xóa status_frame khi vẽ lại
        for widget in self.winfo_children():
            if widget != self.status_frame:
                widget.destroy()
                
        self.set_status("status_idle", 0.0)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text=self.t("title"), font=("Arial", 28, "bold"), text_color="white").pack(side="left")
        
        lang_var = ctk.StringVar(value="Tiếng Việt" if self.lang == "vi" else "English")
        lang_menu = ctk.CTkOptionMenu(header_frame, values=["Tiếng Việt", "English"], variable=lang_var, command=self.change_language,
                                      width=120, height=35, fg_color=self.card_color, button_color=self.border_color, font=("Arial", 12, "bold"))
        lang_menu.pack(side="right", padx=(15, 0))

        self.add_btn = ctk.CTkButton(header_frame, text=self.t("add_btn"), width=160, height=35, fg_color="#3b82f6", hover_color="#2563eb", font=("Arial", 13, "bold"), corner_radius=8, command=self.open_add_window)
        self.add_btn.pack(side="right")

        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self._current_cols = 0
        self._card_frames = []
        self._dragged_acc = None
        self._ghost_window = None 
        
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.refresh_list()

    def _on_window_close(self):
        if self.automation_thread and (self.automation_thread.is_alive() or self.automation_just_completed): return
        try: self.destroy(); os._exit(0)
        except Exception: os._exit(0)

    def load_accounts(self):
        if not os.path.exists(DATA_FILE): return []
        with open(DATA_FILE, "r") as f: accounts = json.load(f)
        for acc in accounts:
            if "display_name" not in acc: acc["display_name"] = ""
        return accounts

    def save_accounts(self):
        with open(DATA_FILE, "w") as f: json.dump(self.accounts, f)

    def _on_frame_configure(self, event):
        cols = max(1, event.width // 350)
        if cols != self._current_cols:
            self._current_cols = cols; self._rearrange_grid()

    def _rearrange_grid(self):
        cols = max(1, self._current_cols)
        for idx, card in enumerate(self._card_frames):
            r, c = idx // cols, idx % cols
            card.grid(row=r, column=c, padx=12, pady=12)

    def _make_draggable(self, widget, acc):
        def on_press(event):
            self._dragged_acc = acc
            self.config(cursor="fleur")
            if self._ghost_window: self._ghost_window.destroy()
            self._ghost_window = ctk.CTkToplevel(self)
            self._ghost_window.overrideredirect(True) 
            self._ghost_window.attributes('-alpha', 0.85) 
            self._ghost_window.configure(fg_color="#3b82f6") 
            ctk.CTkLabel(self._ghost_window, text=self.t("moving", user=acc['username']), font=("Arial", 12, "bold"), text_color="white").pack(padx=15, pady=8)
            x, y = self.winfo_pointerxy(); self._ghost_window.geometry(f"+{x+15}+{y+15}")

        def on_drag(event):
            if self._ghost_window:
                x, y = self.winfo_pointerxy(); self._ghost_window.geometry(f"+{x+15}+{y+15}")

        def on_release(event):
            self.config(cursor="")
            if self._ghost_window: self._ghost_window.destroy(); self._ghost_window = None
            if not self._dragged_acc: return
            x, y = self.winfo_pointerxy()
            target = self.winfo_containing(x, y)
            target_acc = None
            while target:
                if hasattr(target, '_acc'): target_acc = target._acc; break
                target = target.master
            if target_acc and target_acc != self._dragged_acc:
                idx1, idx2 = self.accounts.index(self._dragged_acc), self.accounts.index(target_acc)
                self.accounts[idx1], self.accounts[idx2] = self.accounts[idx2], self.accounts[idx1]
                self.save_accounts(); self.refresh_list()
            self._dragged_acc = None

        for w in [widget] + widget.winfo_children():
            if not isinstance(w, ctk.CTkButton):
                w.bind("<ButtonPress-1>", on_press); w.bind("<B1-Motion>", on_drag); w.bind("<ButtonRelease-1>", on_release)
                if hasattr(w, '_canvas'):
                    w._canvas.bind("<ButtonPress-1>", on_press); w._canvas.bind("<B1-Motion>", on_drag); w._canvas.bind("<ButtonRelease-1>", on_release)

    def refresh_list(self):
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        self._card_frames = []
        for acc in self.accounts:
            card = ctk.CTkFrame(self.scrollable_frame, width=330, height=210, fg_color=self.card_color, corner_radius=12, border_width=1, border_color=self.border_color)
            card.grid_propagate(False); card.pack_propagate(False); card._acc = acc 

            ctk.CTkLabel(card, text=acc["username"], font=("Arial", 22, "bold"), text_color="white", anchor="w").pack(fill="x", padx=20, pady=(20, 2))
            ctk.CTkLabel(card, text=acc.get("display_name") or self.t("no_name"), font=("Arial", 14), text_color=self.text_muted, anchor="w").pack(fill="x", padx=20)

            badge_frame = ctk.CTkFrame(card, fg_color="transparent")
            badge_frame.pack(fill="x", padx=20, pady=(12, 15))
            if "LoL" in acc["games"]: ctk.CTkLabel(badge_frame, text=" League of Legends " if self.lang=="en" else " Liên Minh ", font=("Arial", 12, "bold"), text_color="#0bc6e3", fg_color="#064049", corner_radius=4).pack(side="left", padx=(0, 6))
            if "Valorant" in acc["games"]: ctk.CTkLabel(badge_frame, text=" Valorant ", font=("Arial", 12, "bold"), text_color="#ff4654", fg_color="#111823", corner_radius=4).pack(side="left")
                
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=(5, 10))
            ctk.CTkButton(btn_frame, text=self.t("edit"), width=70, height=36, fg_color="transparent", hover_color=self.border_color, border_width=1, border_color=self.text_muted, text_color=self.text_muted, font=("Arial", 13, "bold"), command=lambda a=acc: self.open_edit_window(a)).pack(side="left", fill="x", expand=True, padx=4)
            ctk.CTkButton(btn_frame, text=self.t("delete"), width=70, height=36, fg_color="transparent", hover_color="#4c0519", border_width=1, border_color="#e11d48", text_color="#e11d48", font=("Arial", 13, "bold"), command=lambda a=acc: self.delete_account(a)).pack(side="left", fill="x", expand=True, padx=4)
            ctk.CTkButton(btn_frame, text=self.t("play"), width=70, height=36, fg_color="#10b981", hover_color="#059669", text_color="white", font=("Arial", 13, "bold"), command=lambda a=acc: self.play_account(a)).pack(side="left", fill="x", expand=True, padx=4)

            self._make_draggable(card, acc)
            self._card_frames.append(card)
        self._rearrange_grid()

    def delete_account(self, acc):
        if messagebox.askyesno(self.t("confirm"), self.t("confirm_delete", user=acc['username'])):
            self.accounts.remove(acc); self.save_accounts(); self.refresh_list()

    def open_add_window(self): self._open_account_form_window(acc=None)
    def open_edit_window(self, acc): self._open_account_form_window(acc=acc)

    def _open_account_form_window(self, acc=None):
        is_edit = acc is not None
        dialog = ctk.CTkToplevel(self)
        dialog.title(self.t("form_edit_title") if is_edit else self.t("form_add_title"))
        w, h = 480, 700
        dialog.geometry(f"{w}x{h}+{int((self.winfo_screenwidth()/2)-(w/2))}+{int((self.winfo_screenheight()/2)-(h/2))}")
        dialog.configure(fg_color=self.bg_color); dialog.transient(self); dialog.grab_set()

        ctk.CTkLabel(dialog, text=self.t("form_edit_title") if is_edit else self.t("form_add_title"), font=("Arial", 28, "bold"), text_color="#38bdf8").pack(pady=(30, 5), anchor="w", padx=40)
        ctk.CTkLabel(dialog, text=self.t("form_desc"), font=("Arial", 14), text_color=self.text_muted).pack(anchor="w", padx=40, pady=(0, 25))

        f = ctk.CTkFrame(dialog, fg_color="transparent"); f.pack(fill="both", expand=True, padx=40)
        cfg = {"width": 400, "height": 45, "fg_color": self.card_color, "border_color": self.border_color, "corner_radius": 8, "font": ("Arial", 15)}

        ctk.CTkLabel(f, text=self.t("username"), font=("Arial", 15, "bold"), text_color="white").pack(anchor="w", pady=(5, 5))
        e_user = ctk.CTkEntry(f, **cfg); e_user.pack()
        ctk.CTkLabel(f, text=self.t("password"), font=("Arial", 15, "bold"), text_color="white").pack(anchor="w", pady=(20, 5))
        e_pass = ctk.CTkEntry(f, show="*", **cfg); e_pass.pack()
        ctk.CTkLabel(f, text=self.t("riot_id"), font=("Arial", 15, "bold"), text_color="white").pack(anchor="w", pady=(20, 5))
        e_riot = ctk.CTkEntry(f, placeholder_text="Ex: Player#VN1", **cfg); e_riot.pack()

        if is_edit:
            e_user.insert(0, acc["username"])
            try: e_pass.insert(0, cipher.decrypt(acc["password"].encode()).decode())
            except: pass
            e_riot.insert(0, acc.get("display_name", ""))

        ctk.CTkLabel(f, text=self.t("choose_game"), font=("Arial", 15, "bold"), text_color="white").pack(anchor="w", pady=(25, 10))
        v_lol = ctk.StringVar(value="LoL" if is_edit and "LoL" in acc["games"] else "off")
        v_val = ctk.StringVar(value="Valorant" if is_edit and "Valorant" in acc["games"] else "off")
        ctk.CTkCheckBox(f, text="League of Legends" if self.lang=="en" else "Liên Minh Huyền Thoại", font=("Arial", 15), variable=v_lol, onvalue="LoL", offvalue="off", fg_color="#38bdf8").pack(anchor="w", pady=8)
        ctk.CTkCheckBox(f, text="Valorant", font=("Arial", 15), variable=v_val, onvalue="Valorant", offvalue="off", fg_color="#fb7185").pack(anchor="w", pady=8)

        def save():
            u, p, r = e_user.get().strip(), e_pass.get(), e_riot.get().strip()
            g = [gm for gm, val in [("LoL", v_lol.get()), ("Valorant", v_val.get())] if val != "off"]
            if u and p and r and g:
                enc = cipher.encrypt(p.encode()).decode()
                if is_edit: acc.update({"username": u, "password": enc, "display_name": r, "games": g})
                else: self.accounts.append({"username": u, "password": enc, "display_name": r, "games": g})
                self.save_accounts(); self.refresh_list(); dialog.destroy()
            else: messagebox.showerror(self.t("err_title"), self.t("err_fill"))
        ctk.CTkButton(dialog, text=self.t("save_btn"), width=400, height=50, fg_color="#3b82f6", font=("Arial", 16, "bold"), command=save).pack(pady=(10, 30))

    def play_account(self, acc):
        if len(acc["games"]) == 2:
            d = ctk.CTkToplevel(self); d.title(self.t("select_game_title"))
            w, h = 520, 380; d.geometry(f"{w}x{h}+{int((self.winfo_screenwidth()/2)-(w/2))}+{int((self.winfo_screenheight()/2)-(h/2))}")
            d.configure(fg_color=self.bg_color); d.transient(self); d.grab_set()
            def sel(g): d.destroy(); self.start_automation(acc, g)
            ctk.CTkLabel(d, text=self.t("select_game_title"), font=("Arial", 24, "bold"), text_color="#38bdf8").pack(pady=(20, 5))
            ctk.CTkLabel(d, text=self.t("select_game_desc"), font=("Arial", 14), text_color=self.text_muted).pack()
            ctk.CTkLabel(d, text=f"{self.t('account')} {acc['username']} • {acc.get('display_name', '')}", font=("Arial", 12, "italic"), text_color=self.text_muted).pack(pady=(5, 15))
            fr = ctk.CTkFrame(d, fg_color="transparent"); fr.pack(fill="both", expand=True, padx=20, pady=10)
            
            for gm, clr, ic in [("LoL", "#fcd34d", "⚔️"), ("Valorant", "#fb7185", "🎯")]:
                c = ctk.CTkFrame(fr, width=220, height=240, fg_color=self.card_color, border_width=1, border_color=clr)
                c.pack(side="left", padx=10, expand=True); c.pack_propagate(False)
                try: img = Image.open(self.get_resource_path(f"assets/{gm.lower()}_icon.png")); ctk.CTkLabel(c, text="", image=ctk.CTkImage(img, size=(80, 80))).pack(pady=(15, 10))
                except: ctk.CTkLabel(c, text=ic, font=("Arial", 50)).pack(pady=(15, 10))
                ctk.CTkLabel(c, text=gm, font=("Arial", 16, "bold"), text_color=clr).pack()
                ctk.CTkButton(c, text=self.t("play_now"), fg_color=clr, text_color="black" if gm=="LoL" else "white", font=("Arial", 12, "bold"), command=lambda g=gm: sel(g)).pack(pady=(20,0))
        else: self.start_automation(acc, acc["games"][0])

    def start_automation(self, acc, game):
        # Đã truyền callback set_status vào RiotAutomator
        pwd = cipher.decrypt(acc["password"].encode()).decode()
        automator = RiotAutomator(acc["username"], pwd, game, display_name=acc.get("display_name", ""), status_callback=self.set_status)
        def run():
            try:
                automator.execute_flow()
                self.automation_just_completed = True
                self.after(5000, lambda: setattr(self, 'automation_just_completed', False))
                self.after(3000, lambda: self.set_status("status_idle", 0.0)) # Reset lại UI sau 3s hoàn thành
            except Exception as e:
                self.set_status("status_err", 1.0, err=e)
                self.progress_bar.configure(progress_color="#e11d48") # Báo đỏ nếu có lỗi
                self.after(500, lambda: messagebox.showerror(self.t("err_title"), f"Error:\n{e}"))
        threading.Thread(target=run, daemon=False).start()