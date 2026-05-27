import requests

BACKEND_URL = "http://127.0.0.1:8000"

def fetch_clients():
    try:
        response = requests.get(f"{BACKEND_URL}/clients/")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.ConnectionError:
        return None  # Tells us the backend server is turned off

def add_new_client(name: str, pan_number: str):
    payload = {
        "name": name,
        "pan_number": pan_number if pan_number else None
    }
    try:
        response = requests.post(f"{BACKEND_URL}/clients/", json=payload)
        return response
    except requests.exceptions.ConnectionError:
        return None
    

def fetch_invoices():
    """Fetches all invoices saved in the system."""
    try:
        response = requests.get(f"{BACKEND_URL}/invoices/")
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.ConnectionError:
        return None

def add_new_invoice(client_id: int, vendor_name: str, invoice_number: str, subtotal: float, vat: float, invoice_date=None):
    payload = {
        "client_id": client_id,
        "vendor_name": vendor_name,
        "invoice_number": invoice_number if invoice_number else None,
        "subtotal": str(subtotal),  
        "vat": str(vat),
        "total": str(subtotal + vat), 
        "pan_number": None, 
        "category": None,
        "invoice_date": invoice_date.strftime("%Y-%m-%d") if invoice_date else None # Formats date correctly for JSON transfer
    }
    try:
        response = requests.post(f"{BACKEND_URL}/invoices/", json=payload)
        return response
    except requests.exceptions.ConnectionError:
        return None