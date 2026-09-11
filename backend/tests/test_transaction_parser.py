"""
Test Suite for TransactionParser — Evidence Ingestion Pipeline
Author: Achyut Pathak (AI/NLP Engineer — Evidence Parsing)
"""

import pytest
from datetime import datetime, timezone, timedelta

from backend.app.services.parsers.transaction_parser import TransactionParser
from backend.app.services.parsers.base_parser import (
    AnomalyLevel,
    ClaimAlignment,
    ParsedEvidence,
)


@pytest.fixture
def parser():
    return TransactionParser()


@pytest.fixture
def valid_payload():
    """Complete transaction payload with all optional fields."""
    return {
        "merchant_name": "Apex Electronics Direct",
        "amount": 249.50,
        "currency": "USD",
        "transaction_date": "2026-08-20T14:32:00Z",
        "card_last_four": "4242",
        "mcc_code": "5411",
        "merchant_location": "San Francisco, CA",
        "payment_method": "VISA_CREDIT",
        "transaction_id": "txn_abc123",
        "authorization_code": "AUTH-789",
        "description": "APEX ELECTRONICS *ONLINE SAN FRANCISCO CA",
    }


@pytest.fixture
def minimal_payload():
    """Transaction payload with only required fields."""
    return {
        "merchant_name": "Quick Mart",
        "amount": 15.99,
        "transaction_date": "2026-08-20",
    }


# ── Validation Tests ─────────────────────────────────────────────

class TestTransactionParserValidation:

    def test_validate_complete_payload(self, parser, valid_payload):
        assert parser.validate(valid_payload) is True

    def test_validate_minimal_payload(self, parser, minimal_payload):
        assert parser.validate(minimal_payload) is True

    def test_validate_missing_merchant_name(self, parser):
        payload = {"amount": 100.0, "transaction_date": "2026-08-20"}
        assert parser.validate(payload) is False

    def test_validate_missing_amount(self, parser):
        payload = {"merchant_name": "Test", "transaction_date": "2026-08-20"}
        assert parser.validate(payload) is False

    def test_validate_missing_transaction_date(self, parser):
        payload = {"merchant_name": "Test", "amount": 100.0}
        assert parser.validate(payload) is False

    def test_validate_none_values(self, parser):
        payload = {"merchant_name": None, "amount": 100.0, "transaction_date": "2026-08-20"}
        assert parser.validate(payload) is False

    def test_validate_empty_payload(self, parser):
        assert parser.validate({}) is False


# ── Core Parsing Tests ───────────────────────────────────────────

class TestTransactionParserParsing:

    def test_parse_complete_payload(self, parser, valid_payload):
        result = parser.parse(valid_payload)
        assert isinstance(result, ParsedEvidence)
        assert result.parser_name == "TransactionParser"
        assert result.structured_data["merchant_name"] == "Apex Electronics Direct"
        assert result.structured_data["amount"] == 249.50
        assert result.structured_data["currency"] == "USD"
        assert result.structured_data["card_last_four"] == "4242"
        assert result.structured_data["mcc_code"] == "5411"
        assert result.structured_data["merchant_location"] == "San Francisco, CA"
        assert result.structured_data["transaction_id"] == "txn_abc123"

    def test_parse_minimal_payload(self, parser, minimal_payload):
        result = parser.parse(minimal_payload)
        assert result.structured_data["merchant_name"] == "Quick Mart"
        assert result.structured_data["amount"] == 15.99
        assert result.structured_data["currency"] == "USD"  # default
        assert result.structured_data["card_last_four"] is None
        assert result.structured_data["mcc_code"] is None

    def test_parse_string_amount(self, parser):
        payload = {
            "merchant_name": "Test Store",
            "amount": "$1,234.56",
            "transaction_date": "2026-08-20",
        }
        result = parser.parse(payload)
        assert result.structured_data["amount"] == 1234.56

    def test_parse_raises_on_missing_required(self, parser):
        with pytest.raises(ValueError, match="missing required fields"):
            parser.parse({"merchant_name": "Test"})

    def test_parse_various_date_formats(self, parser):
        dates = [
            "2026-08-20",
            "2026-08-20T14:32:00Z",
            "08/20/2026",
            "August 20, 2026",
        ]
        for date_str in dates:
            payload = {"merchant_name": "Test", "amount": 10.0, "transaction_date": date_str}
            result = parser.parse(payload)
            assert result.structured_data["transaction_date"] is not None, f"Failed to parse date: {date_str}"


