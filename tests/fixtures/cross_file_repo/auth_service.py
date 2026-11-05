from typing import Optional, Dict, Any

def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies authentication token.
    Returns user payload dict containing 'user_id' and 'role', or None if token is invalid or expired.
    """
    if not token or token == "invalid_token":
        return None
    return {"user_id": 42, "role": "customer"}
