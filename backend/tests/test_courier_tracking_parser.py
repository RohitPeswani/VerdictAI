"""
Test Suite for CourierTrackingParser — Evidence Ingestion Pipeline
Author: Achyut Pathak (AI/NLP Engineer — Evidence Parsing)
"""

import pytest

from backend.app.services.parsers.courier_tracking_parser import CourierTrackingParser
from backend.app.services.parsers.base_parser import (
    AnomalyLevel,
    ClaimAlignment,
    ParsedEvidence,
)


@pytest.fixture
def parser():
    return CourierTrackingParser()


@pytest.fixture
def delivered_payload():
    """Successful delivery with full tracking details."""
    return {
        "carrier": "FedEx",
        "tracking_number": "789123456780",
        "status": "DELIVERED",
        "delivery_date": "2026-08-22T10:30:00Z",
        "shipped_date": "2026-08-20T16:00:00Z",
        "signed_by": "J. DOE",
        "delivery_address": "123 Oak Street, San Francisco, CA 94102",
        "expected_address": "123 Oak Street, San Francisco, CA 94102",
        "gps_latitude": 37.7749,
        "gps_longitude": -122.4194,
        "delivery_address_match": True,
        "service_type": "EXPRESS",
        "weight_kg": 2.5,
        "status_history": [
            {"status": "SHIPPED", "timestamp": "2026-08-20T16:00:00Z"},
            {"status": "IN_TRANSIT", "timestamp": "2026-08-21T08:00:00Z"},
            {"status": "OUT_FOR_DELIVERY", "timestamp": "2026-08-22T06:00:00Z"},
            {"status": "DELIVERED", "timestamp": "2026-08-22T10:30:00Z"},
        ],
    }


@pytest.fixture
def minimal_payload():
    """Tracking with only required fields."""
    return {
        "carrier": "UPS",
        "tracking_number": "1Z999AA10123456784",
        "status": "IN_TRANSIT",
    }


@pytest.fixture
def failed_delivery_payload():
    """Delivery that was returned to sender."""
    return {
        "carrier": "USPS",
        "tracking_number": "9400111899223100000",
        "status": "RETURNED_TO_SENDER",
        "shipped_date": "2026-08-20T12:00:00Z",
    }


# ── Validation Tests ─────────────────────────────────────────────

class TestCourierTrackingParserValidation:

    def test_validate_complete_payload(self, parser, delivered_payload):
        assert parser.validate(delivered_payload) is True

    def test_validate_minimal_payload(self, parser, minimal_payload):
        assert parser.validate(minimal_payload) is True

    def test_validate_missing_carrier(self, parser):
        assert parser.validate({"tracking_number": "123", "status": "DELIVERED"}) is False

    def test_validate_missing_tracking_number(self, parser):
        assert parser.validate({"carrier": "FedEx", "status": "DELIVERED"}) is False

    def test_validate_missing_status(self, parser):
        assert parser.validate({"carrier": "FedEx", "tracking_number": "123"}) is False

    def test_validate_empty_payload(self, parser):
        assert parser.validate({}) is False


# ── Core Parsing Tests ───────────────────────────────────────────

class TestCourierTrackingParserParsing:

    def test_parse_delivered_payload(self, parser, delivered_payload):
        result = parser.parse(delivered_payload)
        assert isinstance(result, ParsedEvidence)
        assert result.parser_name == "CourierTrackingParser"
        assert result.structured_data["carrier"] == "FEDEX"
        assert result.structured_data["tracking_number"] == "789123456780"
        assert result.structured_data["status"] == "DELIVERED"
        assert result.structured_data["signed_by"] == "J. DOE"
        assert result.structured_data["delivery_address_match"] is True

    def test_parse_minimal_payload(self, parser, minimal_payload):
        result = parser.parse(minimal_payload)
        assert result.structured_data["carrier"] == "UPS"
        assert result.structured_data["status"] == "IN_TRANSIT"
        assert result.structured_data["signed_by"] is None

    def test_parse_gps_coordinates(self, parser, delivered_payload):
        result = parser.parse(delivered_payload)
        gps = result.structured_data["gps_coordinates"]
        assert gps is not None
        assert gps["latitude"] == 37.7749
        assert gps["longitude"] == -122.4194

    def test_parse_no_gps(self, parser, minimal_payload):
        result = parser.parse(minimal_payload)
        assert result.structured_data["gps_coordinates"] is None

    def test_parse_raises_on_missing_required(self, parser):
        with pytest.raises(ValueError, match="missing required fields"):
            parser.parse({"carrier": "FedEx"})


# ── Entity Extraction Tests ──────────────────────────────────────