# ── Entity Extraction Tests ──────────────────────────────────────

class TestTransactionParserEntities:

    def test_extracts_merchant_entity(self, parser, valid_payload):
        result = parser.parse(valid_payload)
        merchant_entities = [e for e in result.extracted_entities if e.entity_type == "MERCHANT"]
        assert len(merchant_entities) >= 1
        assert merchant_entities[0].text == "Apex Electronics Direct"

    def test_extracts_money_entity(self, parser, valid_payload):
        result = parser.parse(valid_payload)
        money_entities = [e for e in result.extracted_entities if e.entity_type == "MONEY"]
        assert len(money_entities) >= 1
        assert "249.5" in money_entities[0].text

    def test_extracts_date_entity(self, parser, valid_payload):
        result = parser.parse(valid_payload)
        date_entities = [e for e in result.extracted_entities if e.entity_type == "DATE"]
        assert len(date_entities) >= 1

    def test_extracts_card_last_four(self, parser, valid_payload):
        result = parser.parse(valid_payload)
        card_entities = [e for e in result.extracted_entities if e.entity_type == "CARD_LAST_FOUR"]
        assert len(card_entities) == 1
        assert card_entities[0].text == "4242"

    def test_extracts_location_entity(self, parser, valid_payload):
        result = parser.parse(valid_payload)
        gpe_entities = [e for e in result.extracted_entities if e.entity_type == "GPE"]
        assert len(gpe_entities) >= 1
        assert "San Francisco" in gpe_entities[0].text

    def test_extracts_transaction_id_entity(self, parser, valid_payload):
        result = parser.parse(valid_payload)
        id_entities = [e for e in result.extracted_entities if e.entity_type == "TRANSACTION_ID"]
        assert len(id_entities) == 1
        assert id_entities[0].text == "txn_abc123"

    def test_description_entity_extraction(self, parser):
        payload = {
            "merchant_name": "Test",
            "amount": 50.0,
            "transaction_date": "2026-08-20",
            "description": "Purchase on Aug 20, 2026 for $50.00 at store",
        }
        result = parser.parse(payload)
        entity_types = [e.entity_type for e in result.extracted_entities]
        assert "MONEY" in entity_types  # $50.00 from description
        assert "DATE" in entity_types   # Aug 20, 2026 from description


# ── Anomaly Detection Tests ──────────────────────────────────────

