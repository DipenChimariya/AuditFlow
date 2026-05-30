import requests

BACKEND_URL = "http://127.0.0.1:8000/api"

# ==========================================================
# 🏢 CLIENT MANAGMENT ENDPOINTS
# ==========================================================

def fetch_clients():
    """Fetches all registered client firms from the master directory."""
    try:
        # ⚡ FIX: Removed trailing slash to prevent FastAPI routing mismatch
        response = requests.get(f"{BACKEND_URL}/clients")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.ConnectionError:
        return None  # Alerts frontend that backend engine is offline


def add_new_client(name: str, pan_number: str):
    """Registers a clean corporate profile entity into PostgreSQL."""
    payload = {
        "name": name,
        "pan_number": pan_number if pan_number else None
    }
    try:
        # ⚡ FIX: Removed trailing slash
        response = requests.post(f"{BACKEND_URL}/clients", json=payload)
        return response
    except requests.exceptions.ConnectionError:
        return None


# ==========================================================
# 🧾 INVOICE LEDGER ENDPOINTS
# ==========================================================

def fetch_invoices():
    """Fetches all corporate voucher invoices saved in the system."""
    try:
        # ⚡ FIX: Removed trailing slash
        response = requests.get(f"{BACKEND_URL}/invoices")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.ConnectionError:
        return None


def add_new_invoice(client_id: int, vendor_name: str, invoice_number: str, subtotal: float, vat: float, invoice_date=None):
    """Commits a processed accounting voucher balance line item."""
    payload = {
        "client_id": client_id,
        "vendor_name": vendor_name,
        "invoice_number": invoice_number if invoice_number else None,
        "subtotal": float(subtotal),  
        "vat": float(vat),
        "total": float(subtotal + vat), 
        "pan_number": None, 
        "category": None,
        "invoice_date": invoice_date.strftime("%Y-%m-%d") if invoice_date else None 
    }
    try:
        # ⚡ FIX: Removed trailing slash
        response = requests.post(f"{BACKEND_URL}/invoices", json=payload)
        return response
    except requests.exceptions.ConnectionError:
        return None


def delete_invoice(invoice_id: int):
    """Deletes an invoice permanently from the database via its unique entry identifier ID."""
    try:
        # ⚡ CLEAN PATH: Matches standard FastAPI delete mapping path constraints
        response = requests.delete(f"{BACKEND_URL}/invoices/{invoice_id}")
        return response
    except requests.exceptions.ConnectionError:
        return None


# ==========================================================
# 📦 INVENTORY FINANCIAL LEDGER ENDPOINTS
# ==========================================================

def fetch_inventory_by_client(client_id: int):
    """Fetches total monetary valuation sheets matching a specific corporate client."""
    try:
        response = requests.get(f"{BACKEND_URL}/inventory/{client_id}")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.ConnectionError:
        return None


def add_inventory_item(client_id: int, product_name: str, opening_stock: float, purchased: float, sold: float):
    """Commits a localized financial inventory ledger record for a specified fiscal period."""
    payload = {
        "client_id": client_id,
        "product_name": product_name,          # Saves the period marker context, e.g., 'FY 2025/26 Summary'
        "opening_stock": float(opening_stock), # ⚡ FIX: Shifted from int to float to retain currency precision
        "purchased": float(purchased),         # ⚡ FIX: Shifted from int to float to retain currency precision
        "sold": float(sold)                    # ⚡ FIX: Shifted from int to float to retain currency precision
    }
    try:
        # ⚡ FIX: Removed trailing slash
        response = requests.post(f"{BACKEND_URL}/inventory", json=payload)
        return response
    except requests.exceptions.ConnectionError:
        return None