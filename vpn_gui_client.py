# vpn_gui_client.py - 접속 이력 조회 탭 추가 (트래픽 로그 표시)

import customtkinter as ctk
import socket
import requests
import time
import subprocess
from tkinter import messagebox

API_BASE = "http://127.0.0.1:8000"
LOG_API = "http://127.0.0.1:8010"
FREE_PORT = 9001
PREMIUM_PORT = 9999
VPN_HOST = "127.0.0.1"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class VPNApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🔐 KickVPN")
        self.geometry("480x640")
        self.resizable(False, False)

        self.token = None
        self.sock = None
        self.is_premium = False
        self.usage_left = 0
        self.start_time = None

        self.status_label = ctk.CTkLabel(self, text="● 연결되지 않음", text_color="gray", font=("Arial", 14, "bold"))
        self.status_label.pack(pady=(20, 6))

        self.traffic_label = ctk.CTkLabel(self, text="사용량: -", font=("Arial", 13))
        self.traffic_label.pack(pady=(2, 2))

        self.timer_label = ctk.CTkLabel(self, text="연결 시간: 00:00:00", font=("Arial", 13))
        self.timer_label.pack(pady=(2, 14))

        self.email_entry = ctk.CTkEntry(self, placeholder_text="이메일", width=280)
        self.email_entry.pack(pady=6)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="비밀번호", show="*", width=280)
        self.password_entry.pack(pady=6)

        self.login_button = ctk.CTkButton(self, text="로그인", command=self.login)
        self.login_button.pack(pady=(10, 18))

        self.server_option = ctk.StringVar(value="free")
        self.radio_free = ctk.CTkRadioButton(self, text="무료 서버", variable=self.server_option, value="free")
        self.radio_premium = ctk.CTkRadioButton(self, text="프리미엄 서버", variable=self.server_option, value="premium")
        self.radio_free.pack()
        self.radio_premium.pack(pady=(0, 10))

        self.target_entry = ctk.CTkEntry(self, placeholder_text="접속할 목적지 (예: google.com:443)", width=300)
        self.target_entry.pack(pady=10)
        self.target_entry.insert(0, "google.com:443")

        self.connect_button = ctk.CTkButton(self, text="🌐 VPN 연결", command=self.connect, state="disabled")
        self.connect_button.pack(pady=6)

        self.disconnect_button = ctk.CTkButton(self, text="연결 종료", command=self.disconnect, state="disabled")
        self.disconnect_button.pack()

        self.reward_entry = ctk.CTkEntry(self, placeholder_text="추천 코드 입력", width=240)
        self.reward_entry.pack(pady=(20, 4))

        self.reward_button = ctk.CTkButton(self, text="보상 받기", command=self.claim_reward)
        self.reward_button.pack()

        # 접속 로그 조회
        self.log_button = ctk.CTkButton(self, text="📊 접속 이력 보기", command=self.load_logs)
        self.log_button.pack(pady=(25, 6))

        self.log_textbox = ctk.CTkTextbox(self, width=400, height=180)
        self.log_textbox.pack(pady=6)
        self.log_textbox.insert("0.0", "[접속 이력 표시 영역]")
        self.log_textbox.configure(state="disabled")

    def enable_proxy(self):
        port = PREMIUM_PORT if self.server_option.get() == "premium" else FREE_PORT
        subprocess.run(["networksetup", "-setwebproxy", "Wi-Fi", VPN_HOST, str(port)])
        subprocess.run(["networksetup", "-setsecurewebproxy", "Wi-Fi", VPN_HOST, str(port)])

    def disable_proxy(self):
        subprocess.run(["networksetup", "-setwebproxystate", "Wi-Fi", "off"])
        subprocess.run(["networksetup", "-setsecurewebproxystate", "Wi-Fi", "off"])

    def login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()
        try:
            res = requests.post(f"{API_BASE}/login", data={"username": email, "password": password})
            res.raise_for_status()
            self.token = res.json()["access_token"]
            info = requests.get(f"{API_BASE}/me", params={"token": self.token}).json()
            self.is_premium = info["is_premium"]
            self.usage_left = info["usage_left"]
            self.traffic_label.configure(text=f"사용량: {info['usage_used']}MB / 500MB")
            self.status_label.configure(text="● 로그인 성공", text_color="green")
            self.connect_button.configure(state="normal")
        except Exception as e:
            messagebox.showerror("로그인 오류", f"로그인 실패: {e}")

    def claim_reward(self):
        code = self.reward_entry.get().strip()
        if not code or not self.token:
            messagebox.showwarning("오류", "추천코드 또는 로그인 상태를 확인하세요.")
            return

        try:
            res = requests.post(f"{API_BASE}/reward", params={"token": self.token, "code": code})
            if res.status_code == 200:
                info = res.json()
                self.traffic_label.configure(text=f"사용량: {info['usage_used']}MB / 500MB")
                messagebox.showinfo("보상 완료", f"+{info['reward']}MB 보상받음!")
            else:
                messagebox.showerror("보상 실패", res.text)
        except Exception as e:
            messagebox.showerror("에러", str(e))

    def load_logs(self):
        if not self.token:
            messagebox.showwarning("로그인 필요", "먼저 로그인 해주세요.")
            return
        try:
            res = requests.get(f"{LOG_API}/logs", params={"token": self.token})
            logs = res.json().get("logs", [])
            self.log_textbox.configure(state="normal")
            self.log_textbox.delete("1.0", "end")
            for log in logs:
                line = f"[{log['time']}] {log['target']}  ({log['server']})\n"
                self.log_textbox.insert("end", line)
            self.log_textbox.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("조회 오류", str(e))

    def connect(self):
        port = PREMIUM_PORT if self.server_option.get() == "premium" else FREE_PORT
        if self.server_option.get() == "premium" and not self.is_premium:
            messagebox.showerror("오류", "프리미엄 사용자만 이용 가능합니다.")
            return

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((VPN_HOST, port))
            self.sock.send(self.token.encode())
            auth_reply = self.sock.recv(1024)
            if auth_reply != b"OK":
                raise Exception(auth_reply.decode())

            target = self.target_entry.get()
            self.sock.send(target.encode())
            proxy_reply = self.sock.recv(1024)
            if proxy_reply != b"CONNECTED":
                raise Exception(proxy_reply.decode())

            label = "프리미엄" if self.server_option.get() == "premium" else "무료"
            self.status_label.configure(text=f"● 연결됨 ({label} 서버)", text_color="deepskyblue")
            self.connect_button.configure(state="disabled")
            self.disconnect_button.configure(state="normal")

            self.enable_proxy()

            self.start_time = time.time()
            self.update_timer()

        except Exception as e:
            messagebox.showerror("연결 오류", str(e))
            if self.sock:
                self.sock.close()
            self.status_label.configure(text="● 연결 실패", text_color="gray")

    def update_timer(self):
        if self.start_time and self.sock:
            elapsed = int(time.time() - self.start_time)
            h = elapsed // 3600
            m = (elapsed % 3600) // 60
            s = elapsed % 60
            self.timer_label.configure(text=f"연결 시간: {h:02}:{m:02}:{s:02}")
            self.after(1000, self.update_timer)

    def disconnect(self):
        if self.sock:
            self.sock.close()
            self.sock = None
        self.disable_proxy()
        self.status_label.configure(text="● 연결종료", text_color="gray")
        self.disconnect_button.configure(state="disabled")
        self.connect_button.configure(state="normal")
        self.timer_label.configure(text="연결 시간: 00:00:00")

if __name__ == '__main__':
    app = VPNApp()
    app.mainloop()