class TestCourierTrackingParserEntities:

    def test_extracts_carrier_entity(self, parser, delivered_payload):
        result = parser.parse(delivered_payload)
        carrier_entities = [e for e in result.extracted_entities if e.entity_type == "CARRIER"]
        assert len(carrier_entities) >= 1
        assert carrier_entities[0].text == "FEDEX"

    def test_extracts_tracking_number(self, parser, delivered_payload):
        result = parser.parse(delivered_payload)
        tracking_entities = [e for e in result.extracted_entities if e.entity_type == "TRACKING_NUMBER"]
        assert len(tracking_entities) >= 1

    def test_extracts_delivery_status(self, parser, delivered_payload):
        result = parser.parse(delivered_payload)
        status_entities = [e for e in result.extracted_entities if e.entity_type == "DELIVERY_STATUS"]
        assert len(status_entities) >= 1
        assert status_entities[0].text == "DELIVERED"

    def test_extracts_person_signatory(self, parser, delivered_payload):
        result = parser.parse(delivered_payload)
        person_entities = [e for e in result.extracted_entities if e.entity_type == "PERSON"]
        assert len(person_entities) >= 1
        assert person_entities[0].text == "J. DOE"

    def test_extracts_gps_entity(self, parser, delivered_payload):
        result = parser.parse(delivered_payload)
        gps_entities = [e for e in result.extracted_entities if e.entity_type == "GPS_COORDINATES"]
        assert len(gps_entities) == 1
        assert "37.7749" in gps_entities[0].text

    def test_extracts_date_entity(self, parser, delivered_payload):
        result = parser.parse(delivered_payload)
        date_entities = [e for e in result.extracted_entities if e.entity_type == "DATE"]
        assert len(date_entities) >= 1

    def test_extracts_address_entity(self, parser, delivered_payload):
        result = parser.parse(delivered_payload)
        gpe_entities = [e for e in result.extracted_entities if e.entity_type == "GPE"]
        assert len(gpe_entities) >= 1
        assert "123 Oak Street" in gpe_entities[0].text


# ── Anomaly Detection Tests ──────────────────────────────────────

