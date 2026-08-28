"""
Unit Tests for Fair-Weighing Model
Author: Akshay Purohit (202512033) - ML Engineer
"""

import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from akshay_ml_fairweighing.phase3_model.fair_weighing_model import FairWeighingModel


class TestFairWeighingModel(unittest.TestCase):

    def setUp(self):
        self.model = FairWeighingModel()

    def test_missing_primary_evidence_escalation(self):
        """Test that missing primary evidence results in escalation or penalty."""
        case = {
            "case_id": "TEST-01",
            "dispute_category_id": "CAT-01",
            "dispute_category_name": "Item Not Received",
            "evidence_items": [
                {"evidence_id": "EV-01", "evidence_type": "Transaction Record", "status": "Present", "quality_score": 0.9, "favours": "NEUTRAL"},
                {"evidence_id": "EV-03", "evidence_type": "Delivery Confirmation", "status": "Missing", "quality_score": 0.0, "favours": "MERCHANT"}
            ]
        }
        res = self.model.evaluate_case(case)
        self.assertIn("recommended_resolution", res)
        self.assertLessEqual(res["confidence_score"], 60.0)

    def test_merchant_clear_win(self):
        """Test strong merchant evidence leads to MERCHANT_FAVOUR."""
        case = {
            "case_id": "TEST-02",
            "dispute_category_id": "CAT-03",
            "dispute_category_name": "Unauthorized Transaction",
            "evidence_items": [
                {"evidence_id": "EV-01", "evidence_type": "Transaction Record", "status": "Present", "quality_score": 0.95, "favours": "NEUTRAL"},
                {"evidence_id": "EV-08", "evidence_type": "Authentication Log", "status": "Present", "quality_score": 0.98, "favours": "MERCHANT"},
                {"evidence_id": "EV-02", "evidence_type": "Merchant Receipt", "status": "Present", "quality_score": 0.90, "favours": "MERCHANT"}
            ]
        }
        res = self.model.evaluate_case(case)
        self.assertEqual(res["recommended_resolution"], "MERCHANT_FAVOUR")
        self.assertGreaterEqual(res["confidence_score"], 70.0)

    def test_card_member_clear_win(self):
        """Test strong card member evidence leads to CARD_MEMBER_FAVOUR."""
        case = {
            "case_id": "TEST-03",
            "dispute_category_id": "CAT-04",
            "dispute_category_name": "Duplicate Charge",
            "evidence_items": [
                {"evidence_id": "EV-01", "evidence_type": "Transaction Record", "status": "Present", "quality_score": 0.99, "favours": "NEUTRAL"},
                {"evidence_id": "EV-01_DUP", "evidence_type": "Duplicate Transaction Record", "status": "Present", "quality_score": 0.99, "favours": "CARD_MEMBER"},
                {"evidence_id": "EV-09", "evidence_type": "Dispute Statement", "status": "Present", "quality_score": 0.90, "favours": "CARD_MEMBER"}
            ]
        }
        res = self.model.evaluate_case(case)
        self.assertEqual(res["recommended_resolution"], "CARD_MEMBER_FAVOUR")
        self.assertGreaterEqual(res["confidence_score"], 70.0)

    def test_contributing_factors_count(self):
        """Ensure AC-10 requirement: at least 3 contributing factors included."""
        case = {
            "case_id": "TEST-04",
            "dispute_category_id": "CAT-01",
            "evidence_items": [
                {"evidence_id": "EV-01", "evidence_type": "Transaction Record", "status": "Present", "quality_score": 0.9, "favours": "NEUTRAL"}
            ]
        }
        res = self.model.evaluate_case(case)
        self.assertGreaterEqual(len(res["contributing_factors"]), 3)


if __name__ == "__main__":
    unittest.main()
