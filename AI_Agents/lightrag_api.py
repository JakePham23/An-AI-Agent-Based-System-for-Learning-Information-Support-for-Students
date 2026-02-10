import requests
import json

LIGHTRAG_ENDPOINT = "http://127.0.0.1:9621/query"

HEADERS = {
    "X-API-Key": "sk-any-key", 
    "Content-Type": "application/json"
}

def query_lightrag(query: str, mode: str = "mix") -> str:
    """
    Gửi query đến LightRAG và nhận về context.
    Modes: local, global, hybrid, naive, mix (recommended), bypass.
    """
    payload = {
        "query": query,
        "mode": mode
    }
    
    try:
        response = requests.post(LIGHTRAG_ENDPOINT, json=payload, headers=HEADERS)
        response.raise_for_status()
        data = response.json() 
        if isinstance(data, dict) and "response" in data:
            return data["response"]
        return str(data)
    except Exception as e:
        return f"Error querying LightRAG: {str(e)}"

# output = query_lightrag("Có môn nào liên quan đến công nghệ?", 'local')
# print(output)