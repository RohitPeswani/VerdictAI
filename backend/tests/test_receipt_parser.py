"""
Test Suite for ReceiptParser — Evidence Ingestion Pipeline
Author: Achyut Pathak (AI/NLP Engineer — Evidence Parsing)
"""

import pytest

from backend.app.services.parsers.receipt_parser import ReceiptParser
from backend.app.services.parsers.base_parser import (
    AnomalyLevel,
    ClaimAlignment,
    ParsedEvidence,
)


@pytest.fixture
def parser():
    return ReceiptParser()


@pytest.fixture
def full_receipt_payload():
    """Complete receipt payload with line items and all optional fields."""
    return {
        "merchant_name": "Apex Electronics Direct",
        "total": 339.97,
        "currency": "USD",
        "receipt_number": "INV-2026-08-001",
        "receipt_date": "2026-08-20",
        "subtotal": 319.97,
        "tax": 20.00,
        "payment_method": "VISA ****4242",
        "line_items": [
            {"description": "Wireless Headphones", "quantity": 1, "unit_price": 299.99},
            {"description": "USB-C Cable (3-pack)", "quantity": 2, "unit_price": 9.99},
        ],
        "transaction_amount": 339.97,
    }


@pytest.fixture
def minimal_receipt_payload():
    """Receipt with only required fields."""
    return {
        "merchant_name": "Corner Shop",
        "total": 25.50,
    }


# ── Validation Tests ─────────────────────────────────────────────

class TestReceiptParserValidation:

    def test_validate_complete_payload(self, parser, full_receipt_payload):
        assert parser.validate(full_receipt_payload) is True

    def test_validate_minimal_payload(self, parser, minimal_receipt_payload):
        assert parser.validate(minimal_receipt_payload) is True

    def test_validate_missing_merchant_name(self, parser):
        assert parser.validate({"total": 100.0}) is False

    def test_validate_missing_total(self, parser):
        assert parser.validate({"merchant_name": "Test"}) is False

    def test_validate_empty_payload(self, parser):
        assert parser.validate({}) is False

    def test_validate_none_values(self, parser):
        assert parser.validate({"merchant_name": None, "total": 10.0}) is False


# ── Core Parsing Tests ───────────────────────────────────────────

class TestReceiptParserParsing:

    def test_parse_full_receipt(self, parser, full_receipt_payload):
        result = parser.parse(full_receipt_payload)
        assert isinstance(result, ParsedEvidence)
        assert result.parser_name == "ReceiptParser"
        assert result.structured_data["merchant_name"] == "Apex Electronics Direct"
        assert result.structured_data["total"] == 339.97
        assert result.structured_data["receipt_number"] == "INV-2026-08-001"
        assert result.structured_data["subtotal"] == 319.97
        assert result.structured_data["tax"] == 20.00
        assert result.structured_data["line_item_count"] == 2

    def test_parse_minimal_receipt(self, parser, minimal_receipt_payload):
        result = parser.parse(minimal_receipt_payload)
        assert result.structured_data["merchant_name"] == "Corner Shop"
        assert result.structured_data["total"] == 25.50
        assert result.structured_data["currency"] == "USD"

    def test_parse_raises_on_missing_required(self, parser):
        with pytest.raises(ValueError, match="missing required fields"):
            parser.parse({"merchant_name": "Test"})

    def test_parse_line_items(self, parser, full_receipt_payload):
        result = parser.parse(full_receipt_payload)
        items = result.structured_data["line_items"]
        assert len(items) == 2
        assert items[0]["description"] == "Wireless Headphones"
        assert items[0]["quantity"] == 1
        assert items[0]["unit_price"] == 299.99
        assert items[0]["line_total"] == 299.99
        assert items[1]["line_total"] == 19.98  # 2 * 9.99


# ── Entity Extraction Tests ──────────────────────────────────────

class TestReceiptParserEntities:

    def test_extracts_merchant_entity(self, parser, full_receipt_payload):
        result = parser.parse(full_receipt_payload)
        merchant_entities = [e for e in result.extracted_entities if e.entity_type == "MERCHANT"]
        assert len(merchant_entities) >= 1
        assert merchant_entities[0].text == "Apex Electronics Direct"

    def test_extracts_money_entity(self, parser, full_receipt_payload):
        result = parser.parse(full_receipt_payload)
        money_entities = [e for e in result.extracted_entities if e.entity_type == "MONEY"]
        assert len(money_entities) >= 1

    def test_extracts_receipt_number(self, parser, full_receipt_payload):
        result = parser.parse(full_receipt_payload)
        receipt_entities = [e for e in result.extracted_entities if e.entity_type == "RECEIPT_NUMBER"]
        assert len(receipt_entities) == 1
        assert receipt_entities[0].text == "INV-2026-08-001"

    def test_extracts_date_entity(self, parser, full_receipt_payload):
        result = parser.parse(full_receipt_payload)
        date_entities = [e for e in result.extracted_entities if e.entity_type == "DATE"]
        assert len(date_entities) >= 1

    def test_extracts_payment_method(self, parser, full_receipt_payload):
        result = parser.parse(full_receipt_payload)
        pm_entities = [e for e in result.extracted_entities if e.entity_type == "PAYMENT_METHOD"]
        assert len(pm_entities) == 1

    def test_ocr_entity_extraction(self, parser):
        payload = {
            "merchant_name": "Test Store",
            "total": 99.99,
            "ocr_text": "Invoice #ABC-12345 dated 08/20/2026 for $99.99",
        }
        result = parser.parse(payload)
        entity_types = [e.entity_type for e in result.extracted_entities]
        assert "MONEY" in entity_types
        assert "RECEIPT_NUMBER" in entity_types


