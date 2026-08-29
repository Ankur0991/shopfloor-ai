from fastapi import FastAPI
from app import models, database
from app.routers import machines, readings, users, auth


app = FastAPI()

models.Base.metadata.create_all(bind=database.engine)


app.include_router(machines.router)
app.include_router(readings.router)
app.include_router(users.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"status" : "OK"}
