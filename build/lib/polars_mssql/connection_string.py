from urllib.parse import quote_plus

def connection_string(database, server, driver, username=None, password=None):
    if username and password:
        encoded_password = quote_plus(password)
        conn_str = (
        f"mssql+pyodbc://{username}:{encoded_password}@{server}/{database}"
        f"?driver={driver.replace(' ', '+')}") 
    else:
        conn_str = (
            f"mssql+pyodbc://@{server}/{database}"
            f"?trusted_connection=yes"
            f"&driver={driver.replace(' ', '+')}"  # Ensure proper encoding
        )
    return conn_str