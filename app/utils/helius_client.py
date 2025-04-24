import requests
from flask import current_app

def post(endpoint: str, payload: dict):
    url = f"{current_app.config['HELIUS_API_BASE']}/{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "apiKey": current_app.config["HELIUS_API_KEY"]
    }
    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()  # Using Requests for humans :contentReference[oaicite:7]{index=7}

def get(endpoint: str, params: dict = None):
    url = f"{current_app.config['HELIUS_API_BASE']}/{endpoint}"
    params = params or {}
    params["apiKey"] = current_app.config["HELIUS_API_KEY"]
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return resp.json()
