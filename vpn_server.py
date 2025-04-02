# vpn_server.py - FastAPI 서버 (회원가입/로그인/리워드 + 추천 + 트래픽 리밋)

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import sqlite3
import uuid

# 설정
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
TRIAL_LIMIT_MB = 500
REWARD_MB = 100

# DB 연결
db = sqlite3.connect("vpn_users.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password_hash TEXT,
    is_premium INTEGER,
    usage_mb INTEGER,
    referral_code TEXT,
    referred_by TEXT
)
''')
db.commit()

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 유틸 함수들
def get_user(email: str):
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    return cursor.fetchone()

def get_user_by_referral(code: str):
    cursor.execute("SELECT * FROM users WHERE referral_code = ?", (code,))
    return cursor.fetchone()

def verify_password(plain_password, hashed):
    return pwd_context.verify(plain_password, hashed)

def hash_password(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# 회원가입
class RegisterRequest(BaseModel):
    email: str
    password: str
    referral_code: str = None

@app.post("/register")
def register(req: RegisterRequest):
    if get_user(req.email):
        raise HTTPException(status_code=400, detail="User already exists")
    password_hash = hash_password(req.password)
    code = str(uuid.uuid4())[:8]

    referred_by = None
    usage_mb = 0

    if req.referral_code:
        ref_user = get_user_by_referral(req.referral_code)
        if ref_user:
            referred_by = req.referral_code
            usage_mb += REWARD_MB
            ref_usage = max(ref_user[4] - REWARD_MB, 0)
            cursor.execute("UPDATE users SET usage_mb = ? WHERE referral_code = ?", (ref_usage, req.referral_code))
        else:
            raise HTTPException(status_code=400, detail="Invalid referral code")

    cursor.execute("INSERT INTO users (email, password_hash, is_premium, usage_mb, referral_code, referred_by) VALUES (?, ?, 0, ?, ?, ?)",
                   (req.email, password_hash, usage_mb, code, referred_by))
    db.commit()
    return {"msg": "User created", "referral_code": code, "referred_by": referred_by or ""}

# 로그인
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user[2]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user[1]})
    return {"access_token": access_token, "token_type": "bearer"}

# 광고 리워드 지급 (100MB)
@app.post("/reward/ad")
def reward_ad(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user(email)
    new_usage = max(user[4] - REWARD_MB, 0)
    cursor.execute("UPDATE users SET usage_mb = ? WHERE email = ?", (new_usage, email))
    db.commit()
    return {"msg": f"{REWARD_MB}MB rewarded via ad"}

# 사용량 확인
@app.get("/me")
def get_me(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user(email)
    usage_left = max(TRIAL_LIMIT_MB - user[4], 0)
    blocked = usage_left <= 0 and not user[3]  # not premium and over limit
    return {
        "email": user[1],
        "usage_used": user[4],
        "usage_left": usage_left,
        "is_premium": bool(user[3]),
        "blocked": blocked
    }