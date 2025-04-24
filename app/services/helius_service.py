import json
from typing import List, Dict
from flask import current_app
import requests
from base58 import b58decode


from datetime import datetime

# Custom exceptions
class InvalidPublicKeyError(Exception):
    pass

class HeliusTimeoutError(Exception):
    pass

class HeliusServiceError(Exception):
    pass

def _validate_public_key(address: str):
    try:
        decoded = b58decode(address)
        if len(decoded) != 32:
            raise InvalidPublicKeyError(f"Address {address} is not 32 bytes")
    except Exception:
        raise InvalidPublicKeyError(f"Invalid base58 public key: {address}")

def helius_fetch(method: str, params: list, timeout_ms: int):
    """
    Low-level JSON-RPC helper for Helius.
    """
    timeout_sec = timeout_ms / 1000.0
    rpc_url = current_app.config["HELIUS_RPC_URL"]
    payload = {
        "jsonrpc": "2.0",
        "id": method,
        "method": method,
        "params": params
    }
    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(rpc_url, json=payload, headers=headers, timeout=timeout_sec)
        resp.raise_for_status()
    except requests.Timeout as e:
        raise HeliusTimeoutError(str(e))
    except requests.RequestException as e:
        raise HeliusServiceError(f"HTTP error: {e}")

    data = resp.json()
    if data.get("error"):
        raise HeliusServiceError(json.dumps(data["error"]))
    return data["result"]

def get_top_holders(mint_address: str, top_n: int = 10) -> List[Dict]:
    """
    Fetches the top 'top_n' token holders for 'mint_address' using Helius RPCs.
    Returns a list of dicts with keys: address, amount, uiAmount, percentage.
    """
    # Validate the mint before making RPC calls
    _validate_public_key(mint_address)

    timeout = current_app.config.get("DEFAULT_TIMEOUT_MS", 20000)

    # 1. Largest accounts (returns up to 20)
    result = helius_fetch("getTokenLargestAccounts", [mint_address], timeout)
    accounts = result.get("value", [])

    # 2. Total supply (for percentage calculation)
    supply_resp = helius_fetch("getTokenSupply", [mint_address], timeout)
    supply_info = supply_resp.get("value", {})
    raw_supply = float(supply_info.get("amount", "0"))
    decimals = int(supply_info.get("decimals", 0))
    total_supply = raw_supply / (10 ** decimals) if decimals else 0

    # 3. Build the holder list with percentages
    holders = []
    for acct in accounts[:top_n]:
        ui_amount = acct.get("uiAmount", 0)
        percentage = (ui_amount / total_supply * 100) if total_supply else 0
        holders.append({
            "address": acct.get("address"),
            "amount": acct.get("amount"),
            "uiAmount": ui_amount,
            "percentage": round(percentage, 4)
        })

    return holders



