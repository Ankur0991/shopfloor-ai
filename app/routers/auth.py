
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app import models, database, schemas, utils, oauth2
from sqlalchemy.orm import Session


router = APIRouter(tags=["Authentication"])

@router.post("/login", status_code = status.HTTP_200_OK, response_model= schemas.Token)
def user_auth(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")
    if not utils.verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Denied")
    
    jwt_token = oauth2.create_access_token(data = {"user_id": user.id}) 
    return {"access_token" : jwt_token, "token_type" : "bearer"}