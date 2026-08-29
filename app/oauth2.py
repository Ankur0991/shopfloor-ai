from fastapi import Depends, status, HTTPException
import jwt
from app import schemas, database, models
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

unauth_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers={"WWW-Authenticate": "Bearer"}, detail="Unauthorized")

def create_access_token(data: dict, expiry_delta : timedelta | None = None):
    to_encode = data.copy()
    if expiry_delta:
        expiry = datetime.now(timezone.utc) + expiry_delta
    else: 
        expiry = datetime.now(timezone.utc) + timedelta(minutes = settings.access_token_expire_minutes)
    to_encode.update({"exp" : expiry})
    jwt_token = jwt.encode(to_encode, settings.secret_key, algorithm = settings.algorithm)
    return jwt_token

def verify_access_token(token : str):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms = [settings.algorithm])
        id : int = payload.get("user_id")
        if id is None:
            raise unauth_exception
        token_data = schemas.TokenData(id= id)
    except jwt.PyJWTError:
            raise unauth_exception
    return token_data

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
     token_data = verify_access_token(token)
     userData = db.query(models.User).filter(models.User.id == token_data.id).first()
     if userData is None:
          raise unauth_exception
     return userData