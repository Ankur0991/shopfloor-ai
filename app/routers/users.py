from fastapi import Depends, HTTPException, status, APIRouter
from app import schemas,models,database, utils
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=schemas.UserOut, status_code= status.HTTP_201_CREATED)
def create_user(user_data : schemas.UserCreate, db : Session = Depends(database.get_db)):
    user_exists = db.query(models.User).filter(models.User.email == user_data.email).first()
    if user_exists is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail= f"User with email = {user_data.email} already exists")
    new_user = models.User(email= user_data.email, 
                           hashed_password= utils.hash_password(user_data.password), 
                           full_name= user_data.full_name)
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"User with email = {user_data.email} already exists")
    db.refresh(new_user)
    return new_user


@router.get("/{id}", response_model = schemas.UserOut, status_code= status.HTTP_200_OK)
def get_user(id: int, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail= f"User with id = {id} not found")
    return user