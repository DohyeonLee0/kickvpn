# vpn_client.py - 서버 선택 (무료/프리미엄) 지원

import socket
import requests

API_BASE = "http://127.0.0.1:8000"
FREE_VPN_PORT = 9001
PREMIUM_VPN_PORT = 9999
VPN_HOST = "127.0.0.1"

email = input("이메일: ")
password = input("비밀번호: ")

# 1. 로그인 → JWT 발급
resp = requests.post(f"{API_BASE}/login", data={"username": email, "password": password})
if resp.status_code != 200:
    print("[!] 로그인 실패", resp.text)
    exit()
token = resp.json()["access_token"]
print("[+] 로그인 성공, 토큰 발급 완료")

# 2. 사용자 정보 확인 (프리미엄 여부)
me = requests.get(f"{API_BASE}/me", params={"token": token})
is_premium = me.json()["is_premium"]

# 3. 연결할 서버 선택
print("[서버 선택]")
print("1. 무료 서버")
print("2. 프리미엄 서버")
choice = input("선택 (1 또는 2): ")

if choice == "1":
    port = FREE_VPN_PORT
elif choice == "2":
    if not is_premium:
        print("[!] 프리미엄 유저만 사용 가능합니다.")
        exit()
    port = PREMIUM_VPN_PORT
else:
    print("[!] 잘못된 입력")
    exit()

# 4. VPN 서버 접속
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((VPN_HOST, port))
s.send(token.encode())

auth_reply = s.recv(1024)
if auth_reply == b"OK":
    print("[+] VPN 서버 인증 성공")
elif auth_reply == b"BLOCKED":
    print("[!] 차단된 사용자 (트래픽 초과)")
    s.close()
    exit()
elif auth_reply == b"PREMIUM_NOT_ALLOWED_HERE":
    print("[!] 프리미엄 유저는 무료 서버에 접속할 수 없습니다")
    s.close()
    exit()
else:
    print("[!] 인증 실패")
    s.close()
    exit()

# 5. 목적지 주소 입력
target = input(">> 접속할 목적지 (예: google.com:80): ")
s.send(target.encode())

proxy_reply = s.recv(1024)
if proxy_reply != b"CONNECTED":
    print("[!] 목적지 연결 실패:", proxy_reply.decode())
    s.close()
    exit()
print("[+] 목적지 연결 완료")

# 6. 메시지 전송 루프
while True:
    msg = input(">> 보낼 메시지 (exit 입력 시 종료): ")
    if msg.strip().lower() == "exit":
        break
    s.send(msg.encode())
    try:
        reply = s.recv(4096)
        print("[서버 응답]:", reply.decode(errors="ignore"))
    except:
        print("[!] 응답 수신 실패")

s.close()
print("[+] 연결 종료")