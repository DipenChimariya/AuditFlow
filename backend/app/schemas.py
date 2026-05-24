from datetime import date, datetime
from decimal import Decimal
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
    client_id: int # Pointing to the unique ID of the client being audited
    
    vendor_name: str = Field(..., min_length=1)
    pan_number: str | None = Field(None, min_length=9, max_length=9, pattern=r"^\d{9}$") # Vendor's PAN
    invoice_number: str | None = None

    
    subtotal: Decimal = Field(default_factory=lambda: Decimal("0.00"))
    vat: Decimal = Field(default_factory=lambda: Decimal("0.00"))
    total: Decimal = Field(default_factory=lambda: Decimal("0.00"))

    category: str | None = None
    invoice_date: date | None = None

class InvoiceResponse(InvoiceCreate):
    id: int
    created_at: datetime
    
    # Optional but highly recommended: nested client data so we can easily show
    # "Client: ABC Trading Pvt. Ltd." on Streamlit dashboard side-by-side with invoice details
    client: ClientResponse | None = None 

    class Config:
        from_attributes = True