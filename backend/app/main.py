from fastapi import FastAPI
from .database import engine
from .models import Base
from .routes import clients, invoice, inventory

# Initialize and generate all PostgreSQL database tables on server spin-up
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AuditFlow API Ecosystem",
    description="Centralized data processing routing pipeline for AuditFlow enterprise accounts.",
    version="1.0.0"
)

# ---- REGISTER ROUTING INSTANCES ----

app.include_router(clients.router)
app.include_router(invoice.router)
app.include_router(inventory.router)