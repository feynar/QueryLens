import json
import os
import unittest
from src.correlation.correlator import correlate

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class TestPipelineIntegration(unittest.TestCase):

    def test_pipeline_outputs_correlate(self):
        static_path = os.path.join(BASE_DIR, "artifacts", "analyzer", "static_results.json")
        runtime_path = os.path.join(BASE_DIR, "artifacts", "analyzer", "plan_results.json")

        self.assertTrue(os.path.exists(static_path))
        self.assertTrue(os.path.exists(runtime_path))

        with open(static_path) as f:
            static_data = json.load(f)
        with open(runtime_path) as f:
            runtime_data = json.load(f)

        results = correlate(static_data, runtime_data)
        self.assertTrue(len(results) > 0)
