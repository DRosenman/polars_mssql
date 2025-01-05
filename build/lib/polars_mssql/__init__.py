# polars_sqlserver/__init__.py

from .config import set_default_mssql_config, get_default_mssql_config
from .connection import Connection
from .connection_string import connection_string

__version__ = "0.3.2"

__all__ = [
    "set_default_mssql_config", 
    "get_default_mssql_config",
    "Connection",
    "connection_string"
]
