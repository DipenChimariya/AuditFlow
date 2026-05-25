from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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