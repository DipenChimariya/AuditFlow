from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    pan_number = Column(String(20), unique=True, index=True) # Unique PAN for each client firm

    # ---- RECIPIOCAL RELATIONSHIP LINKS ----
    invoices = relationship("Invoice", back_populates="client", cascade="all, delete-orphan")
    # FIX: Added this missing link so that Inventory can back-populate cleanly!
    inventory_items = relationship("Inventory", back_populates="client", cascade="all, delete-orphan")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    vendor_name = Column(String(255), index=True, nullable=False)
    pan_number = Column(String(20), index=True) # This is the vendor's PAN (seller)
    invoice_number = Column(String(100), index=True)
    subtotal = Column(Numeric(precision=12, scale=2), default=0.00)
    vat = Column(Numeric(precision=12, scale=2), default=0.00)     
    total = Column(Numeric(precision=12, scale=2), default=0.00)
    
    # Categorization
    category = Column(String(100))
    
    # Timeline
    invoice_date = Column(Date)     
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Link back to Client
    client = relationship("Client", back_populates="invoices")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String(255), nullable=False)
    opening_stock = Column(Integer, default=0, nullable=False)
    purchased = Column(Integer, default=0, nullable=False)
    sold = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Link back to Client
    client = relationship("Client", back_populates="inventory_items")