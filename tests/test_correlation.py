import unittest

from src.correlation.correlator import correlate


class TestCorrelation(unittest.TestCase):

    def test_non_sargable_confirmed(self):
        static = [{"query_id": "Q1", "rule": "non_sargable_predicate"}]
        runtime = [{
            "query_id": "Q1",
            "operator": "Index Scan",
            "logical_op": "",
            "estimated_rows": 12000
        }]

        results = correlate(static, runtime)
        self.assertTrue(results[0]["confirmed"])
        self.assertEqual(results[0]["confidence"], "high")

    def test_select_star_not_confirmed(self):
        static = [{"query_id": "Q2", "rule": "select_star"}]
        runtime = [{
            "query_id": "Q2",
            "operator": "Index Seek",
            "logical_op": "",
            "estimated_rows": 10
        }]

        results = correlate(static, runtime)
        self.assertFalse(results[0]["confirmed"])

    def test_complex_join_confirmed_by_hash_join(self):
        static = [{"query_id": "Q3", "rule": "complex_join"}]
        runtime = [{
            "query_id": "Q3",
            "operator": "Hash Match",
            "logical_op": "Inner Join",
            "estimated_rows": 4000
        }]

        results = correlate(static, runtime)
        self.assertTrue(results[0]["confirmed"])

    def test_order_by_no_index_confirmed_by_sort(self):
        static = [{"query_id": "Q4", "rule": "order_by_no_index"}]
        runtime = [{
            "query_id": "Q4",
            "operator": "Sort",
            "logical_op": "",
            "estimated_rows": 1500
        }]

        results = correlate(static, runtime)
        self.assertTrue(results[0]["confirmed"])
        self.assertEqual(results[0]["confidence"], "high")

    def test_window_function_confirmed(self):
        static = [{"query_id": "Q5", "rule": "window_function"}]
        runtime = [{
            "query_id": "Q5",
            "operator": "Sequence Project",
            "logical_op": "",
            "estimated_rows": 500
        }]

        results = correlate(static, runtime)
        self.assertTrue(results[0]["confirmed"])

    def test_having_clause_confirmed(self):
        static = [{"query_id": "Q6", "rule": "having_clause"}]
        runtime = [{
            "query_id": "Q6",
            "operator": "Hash Match",
            "logical_op": "Aggregate",
            "estimated_rows": 800
        }]

        results = correlate(static, runtime)
        self.assertTrue(results[0]["confirmed"])

    def test_missing_index_confirmed_by_missing_index_hint(self):
        static = [{"query_id": "Q7", "rule": "missing_index"}]
        runtime = [{
            "query_id": "Q7",
            "operator": "Index Scan | MISSING INDEX",
            "logical_op": "",
            "estimated_rows": 25000
        }]

        results = correlate(static, runtime)
        self.assertTrue(results[0]["confirmed"])
        self.assertIn(results[0]["confidence"], {"high"})

    def test_missing_index_not_confirmed_when_seek_exists(self):
        static = [{"query_id": "Q8", "rule": "missing_index"}]
        runtime = [{
            "query_id": "Q8",
            "operator": "Index Seek",
            "logical_op": "",
            "estimated_rows": 100
        }]

        results = correlate(static, runtime)
        self.assertFalse(results[0]["confirmed"])


if __name__ == "__main__":
    unittest.main()