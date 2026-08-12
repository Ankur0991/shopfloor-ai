from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DARABASE_URL = "postgresql://postgres:ank@localhost/shopfloor"

engine = create_engine(SQLALCHEMY_DARABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()