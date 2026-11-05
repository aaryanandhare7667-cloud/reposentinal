from auth_service import verify_jwt_token
from db_gateway import DatabaseGateway

def process_order_checkout(token: str, order_id: str, amount: float):
    # 1. Cross-module bug: assumes verify_jwt_token always returns dict
    user = verify_jwt_token(token)
    user_role = user["role"]
    user_id = user["user_id"]

    # 2. SQL injection
    gateway = DatabaseGateway()
    query = f"INSERT INTO orders (id, user_id, amount) VALUES ('{order_id}', {user_id}, {amount})"
    return gateway.execute_raw_sql(query)
