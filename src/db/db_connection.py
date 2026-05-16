"""
QueryLens — SQL Server Database Connection Test

Verifies that pyodbc can connect to the QueryLensDB database and run
a simple test query.

Run:
    python -m src.db.db_connection
"""

import pyodbc

from src.config.db_config import CONNECTION_STRING


def get_connection():
    """
    Opens and returns a pyodbc connection to SQL Server.
    """
    return pyodbc.connect(CONNECTION_STRING)


def test_connection():
    """
    Verifies SQL Server connectivity by running SELECT 1.
    """
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1 AS connection_test;")
            row = cursor.fetchone()

            if row and row.connection_test == 1:
                print("Connected to QueryLensDB")
                print("SELECT 1 succeeded")
                return True

            print("Connection opened, but SELECT 1 returned unexpected result")
            return False

    except pyodbc.Error as ex:
        print("Database connection failed")
        print(ex)
        return False


if __name__ == "__main__":
    test_connection()