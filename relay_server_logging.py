# relay_server_logging.py - 목적지 요청 + 로그 전송 포함 중계 서버

import socket
import threading
import requests
import jwt

LISTEN_HOST = '0.0.0.0'
LISTEN_PORT = 9999
LOG_API = 'http://127.0.0.1:8010/log'
SECRET_KEY = 'supersecretkey'

# 인증 및 사용자 추출
def get_email_from_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload.get("sub")
    except:
        return None

# 연결 처리
def handle_client(client_socket):
    try:
        token = client_socket.recv(1024).decode()
        email = get_email_from_token(token)
        if not email:
            client_socket.send(b"AUTH_FAIL")
            client_socket.close()
            return

        client_socket.send(b"OK")
        target = client_socket.recv(1024).decode()
        host, port = target.split(":")
        port = int(port)

        try:
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.connect((host, port))
            client_socket.send(b"CONNECTED")

            # 로그 기록
            requests.post(LOG_API, json={
                "token": token,
                "target": target,
                "server_type": "premium"
            })

            # 파이프링크
            threading.Thread(target=pipe, args=(client_socket, remote)).start()
            threading.Thread(target=pipe, args=(remote, client_socket)).start()
        except:
            client_socket.send(b"FAILED")
            client_socket.close()

    except Exception as e:
        print(f"[!] 예외: {e}")
        client_socket.close()

# 데이터 중계
def pipe(src, dst):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            dst.sendall(data)
    except:
        pass
    finally:
        src.close()
        dst.close()

# 서버 시작
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((LISTEN_HOST, LISTEN_PORT))
    server.listen(100)
    print(f"[+] 로그 연동 중계 서버 실행 중: {LISTEN_HOST}:{LISTEN_PORT}")

    while True:
        client, addr = server.accept()
        threading.Thread(target=handle_client, args=(client,)).start()

if __name__ == '__main__':
    start_server()