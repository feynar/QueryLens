"""
QueryLens — HTML Report Generator

Builds a human-readable HTML report showing:
- global metrics
- per-query summary
- detailed rule findings
- recommendations
- rewrite suggestions
- confidence-based color intensity
- expand/collapse per query
"""

import json
import os
import html
from collections import defaultdict

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

SUMMARY_INPUT = os.path.join(
    PROJECT_ROOT, "artifacts", "evaluation", "expanded_runtime_report.json"
)
DETAIL_INPUT = os.path.join(
    PROJECT_ROOT, "artifacts", "analysis", "correlation_output.json"
)
STATIC_INPUT = os.path.join(
    PROJECT_ROOT, "artifacts", "analysis", "static_results.json"
)
OUTPUT_PATH = os.path.join(
    PROJECT_ROOT, "artifacts", "reports", "runtime_validation_report.html"
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_results():
    summary_report = load_json(SUMMARY_INPUT)
    correlation_results = load_json(DETAIL_INPUT)
    static_results = load_json(STATIC_INPUT)
    return summary_report, correlation_results, static_results


def group_details_by_query(correlation_results):
    grouped = defaultdict(list)
    for item in correlation_results:
        query_id = item.get("query_id", "unknown")
        grouped[query_id].append(item)
    return grouped


def build_static_lookup(static_results):
    lookup = {}
    for item in static_results:
        key = (item.get("query_id"), item.get("rule"))
        lookup[key] = item
    return lookup


def get_row_class(confirmed, confidence, validation_type=None):
    if validation_type == "static-only":
        return "static-only"

    if not confirmed:
        return "not-confirmed"

    if confidence == "high":
        return "confirmed-high"
    if confidence == "medium":
        return "confirmed-medium"
    return "confirmed-low"


def get_summary_class(confirmed_warnings, static_warnings):
    if static_warnings == 0:
        return "summary-neutral"
    if confirmed_warnings == static_warnings:
        return "summary-good"
    if confirmed_warnings == 0:
        return "summary-bad"
    return "summary-mixed"


def render_recommendation_block(details):
    if not details:
        return "<p>None</p>"

    issue = html.escape(str(details.get("issue", "N/A")))
    impact = html.escape(str(details.get("impact", "N/A")))
    recommendation = html.escape(str(details.get("recommendation", "N/A")))

    return f"""
    <div class="recommendation-box">
        <p><b>Issue:</b> {issue}</p>
        <p><b>Impact:</b> {impact}</p>
        <p><b>Recommendation:</b> {recommendation}</p>
    </div>
    """


def render_rewrites_block(rewrites):
    if not rewrites:
        return "<p>None</p>"

    items = []
    for rw in rewrites:
        rule = html.escape(str(rw.get("rule", "unknown")))
        issue = html.escape(str(rw.get("issue", "N/A")))
        suggestion = html.escape(str(rw.get("suggestion", "N/A")))
        example = html.escape(str(rw.get("example", "N/A")))

        items.append(f"""
        <div class="rewrite-box">
            <p><b>Rule:</b> {rule}</p>
            <p><b>Issue:</b> {issue}</p>
            <p><b>Suggestion:</b> {suggestion}</p>
            <p><b>Example:</b></p>
            <pre>{example}</pre>
        </div>
        """)

    return "\n".join(items)

def build_per_query_summary(rows):
    rows = sorted(rows, key=lambda r: r["query"])

    table_rows = []
    for r in rows:
        query = html.escape(str(r.get("query", "unknown")))
        static_warnings = r.get("static_warnings", 0)
        confirmed_warnings = r.get("confirmed_warnings", 0)
        confirmation_rate = r.get("confirmation_rate", 0)

        summary_class = get_summary_class(confirmed_warnings, static_warnings)

        table_rows.append(f"""
        <tr class="{summary_class}">
            <td>{query}</td>
            <td>{static_warnings}</td>
            <td>{confirmed_warnings}</td>
            <td>{confirmation_rate}</td>
        </tr>
        """)

    return "\n".join(table_rows)

def render_operator_summary(details):
    if not details:
        return ""

    evidence = details[0].get("evidence", {})

    return f"""
    <div class="operator-summary">
        <div><b>Scans</b><br>{html.escape(str(evidence.get("scan_count", 0)))}</div>
        <div><b>Seeks</b><br>{html.escape(str(evidence.get("seek_count", 0)))}</div>
        <div><b>Sorts</b><br>{html.escape(str(evidence.get("sort_count", 0)))}</div>
        <div><b>Hash Joins</b><br>{html.escape(str(evidence.get("hash_join_count", 0)))}</div>
        <div><b>Nested Loops</b><br>{html.escape(str(evidence.get("nested_loop_count", 0)))}</div>
        <div><b>Key Lookups</b><br>{html.escape(str(evidence.get("key_lookup_count", 0)))}</div>
    </div>
    """

def build_detailed_findings(rows, grouped_details, static_lookup):
    rows = sorted(rows, key=lambda r: r["query"])
    sections = []

    for row in rows:
        query_name = row.get("query", "unknown")
        query_key = os.path.splitext(query_name)[0]
        safe_query_name = html.escape(str(query_name))
        static_warnings = row.get("static_warnings", 0)
        confirmed_warnings = row.get("confirmed_warnings", 0)
        confirmation_rate = row.get("confirmation_rate", 0)

        summary_class = get_summary_class(confirmed_warnings, static_warnings)
        details = grouped_details.get(query_key, [])
        
        operator_summary_html = render_operator_summary(details)

        if not details:
            sections.append(f"""
            <details class="query-details">
                <summary>{safe_query_name}</summary>
                <div class="query-section">
                    <p class="summary-line {summary_class}">
                        <b>Summary:</b> {confirmed_warnings} / {static_warnings} runtime-verifiable findings confirmed
                    </p>

                    <p>
                        Runtime-Verifiable Warnings: {static_warnings} |
                        Runtime-Confirmed Findings: {confirmed_warnings} |
                        Rate: {confirmation_rate}
                    </p>

                    <p><b>No runtime-verifiable findings.</b></p>
                    <p>
                        This query triggered no runtime-verifiable warnings.
                    </p>

                    <h4>Recommendations</h4>
                    <p>None</p>

                    <h4>Rewrite Suggestions</h4>
                    <p>None</p>
                </div>
            </details>
            """)
            continue

        detail_rows = []
        seen_rewrites = []
        seen_rewrite_keys = set()

        for item in details:
            rule_name = item.get("rule", "unknown")
            rule = html.escape(str(rule_name))
            confirmed = item.get("confirmed", False)
            raw_confidence = item.get("confidence", "none")
            raw_validation_type = item.get("validation_type", "unknown")

            if raw_validation_type == "static-only":
                confirmed_display = "N/A"
                confidence_display = "N/A"
            else:
                confirmed_display = str(confirmed)
                confidence_display = str(raw_confidence)

            confidence = html.escape(confidence_display)
            validation_type = html.escape(str(raw_validation_type))
            reason = html.escape(str(item.get("reason", "No explanation available")))

            evidence = item.get("evidence", {})
            max_actual_rows = evidence.get("max_actual_rows", 0)
            max_actual_executions = evidence.get("max_actual_executions", 0)
            total_actual_executions = evidence.get("total_actual_executions", 0)
            scan_count = evidence.get("scan_count", 0)
            has_actual_stats = evidence.get("has_actual_stats", False)

            evidence_html = ""

            if raw_validation_type != "static-only":
                if raw_validation_type != "static-only":
                    evidence_html = f"""
                    <div class="evidence-box">
                        <p><b>Max Actual Rows:</b> {html.escape(str(max_actual_rows))}</p>
                        <p><b>Max Actual Executions:</b> {html.escape(str(max_actual_executions))}</p>
                        <p><b>Total Actual Executions:</b> {html.escape(str(total_actual_executions))}</p>
                        <p><b>Scan Count:</b> {html.escape(str(scan_count))}</p>
                        <p><b>Actual Stats Available:</b> {html.escape(str(has_actual_stats))}</p>
                    </div>
                    """

            row_class = get_row_class(
                confirmed,
                raw_confidence,
                raw_validation_type
            )

            static_item = static_lookup.get((query_key, rule_name), {})
            recommendation_html = render_recommendation_block(
                static_item.get("details") or static_item.get("recommendation")
            )

            rewrites = item.get("rewrites", [])
            for rw in rewrites:
                rw_key = (
                    rw.get("rule"),
                    rw.get("issue"),
                    rw.get("suggestion"),
                    rw.get("example"),
                )
                if rw_key not in seen_rewrite_keys:
                    seen_rewrite_keys.add(rw_key)
                    seen_rewrites.append(rw)

            detail_rows.append(f"""
            <tr class="{row_class}">
                <td>{rule}</td>
                <td>{html.escape(confirmed_display)}</td>
                <td>{confidence}</td>
                <td>{validation_type}</td>
                <td>{reason}{evidence_html}</td>
                <td>{recommendation_html}</td>
            </tr>
            """)

        rewrites_html = render_rewrites_block(seen_rewrites)

        sections.append(f"""
        <details class="query-details">
            <summary>{safe_query_name}</summary>
            <div class="query-section">
                <p class="summary-line {summary_class}">
                    <b>Summary:</b> {confirmed_warnings} / {static_warnings} runtime-verifiable findings confirmed
                </p>

                <p>
                    Runtime-Verifiable Warnings: {static_warnings} |
                    Runtime-Confirmed Findings: {confirmed_warnings} |
                    Rate: {confirmation_rate}
                </p>
    
                <h4>Operator Summary</h4>
                {operator_summary_html}
    
                <table class="detail-table">
                    <tr>
                        <th>Rule</th>
                        <th>Confirmed</th>
                        <th>Confidence</th>
                        <th>Validation Type</th>
                        <th>Reason</th>
                        <th>Recommendation</th>
                    </tr>
                    {''.join(detail_rows)}
                </table>

                <h4>Rewrite Suggestions</h4>
                {rewrites_html}
            </div>
        </details>
        """)

    return "\n".join(sections)


def build_html(summary_report, correlation_results, static_results):
    metrics = summary_report["global_metrics"]
    rows = summary_report["per_query_results"]
    grouped_details = group_details_by_query(correlation_results)
    static_lookup = build_static_lookup(static_results)

    per_query_summary_html = build_per_query_summary(rows)
    detailed_findings_html = build_detailed_findings(
        rows,
        grouped_details,
        static_lookup
    )

    html_output = f"""
    <html>
    <head>
        <title>QueryLens Runtime Validation Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                color: #222;
                background: #fff;
            }}

            h1 {{
                color: #2c3e50;
                margin-bottom: 8px;
            }}

            h2 {{
                margin-top: 30px;
                color: #2c3e50;
                border-bottom: 2px solid #eee;
                padding-bottom: 6px;
            }}

            h4 {{
                margin-top: 18px;
                color: #444;
            }}

            p {{
                max-width: 1000px;
                line-height: 1.5;
            }}

            table {{
                border-collapse: collapse;
                width: 100%;
                margin-top: 12px;
                margin-bottom: 20px;
            }}

            th, td {{
                border: 1px solid #ccc;
                padding: 10px;
                text-align: left;
                vertical-align: top;
            }}

            th {{
                background-color: #f4f4f4;
            }}

            details.query-details {{
                margin-top: 18px;
                border: 1px solid #ddd;
                border-radius: 8px;
                background: #fafafa;
                padding: 0;
                overflow: hidden;
            }}

            details.query-details summary {{
                cursor: pointer;
                padding: 14px 18px;
                font-weight: bold;
                color: #34495e;
                background: #f0f3f5;
                list-style: none;
            }}

            details.query-details summary::-webkit-details-marker {{
                display: none;
            }}

            details.query-details summary::before {{
                content: "▶ ";
                font-size: 12px;
            }}

            details.query-details[open] summary::before {{
                content: "▼ ";
            }}

            .query-section {{
                padding: 18px;
                background: #fafafa;
            }}

            .recommendation-box {{
                background: #fff;
                border: 1px solid #e3e3e3;
                border-radius: 6px;
                padding: 10px;
            }}

            .rewrite-box {{
                background: #fff;
                border: 1px solid #e3e3e3;
                border-radius: 6px;
                padding: 10px;
                margin-bottom: 12px;
            }}

            pre {{
                background: #f7f7f7;
                border: 1px solid #ddd;
                padding: 10px;
                overflow-x: auto;
                white-space: pre-wrap;
                word-break: break-word;
            }}

            .metric-list p {{
                margin: 6px 0;
            }}

            .summary-line {{
                margin: 10px 0 6px 0;
                padding: 8px 10px;
                border-radius: 6px;
                display: inline-block;
            }}

            .summary-good {{
                background-color: #d4edda;
            }}

            .summary-mixed {{
                background-color: #fff3cd;
            }}

            .summary-bad {{
                background-color: #f8d7da;
            }}

            .summary-neutral {{
                background-color: #e2e3e5;
            }}

            .confirmed-high {{
                background-color: #8fd19e;
                font-weight: bold;
            }}

            .confirmed-medium {{
                background-color: #c3e6cb;
                font-weight: bold;
            }}

            .confirmed-low {{
                background-color: #e2f0d9;
                font-weight: bold;
            }}

            .not-confirmed {{
                background-color: #f8d7da;
                font-weight: bold;
            }}

            .static-only {{
                background-color: #e2e3e5;
                font-weight: bold;
            }}  

            .evidence-box {{
                margin-top: 8px;
                padding: 8px;
                background: #f7f7f7;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 0.9em;
            }}

            .evidence-box p {{
                margin: 3px 0;
            }}            
            
            .operator-summary {{
                display: grid;
                grid-template-columns: repeat(6, 1fr);
                gap: 10px;
                margin: 12px 0 18px 0;
            }}

            .operator-summary div {{
                background: #fff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <h1>QueryLens Validation-Aware Analysis Report</h1>

        <p>
            This report summarizes runtime validation results for QueryLens by comparing
            runtime-verifiable static warnings against SQL Server execution plan evidence.
        </p>

        <p>
            It includes global metrics, per-query summaries, detailed rule findings,
            plain-language recommendations, and rewrite suggestions.
        </p>

        <h2>Global Metrics</h2>
        <div class="metric-list">
            <p><b>Total Runtime-Verifiable Static Warnings:</b> {metrics['total_static_warnings']}</p>
            <p><b>Total Runtime-Confirmed Findings:</b> {metrics['total_confirmed_warnings']}</p>
            <p><b>Confirmation Rate:</b> {metrics['confirmation_rate']}</p>
        </div>

        <h2>Per-Query Summary</h2>
        <table>
            <tr>
                <th>Query</th>
                <th>Runtime-Verifiable Warnings</th>
                <th>Runtime-Confirmed Findings</th>
                <th>Confirmation Rate</th>
            </tr>
            {per_query_summary_html}
        </table>

        <h2>Detailed Rule Findings</h2>
        {detailed_findings_html}
    </body>
    </html>
    """
    return html_output


def generate_report():
    summary_report, correlation_results, static_results = load_results()
    html_output = build_html(summary_report, correlation_results, static_results)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_output)

    print(f"✔ HTML report generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_report()