import os
import json

from src.analysis.legacy_regex_rules import analyze_with_regex
from src.analysis.static_analyzer import analyze_sql  # AST analyzer


def compare_on_file(sql_file):
    regex_results = analyze_with_regex(sql_file)
    ast_results = analyze_sql(sql_file)

    regex_issues = sorted(set(r["issue_type"] for r in regex_results))
    ast_issues = sorted(set(r["issue_type"] for r in ast_results))

    return {
        "query": os.path.basename(sql_file),
        "regex_issues": regex_issues,
        "ast_issues": ast_issues,
        "regex_count": len(regex_issues),
        "ast_count": len(ast_issues),
        "agreement": regex_issues == ast_issues
    }


def run_comparison(dataset_folder):
    comparisons = []

    for file in os.listdir(dataset_folder):
        if file.endswith(".sql"):
            path = os.path.join(dataset_folder, file)
            comparisons.append(compare_on_file(path))

    return comparisons


def save_comparison(results, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w") as f:
        json.dump(results, f, indent=4)

    print("✔ Comparison results saved:", out_path)


if __name__ == "__main__":
    results = run_comparison("datasets")
    save_comparison(results, "artifacts/evaluation/regex_vs_ast_comparison.json")
