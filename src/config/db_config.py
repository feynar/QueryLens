"""
QueryLens — SQL Server Database Configuration

Centralizes the pyodbc connection string used by the live SQL Server
plan capture layer.
"""

# Set to True to generate fresh actual execution plans using pyodbc.
# Set to False to use saved .sqlplan files from plans/.
ENABLE_LIVE_CAPTURE = True

# Adjust SERVER if your SQL Server instance name is different.
# Common examples:
#   localhost
#   localhost\\SQLEXPRESS
#   .\\SQLEXPRESS
#   (localdb)\\MSSQLLocalDB

SERVER = "localhost"
DATABASE = "QueryLensDB"
DRIVER = "ODBC Driver 17 for SQL Server"

CONNECTION_STRING = (
    f"DRIVER={{{DRIVER}}};"
    f"SERVER={SERVER};"
    f"DATABASE={DATABASE};"
    "Trusted_Connection=yes;"
    "TrustServerCertificate=yes;"
)