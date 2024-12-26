import polars as pl
from sqlalchemy import create_engine
from .config import get_default_mssql_config
from typing import Any, Dict, Optional, Union
from urllib.parse import quote_plus

class Connection:
    """
    A class for managing connections to SQL Server and performing operations using Polars DataFrames.

    This class simplifies working with SQL Server by integrating Polars for fast and efficient data processing.
    It allows users to:

    - Run SQL queries and retrieve results as Polars DataFrames
    - Save (write) Polars DataFrames to SQL Server tables
    - List tables and views in the connected database

    Parameters
    ----------
    database : str, optional
        Name of the database to connect to. If not provided, will use the default from `get_default_mssql_config()`.
    server : str, optional
        Name or address of the SQL Server. If not provided, will use the default from `get_default_mssql_config()`.
    driver : str, optional
        ODBC driver to use (e.g., "ODBC Driver 17 for SQL Server"). If not provided, 
        uses the default from `get_default_mssql_config()`.
    username : str, optional
        SQL Server login name. If both `username` and `password` are provided, SQL authentication is used.
    password : str, optional
        SQL Server login password. If both `username` and `password` are provided, SQL authentication is used.

    Attributes
    ----------
    database : str
        The database name in use.
    server : str
        The server name in use.
    connection_string : str
        The SQLAlchemy connection string built from the provided parameters.
    _engine : sqlalchemy.engine.base.Engine
        The SQLAlchemy engine used for database interactions.

    Methods
    -------
    read_query(
        query: str,
        iter_batches: bool = False,
        batch_size: Optional[int] = None,
        schema_overrides: Optional[Dict[str, Any]] = None,
        infer_schema_length: Optional[int] = 100,
        execute_options: Optional[Dict[str, Any]] = None
    ) -> pl.DataFrame:
        Execute an SQL query with additional options and return the result as a Polars DataFrame.

    read_table(name: str) -> pl.DataFrame:
        Read all rows from the specified table into a Polars DataFrame.

    write_table(df: pl.DataFrame, name: str, if_exists: str = "fail"):
        Save a Polars DataFrame to a SQL Server table.

    close():
        Dispose of the SQLAlchemy engine and close the connection.

    __enter__():
        Enter the runtime context related to this object.

    __exit__(exc_type, exc_val, exc_tb):
        Exit the runtime context and close the connection.
    """

    def __init__(
        self,
        database: Optional[str] = None,
        server: Optional[str] = None,
        driver: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        # Load any project-specific defaults (which now do NOT include username/password).
        config = get_default_mssql_config()

        # Resolve parameters with config defaults if not provided
        self.database = database or config["database"]
        self.server = server or config["server"]
        driver = driver or config["driver"]

        # If both username and password are provided, use SQL Authentication
        if username and password:
            encoded_password = quote_plus(password)
            conn_str = (
        f"mssql+pyodbc://{username}:{encoded_password}@{self.server}/{self.database}"
        f"?driver={driver.replace(' ', '+')}") 
        else:
             # Windows Integrated Authentication
            conn_str = (
            f"mssql+pyodbc://@{self.server}/{self.database}"
            f"?trusted_connection=yes"
            f"&driver={driver.replace(' ', '+')}"  # Ensure proper encoding
        )

        self.connection_string = conn_str
        self._engine = create_engine(conn_str, echo=False)

    def read_query(self,
        query: str,
        iter_batches: bool = False,
        batch_size: Optional[int] = None,
        schema_overrides: Optional[Dict[str, Any]] = None,
        infer_schema_length: Optional[int] = 100,
        execute_options: Optional[Dict[str, Any]] = None
    ) -> pl.DataFrame:
        """
        Execute an SQL query with additional options and return the result as a Polars DataFrame.

        Parameters
        ----------
        query : str
            The SQL query to execute.
        iter_batches : bool, default False
            If True, returns an iterator that yields DataFrame batches.
        batch_size : int, optional
            The number of rows per batch when `iter_batches` is True.
        schema_overrides : dict, optional
            A dictionary to override inferred schema types. Keys should be column names,
            and values should be Polars data types.
        infer_schema_length : int, optional
            The number of rows to read for inferring schema types. Default is 100.
        execute_options : dict, optional
            Additional execution options for the database driver.

        Returns
        -------
        pl.DataFrame or pl.DataFrameIterator
            The result of the query as a Polars DataFrame, or an iterator of DataFrame batches
            if `iter_batches` is True.

        Raises
        ------
        RuntimeError
            If the query execution fails.
        """
        try:
            return pl.read_database(
                query=query,
                connection=self._engine,
                iter_batches=iter_batches,
                batch_size=batch_size,
                schema_overrides=schema_overrides,
                infer_schema_length=infer_schema_length,
                execute_options=execute_options
            )
        except Exception as e:
            raise RuntimeError(f"Failed to execute query: {e}") from e

    def read_table(self, name: str) -> pl.DataFrame:
        """
        Read all rows from the specified table into a Polars DataFrame.

        Parameters
        ----------
        name : str
            The full table name, including schema if necessary (e.g., "schema.table").

        Returns
        -------
        pl.DataFrame
            All rows from the specified table.

        Raises
        ------
        RuntimeError
            If the query execution fails.
        """
        query = f"SELECT * FROM {name}"
        return self.read_query(query)

    def write_table(self, df: pl.DataFrame, name: str, if_exists: str = "fail"):
        """
        Save a Polars DataFrame to a specified table in SQL Server.

        Parameters
        ----------
        df : pl.DataFrame
            The Polars DataFrame to be written.
        name : str
            The target table name in the database.
        if_exists : {'fail', 'append', 'replace'}, default 'fail'
            What to do if the target table already exists:
            - 'fail': raises an error
            - 'append': inserts data
            - 'replace': drops and recreates the table, then inserts data

        Raises
        ------
        ValueError
            If `if_exists` has an invalid value.
        RuntimeError
            If the write operation fails.
        """
        valid_options = {"fail", "append", "replace"}
        if if_exists not in valid_options:
            raise ValueError(f"Invalid option for if_exists: '{if_exists}'. "
                             f"Choose from {valid_options}.")

        try:
            df.write_database(name, connection=self._engine, if_exists=if_exists)
        except Exception as e:
            raise RuntimeError(f"Failed to write table '{name}': {e}") from e

    def close(self):
        """
        Dispose of the SQLAlchemy engine, closing the connection.

        This frees up any database-related resources used by the engine.
        """
        try:
            self._engine.dispose()
            print("Engine disposed and connection closed")
        except Exception as e:
            print(f"Error closing connection: {e}")

    def __del__(self):
        """
        Destructor that disposes of the engine if not already closed.
        """
        self.close()

    def __enter__(self):
        """
        Enter the runtime context related to this object.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the runtime context and close the connection.
        """
        self.close()
