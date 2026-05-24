from sqlalchemy.orm import Session

from . import models, schemas


def create_client(
    db: Session,
    client: schemas.ClientCreate
):
    db_client = models.Client(
        name=client.name,
        pan_number=client.pan_number
    )

    db.add(db_client)
    db.commit()
    db.refresh(db_client)

    return db_client

def get_clients(db: Session):
    return db.query(models.Client).all()

def get_client(
    db: Session,
    client_id: int
):
    return (
        db.query(models.Client)
        .filter(models.Client.id == client_id)
        .first()
    )



def create_invoice(
    db: Session,
    invoice: schemas.InvoiceCreate
):
    db_invoice = models.Invoice(
        **invoice.model_dump()
    )

    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)

    return db_invoice


def get_invoices(db: Session):
    return db.query(models.Invoice).all()