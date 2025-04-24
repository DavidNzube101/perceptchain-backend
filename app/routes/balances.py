import requests
from flask import Blueprint, jsonify, current_app

balances_bp = Blueprint("balances", __name__)

@balances_bp.route("/balances/<wallet_address>")
def get_balances(wallet_address):
    url = f"{current_app.config['ECHO_API_BASE']}/balances/svm/{wallet_address}"
    try:
        resp = requests.get(url, headers={"X-Dune-Api-Key": current_app.config["DUNE_API_KEY"]},
                             params={"chains": "solana"})
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500
