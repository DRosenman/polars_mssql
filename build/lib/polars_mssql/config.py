# polars_mssql/config.py

_default_config = {
    "driver": None,          # e.g., "ODBC Driver 17 for SQL Server"
    "server": None,
    "database": None,
}


def set_default_mssql_config(
    driver: str = None,
    server: str = None,
    database: str = None
):
    """
    Set or update the default Microsoft SQL Server configuration.
    
    :param driver: e.g., 'ODBC Driver 17 for SQL Server'
    :param server: Server address or hostname
    :param database: Default database name to connect to
    """
    global _default_config

    if driver is not None:
        _default_config["driver"] = driver
    if server is not None:
        _default_config["server"] = server
    if database is not None:
        _default_config["database"] = database


def get_default_mssql_config() -> dict:
    """
    Returns the current default configuration as a dictionary.
    """
    return dict(_default_config)  # Return a copy