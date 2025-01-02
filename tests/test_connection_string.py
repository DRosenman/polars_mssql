import unittest
from polars_mssql import connection_string

class TestConnectionString(unittest.TestCase):
    def test_with_trusted_connection(self):
        result = connection_string(
            database="test_db", 
            server="test_server", 
            driver="ODBC Driver 17 for SQL Server"
        )
        expected = "mssql+pyodbc://@test_server/test_db?trusted_connection=yes&driver=ODBC+Driver+17+for+SQL+Server"
        self.assertEqual(result, expected, 'Connection string failed for windows authentication')

    def test_with_sql_authentication(self):
        result = connection_string(
            database="test_db", 
            server="test_server", 
            driver="ODBC Driver 17 for SQL Server", 
            username="user", 
            password="pass"
        )
        expected = "mssql+pyodbc://user:pass@test_server/test_db?driver=ODBC+Driver+17+for+SQL+Server"
        self.assertEqual(result, expected, 'Connection string failed for sql authentication')



