from fastapi import APIRouter
from fastapi import Depends,status
from sqlalchemy.orm import Session

from backend.app.dependencies import get_db
from backend.app import crud, schemas

router = APIRouter(
    prefix="/api/clients",
    tags=["Clients Management Directory"]
)

@router.post(
    "/",
    response_model=schemas.ClientResponse,
    status_code=status.HTTP_201_CREATED 
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