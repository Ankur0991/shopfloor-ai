from fastapi import Depends, HTTPException, status, APIRouter, Response, Query
from app import schemas,models,database, oauth2, ownership
from sqlalchemy.orm import Session
from typing import Optional


router = APIRouter(prefix="/machines", tags=["Machines"])

#Create new Machine
@router.post("/", response_model=schemas.MachineOut, status_code=status.HTTP_201_CREATED)
def new_machine(NewMachinedata : schemas.MachineCreate, 
                current_user: models.User = Depends(oauth2.get_current_user), 
                db: Session = Depends(database.get_db)):
    new_machine: schemas.MachineOut = models.Machine(**NewMachinedata.model_dump(), created_by = current_user.id)
    db.add(new_machine)
    db.commit()
    db.refresh(new_machine) 
    return new_machine


#Gets list of all machine created by me
@router.get("/mine", status_code=status.HTTP_200_OK, response_model= list[schemas.MachineOut])
def get_my_machines(current_user: models.User = Depends(oauth2.get_current_user), db: Session = Depends(database.get_db)):
    my_machines = db.query(models.Machine).filter(models.Machine.created_by == current_user.id).all()
    if my_machines is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No machines were created by User with ID= {current_user.id}")
    return my_machines


#Get all Machine data
@router.get("/", response_model=list[schemas.MachineOut], status_code=status.HTTP_200_OK)
def get_all_machines(search_str: Optional[str] = None,
                     limit_number: int = Query(10, ge=1, le=100), 
                     skip: int = 0, db: Session = Depends(database.get_db)):
    query = db.query(models.Machine)
    if search_str:
        query = query.filter(models.Machine.name.ilike(f"%{search_str}%"))
    machine_list = query.order_by(models.Machine.id.desc()).offset(skip).limit(limit_number).all()
    return machine_list


#Get single Machine data using its ID
@router.get("/{id}", response_model=schemas.MachineOut, status_code=status.HTTP_200_OK)
def get_single_machine(id: int, db: Session = Depends(database.get_db)):
    machine = db.query(models.Machine).filter(models.Machine.id == id).first()
    if machine == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"Machine with id = {id} not found")
    return machine


#Update Machine with a particular ID
@router.put("/{id}", response_model=schemas.MachineOut, status_code=status.HTTP_200_OK)
def update_machine(id: int, machinedata : schemas.MachineCreate, 
                   current_user: models.User = Depends(oauth2.get_current_user), 
                   db: Session = Depends(database.get_db)):
    machine_to_update = ownership.get_owned_machine(machine_id= id, current_user=current_user, db=db)
    for field, value in machinedata.model_dump().items():
        setattr(machine_to_update, field, value)
    db.commit()
    db.refresh(machine_to_update)
    return machine_to_update


#Delete Machine with particular ID
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_machine(id: int, current_user: models.User = Depends(oauth2.get_current_user), db: Session = Depends(database.get_db)):
    machine_to_delete = ownership.get_owned_machine(machine_id= id, current_user= current_user, db= db)
    db.delete(machine_to_delete)
    db.commit()
    return Response(status_code = status.HTTP_204_NO_CONTENT)


#Get all Sensor data
@router.get("/{machine_id}/readings", response_model=list[schemas.SensorReadingOut], status_code=status.HTTP_200_OK)
def get_all_data(machine_id : int, metric: Optional[str] = None, 
                 limit_number: int = Query(50, ge=1, le=1000), 
                 db: Session = Depends(database.get_db)):
    machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if machine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail= f"Machine with id = {machine_id} not found")
    query = db.query(models.SensorReading).filter(models.SensorReading.machine_id == machine_id)
    if metric is not None:
        query = db.query(models.SensorReading).filter(models.SensorReading.metric == metric)
        
    return query.order_by(models.SensorReading.recorded_at.desc()).limit(limit_number).all()
    