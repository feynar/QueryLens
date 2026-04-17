import json
import os
import unittest

from src.correlation.correlator import correlate

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestPipelineIntegration(unittest.TestCase):

    def test_pipeline_outputs_correlate(self):
        static_path = os.path.join(BASE_DIR, "artifacts", "analysis", "static_results.json")
        runtime_path = os.path.join(BASE_DIR, "artifacts", "analysis", "plan_results.json")

        self.assertTrue(os.path.exists(static_path), f"Missing file: {static_path}")
        self.assertTrue(os.path.exists(runtime_path), f"Missing file: {runtime_path}")

        with open(static_path, "r", encoding="utf-8") as f:
            static_data = json.load(f)

        with open(runtime_path, "r", encoding="utf-8") as f:
            runtime_data = json.load(f)

        self.assertIsInstance(static_data, list)
        self.assertIsInstance(runtime_data, list)
        self.assertGreater(len(static_data), 0)
        self.assertGreater(len(runtime_data), 0)

        # Correlate all available findings as a smoke/integration test.
        results = correlate(static_data, runtime_data)

        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

        required_keys = {
            "query_id",
            "rule",
            "confirmed",
            "suppressed",
            "validated",
            "validation_type",
            "confidence",
            "score",
            "evidence",
            "reason",
        }

        for item in results[:5]:
            self.assertTrue(required_keys.issubset(item.keys()))


if __name__ == "__main__":
    unittest.main()