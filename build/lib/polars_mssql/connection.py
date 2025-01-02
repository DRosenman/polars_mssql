import polars as pl
from sqlalchemy import create_engine, inspect
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError
from .config import get_default_mssql_config
from .connection_string import connection_string
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
    engine : sqlalchemy.engine.base.Engine
        The SQLAlchemy engine used for database interactions.

    Methods
    -------
    read_query(query: str) -> pl.DataFrame:
        Execute an SQL query and return the result as a Polars DataFrame.

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
        if database is None:
            self.database = config['database']
            if self.database is None:
                raise ValueError("Database name cannot be None.")
            else:
                print(f"Default database used: {self.database}")
        else:
            self.database = database

        if server is None:
            self.server = config['server']
            if self.server is None:
                raise ValueError("Server cannot be None.")
            else:
                print(f"Default server used: {self.server}")
        else:
            self.server = server

        if driver is None:
            self.driver = config['driver']
            if self.driver is None:
                raise ValueError("Driver cannot be None.")
            else:
                print(f"Default driver used: {self.driver}")
        else:
            self.driver = driver
        
        conn_str = connection_string(self.database, self.server, self.driver, username, password)
        
        self.engine = create_engine(conn_str, echo=False)
        self.connection_string = str(self.engine.engine.url)
        try:
            inspector = inspect(self.engine)
            print(f"Connection to [{self.server}]:[{self.database}] successful.")
        except SQLAlchemyError as e:
            print(f"An error occurred connecting to [{self.server}]:[{self.database}]:", e)

    def read_query(self, query: str) -> pl.DataFrame:
        """
        Execute a SQL query and return the result as a Polars DataFrame.

        This method provides a simple interface to run SQL queries and retrieve the results
        as a Polars DataFrame. For advanced functionality, users can directly use
        `polars.read_database` with the engine attribute.

        Parameters
        ----------
        query : str
            The SQL query to execute.

        Returns
        -------
        pl.DataFrame
            The result of the query as a Polars DataFrame.

        Raises
        ------
        RuntimeError
            If the query execution fails.

        Examples
        --------
        **Run a simple query and return results as a Polars DataFrame:**
            query = "SELECT * FROM users"
            df = conn.read_query(query)

        **Usage with polars.read_database:** You can use pl.read_database.
            import polars as pl
            pl.read_database("SELECT * FROM users", connection = conn.engine)
    """
        try:
            # Use polars.read_database with the engine
            return pl.read_database(query=query, connection=self.engine)
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
            df.write_database(name, connection=self.engine, if_exists=if_exists)
        except Exception as e:
            raise RuntimeError(f"Failed to write table '{name}': {e}") from e
        
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> None:
        """
        Execute a SQL query with optional parameterized inputs.

        This method allows users to execute SQL queries securely using parameterized inputs
        (to prevent accidental SQL injection) while maintaining flexibility for any valid SQL commands.

        Parameters
        ----------
        query : str
            The SQL query to execute. It can include placeholders for parameterized queries
            (e.g., `:param_name` or `?` depending on your database backend).
        params : dict, optional
            A dictionary of parameters to bind to the query for safe execution.
            The keys in the dictionary should match the placeholders in the query.

        Raises
        ------
        RuntimeError
            If query execution fails due to a database error.

        Examples
        --------
        **Insert a new user securely using parameters:**
            query = "INSERT INTO users (id, name, email) VALUES (:id, :name, :email)"
            params = {"id": 1, "name": "John Doe", "email": "john.doe@example.com"}
            connection.execute_query(query, params)

        **Delete a user without using parameters:**
            query = "DELETE FROM users WHERE id = 1"
            connection.execute_query(query)

        **Perform a destructive operation (e.g., drop a table):**
            query = "DROP TABLE users"
            connection.execute_query(query)

        **Prevent accidental SQL injection:**
            query = "SELECT * FROM users WHERE name = :name"
            params = {"name": "John'; DROP TABLE users; --"}
            connection.execute_query(query, params)
            # Safely executed as:
            # SELECT * FROM users WHERE name = 'John''; DROP TABLE users; --'
        """
        try:
            with self.engine.connect() as connection:
            # Begin a transaction
                with connection.begin():
                    if params:
                        connection.execute(text(query), params or {})
                    else:
                        connection.execute(query)
                    print("Query executed and committed successfully.")
        except SQLAlchemyError as e:
            raise RuntimeError(f"Failed to execute query: {e}") from e

    def close(self):
        """
        Dispose of the SQLAlchemy engine, closing the connection.

        This frees up any database-related resources used by the engine.
        """
        try:
            self.engine.dispose()
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

    def __repr__(self):
        return f"Connection(database={self.database}, server={self.server}, driver={self.driver})"

    def __str__(self):
        """
        Return a user-friendly string representation of the connection, hiding sensitive data.
        """
        return f"Connection:\n\tDatabase: {self.database}\n\tServer: {self.server}\n\tDriver: {self.driver}"