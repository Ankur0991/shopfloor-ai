from fastapi import Depends, status, HTTPException
from jose import JWTError
import jwt
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY: str = ""
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES : int = 60 