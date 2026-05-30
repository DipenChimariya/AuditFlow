from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from . import models, schemas

# ==========================================
# CLIENT CRUD OPERATIONS
# ==========================================

def create_client(db: Session, client: schemas.ClientCreate):
    # Proactive Check: Force a case-insensitive check on Name and match PAN number
    existing = db.query(models.Client).filter(
        (func.lower(models.Client.name) == func.lower(client.name.strip())) |
        (models.Client.pan_number == client.pan_number)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="⚠️ A client firm with this Name or PAN number is already registered."
        )

    # Strip unexpected whitespace gaps but keep user casing preference for display
    db_client = models.Client(
        name=client.name.strip(),
        pan_number=client.pan_number
    )
    try:
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        return db_client
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client registration failed due to a database conflict."
        )

def get_clients(db: Session):
    """Fetches all active audit client profiles."""
    return db.query(models.Client).all()

def get_client(db: Session, client_id: int):
    """Retrieves a single target client by primary key ID."""
    return db.query(models.Client).filter(models.Client.id == client_id).first()


# ==========================================
# INVOICE CRUD OPERATIONS
# ==========================================

def create_invoice(db: Session, invoice: schemas.InvoiceCreate):
    # Verify the target client actually exists in our DB
    client_exists = db.query(models.Client).filter(models.Client.id == invoice.client_id).first()
    if not client_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"❌ Cannot link invoice. Client ID {invoice.client_id} does not exist."
        )

    # Verify this specific client hasn't already claimed this invoice number
    if invoice.invoice_number:
        existing_invoice = db.query(models.Invoice).filter(
            models.Invoice.client_id == invoice.client_id,
            models.Invoice.invoice_number == invoice.invoice_number
        ).first()
        
        if existing_invoice:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"⚠️ Invoice/Bill number '{invoice.invoice_number}' has already been logged for this client."
            )

    # Safe Insertion
    db_invoice = models.Invoice(**invoice.model_dump())
    try:
        db.add(db_invoice)
        db.commit()
        db.refresh(db_invoice)
        return db_invoice
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity violation occurred while saving invoice record."
        )

def get_invoices(db: Session):
    """Fetches every logged voucher for the global ledger view."""
    return db.query(models.Invoice).all()

# ➕ ADDED: Fetch invoices specifically matching a targeted client ID
def get_invoices_by_client(db: Session, client_id: int):
    """Retrieves all historical logged vouchers linked to an isolated client company."""
    return db.query(models.Invoice).filter(models.Invoice.client_id == client_id).all()


# ==========================================
# ➕ ADDED: INVENTORY CRUD OPERATIONS
# ==========================================

def create_inventory_item(db: Session, item: schemas.InventoryCreate):
    """Pins a verified product warehouse stock line into PostgreSQL."""
    # Ensure client profile is valid before trying to assign inventory
    client_exists = db.query(models.Client).filter(models.Client.id == item.client_id).first()
    if not client_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"❌ Cannot map inventory line. Client ID {item.client_id} does not exist."
        )

    db_item = models.Inventory(**item.model_dump())
    try:
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database error occurred while adding warehouse stock row."
        )

def get_inventory_by_client(db: Session, client_id: int):
    """Fetches complete stock sheets filtered by client ID."""
    return db.query(models.Inventory).filter(models.Inventory.client_id == client_id).all()