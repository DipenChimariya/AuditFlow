from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.app.dependencies import get_db  
from backend.app.models import Inventory
from backend.app.schemas import InventoryCreate, InventoryResponse

router = APIRouter(
    prefix="/api/inventory",
    tags=["Inventory Tracking Management"]
)

@router.get("/{client_id}", response_model=List[InventoryResponse])
def read_inventory_by_client(client_id: int, db: Session = Depends(get_db)):
    """Fetches the complete warehouse stock profiles matching a specific client ID."""
    stock_sheet = db.query(Inventory).filter(Inventory.client_id == client_id).all()
    return stock_sheet

@router.post("/", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
def create_inventory_item(item: InventoryCreate, db: Session = Depends(get_db)):
    """Pins a verified product ledger line for an audited firm profile."""
    # Safety Check: Guard against negative ending calculations
    if (item.opening_stock + item.purchased - item.sold) < 0:
        raise HTTPException(
            status_code=400, 
            detail="Accounting Validation Failed: On-hand remaining inventory balance cannot drop below zero."
        )
        
    db_item = Inventory(
        client_id=item.client_id,
        product_name=item.product_name,
        opening_stock=item.opening_stock,
        purchased=item.purchased,
        sold=item.sold
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item