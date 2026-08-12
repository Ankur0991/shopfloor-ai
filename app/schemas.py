from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime
from typing import Optional

class MachineBase(BaseModel):
    name: str
    line: str
    location: Optional[str] = None
    installed_at : Optional[datetime]= None

class MachineCreate(MachineBase):
    pass

class MachineUpdate(MachineBase):
    pass

class MachineOut(MachineBase):
    id: int
    created_at : datetime
    model_config = ConfigDict(from_attributes=True)

class SensorReadingBase(BaseModel):
    machine_id: int
    metric: str
    value: float
    unit: str

class SensorReadingCreate(SensorReadingBase):
    pass

class SensorReadingOut(SensorReadingBase):
    recorded_at: datetime
    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None