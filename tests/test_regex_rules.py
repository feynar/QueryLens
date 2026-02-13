import unittest
from src.analysis.legacy_regex_rules import analyze_with_regex
import tempfile
import os


def run_sql(sql_text):
    """
    Helper: write SQL to temp file so analyzer can read it
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sql", mode="w") as tmp:
        tmp.write(sql_text)
        tmp_path = tmp.name

    results = analyze_with_regex(tmp_path)
    os.remove(tmp_path)
    return results


class TestStaticRules(unittest.TestCase):

    # ---------- SELECT * RULE ----------
    def test_select_star_detected(self):
        sql = "SELECT * FROM Customers;"
        results = run_sql(sql)
        self.assertTrue(any(r["issue_type"] == "SELECT_STAR" for r in results))

    def test_select_columns_not_flagged(self):
        sql = "SELECT CustomerID FROM Customers;"
        results = run_sql(sql)
        self.assertFalse(any(r["issue_type"] == "SELECT_STAR" for r in results))

    # ---------- NON-SARGABLE RULE ----------
    def test_year_function_detected(self):
        sql = "SELECT * FROM Customers WHERE YEAR(CreatedDate) = 2025;"
        results = run_sql(sql)
        self.assertTrue(any(r["issue_type"] == "NON_SARGABLE_PREDICATE" for r in results))

    def test_month_function_detected(self):
        sql = "SELECT * FROM Customers WHERE MONTH(CreatedDate) = 1;"
        results = run_sql(sql)
        self.assertTrue(any(r["issue_type"] == "NON_SARGABLE_PREDICATE" for r in results))

    def test_sargable_date_not_flagged(self):
        sql = "SELECT * FROM Customers WHERE CreatedDate >= '2025-01-01';"
        results = run_sql(sql)
        self.assertFalse(any(r["issue_type"] == "NON_SARGABLE_PREDICATE" for r in results))

    # ---------- COMPLEX JOIN RULE ----------
    def test_multiple_joins_detected(self):
        sql = """
        SELECT *
        FROM A
        JOIN B ON A.id = B.id
        JOIN C ON B.id = C.id;
        """
        results = run_sql(sql)
        self.assertTrue(any(r["issue_type"] == "COMPLEX_JOIN" for r in results))

    def test_single_join_not_flagged(self):
        sql = "SELECT * FROM A JOIN B ON A.id = B.id;"
        results = run_sql(sql)
        self.assertFalse(any(r["issue_type"] == "COMPLEX_JOIN" for r in results))


if __name__ == "__main__":
    unittest.main()
