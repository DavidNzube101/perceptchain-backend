from flask import Blueprint, jsonify, request
from app.services.dune import execute_dune_query

queries_bp = Blueprint("queries", __name__)

TOP_HOLDERS_ID = "1234567"
TOKEN_TRANSFERS_ID = "1234568"
PROTOCOL_ACTIVITY_ID = "1234569"

@queries_bp.route("/top-holders/<token_symbol>")
def top_holders(token_symbol):
    limit = request.args.get("limit", 10, int)
    try:
        data = execute_dune_query(TOP_HOLDERS_ID, {"TOKEN": token_symbol, "N": limit})
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@queries_bp.route("/token-transfers/<token_symbol>")
def token_transfers(token_symbol):
    days = request.args.get("days", 7, int)
    limit = request.args.get("limit", 100, int)
    try:
        data = execute_dune_query(TOKEN_TRANSFERS_ID, {"TOKEN": token_symbol, "DAYS": days, "LIMIT": limit})
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@queries_bp.route("/protocol-activity/<protocol_name>")
def protocol_activity(protocol_name):
    days = request.args.get("days", 30, int)
    try:
        data = execute_dune_query(PROTOCOL_ACTIVITY_ID, {"PROTOCOL": protocol_name, "DAYS": days})
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
