from fastapi import Depends, HTTPException, status, APIRouter, Response
from typing import Optional
from app import schemas,models,database
from sqlalchemy.orm import Session


router = APIRouter(prefix="/readings", tags=["Sensor_Readings"])


#Create new Sensor data
@router.post("/", response_model=schemas.SensorReadingOut, status_code=status.HTTP_201_CREATED)
def sensor_new_data(SensorData : schemas.SensorReadingCreate, db: Session = Depends(database.get_db)):
    machine_exists = db.query(models.Machine).filter(models.Machine.id == SensorData.machine_id).first()
    if machine_exists == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail= f"Machine with id ={SensorData.machine_id} not found")
    new_data = models.SensorReading(**SensorData.model_dump())
    db.add(new_data)
    db.commit()
    db.refresh(new_data) 
    return new_data


#Get all sensor data moved to machine.py file


#Get single Sensor data using its ID
@router.get("/{id}", response_model=schemas.SensorReadingOut, status_code=status.HTTP_200_OK)
def single_sensor_data(id: int, db: Session = Depends(database.get_db)):
    data = db.query(models.SensorReading).filter(models.SensorReading.id == id).first()
    if data == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"Sensor with id = {id} not found")
    return data


#Delete Sensor data with particular ID
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_data(id: int, db: Session = Depends(database.get_db)):
    deleted_data_count = db.query(models.SensorReading).filter(models.SensorReading.id == id).delete(synchronize_session=False)
    if deleted_data_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail=f"Sensor with id = {id} not found")
    db.commit()
    return Response(status_code = status.HTTP_204_NO_CONTENT)