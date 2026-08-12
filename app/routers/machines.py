from fastapi import Depends, HTTPException, status, APIRouter, Response, Query
from app import schemas,models,database
from sqlalchemy.orm import Session
from typing import Optional


router = APIRouter(prefix="/machines", tags=["Machines"])

#Create new Machine
@router.post("/", response_model=schemas.MachineOut, status_code=status.HTTP_201_CREATED)
def new_machine(NewMachinedata : schemas.MachineCreate, db: Session = Depends(database.get_db)):
    new_machine = models.Machine(**NewMachinedata.model_dump())
    db.add(new_machine)
    db.commit()
    db.refresh(new_machine) 
    return new_machine


#Get all Machine data
@router.get("/", response_model=list[schemas.MachineOut], status_code=status.HTTP_200_OK)
def get_all_machines(search_str: Optional[str] = None, limit_number: int = Query(10, ge=1, le=100), skip: int = 0, db: Session = Depends(database.get_db)):
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
    else:
        return machine


#Update Machine with a particular ID
@router.put("/{id}", response_model=schemas.MachineOut, status_code=status.HTTP_200_OK)
def update_machine(id: int, Machinedata : schemas.MachineOut, db: Session = Depends(database.get_db)):
    machine_query = db.query(models.Machine).filter(models.Machine.id == id)
    machine_to_update = machine_query.first()
    if machine_to_update == None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                                detail=f"Machine with id = {id} not found")
    machine_query.update(Machinedata.dict(),synchronize_session=False)
    db.commit()
    db.refresh(machine_to_update)
    return machine_to_update


#Delete Machine with particular ID
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_machine(id: int, db: Session = Depends(database.get_db)):
    deleted_machine_count = db.query(models.Machine).filter(models.Machine.id == id).delete(synchronize_session=False)
    if deleted_machine_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"Machine with id = {id} not found")
    db.commit()
    return Response(status_code = status.HTTP_204_NO_CONTENT)


#Get all Sensor data
@router.get("/{machine_id}/readings", response_model=list[schemas.SensorReadingOut], status_code=status.HTTP_200_OK)
def get_all_data(machine_id : int, metric: Optional[str] = None, limit_number: int = Query(50, ge=1, le=100), db: Session = Depends(database.get_db)):
    query = db.query(models.Machine).filter(models.Machine.id == machine_id)
    if query is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail= f"Machine with id = {machine_id} not found")
    if metric is not None:
        query = query.filter(models.SensorReading.metric == metric)
        all_data = query.order_by(models.SensorReading.recorded_at.desc()).limit(limit_number).all()
    if all_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail= f"Machine with Sensor reading metric = {metric} was not found")
    return all_data