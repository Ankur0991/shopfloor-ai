from fastapi import Depends, HTTPException, status, APIRouter, Response
from typing import Optional
from app import schemas,models,database
from sqlalchemy.orm import Session


router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=schemas.UserOut, status_code= status.HTTP_201_CREATED)
def create_user(user_data : schemas.UserCreate, db : Session = Depends(database.get_db)):
    user_exists = db.query(models.User).filter(models.User.email == user_data.email).first()
    if user_exists is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail= f"User with email = {user_data.email} already exists")
    new_user = models.User(**user_data.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.get("/{id}", response_model = schemas.UserOut, status_code= status.HTTP_200_OK)
def get_user(id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail= f"User with id = {id} not found")
    return user