from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

# ==========================================
# CLIENT SCHEMAS
# ==========================================

class ClientCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Official registered name of the audited firm")
    # Enforces exactly 9 digits if a PAN is provided, matching Nepalese law
    pan_number: str | None = Field(None, min_length=9, max_length=9, pattern=r"^\d{9}$")

class ClientResponse(ClientCreate):
    id: int

    class Config:
        from_attributes = True


# ==========================================
# INVOICE SCHEMAS
# ==========================================
class InvoiceCreate(BaseModel):
    client_id: int
    vendor_name: str
    invoice_number: Optional[str] = None
    subtotal: Decimal
    vat: Decimal
    total: Decimal
    pan_number: Optional[str] = Field(None,pattern=r"^\d{9}$")
    category: Optional[str] = None
    invoice_date: Optional[date] = None

class InvoiceResponse(BaseModel):
    id: int
    client_id: int
    vendor_name: str
    invoice_number: Optional[str] = None
    subtotal: Decimal
    vat: Decimal
    total: Decimal
    pan_number: Optional[str] = Field(None,pattern=r"^\d{9}$")
    category: Optional[str] = None
    invoice_date: Optional[date] = None 

    class Config:
        from_attributes = True


# ==========================================
# INVENTORY SCHEMAS
# ==========================================

class InventoryCreate(BaseModel):
    client_id: int
    product_name: str  # We will use this field to save the Period or Category name (e.g., "FY 2025/26")
    opening_stock: float  
    purchased: float    
    sold: float

class InventoryResponse(BaseModel):
    id: int
    client_id: int
    product_name: str
    opening_stock: int
    purchased: int
    sold: int
    created_at: datetime

    class Config:
        from_attributes = True # Allows Pydantic to read SQLAlchemy lazy objects natively