# ── Anomaly Detection Tests ──────────────────────────────────────

class TestReceiptParserAnomalies:

    def test_no_anomalies_matching_amounts(self, parser, full_receipt_payload):
        """When receipt total matches transaction amount, no discrepancy."""
        result = parser.parse(full_receipt_payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "AMOUNT_DISCREPANCY" not in anomaly_types

    def test_amount_discrepancy_detected(self, parser):
        payload = {
            "merchant_name": "Test Store",
            "total": 150.00,
            "transaction_amount": 100.00,
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "AMOUNT_DISCREPANCY" in anomaly_types
        discrepancy_anomaly = [a for a in result.anomalies if a.anomaly_type == "AMOUNT_DISCREPANCY"][0]
        assert discrepancy_anomaly.severity == AnomalyLevel.HIGH
        assert discrepancy_anomaly.supporting_data["discrepancy"] == 50.00

    def test_subtotal_mismatch_detected(self, parser):
        payload = {
            "merchant_name": "Test Store",
            "total": 120.00,
            "subtotal": 100.00,
            "tax": 10.00,
            "line_items": [
                {"description": "Item A", "quantity": 1, "unit_price": 80.00},
            ],
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "SUBTOTAL_MISMATCH" in anomaly_types

    def test_total_calculation_error_detected(self, parser):
        payload = {
            "merchant_name": "Test Store",
            "total": 200.00,
            "subtotal": 100.00,
            "tax": 10.00,
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "TOTAL_CALCULATION_ERROR" in anomaly_types

    def test_missing_receipt_number_anomaly(self, parser, minimal_receipt_payload):
        result = parser.parse(minimal_receipt_payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "MISSING_RECEIPT_NUMBER" in anomaly_types

    def test_missing_receipt_date_anomaly(self, parser, minimal_receipt_payload):
        result = parser.parse(minimal_receipt_payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "MISSING_RECEIPT_DATE" in anomaly_types


# ── Claim Alignment Tests ────────────────────────────────────────

class TestReceiptParserAlignment:

    def test_clean_receipt_supports_merchant(self, parser, full_receipt_payload):
        """A clean receipt with no anomalies supports the merchant."""
        result = parser.parse(full_receipt_payload)
        assert result.claim_alignment == ClaimAlignment.SUPPORTS_MERCHANT

    def test_receipt_with_anomalies_is_neutral(self, parser):
        """A receipt with anomalies should be NEUTRAL."""
        payload = {
            "merchant_name": "Test Store",
            "total": 150.00,
            "transaction_amount": 100.00,  # mismatch
        }
        result = parser.parse(payload)
        assert result.claim_alignment == ClaimAlignment.NEUTRAL


# ── Confidence Scoring Tests ─────────────────────────────────────

class TestReceiptParserConfidence:

    def test_full_payload_high_confidence(self, parser, full_receipt_payload):
        result = parser.parse(full_receipt_payload)
        assert result.confidence_score >= 0.85

    def test_minimal_payload_lower_confidence(self, parser, minimal_receipt_payload):
        result = parser.parse(minimal_receipt_payload)
        assert result.confidence_score < 0.90

    def test_confidence_reduced_by_anomalies(self, parser):
        payload = {
            "merchant_name": "Test Store",
            "total": 999.00,
            "transaction_amount": 100.00,  # big discrepancy
        }
        result = parser.parse(payload)
        assert result.confidence_score < 0.80


# ── Edge Case Tests ──────────────────────────────────────────────

class TestReceiptParserEdgeCases:

    def test_parser_name_property(self, parser):
        assert parser.parser_name == "ReceiptParser"

    def test_string_total_with_dollar_sign(self, parser):
        payload = {
            "merchant_name": "Store",
            "total": "$1,234.56",
        }
        result = parser.parse(payload)
        assert result.structured_data["total"] == 1234.56

    def test_empty_line_items_list(self, parser):
        payload = {
            "merchant_name": "Store",
            "total": 50.00,
            "line_items": [],
        }
        result = parser.parse(payload)
        assert result.structured_data["line_item_count"] == 0

    def test_invalid_line_item_skipped(self, parser):
        payload = {
            "merchant_name": "Store",
            "total": 50.00,
            "line_items": ["not_a_dict", {"description": "Valid Item", "quantity": 1, "unit_price": 50.0}],
        }
        result = parser.parse(payload)
        assert result.structured_data["line_item_count"] == 1

    def test_metadata_has_ocr_flag(self, parser):
        payload = {
            "merchant_name": "Store",
            "total": 50.00,
            "ocr_text": "Some OCR text",
        }
        result = parser.parse(payload)
        assert result.metadata["has_ocr_text"] is True

    def test_nlp_entities_dict_output(self, parser, full_receipt_payload):
        result = parser.parse(full_receipt_payload)
        nlp_dict = result.to_nlp_entities_dict()
        assert "extracted_entities" in nlp_dict
        assert "claim_alignment" in nlp_dict
        assert nlp_dict["claim_alignment"] == "SUPPORTS_MERCHANT"
