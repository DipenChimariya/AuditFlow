from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.dependencies import get_db
from backend.app import crud, schemas

router = APIRouter(
    prefix="/clients",
    tags=["Clients"]
)

@router.post(
    "/",
    response_model=schemas.ClientResponse
)
def create_client(
    client: schemas.ClientCreate,
    db: Session = Depends(get_db)
):
    return crud.create_client(db, client)


@router.get(
    "/",
    response_model=list[schemas.ClientResponse]
)
def get_clients(
    db: Session = Depends(get_db)
):
    return crud.get_clients(db)