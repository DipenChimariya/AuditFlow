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