def get_assets_by_group(group_key: str, group_value: str, page: int = 1, limit: int = 20) -> Dict:
    """
    Fetches assets by a specified grouping (collection, creator, etc).
    
    Args:
        group_key: The type of grouping (e.g., 'collection', 'creator')
        group_value: The value to search for (e.g., collection ID or creator address)
        page: Page number for pagination
        limit: Number of results per page
    
    Returns:
        Dictionary containing assets and metadata
    """
    # Validate if group_value is a public key when appropriate
    if group_key == "creator" or group_key == "owner":
        _validate_public_key(group_value)
    
    timeout = current_app.config.get("DEFAULT_TIMEOUT_MS", 20000)
    
    # Calculate offset for pagination
    offset = (page - 1) * limit
    
    # Build params for the Helius RPC call
    params = [
        {
            "groupKey": group_key,
            "groupValue": group_value,
            "page": page,
            "limit": limit
        }
    ]
    
    # Make the RPC call
    result = helius_fetch("getAssetsByGroup", params, timeout)
    
    # Process the result to enhance visualization potential
    processed_result = {
        "total": result.get("total", 0),
        "limit": limit,
        "page": page,
        "groupKey": group_key,
        "groupValue": group_value,
        "assets": []
    }
    
    # Extract and organize the assets data
    for asset in result.get("items", []):
        processed_asset = {
            "id": asset.get("id"),
            "name": asset.get("content", {}).get("metadata", {}).get("name"),
            "symbol": asset.get("content", {}).get("metadata", {}).get("symbol"),
            "image": asset.get("content", {}).get("links", {}).get("image"),
            "owner": asset.get("ownership", {}).get("owner"),
            "attributes": asset.get("content", {}).get("metadata", {}).get("attributes", []),
            "royalty": asset.get("royalty", {}).get("basis_points", 0) / 100.0,  # Convert to percentage
            "collection": {
                "name": asset.get("grouping", [{}])[0].get("group_value") if asset.get("grouping") else None,
                "id": asset.get("grouping", [{}])[0].get("collection_id") if asset.get("grouping") else None
            }
        }
        processed_result["assets"].append(processed_asset)
    
    # Add aggregated stats for visualization
    if processed_result["assets"]:
        # Count attributes for potential visualizations
        attribute_counts = {}
        for asset in processed_result["assets"]:
            for attr in asset["attributes"]:
                trait_type = attr.get("trait_type")
                value = attr.get("value")
                
                if trait_type not in attribute_counts:
                    attribute_counts[trait_type] = {}
                
                if value not in attribute_counts[trait_type]:
                    attribute_counts[trait_type][value] = 0
                    
                attribute_counts[trait_type][value] += 1
        
        processed_result["attribute_stats"] = attribute_counts
        
        # Count owners for distribution visualization
        owner_counts = {}
        for asset in processed_result["assets"]:
            owner = asset["owner"]
            if owner not in owner_counts:
                owner_counts[owner] = 0
            owner_counts[owner] += 1
        
        processed_result["owner_distribution"] = owner_counts
    
    return processed_result



def get_token_accounts_by_owner(owner_address: str, include_details: bool = True) -> Dict:
    """
    Fetches all SPL token accounts owned by a specific wallet address.
    
    Args:
        owner_address: The wallet address to query
        include_details: If True, fetch additional token metadata for each token
        
    Returns:
        Dictionary containing token accounts with balances and metadata
    """
    # Validate owner address
    _validate_public_key(owner_address)
    
    timeout = current_app.config.get("DEFAULT_TIMEOUT_MS", 20000)
    
    # Build params for Helius RPC call
    # We're requesting the "jsonParsed" encoding to get nicely formatted data
    params = [
        owner_address,
        {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},  # SPL Token program ID
        {"encoding": "jsonParsed"}
    ]
    
    # Make the RPC call
    result = helius_fetch("getTokenAccountsByOwner", params, timeout)
    
    # Process token accounts
    token_accounts = []
    
    for account in result.get("value", []):
        # Extract account data
        account_data = account.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
        mint = account_data.get("mint")
        ui_amount = account_data.get("tokenAmount", {}).get("uiAmount", 0)
        
        # Skip accounts with zero balance if they exist
        if ui_amount == 0:
            continue
            
        token_info = {
            "mint": mint,
            "address": account.get("pubkey"),
            "amount": account_data.get("tokenAmount", {}).get("amount"),
            "uiAmount": ui_amount,
            "decimals": account_data.get("tokenAmount", {}).get("decimals", 0)
        }
        
        # Fetch additional token metadata if requested
        if include_details and mint:
            try:
                # Get token metadata (supply, etc.)
                supply_resp = helius_fetch("getTokenSupply", [mint], timeout)
                supply_info = supply_resp.get("value", {})
                
                token_info["tokenSupply"] = {
                    "amount": supply_info.get("amount"),
                    "uiAmount": supply_info.get("uiAmount"),
                    "decimals": supply_info.get("decimals", 0)
                }
                
                # Calculate percentage of total supply
                total_supply = float(supply_info.get("uiAmount", 0))
                if total_supply > 0:
                    token_info["percentageOwned"] = round((ui_amount / total_supply) * 100, 4)
                else:
                    token_info["percentageOwned"] = 0
                    
            except Exception as e:
                current_app.logger.warning(f"Failed to fetch details for token {mint}: {e}")
                token_info["error"] = "Failed to fetch token details"
                
        token_accounts.append(token_info)
    
    # Sort by UI amount in descending order
    token_accounts.sort(key=lambda x: x.get("uiAmount", 0), reverse=True)
    
    return {
        "owner": owner_address,
        "count": len(token_accounts),
        "tokens": token_accounts
    }



