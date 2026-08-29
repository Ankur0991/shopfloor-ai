from sqlalchemy import Boolean, Integer, String, Float, ForeignKey, DateTime, Column
from sqlalchemy.sql import func
from .database import Base


class Machine(Base):
    __tablename__ = "machines"
    id = Column(Integer, primary_key = True, nullable = False)
    name = Column(String, nullable=False)
    line = Column(String, nullable=False)
    location = Column(String, nullable=True)
    installed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id = Column(Integer, primary_key = True, nullable = False)
    machine_id = Column(Integer, ForeignKey("machines.id",ondelete="CASCADE"), nullable=False)
    metric = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key = True, nullable = False)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