class TestTransactionParserAnomalies:

    def test_no_anomalies_normal_transaction(self, parser, valid_payload):
        result = parser.parse(valid_payload)
        # Valid payload with normal amount on weekday should have minimal anomalies
        high_anomalies = [a for a in result.anomalies if a.severity in (AnomalyLevel.HIGH, AnomalyLevel.CRITICAL)]
        assert len(high_anomalies) == 0

    def test_high_value_transaction_anomaly(self, parser):
        payload = {
            "merchant_name": "Luxury Store",
            "amount": 15000.00,
            "transaction_date": "2026-08-20",
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "HIGH_VALUE_TRANSACTION" in anomaly_types

    def test_negative_amount_anomaly(self, parser):
        payload = {
            "merchant_name": "Test Store",
            "amount": -50.00,
            "transaction_date": "2026-08-20",
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "INVALID_AMOUNT" in anomaly_types

    def test_zero_amount_anomaly(self, parser):
        payload = {
            "merchant_name": "Test Store",
            "amount": 0,
            "transaction_date": "2026-08-20",
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "INVALID_AMOUNT" in anomaly_types

    def test_weekend_transaction_anomaly(self, parser):
        # Find a Saturday
        payload = {
            "merchant_name": "Test Store",
            "amount": 50.00,
            "transaction_date": "2026-08-22",  # Saturday
        }
        result = parser.parse(payload)
        # Check if date is actually a weekend
        parsed_date = TransactionParser._parse_date("2026-08-22")
        if parsed_date and parsed_date.weekday() in (5, 6):
            anomaly_types = [a.anomaly_type for a in result.anomalies]
            assert "WEEKEND_TRANSACTION" in anomaly_types

    def test_high_risk_mcc_anomaly(self, parser):
        payload = {
            "merchant_name": "Online Casino",
            "amount": 500.00,
            "transaction_date": "2026-08-20",
            "mcc_code": "7995",
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "HIGH_RISK_MCC" in anomaly_types

    def test_future_dated_transaction_anomaly(self, parser):
        future_date = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
        payload = {
            "merchant_name": "Test Store",
            "amount": 50.00,
            "transaction_date": future_date,
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "FUTURE_DATED_TRANSACTION" in anomaly_types


# ── Confidence Scoring Tests ─────────────────────────────────────

class TestTransactionParserConfidence:

    def test_full_payload_high_confidence(self, parser, valid_payload):
        result = parser.parse(valid_payload)
        assert result.confidence_score >= 0.85

    def test_minimal_payload_lower_confidence(self, parser, minimal_payload):
        result = parser.parse(minimal_payload)
        assert result.confidence_score < result.confidence_score or result.confidence_score <= 0.85

    def test_confidence_reduced_by_anomalies(self, parser):
        payload = {
            "merchant_name": "Casino",
            "amount": -500.00,
            "transaction_date": "2026-08-20",
            "mcc_code": "7995",
        }
        result = parser.parse(payload)
        assert result.confidence_score < 0.80  # penalties applied


# ── Claim Alignment Tests ────────────────────────────────────────

class TestTransactionParserAlignment:

    def test_transaction_alignment_is_neutral(self, parser, valid_payload):
        """Transactions alone are factual — should always be NEUTRAL."""
        result = parser.parse(valid_payload)
        assert result.claim_alignment == ClaimAlignment.NEUTRAL


# ── NLP Entity Dict Output Tests ─────────────────────────────────

class TestTransactionParserNLPOutput:

    def test_to_nlp_entities_dict(self, parser, valid_payload):
        result = parser.parse(valid_payload)
        nlp_dict = result.to_nlp_entities_dict()
        assert "extracted_entities" in nlp_dict
        assert "anomalies" in nlp_dict
        assert "claim_alignment" in nlp_dict
        assert "confidence_score" in nlp_dict
        assert isinstance(nlp_dict["extracted_entities"], list)
        assert nlp_dict["claim_alignment"] == "NEUTRAL"


# ── Edge Case Tests ──────────────────────────────────────────────

class TestTransactionParserEdgeCases:

    def test_parser_name_property(self, parser):
        assert parser.parser_name == "TransactionParser"

    def test_amount_with_commas(self, parser):
        payload = {
            "merchant_name": "Store",
            "amount": "1,234,567.89",
            "transaction_date": "2026-08-20",
        }
        result = parser.parse(payload)
        assert result.structured_data["amount"] == 1234567.89

    def test_unparseable_amount_raises(self, parser):
        payload = {
            "merchant_name": "Store",
            "amount": "not-a-number",
            "transaction_date": "2026-08-20",
        }
        with pytest.raises(ValueError, match="Cannot parse amount"):
            parser.parse(payload)

    def test_unparseable_date_returns_none(self, parser):
        payload = {
            "merchant_name": "Store",
            "amount": 10.0,
            "transaction_date": "not-a-date",
        }
        result = parser.parse(payload)
        assert result.structured_data["transaction_date"] is None

    def test_whitespace_in_merchant_name(self, parser):
        payload = {
            "merchant_name": "  Test Store  ",
            "amount": 10.0,
            "transaction_date": "2026-08-20",
        }
        result = parser.parse(payload)
        assert result.structured_data["merchant_name"] == "Test Store"

    def test_has_anomalies_property(self, parser):
        payload = {
            "merchant_name": "Store",
            "amount": -10.0,
            "transaction_date": "2026-08-20",
        }
        result = parser.parse(payload)
        assert result.has_anomalies is True

    def test_highest_anomaly_severity(self, parser):
        payload = {
            "merchant_name": "Store",
            "amount": -10.0,
            "transaction_date": "2026-08-20",
        }
        result = parser.parse(payload)
        assert result.highest_anomaly_severity in (AnomalyLevel.HIGH, AnomalyLevel.CRITICAL)
