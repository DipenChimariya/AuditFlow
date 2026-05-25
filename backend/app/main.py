from fastapi import FastAPI

from .database import engine
from .models import Base

from .routes import clients
from .routes import invoice

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AuditFlow"
)

app.include_router(clients.router)
app.include_router(invoice.router)