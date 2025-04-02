# relay_server.py - VPN 중계 서버 (HTTP + HTTPS 지원 프록시)

import socket
import threading
import sqlite3
import jwt

# 설정
RELAY_HOST = '0.0.0.0'
RELAY_PORT = 9999
SECRET_KEY = "supersecretkey"
TRIAL_LIMIT_MB = 500

# DB 연결
db = sqlite3.connect("vpn_users.db", check_same_thread=False)
cursor = db.cursor()

# 유틸 함수들
def get_user(email: str):
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    return cursor.fetchone()

def update_usage(email: str, amount_mb: int):
    cursor.execute("UPDATE users SET usage_mb = usage_mb + ? WHERE email = ?", (amount_mb, email))
    db.commit()

def is_blocked(user):
    usage = user[4]
    premium = user[3]
    return not premium and usage >= TRIAL_LIMIT_MB

# 양방향 데이터 중계
def proxy_data(source, destination):
    try:
        while True:
            data = source.recv(4096)
            if not data:
                break
            destination.sendall(data)
    except:
        pass

# 클라이언트 처리
def handle_client(client_socket):
    try:
        # 1. 인증: 첫 메시지 = JWT 토큰
        token = client_socket.recv(1024).decode()
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            email = payload.get("sub")
            user = get_user(email)
            if not user or is_blocked(user):
                client_socket.send(b"BLOCKED")
                client_socket.close()
                return
        except Exception:
            client_socket.send(b"INVALID TOKEN")
            client_socket.close()
            return

        client_socket.send(b"OK")

        # 2. 목적지 주소 수신 (예: google.com:443)
        dest_info = client_socket.recv(1024).decode().strip()
        if ':' not in dest_info:
            client_socket.send(b"INVALID DEST")
            client_socket.close()
            return

        dest_host, dest_port = dest_info.split(':')
        dest_port = int(dest_port)

        # 3. 목적지 연결
        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote.connect((dest_host, dest_port))
        client_socket.send(b"CONNECTED")

        # 4. 트래픽 중계 시작
        t1 = threading.Thread(target=proxy_data, args=(client_socket, remote))
        t2 = threading.Thread(target=proxy_data, args=(remote, client_socket))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # 5. 간단 트래픽 계산 (1MB씩 증가)
        update_usage(email, 1)

    except Exception as e:
        print(f"[!] 에러: {e}")
    finally:
        client_socket.close()

# 서버 시작
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((RELAY_HOST, RELAY_PORT))
    server.listen(5)
    print(f"[+] VPN 중계 서버 실행 중 (HTTPS 지원): {RELAY_HOST}:{RELAY_PORT}")

    while True:
        client, addr = server.accept()
        print(f"[*] 접속됨: {addr}")
        threading.Thread(target=handle_client, args=(client,)).start()

if __name__ == '__main__':
    start_server()