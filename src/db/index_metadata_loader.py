"""
QueryLens — SQL Server Index Metadata Loader

Uses pyodbc to read indexed columns from SQL Server system catalog views.
This allows QueryLens to avoid false positives such as flagging
ORDER BY on an indexed column as order_by_no_index.
"""

import json
from pathlib import Path

import pyodbc

from src.config.db_config import CONNECTION_STRING


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "artifacts" / "index_metadata.json"


INDEX_METADATA_QUERY = """
SELECT
    t.name AS table_name,
    c.name AS column_name
FROM sys.indexes i
JOIN sys.index_columns ic
    ON i.object_id = ic.object_id
   AND i.index_id = ic.index_id
JOIN sys.columns c
    ON ic.object_id = c.object_id
   AND ic.column_id = c.column_id
JOIN sys.tables t
    ON i.object_id = t.object_id
WHERE i.is_hypothetical = 0
  AND i.is_disabled = 0
  AND i.index_id > 0;
"""


def load_index_metadata(save_to_file=True):
    """
    Loads indexed columns from SQL Server.

    Returns:
        {
            "orders": {"orderid", "customerid", "orderdate"},
            "customers": {"customerid", "createddate"}
        }
    """
    metadata = {}

    with pyodbc.connect(CONNECTION_STRING) as connection:
        cursor = connection.cursor()
        cursor.execute(INDEX_METADATA_QUERY)

        for table_name, column_name in cursor.fetchall():
            table = str(table_name).lower()
            column = str(column_name).lower()

            metadata.setdefault(table, set()).add(column)

    if save_to_file:
        save_index_metadata(metadata)

    return metadata


def save_index_metadata(metadata):
    """
    Saves metadata as JSON for reproducibility/debugging.
    Sets are converted to sorted lists.
    """
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    serializable = {
        table: sorted(columns)
        for table, columns in metadata.items()
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(serializable, f, indent=4)


def load_index_metadata_from_file():
    """
    Loads cached metadata from artifacts/index_metadata.json.
    Converts lists back into sets.
    """
    if not OUTPUT_PATH.exists():
        return {}

    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        table.lower(): {col.lower() for col in columns}
        for table, columns in data.items()
    }


if __name__ == "__main__":
    metadata = load_index_metadata(save_to_file=True)

    print("Loaded SQL Server index metadata")
    for table, columns in metadata.items():
        print(f"{table}: {sorted(columns)}")