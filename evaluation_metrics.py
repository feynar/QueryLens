import json
import os


def generate_metrics(correlation_file, output_file):
    with open(correlation_file, "r") as f:
        results = json.load(f)

    static_warnings = len(results)
    confirmed = sum(1 for r in results if r["confirmed"])
    suppressed = static_warnings - confirmed
    confirmation_rate = confirmed / static_warnings if static_warnings else 0

    metrics = {
        "static_warnings": static_warnings,
        "confirmed": confirmed,
        "suppressed": suppressed,
        "confirmation_rate": round(confirmation_rate, 2)
    }

    os.makedirs("artifacts", exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(metrics, f, indent=4)

    print("✔ Evaluation metrics saved")
    print(json.dumps(metrics, indent=4))


if __name__ == "__main__":
    generate_metrics(
        "artifacts/correlation_output.json",
        "artifacts/evaluation_metrics.json"
    )