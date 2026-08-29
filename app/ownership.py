from fastapi import HTTPException, status
from app import models, schemas
from sqlalchemy.orm import Session


def check_machine_existence(machine_id: int, db: Session):
    existing_machine: schemas.MachineOut = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if existing_machine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Machine doesnt exist")
    return existing_machine

def get_owned_machine(machine_id: int, current_user: models.User, db: Session):
    existing_machine: schemas.MachineOut = check_machine_existence(machine_id=machine_id, db= db)
    if existing_machine.created_by != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Machine was not created by you")
    return existing_machine