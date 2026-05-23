from fastapi import FastAPI
from .database import engine
from .models import Base

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {"message": "AuditFlow API Running"}