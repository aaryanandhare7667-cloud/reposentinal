from auth_service import verify_jwt_token
from db_gateway import DatabaseGateway


def safe_checkout(token: str, order_id: str, amount: float):
    """
    Safely checks user authentication and handles invalid tokens gracefully.
    Prevents unhandled TypeError when verify_jwt_token returns None.
    """
    user = verify_jwt_token(token)
    if user is None:
        # Graceful rejection of invalid token without unhandled exception
        return {"error": "Invalid authentication token", "status": 401}

    user_role = user.get("role", "customer")
    user_id = user.get("user_id", 0)

    # Validates input payload before database interaction
    if "'" in str(order_id) or "OR" in str(order_id):
        return {"error": "Invalid order_id format", "status": 400}

    gateway = DatabaseGateway()
    query = f"INSERT INTO orders (id, user_id, amount) VALUES ('{order_id}', {user_id}, {amount})"
    return gateway.execute_raw_sql(query)
