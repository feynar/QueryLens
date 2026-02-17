import unittest
import tempfile
import os

from src.analysis.static_analyzer import analyze_sql, analyze_with_ast_text



def run_sql(sql_text):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sql", mode="w") as tmp:
        tmp.write(sql_text)
        tmp_path = tmp.name

    results = analyze_sql(tmp_path)
    os.remove(tmp_path)
    return results


class TestASTRules(unittest.TestCase):

    def test_select_star_detected(self):
        sql = "SELECT * FROM Customers;"
        results = run_sql(sql)
        self.assertTrue(any(r["issue_type"] == "SELECT_STAR" for r in results))

    def test_non_sargable_function_detected(self):
        sql = "SELECT CustomerID FROM Customers WHERE YEAR(CreatedDate) = 2025;"
        results = run_sql(sql)
        self.assertTrue(any(r["issue_type"] == "NON_SARGABLE_PREDICATE" for r in results))

    def test_complex_join_detected(self):
        sql = """
        SELECT *
        FROM A
        JOIN B ON A.id = B.id
        JOIN C ON B.id = C.id;
        """
        results = run_sql(sql)
        self.assertTrue(any(r["issue_type"] == "COMPLEX_JOIN" for r in results))

    def test_function_on_constant_not_flagged(self):
        sql = "SELECT * FROM Orders WHERE OrderDate >= GETDATE();"
        results = analyze_with_ast_text(sql)
        self.assertFalse(any(r["issue_type"] == "NON_SARGABLE_PREDICATE" for r in results))

if __name__ == "__main__":
    unittest.main()