def get_signatures_for_address(address: str, limit: int = 20, before: str = None, until: str = None) -> Dict:
    """
    Fetches transaction signatures for an address with detailed analytics.
    
    Args:
        address: The wallet or contract address to query
        limit: Maximum number of signatures to fetch (default: 20, max: 1000)
        before: Start searching from this signature (pagination token)
        until: Search until this signature (optional)
        
    Returns:
        Dictionary containing signatures with analytics data
    """
    # Validate address
    _validate_public_key(address)
    
    # Validate limit
    if limit > 1000:
        limit = 1000  # API maximum
    
    timeout = current_app.config.get("DEFAULT_TIMEOUT_MS", 30000)  # Higher timeout for transaction history
    
    # Build params for Helius RPC call
    params = [address, {"limit": limit}]
    
    # Add pagination parameters if provided
    if before:
        params[1]["before"] = before
    if until:
        params[1]["until"] = until
    
    # Make the RPC call
    result = helius_fetch("getSignaturesForAddress", params, timeout)
    
    # Process transaction signatures
    signatures = []
    
    # Variables for analytics
    time_data = {}  # For time-based analytics
    programs_involved = {}  # Count program invocations
    total_fees = 0
    success_count = 0
    
    for tx in result:
        signature = tx.get("signature")
        timestamp = tx.get("blockTime")
        status = "success" if tx.get("confirmationStatus") == "finalized" and not tx.get("err") else "failed"
        
        # Increment success counter
        if status == "success":
            success_count += 1
        
        # Parse block time to readable format
        readable_time = None
        if timestamp:
            try:
                dt = datetime.fromtimestamp(timestamp)
                readable_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                
                # Collect time data for analytics
                hour = dt.hour
                day = dt.strftime("%Y-%m-%d")
                
                # Count by hour (for hour of day analysis)
                if hour not in time_data:
                    time_data[hour] = 0
                time_data[hour] += 1
                
                # Count by day (for daily activity)
                if day not in time_data:
                    time_data[day] = 0
                time_data[day] += 1
                
            except Exception as e:
                current_app.logger.warning(f"Failed to parse timestamp {timestamp}: {e}")
        
        # Track programs used in the transaction - FIX: Safe handling of memo field
        memo = tx.get("memo")
        if memo and isinstance(memo, str):  # Check if memo exists and is a string
            for account_key in memo.split(','):
                if account_key and len(account_key) > 10:  # Simple validation
                    if account_key not in programs_involved:
                        programs_involved[account_key] = 0
                    programs_involved[account_key] += 1
        
        # Track fees
        if "fee" in tx:
            total_fees += tx.get("fee", 0)
        
        signatures.append({
            "signature": signature,
            "blockTime": timestamp,
            "readableTime": readable_time,
            "slot": tx.get("slot"),
            "err": tx.get("err"),
            "status": status,
            "fee": tx.get("fee"),
            "memo": tx.get("memo")
        })
    
    # Prepare time analytics
    hourly_activity = [{"hour": hour, "count": count} for hour, count in time_data.items() 
                      if isinstance(hour, int)]
    
    # Sort hourly activity
    hourly_activity.sort(key=lambda x: x["hour"])
    
    # Prepare program analytics - get top programs
    program_usage = [{"program": program, "count": count} 
                    for program, count in sorted(programs_involved.items(), 
                                              key=lambda item: item[1], 
                                              reverse=True)][:10]  # Top 10
    
    # Calculate success rate
    success_rate = (success_count / len(signatures)) * 100 if signatures else 0
    
    return {
        "address": address,
        "count": len(signatures),
        "successRate": round(success_rate, 2),
        "totalFees": total_fees,
        "signatures": signatures,
        "analytics": {
            "hourlyActivity": hourly_activity,
            "topPrograms": program_usage
        },
        "pagination": {
            "before": signatures[-1].get("signature") if signatures else None,
            "hasMore": len(signatures) >= limit
        }
    }