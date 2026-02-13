import unittest
from src.correlation.correlator import correlate


class TestCorrelation(unittest.TestCase):

    def test_non_sargable_confirmed(self):
        static = [{"query_id": "Q1", "issue_type": "NON_SARGABLE_PREDICATE"}]
        runtime = [{"query_id": "Q1", "operator": "Index Scan", "estimated_rows": 12000}]

        results = correlate(static, runtime)
        self.assertTrue(results[0]["confirmed"])
        self.assertEqual(results[0]["confidence"], "high")

    def test_select_star_not_confirmed(self):
        static = [{"query_id": "Q2", "issue_type": "SELECT_STAR"}]
        runtime = [{"query_id": "Q2", "operator": "Index Seek", "estimated_rows": 10}]

        results = correlate(static, runtime)
        self.assertFalse(results[0]["confirmed"])

    def test_complex_join_hash(self):
        static = [{"query_id": "Q3", "issue_type": "COMPLEX_JOIN"}]
        runtime = [{"query_id": "Q3", "operator": "Hash Match", "estimated_rows": 4000}]

        results = correlate(static, runtime)
        self.assertTrue(results[0]["confirmed"])


if __name__ == "__main__":
    unittest.main()
