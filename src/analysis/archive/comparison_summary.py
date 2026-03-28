import json
from pathlib import Path


def generate_summary(comparison_file, output_file):
    with open(comparison_file, "r", encoding="utf-8") as f:
        results = json.load(f)

    total_queries = len(results)
    agreements = sum(1 for r in results if r["agreement"])
    disagreements = total_queries - agreements

    total_regex_issues = sum(r["regex_count"] for r in results)
    total_ast_issues = sum(r["ast_count"] for r in results)

    agreement_rate = agreements / total_queries if total_queries else 0

    summary = {
        "total_queries": total_queries,
        "agreements": agreements,
        "disagreements": disagreements,
        "agreement_rate": round(agreement_rate, 3),
        "total_regex_issues": total_regex_issues,
        "total_ast_issues": total_ast_issues,
        "issue_count_difference": total_ast_issues - total_regex_issues
    }

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)

    print("✔ Comparison summary generated")
    print(json.dumps(summary, indent=4))


if __name__ == "__main__":
    generate_summary(
        "artifacts/eval/regex_vs_ast_comparison.json",
        "artifacts/eval/comparison_summary.json"
    )
