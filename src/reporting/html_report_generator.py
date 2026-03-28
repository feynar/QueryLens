"""
QueryLens — HTML Report Generator (Week 13)

Converts runtime validation results into a formatted HTML report.
"""

import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_PATH = os.path.join(PROJECT_ROOT, "artifacts", "eval", "full_pipeline_report.json")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "artifacts", "reports", "runtime_validation_report.html")


def load_results():
    with open(INPUT_PATH, "r") as f:
        return json.load(f)


def build_html(report):
    metrics = report["global_metrics"]
    rows = report["per_query_results"]

    table_rows = ""
    for r in rows:
        table_rows += f"""
        <tr>
            <td>{r['query']}</td>
            <td>{r['static_warnings']}</td>
            <td>{r['confirmed_warnings']}</td>
            <td>{r['confirmation_rate']}</td>
        </tr>
        """

    html = f"""
    <html>
    <head>
        <title>QueryLens Runtime Validation Report</title>
        <style>
            body {{ font-family: Arial; margin: 40px; }}
            h1 {{ color: #2c3e50; }}
            table {{ border-collapse: collapse; width: 80%; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: center; }}
            th {{ background-color: #f4f4f4; }}
        </style>
    </head>

    <body>
        <h1>QueryLens Runtime Validation Report</h1>

        <h2>Global Metrics</h2>
        <p><b>Total Static Warnings:</b> {metrics['total_static_warnings']}</p>
        <p><b>Total Confirmed Warnings:</b> {metrics['total_confirmed_warnings']}</p>
        <p><b>Confirmation Rate:</b> {metrics['confirmation_rate']}</p>

        <h2>Per-Query Results</h2>
        <table>
            <tr>
                <th>Query</th>
                <th>Static Warnings</th>
                <th>Confirmed Warnings</th>
                <th>Confirmation Rate</th>
            </tr>
            {table_rows}
        </table>

        <h2>System Pipeline</h2>
        <p>
        QueryLens performs static SQL analysis, extracts execution plan operators,
        correlates detected anti-patterns with runtime behavior, and evaluates
        confirmation agreement between analysis layers.
        </p>
    </body>
    </html>
    """

    return html


def generate_report():
    report = load_results()
    html = build_html(report)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w") as f:
        f.write(html)

    print("✔ HTML report generated")


if __name__ == "__main__":
    generate_report()