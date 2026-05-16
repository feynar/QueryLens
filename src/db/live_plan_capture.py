"""
QueryLens — Live SQL Server Actual Plan Capture

Runs safe SELECT workload queries through SQL Server using pyodbc,
captures actual execution plans with SET STATISTICS XML ON, and saves
the resulting XML plans into plans_live/.

This module is intentionally separate from run_full_analysis.py so the
main analysis pipeline remains reproducible without requiring SQL Server.
"""

import os
import re
from pathlib import Path

import pyodbc

from src.config.db_config import CONNECTION_STRING


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLANS_DIR = PROJECT_ROOT / "plans"
PLANS_LIVE_DIR = PROJECT_ROOT / "plans_live"
LOG_PATH = PROJECT_ROOT / "artifacts" / "live_capture_log.txt"

def clean_sql_for_execution(sql_text):
    """
    Removes comments and batch/setup lines so pyodbc executes only the query.
    """
    # Remove block comments like /* ... */
    sql_text = re.sub(r"/\*.*?\*/", "", sql_text, flags=re.DOTALL)

    cleaned_lines = []

    for line in sql_text.splitlines():
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.startswith("--"):
            continue

        upper = stripped.upper()

        if upper == "GO":
            continue

        if upper.startswith("USE "):
            continue

        if upper.startswith("SET "):
            continue

        cleaned_lines.append(stripped)

    return "\n".join(cleaned_lines).strip()
    
def is_safe_select(sql_text):
    """
    Allows only read-only SELECT-style workload queries.
    """
    cleaned = clean_sql_for_execution(sql_text).upper()

    blocked_tokens = [
        "INSERT ",
        "UPDATE ",
        "DELETE ",
        "DROP ",
        "ALTER ",
        "CREATE ",
        "MERGE ",
        "TRUNCATE ",
        "EXEC ",
        "EXECUTE "
    ]

    if not cleaned.startswith("SELECT") and not cleaned.startswith("WITH"):
        return False

    return not any(token in cleaned for token in blocked_tokens)


def read_sql_file(sql_path):
    """Reads SQL text with Windows-friendly encoding fallback."""
    try:
        return sql_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return sql_path.read_text(encoding="cp1252")


def extract_xml_plan(cursor):
    """
    Walks through result sets until SQL Server returns the STATISTICS XML output.

    SET STATISTICS XML ON returns XML after the query executes. Depending on
    the query, pyodbc may expose normal result sets before the XML result set.
    """
    while True:
        try:
            if cursor.description:
                rows = cursor.fetchall()

                for row in rows:
                    for value in row:
                        if isinstance(value, str) and "<ShowPlanXML" in value:
                            return value
        except pyodbc.ProgrammingError:
            pass

        if not cursor.nextset():
            break

    return None


def capture_plan_for_file(connection, sql_path):
    """
    Executes one SQL file with STATISTICS XML enabled and writes the actual plan.
    """
    raw_sql_text = read_sql_file(sql_path)
    sql_text = clean_sql_for_execution(raw_sql_text)

    if not is_safe_select(raw_sql_text):
        return False, f"Skipped unsafe or non-SELECT query: {sql_path.name}"

    output_path = PLANS_LIVE_DIR / f"{sql_path.stem}.sqlplan"

    cursor = connection.cursor()

    try:
        cursor.execute("SET STATISTICS XML ON;")
        cursor.execute(sql_text)

        xml_plan = extract_xml_plan(cursor)

        cursor.execute("SET STATISTICS XML OFF;")

        if not xml_plan:
            return False, f"No XML plan returned for: {sql_path.name}"

        output_path.write_text(xml_plan, encoding="utf-8")
        return True, f"Captured actual plan: {output_path.name}"

    except Exception as ex:
        try:
            cursor.execute("SET STATISTICS XML OFF;")
        except Exception:
            pass

        return False, f"Failed {sql_path.name}: {ex}"


def capture_all_plans():
    """
    Captures actual execution plans for all safe .sql files in plans/.
    """
    PLANS_LIVE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    log_lines = []
    success_count = 0
    failure_count = 0

    with pyodbc.connect(CONNECTION_STRING) as connection:
        for sql_path in sorted(PLANS_DIR.glob("*.sql")):
            ok, message = capture_plan_for_file(connection, sql_path)
            log_lines.append(message)
            print(message)

            if ok:
                success_count += 1
            else:
                failure_count += 1

    log_lines.append("")
    log_lines.append("Summary")
    log_lines.append("-------")
    log_lines.append(f"Successful captures: {success_count}")
    log_lines.append(f"Failed or skipped captures: {failure_count}")

    LOG_PATH.write_text("\n".join(log_lines), encoding="utf-8")

    print(f"\nLive capture log saved → {LOG_PATH}")


if __name__ == "__main__":
    capture_all_plans()