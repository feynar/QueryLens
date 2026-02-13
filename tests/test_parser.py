import unittest
from src.analysis.sql_parser import parse_sql_text


class TestSQLParser(unittest.TestCase):

    def test_parser_runs(self):
        sql = "SELECT * FROM Customers WHERE YEAR(CreatedDate) = 2025;"
        tree, parser = parse_sql_text(sql)
        self.assertIsNotNone(tree)


if __name__ == "__main__":
    unittest.main()
