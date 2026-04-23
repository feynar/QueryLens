"""
QueryLens — Static Test Log Generator

Runs the AST-based static analysis unit tests and writes the results
to a plain-text artifact for proposal traceability.
"""

import io
import os
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "artifacts", "static_test_log.txt")


def generate_static_test_log():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName("tests.test_ast_rules")

    stream = io.StringIO()
    runner = unittest.TextTestRunner(stream=stream, verbosity=2)
    result = runner.run(suite)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("QueryLens Static Analysis Test Log\n")
        f.write("=================================\n\n")
        f.write(stream.getvalue())
        f.write("\n")
        f.write(f"Ran {result.testsRun} tests\n")
        f.write(f"Failures: {len(result.failures)}\n")
        f.write(f"Errors: {len(result.errors)}\n")
        f.write(f"Successful: {result.wasSuccessful()}\n")

    print(f"✔ Static test log generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_static_test_log()