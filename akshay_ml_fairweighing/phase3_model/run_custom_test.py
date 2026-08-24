"""
Run Custom Dispute Test Case
Author: Akshay Purohit (ML Engineer)
"""

import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from akshay_ml_fairweighing.phase3_model.fair_weighing_model import FairWeighingModel

# =========================================================
# 🔑 PASTE YOUR GEMINI API KEY HERE (or leave as "" for default template):
GEMINI_API_KEY = ""
# =========================================================

# --- EDIT YOUR CUSTOM CASE HERE ---
my_custom_case = {
    "case_id": "MY-CUSTOM-DISPUTE-001",
    "dispute_category_id": "CAT-01",              # CAT-01: Item Not Received, CAT-03: Unauthorized, etc.
    "dispute_category_name": "Item Not Received",
    "amount": 2999.0,
    "currency": "INR",
    "evidence_items": [
        {
            "evidence_id": "EV-01",
            "evidence_type": "Transaction Record",
            "status": "Present",
            "quality_score": 0.95,
            "favours": "NEUTRAL"
        },
        {
            "evidence_id": "EV-03",                 # Primary evidence for CAT-01
            "evidence_type": "Delivery Confirmation",
            "status": "Missing",                    # Try changing to "Present"
            "quality_score": 0.0,
            "favours": "CARD_MEMBER"
        },
        {
            "evidence_id": "EV-09",
            "evidence_type": "Dispute Reason Statement",
            "status": "Present",
            "quality_score": 0.90,
            "favours": "CARD_MEMBER"
        }
    ]
}


def main():
    # Uses key defined at top of file, or fallback to environment variable
    api_key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", None)
    model = FairWeighingModel(api_key=api_key)

    print("\nEvaluating Custom Dispute Case...")
    result = model.evaluate_case(my_custom_case)

    print("\n================ RESULT SUMMARY ================")
    print(f"Case ID:                 {result['case_id']}")
    print(f"Category:                {result['dispute_category_id']}")
    print(f"Recommended Resolution:  {result['recommended_resolution']}")
    print(f"Confidence Score:        {result['confidence_score']}%")
    print(f"Card Member Score:       {result['card_member_score']}%")
    print(f"Merchant Score:          {result['merchant_score']}%")
    print("\nPlain Language Explanation:")
    print(f"'{result['plain_language_explanation']}'")
    print("\nContributing Factors:")
    for factor in result['contributing_factors']:
        print(f"  * {factor}")
    print("=================================================\n")


if __name__ == "__main__":
    main()
