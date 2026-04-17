import os
import tempfile
import unittest

from src.analysis.static_analyzer import analyze_sql, analyze_with_ast_text


def run_sql(sql_text: str):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sql", mode="w", encoding="utf-8") as tmp:
        tmp.write(sql_text)
        tmp_path = tmp.name

    try:
        results = analyze_sql(tmp_path)
    finally:
        os.remove(tmp_path)

    return results


class TestASTRules(unittest.TestCase):

    def test_select_star_detected(self):
        sql = "SELECT * FROM Customers;"
        results = run_sql(sql)
        self.assertTrue(any(r["rule"] == "select_star" for r in results))

    def test_non_sargable_function_detected(self):
        sql = "SELECT CustomerID FROM Customers WHERE YEAR(CreatedDate) = 2025;"
        results = run_sql(sql)
        self.assertTrue(any(r["rule"] == "non_sargable_predicate" for r in results))

    def test_complex_join_detected(self):
        sql = """
        SELECT *
        FROM A
        JOIN B ON A.id = B.id
        JOIN C ON B.id = C.id
        JOIN D ON C.id = D.id;
        """
        results = run_sql(sql)
        self.assertTrue(any(r["rule"] == "complex_join" for r in results))

    def test_function_on_constant_not_flagged(self):
        sql = "SELECT * FROM Orders WHERE OrderDate >= GETDATE();"
        results = analyze_with_ast_text(sql)
        self.assertFalse(any(r["rule"] == "non_sargable_predicate" for r in results))

    def test_exists_detected(self):
        sql = """
        SELECT c.CustomerID
        FROM Customers c
        WHERE EXISTS (
            SELECT 1
            FROM Orders o
            WHERE o.CustomerID = c.CustomerID
        );
        """
        results = analyze_with_ast_text(sql)
        self.assertTrue(any(r["rule"] == "exists_subquery" for r in results))

    def test_not_exists_detected(self):
        sql = """
        SELECT *
        FROM Customers c
        WHERE NOT EXISTS (
            SELECT 1
            FROM Orders o
            WHERE o.CustomerID = c.CustomerID
        );
        """
        results = analyze_with_ast_text(sql)
        self.assertTrue(any(r["rule"] == "not_exists_subquery" for r in results))

    def test_correlated_subquery_detected(self):
        sql = """
        SELECT c.CustomerID,
               (SELECT COUNT(*) FROM Orders o WHERE o.CustomerID = c.CustomerID)
        FROM Customers c;
        """
        results = analyze_with_ast_text(sql)
        self.assertTrue(any(r["rule"] == "correlated_subquery" for r in results))

    def test_having_clause_detected(self):
        sql = """
        SELECT CustomerID, COUNT(*) AS OrderCount
        FROM Orders
        GROUP BY CustomerID
        HAVING COUNT(*) > 5;
        """
        results = analyze_with_ast_text(sql)
        self.assertTrue(any(r["rule"] == "having_clause" for r in results))


if __name__ == "__main__":
    unittest.main()