# polars_sqlserver/__init__.py

from .config import set_default_mssql_config, get_default_mssql_config
from .connection import Connection


__all__ = [
    "set_default_mssql_config", 
    "get_default_mssql_config",
    "Connection"
]
