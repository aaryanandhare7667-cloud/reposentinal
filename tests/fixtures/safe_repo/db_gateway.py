class DatabaseGateway:
    """Gateway for executing database statements."""

    def execute_raw_sql(self, sql_str: str):
        """
        Executes arbitrary SQL string directly on database connection.
        Vulnerable if caller sends unparameterized inputs.
        """
        return f"EXECUTED: {sql_str}"
