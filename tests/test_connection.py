import unittest
from unittest.mock import patch, MagicMock
from polars_mssql import Connection


#unit test in progress

class TestConnection(unittest.TestCase):
    @patch("polars_mssql.connection.create_engine")
    def test_connection_initialization(self, mock_create_engine):
        # Mock the SQLAlchemy engine
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        conn = Connection(
            database="test_db",
            server="test_server",
            driver="ODBC Driver 17 for SQL Server"
        )
        
        self.assertEqual(conn.database, "test_db")
        self.assertEqual(conn.server, "test_server")
        self.assertEqual(conn.driver, "ODBC Driver 17 for SQL Server")
        mock_create_engine.assert_called_once_with(
            "mssql+pyodbc://@test_server/test_db?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server",
            echo=False
        )

    @patch("polars_mssql.connection.create_engine")
    def test_read_query(self, mock_create_engine):
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        conn = Connection(
            database="test_db",
            server="test_server",
            driver="ODBC Driver 17 for SQL Server"
        )

        # Mock `pl.read_database`
        with patch("polars.read_database") as mock_read_database:
            mock_read_database.return_value = "mock_dataframe"
            result = conn.read_query("SELECT * FROM test_table")
            self.assertEqual(result, "mock_dataframe")
            mock_read_database.assert_called_once_with(
                query="SELECT * FROM test_table",
                connection=mock_engine,
                iter_batches=False,
                batch_size=None,
                schema_overrides=None,
                infer_schema_length=100,
                execute_options=None
            )

unittest.main()