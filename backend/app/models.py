from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    pan_number = Column(String(20), unique=True, index=True) # Unique PAN for each client firm

    invoices = relationship("Invoice", back_populates="client")


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

    # Link: invoice.client will let us see the details of the client it belongs to
    client = relationship("Client", back_populates="invoices")