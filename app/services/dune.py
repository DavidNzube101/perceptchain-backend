import time, requests
from flask import current_app

def execute_dune_query(query_id: str, parameters: dict, max_attempts: int = 10, delay: float = 2.0):
    base = current_app.config["V1_API_BASE"]
    headers = {"X-Dune-Api-Key": current_app.config["DUNE_API_KEY"]}
    
    exec_resp = requests.post(f"{base}/query/{query_id}/execute",
                              headers=headers, json={"query_parameters": parameters})
    exec_resp.raise_for_status()
    execution_id = exec_resp.json()["execution_id"]
    
    for _ in range(max_attempts):
        res = requests.get(f"{base}/execution/{execution_id}/results", headers=headers)
        res.raise_for_status()
        data = res.json()
        if data.get("state") == "QUERY_STATE_COMPLETED":
            return data
        time.sleep(delay)
    raise TimeoutError("Dune query execution timed out")
