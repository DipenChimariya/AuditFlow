from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime
from sqlalchemy.sql import func
from .database import Base

class Invoice(Base):
    __tablename__ = "invoices"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Core Identifiers (Indexed for quick searching)
    vendor_name = Column(String(255), index=True, nullable=False)
    pan_number = Column(String(20), index=True)
    invoice_number = Column(String(100), index=True)

    # Financial Figures (Swapped Float for Numeric for exact decimals)
    subtotal = Column(Numeric(precision=12, scale=2), default=0.00)
    vat = Column(Numeric(precision=12, scale=2), default=0.00)     # Typically 13% or 0 for exempt
    total = Column(Numeric(precision=12, scale=2), default=0.00)

    # Categorization
    category = Column(String(100))
    
    # Timeline
    invoice_date = Column(Date)     # The date written on the physical invoice
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # Automatically tracks when uploaded