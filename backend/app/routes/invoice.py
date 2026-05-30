from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.models import Invoice
from backend.app.dependencies import get_db
from backend.app import crud, schemas

router = APIRouter(
    prefix="/api/invoices",  # FIXED: Aligned prefix with your frontend API layout
    tags=["Invoices Ledger Management"]
)

@router.post("/", response_model=schemas.InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(invoice: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    return crud.create_invoice(db, invoice)


@router.get("/", response_model=list[schemas.InvoiceResponse])
def get_invoices(db: Session = Depends(get_db)):
    """Fetches the global ledger array across every single customer."""
    return crud.get_invoices(db)



@router.get("/{client_id}", response_model=list[schemas.InvoiceResponse])
def get_invoices_by_client(client_id: int, db: Session = Depends(get_db)):
    """Retrieves all logged invoices linked to an isolated client ID profile."""
    return crud.get_invoices_by_client(db, client_id=client_id)


@router.delete("/{invoice_id}")
def remove_invoice_from_db(invoice_id: int, db: Session = Depends(get_db)):
    """Looks up an invoice by its unique database ID and deletes it permanently."""
    db_invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice record not found in database.")
    
    db.delete(db_invoice)
    db.commit()
    
    return {"status": "success", "message": f"Invoice {invoice_id} deleted successfully"}