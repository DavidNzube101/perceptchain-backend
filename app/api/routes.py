import time
from base58 import b58decode
from flask import request, jsonify, current_app
from app.api import api_bp
from app.services.helius_service import (
    get_signatures_for_address,
    get_token_accounts_by_owner,
    get_top_holders,
    InvalidPublicKeyError,
    HeliusServiceError,
    HeliusTimeoutError
)

def is_valid_public_key(address: str) -> bool:
    """Check if the given string is a valid Solana public key."""
    try:
        decoded = b58decode(address)
        return len(decoded) == 32
    except Exception:
        return False

@api_bp.route('/token-holders/<string:token_address>/<int:limit>')
def token_holders_route(token_address: str, limit: int):
    
    # 1. Validate address
    if not is_valid_public_key(token_address):
        return jsonify({"error": f"Invalid token mint address: {token_address}"}), 400

    try:
        # 2. go to helius service
        holders = get_top_holders(
            mint_address=token_address,
            top_n=limit
        )
        return jsonify(holders)


    # serious error handling
    except InvalidPublicKeyError as e:
        current_app.logger.error(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400

    except HeliusTimeoutError as e:
        current_app.logger.error(f"Helius timeout for {token_address}: {e}")
        return jsonify({"error": "Helius API timed out"}), 504

    except HeliusServiceError as e:
        current_app.logger.error(f"Helius service error for {token_address}: {e}")
        status = 403 if "403" in str(e) else 500
        return jsonify({"error": str(e)}), status

    except Exception as e:
        current_app.logger.exception(f"Unexpected error for {token_address}")
        return jsonify({"error": "Unexpected server error"}), 500


@api_bp.route('/wallet/tokens/<string:wallet_address>')
def token_accounts_route(wallet_address: str):
    """
    Endpoint to fetch all token accounts owned by a specific wallet.
    
    URL parameters:
    - wallet_address: The wallet address to query
    
    Query parameters:
    - include_details: Whether to include detailed token metadata (default: true)
    """
    # Get query parameters
    include_details = request.args.get('include_details', default="true", type=str).lower() == "true"
    
    # Validate wallet address
    if not is_valid_public_key(wallet_address):
        return jsonify({"error": f"Invalid wallet address: {wallet_address}"}), 400
    
    try:
        # Fetch token accounts
        token_accounts = get_token_accounts_by_owner(
            owner_address=wallet_address,
            include_details=include_details
        )
        return jsonify(token_accounts)
        
    except InvalidPublicKeyError as e:
        current_app.logger.error(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
        
    except HeliusTimeoutError as e:
        current_app.logger.error(f"Helius timeout for wallet {wallet_address}: {e}")
        return jsonify({"error": "Helius API timed out"}), 504
        
    except HeliusServiceError as e:
        current_app.logger.error(f"Helius service error for wallet {wallet_address}: {e}")
        status = 403 if "403" in str(e) else 500
        return jsonify({"error": str(e)}), status
        
    except Exception as e:
        current_app.logger.exception(f"Unexpected error fetching tokens for {wallet_address}")
        return jsonify({"error": "Unexpected server error"}), 500
    
    
@api_bp.route('/transactions/<string:address>')
def signatures_route(address: str):
    """
    Endpoint to fetch transaction signatures for an address with analytics.
    
    URL parameters:
    - address: The wallet or contract address to query
    
    Query parameters:
    - limit: Maximum number of signatures to fetch (default: 20, max: 1000)
    - before: Start searching from this signature (pagination)
    - until: Search until this signature (optional)
    """
    # Get query parameters
    limit = min(request.args.get('limit', default=20, type=int), 1000)
    before = request.args.get('before', default=None, type=str)
    until = request.args.get('until', default=None, type=str)
    
    # Validate address
    if not is_valid_public_key(address):
        return jsonify({"error": f"Invalid address: {address}"}), 400
    
    try:
        # Fetch transaction signatures
        signature_data = get_signatures_for_address(
            address=address,
            limit=limit,
            before=before,
            until=until
        )
        return jsonify(signature_data)
        
    except InvalidPublicKeyError as e:
        current_app.logger.error(f"Validation error: {e}")
        return jsonify({"error": str(e)}), 400
        
    except HeliusTimeoutError as e:
        current_app.logger.error(f"Helius timeout for address {address}: {e}")
        return jsonify({"error": "Helius API timed out"}), 504
        
    except HeliusServiceError as e:
        current_app.logger.error(f"Helius service error for address {address}: {e}")
        status = 403 if "403" in str(e) else 500
        return jsonify({"error": str(e)}), status
        
    except Exception as e:
        current_app.logger.exception(f"Unexpected error fetching signatures for {address}")
        return jsonify({"error": "Unexpected server error"}), 500