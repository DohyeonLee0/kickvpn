# relay_proxy_server.py - HTTP CONNECT 지원 브라우저용 프록시 서버

import socket
import threading

LISTEN_HOST = '0.0.0.0'
LISTEN_PORT = 9009

# HTTP CONNECT 요청 처리

def handle_client(client_socket):
    try:
        request_line = client_socket.recv(1024).decode(errors='ignore')
        if not request_line.startswith('CONNECT'):
            client_socket.send(b"HTTP/1.1 405 Method Not Allowed\r\n\r\n")
            client_socket.close()
            return

        # CONNECT www.example.com:443 HTTP/1.1
        dest = request_line.split()[1]
        host, port = dest.split(':')
        port = int(port)

        # 목적지에 연결 시도
        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote.connect((host, port))

        # 연결 성공 응답 보내기
        client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")

        # 데이터 중계 시작
        threading.Thread(target=pipe, args=(client_socket, remote)).start()
        threading.Thread(target=pipe, args=(remote, client_socket)).start()

    except Exception as e:
        print(f"[!] 에러: {e}")
        client_socket.close()

# 양방향 소켓 파이프

def pipe(source, dest):
    try:
        while True:
            data = source.recv(4096)
            if not data:
                break
            dest.sendall(data)
    except:
        pass
    finally:
        source.close()
        dest.close()

# 프록시 서버 실행

def start_proxy():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((LISTEN_HOST, LISTEN_PORT))
    server.listen(50)
    print(f"[+] 브라우저 프록시 서버 실행 중: {LISTEN_HOST}:{LISTEN_PORT}")

    while True:
        client, addr = server.accept()
        print(f"[*] 연결됨: {addr}")
        threading.Thread(target=handle_client, args=(client,)).start()

if __name__ == '__main__':
    start_proxy()