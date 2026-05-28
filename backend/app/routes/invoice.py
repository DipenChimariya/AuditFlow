from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
from backend.app.models import Invoice
from backend.app.dependencies import get_db
from backend.app import crud, schemas

router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"]
)

@router.post(
    "/",
    response_model=schemas.InvoiceResponse
)
def create_invoice(
    invoice: schemas.InvoiceCreate,
    db: Session = Depends(get_db)
):
    return crud.create_invoice(db, invoice)


@router.get(
    "/",
    response_model=list[schemas.InvoiceResponse]
)
def get_invoices(
    db: Session = Depends(get_db)
):
    return crud.get_invoices(db)


@router.delete("/{invoice_id}")
def remove_invoice_from_db(invoice_id: int, db: Session = Depends(get_db)):
    """
    Looks up an invoice by its unique database ID and deletes it permanently.
    """
    # Query the database for the targeted invoice record
    db_invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice record not found in database.")
    
    db.delete(db_invoice)
    db.commit()
    
    return {"status": "success", "message": f"Invoice {invoice_id} deleted successfully"}
 

