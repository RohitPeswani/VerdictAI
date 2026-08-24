"""
Model Validation Script
Runs FairWeighingModel against all 56 synthetic dispute cases in mock_disputes_dataset.json.
Calculates Accuracy, False Positive Rate (FPR), Escalation Rate, and Latency metrics.
Author: Akshay Purohit (202512033) - ML Engineer
"""

import json
import time
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from akshay_ml_fairweighing.phase3_model.fair_weighing_model import FairWeighingModel


def validate_model():
    dataset_path = os.path.join(os.path.dirname(__file__), "..", "phase2_mockdata", "mock_disputes_dataset.json")
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}")
        return

    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    cases = dataset.get("cases", [])
    print(f"Loaded {len(cases)} dispute benchmark cases.\n")

    model = FairWeighingModel()

    total_cases = len(cases)
    correct_matches = 0
    false_positives = 0  # Resolved against ground truth (e.g. MR win when GT was CM win)
    escalated_count = 0
    latencies = []

    results_summary = []

    start_total_time = time.time()

    for case in cases:
        t0 = time.time()
        output = model.evaluate_case(case)
        t1 = time.time()
        elapsed_ms = (t1 - t0) * 1000.0
        latencies.append(elapsed_ms)

        gt = case.get("ground_truth_resolution")
        rec = output.get("recommended_resolution")
        conf = output.get("confidence_score")

        is_correct = (rec == gt)
        if is_correct:
            correct_matches += 1

        if rec == "ESCALATE":
            escalated_count += 1
        elif rec != gt:
            false_positives += 1

        results_summary.append({
            "case_id": case.get("case_id"),
            "category": case.get("dispute_category_id"),
            "ground_truth": gt,
            "predicted": rec,
            "confidence": conf,
            "is_correct": is_correct,
            "latency_ms": round(elapsed_ms, 2)
        })

    total_time = time.time() - start_total_time

    accuracy = (correct_matches / total_cases) * 100.0
    fpr = (false_positives / total_cases) * 100.0
    esc_rate = (escalated_count / total_cases) * 100.0
    avg_latency = sum(latencies) / len(latencies)

    print("================ MODEL VALIDATION REPORT ================")
    print(f"Total Cases Tested:      {total_cases}")
    print(f"Correct Predictions:    {correct_matches} / {total_cases} ({accuracy:.2f}%)")
    print(f"False Positive Rate:    {false_positives} / {total_cases} ({fpr:.2f}%) [Target: <= 2.0%]")
    print(f"Escalation Rate:        {escalated_count} / {total_cases} ({esc_rate:.2f}%)")
    print(f"Average Execution Time: {avg_latency:.2f} ms")
    print(f"Total Validation Time:  {total_time:.2f} s")
    print("=========================================================\n")

    # Save Validation Results
    val_out_path = os.path.join(os.path.dirname(__file__), "validation_results.json")
    val_report = {
        "validation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "total_cases": total_cases,
            "accuracy_pct": round(accuracy, 2),
            "false_positive_rate_pct": round(fpr, 2),
            "escalation_rate_pct": round(esc_rate, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "nfr_14_compliant": fpr <= 2.0 or false_positives <= 1
        },
        "details": results_summary
    }

    with open(val_out_path, "w") as f:
        json.dump(val_report, f, indent=2)

    print(f"Validation report saved to {val_out_path}")


if __name__ == "__main__":
    validate_model()
