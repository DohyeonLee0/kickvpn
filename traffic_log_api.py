# traffic_log_api.py - 트래픽 로그 기록/조회 API (FastAPI 기반)

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3, jwt
from datetime import datetime

SECRET_KEY = "supersecretkey"
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 초기화
conn = sqlite3.connect("vpn_users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    target TEXT,
    timestamp TEXT,
    server_type TEXT
)''')
conn.commit()

# 모델
class LogEntry(BaseModel):
    token: str
    target: str
    server_type: str

# JWT 검증 함수
def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except:
        return None

# 로그 기록 API
@app.post("/log")
def save_log(log: LogEntry):
    email = verify_token(log.token)
    if not email:
        return JSONResponse(content={"error": "Invalid token"}, status_code=401)

    cursor.execute("INSERT INTO logs (email, target, timestamp, server_type) VALUES (?, ?, ?, ?)",
                   (email, log.target, datetime.now().isoformat(), log.server_type))
    conn.commit()
    return {"message": "Log saved"}

# 로그 조회 API
@app.get("/logs")
def get_logs(token: str):
    email = verify_token(token)
    if not email:
        return JSONResponse(content={"error": "Invalid token"}, status_code=401)

    cursor.execute("SELECT target, timestamp, server_type FROM logs WHERE email = ? ORDER BY id DESC LIMIT 50", (email,))
    rows = cursor.fetchall()
    return {"logs": [{"target": r[0], "time": r[1], "server": r[2]} for r in rows]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)