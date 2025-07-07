import os, datetime
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from passlib.hash import bcrypt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

ALGORITHM = "HS256"
SECRET = os.getenv("JWT_SECRET")
security = HTTPBearer()

def create_token():
    payload = {"sub": "admin", "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=12)}
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)

def admin_login(email: str, password: str):
    if email == os.getenv("ADMIN_EMAIL") and bcrypt.verify(password, os.getenv("ADMIN_PWD_HASH")):
        return create_token()
    raise HTTPException(status_code=401, detail="bad credentials")

def admin_only(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        jwt.decode(credentials.credentials, SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="token invalid")