class TestCourierTrackingParserAnomalies:

    def test_no_anomalies_clean_delivery(self, parser, delivered_payload):
        """A clean, signed delivery with matching address should have no critical anomalies."""
        result = parser.parse(delivered_payload)
        critical_anomalies = [
            a for a in result.anomalies
            if a.severity in (AnomalyLevel.HIGH, AnomalyLevel.CRITICAL)
        ]
        assert len(critical_anomalies) == 0

    def test_delivery_exception_anomaly(self, parser, failed_delivery_payload):
        result = parser.parse(failed_delivery_payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "DELIVERY_EXCEPTION" in anomaly_types

    def test_unsigned_delivery_anomaly(self, parser):
        payload = {
            "carrier": "FedEx",
            "tracking_number": "789123456780",
            "status": "DELIVERED",
            # No signed_by
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "UNSIGNED_DELIVERY" in anomaly_types

    def test_address_mismatch_explicit(self, parser):
        payload = {
            "carrier": "FedEx",
            "tracking_number": "789123456780",
            "status": "DELIVERED",
            "signed_by": "J. DOE",
            "delivery_address_match": False,
            "delivery_address": "456 Elm St",
            "expected_address": "123 Oak St",
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "ADDRESS_MISMATCH" in anomaly_types

    def test_address_mismatch_detected_by_comparison(self, parser):
        payload = {
            "carrier": "FedEx",
            "tracking_number": "789123456780",
            "status": "DELIVERED",
            "signed_by": "J. DOE",
            "delivery_address": "456 Elm Street, NY",
            "expected_address": "123 Oak Street, CA",
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "ADDRESS_MISMATCH" in anomaly_types

    def test_short_tracking_number_anomaly(self, parser):
        payload = {
            "carrier": "FedEx",
            "tracking_number": "12345",
            "status": "IN_TRANSIT",
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "INVALID_TRACKING_NUMBER" in anomaly_types

    def test_unknown_carrier_anomaly(self, parser):
        payload = {
            "carrier": "SuperFastShipping",
            "tracking_number": "123456789012",
            "status": "IN_TRANSIT",
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "UNKNOWN_CARRIER" in anomaly_types

    def test_excessive_transit_time(self, parser):
        payload = {
            "carrier": "USPS",
            "tracking_number": "9400111899223100000",
            "status": "DELIVERED",
            "shipped_date": "2026-06-01T12:00:00Z",
            "delivery_date": "2026-08-15T12:00:00Z",
            "signed_by": "Recipient",
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "EXCESSIVE_TRANSIT_TIME" in anomaly_types

    def test_status_chain_regression_detected(self, parser):
        payload = {
            "carrier": "FedEx",
            "tracking_number": "789123456780",
            "status": "IN_TRANSIT",
            "status_history": [
                {"status": "DELIVERED", "timestamp": "2026-08-22T10:00:00Z"},
                {"status": "IN_TRANSIT", "timestamp": "2026-08-23T08:00:00Z"},
            ],
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "STATUS_CHAIN_REGRESSION" in anomaly_types

    def test_duplicate_status_event(self, parser):
        payload = {
            "carrier": "FedEx",
            "tracking_number": "789123456780",
            "status": "IN_TRANSIT",
            "status_history": [
                {"status": "IN_TRANSIT", "timestamp": "2026-08-21T08:00:00Z"},
                {"status": "IN_TRANSIT", "timestamp": "2026-08-21T12:00:00Z"},
            ],
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "DUPLICATE_STATUS_EVENT" in anomaly_types

    def test_late_delivery_detected(self, parser):
        payload = {
            "carrier": "FedEx",
            "tracking_number": "789123456780",
            "status": "DELIVERED",
            "signed_by": "Recipient",
            "delivery_date": "2026-08-25T10:00:00Z",
            "estimated_delivery": "2026-08-22T10:00:00Z",
        }
        result = parser.parse(payload)
        anomaly_types = [a.anomaly_type for a in result.anomalies]
        assert "LATE_DELIVERY" in anomaly_types


# ── Claim Alignment Tests ────────────────────────────────────────

class TestCourierTrackingParserAlignment:

    def test_delivered_supports_merchant(self, parser, delivered_payload):
        result = parser.parse(delivered_payload)
        assert result.claim_alignment == ClaimAlignment.SUPPORTS_MERCHANT

    def test_delivery_exception_supports_cardholder(self, parser, failed_delivery_payload):
        result = parser.parse(failed_delivery_payload)
        assert result.claim_alignment == ClaimAlignment.SUPPORTS_CARDHOLDER

    def test_address_mismatch_supports_cardholder(self, parser):
        payload = {
            "carrier": "FedEx",
            "tracking_number": "789123456780",
            "status": "DELIVERED",
            "signed_by": "Someone",
            "delivery_address_match": False,
        }
        result = parser.parse(payload)
        assert result.claim_alignment == ClaimAlignment.SUPPORTS_CARDHOLDER

    def test_in_transit_is_neutral(self, parser, minimal_payload):
        result = parser.parse(minimal_payload)
        assert result.claim_alignment == ClaimAlignment.NEUTRAL


# ── Confidence Scoring Tests ─────────────────────────────────────

class TestCourierTrackingParserConfidence:

    def test_full_payload_high_confidence(self, parser, delivered_payload):
        result = parser.parse(delivered_payload)
        assert result.confidence_score >= 0.80

    def test_minimal_payload_lower_confidence(self, parser, minimal_payload):
        result = parser.parse(minimal_payload)
        assert result.confidence_score <= 0.85

    def test_confidence_reduced_by_anomalies(self, parser, failed_delivery_payload):
        result = parser.parse(failed_delivery_payload)
        assert result.confidence_score < 0.90


# ── Edge Case Tests ──────────────────────────────────────────────

class TestCourierTrackingParserEdgeCases:

    def test_parser_name_property(self, parser):
        assert parser.parser_name == "CourierTrackingParser"

    def test_carrier_normalised_to_uppercase(self, parser):
        payload = {
            "carrier": "fedex",
            "tracking_number": "789123456780",
            "status": "in_transit",
        }
        result = parser.parse(payload)
        assert result.structured_data["carrier"] == "FEDEX"
        assert result.structured_data["status"] == "IN_TRANSIT"

    def test_metadata_flags(self, parser, delivered_payload):
        result = parser.parse(delivered_payload)
        assert result.metadata["has_gps"] is True
        assert result.metadata["has_signature"] is True
        assert result.metadata["has_status_history"] is True

    def test_metadata_flags_minimal(self, parser, minimal_payload):
        result = parser.parse(minimal_payload)
        assert result.metadata["has_gps"] is False
        assert result.metadata["has_signature"] is False
        assert result.metadata["has_status_history"] is False

    def test_nlp_entities_dict_output(self, parser, delivered_payload):
        result = parser.parse(delivered_payload)
        nlp_dict = result.to_nlp_entities_dict()
        assert "extracted_entities" in nlp_dict
        assert "claim_alignment" in nlp_dict
        assert nlp_dict["claim_alignment"] == "SUPPORTS_MERCHANT"

    def test_addresses_match_normalisation(self, parser):
        payload = {
            "carrier": "FedEx",
            "tracking_number": "789123456780",
            "status": "DELIVERED",
            "signed_by": "J. DOE",
            "delivery_address": "123 Oak St, San Francisco, CA",
            "expected_address": "123 oak st san francisco ca",
        }
        result = parser.parse(payload)
        # After normalisation these should match
        address_anomalies = [a for a in result.anomalies if a.anomaly_type == "ADDRESS_MISMATCH"]
        assert len(address_anomalies) == 0
