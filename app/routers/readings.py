from fastapi import Depends, HTTPException, status, APIRouter, Response
from typing import Optional
from app import schemas,models,database, oauth2, ownership
from sqlalchemy.orm import Session


router = APIRouter(prefix="/readings", tags=["Sensor_Readings"])


#Create new Sensor data
@router.post("/", response_model=schemas.SensorReadingOut, status_code=status.HTTP_201_CREATED)
def sensor_new_data(sensor_data : schemas.SensorReadingCreate, current_user : models.User = Depends(oauth2.get_current_user), db: Session = Depends(database.get_db)):
    ownership.check_machine_existence(machine_id=sensor_data.machine_id, db=db)
    new_data = models.SensorReading(**sensor_data.model_dump(), created_by = current_user.id)
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
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies = [Depends(oauth2.get_current_user)])
def delete_data(id: int, db: Session = Depends(database.get_db)):
    reading = db.query(models.SensorReading).filter(models.SensorReading.id == id).first()
    if reading is None:
        raise HTTPException(404, detail=f"Reading with id = {id} not found")
    db.delete(reading)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)