"""
VerdictAI Evidence Pipeline Integration Tests
Author: Nirav Kachhiya (Project Lead / Backend Engineer)

Verifies end-to-end integration between CaseService.attach_evidence(),
EvidenceParserDispatcher, polymorphic parsers, and the Merkle AuditEngine.
"""

import pytest
from datetime import datetime, timezone

from backend.app.models.schemas import DisputeReason, DisputeStatus
from backend.app.services.case_builder.service import case_service
from backend.app.services.audit_engine.audit import audit_engine
from backend.app.services.parsers import evidence_dispatcher
from database.mongodb.models import EvidenceType, EvidenceSource


@pytest.fixture(autouse=True)
def clean_database():
    """Clear memory DB before and after tests."""
    from backend.app.core.db import db_manager
    db_manager.reset_in_memory_stores()
    audit_engine._chain_store.clear()
    yield
    db_manager.reset_in_memory_stores()
    audit_engine._chain_store.clear()


def test_attach_receipt_evidence_enriched():
    """Test attaching receipt evidence parses totals, line items, and entities."""
    case = case_service.create_dispute_case(
        transaction_id="txn_receipt_001",
        cardholder_id="usr_alice",
        dispute_reason=DisputeReason.INCORRECT_AMOUNT_CHARGED,
        disputed_amount=250.00
    )
    dispute_id = case.header.dispute_id

    receipt_payload = {
        "merchant_name": "Apex Electronics Direct",
        "total": 250.00,
        "currency": "USD",
        "receipt_number": "INV-2026-999",
        "receipt_date": "2026-08-20T14:30:00Z",
        "line_items": [
            {"description": "Wireless Mouse", "quantity": 1, "unit_price": 50.00},
            {"description": "Mechanical Keyboard", "quantity": 1, "unit_price": 200.00}
        ],
        "transaction_amount": 250.00
    }

    evidence = case_service.attach_evidence(
        dispute_id=dispute_id,
        evidence_type=EvidenceType.RECEIPT_INVOICE,
        source=EvidenceSource.MERCHANT,
        raw_payload=receipt_payload,
        actor="MERCHANT:m_apex"
    )

    # Verify model fields
    assert evidence.evidence_id.startswith("evi_")
    assert evidence.confidence_rating >= 0.80
    assert evidence.sha256_checksum is not None

    # Verify NLP extraction enrichment
    nlp = evidence.nlp_extracted_entities
    assert "extracted_entities" in nlp
    assert "claim_alignment" in nlp
    assert nlp["claim_alignment"] in ["SUPPORTS_MERCHANT", "NEUTRAL", "SUPPORTS_CARDHOLDER"]
    assert any(e["entity"] == "MERCHANT" and "Apex Electronics" in e["text"] for e in nlp["extracted_entities"])
    assert any(e["entity"] == "MONEY" for e in nlp["extracted_entities"])

    # Verify unified case file includes parsed evidence
    unified_case = case_service.get_unified_case_file(dispute_id)
    assert unified_case is not None
    assert len(unified_case.evidence_items) == 1
    assert unified_case.header.current_status == DisputeStatus.EVIDENCE_INGESTED


def test_attach_courier_tracking_anomaly_detection():
    """Test attaching courier tracking with address mismatch triggers critical anomaly and audit log."""
    case = case_service.create_dispute_case(
        transaction_id="txn_tracking_002",
        cardholder_id="usr_bob",
        dispute_reason=DisputeReason.PRODUCT_NOT_RECEIVED,
        disputed_amount=899.99
    )
    dispute_id = case.header.dispute_id

    tracking_payload = {
        "carrier": "FedEx",
        "tracking_number": "789123456780",
        "status": "DELIVERED",
        "delivery_date": "2026-08-25T11:00:00Z",
        "signed_by": "R. STRANGER",
        "delivery_address": "999 Wrong Boulevard, Austin, TX 78701",
        "expected_address": "123 True Street, San Francisco, CA 94102",
        "delivery_address_match": False
    }

    evidence = case_service.attach_evidence(
        dispute_id=dispute_id,
        evidence_type=EvidenceType.COURIER_TRACKING,
        source=EvidenceSource.COURIER_CARRIER,
        raw_payload=tracking_payload,
        actor="CARRIER:FEDEX"
    )

    # Verify anomaly extraction
    nlp = evidence.nlp_extracted_entities
    anomalies = nlp.get("anomalies", [])
    assert len(anomalies) > 0
    assert any("ADDRESS_MISMATCH" in a.get("type", "") for a in anomalies)

    # Verify audit log captured the critical anomaly
    audit_trail = audit_engine.get_audit_trail(dispute_id)
    anomaly_events = [e for e in audit_trail if e.action_type == "EVIDENCE_ANOMALY_DETECTED"]
    assert len(anomaly_events) >= 1
    assert anomaly_events[0].performed_by == "SYSTEM_EVIDENCE_PIPELINE"
    assert audit_engine.verify_integrity(dispute_id) is True


def test_attach_communication_log_parsing():
    """Test attaching email/chat logs parses transcript and extracts entities."""
    case = case_service.create_dispute_case(
        transaction_id="txn_chat_003",
        cardholder_id="usr_charlie",
        dispute_reason=DisputeReason.SUBSCRIPTION_CANCELLED_CHARGED,
        disputed_amount=120.00
    )
    dispute_id = case.header.dispute_id

    chat_payload = {
        "channel": "CHAT",
        "messages": [
            {
                "sender": "Charlie Cardholder",
                "role": "CARDHOLDER",
                "content": "I requested a cancellation for order ORD-998822 on 2026-08-15, but was billed $120.00.",
                "timestamp": "2026-08-15T10:00:00Z"
            },
            {
                "sender": "Merchant Support",
                "role": "MERCHANT",
                "content": "We apologize, our policy takes 5 business days. Please note your refund is being processed.",
                "timestamp": "2026-08-15T11:00:00Z"
            }
        ]
    }

    evidence = case_service.attach_evidence(
        dispute_id=dispute_id,
        evidence_type=EvidenceType.COMMUNICATION_LOG,
        source=EvidenceSource.CARDHOLDER,
        raw_payload=chat_payload,
        actor="USER:usr_charlie"
    )

    nlp = evidence.nlp_extracted_entities
    entities = nlp.get("extracted_entities", [])
    entity_types = [e["entity"] for e in entities]
    assert "MONEY" in entity_types or "ORDER_ID" in entity_types or "DATE" in entity_types


def test_attach_bank_statement_parsing():
    """Test attaching bank statement transaction parses amount and date."""
    case = case_service.create_dispute_case(
        transaction_id="txn_bank_004",
        cardholder_id="usr_dana",
        dispute_reason=DisputeReason.FRAUD_UNRECOGNIZED_CHARGE,
        disputed_amount=450.00
    )
    dispute_id = case.header.dispute_id

    bank_payload = {
        "merchant_name": "Apex Electronics Direct",
        "amount": 450.00,
        "currency": "USD",
        "transaction_date": "2026-08-20T16:00:00Z",
        "card_last_four": "1122",
        "mcc_code": "5411"
    }

    evidence = case_service.attach_evidence(
        dispute_id=dispute_id,
        evidence_type=EvidenceType.BANK_STATEMENT,
        source=EvidenceSource.CARDHOLDER,
        raw_payload=bank_payload,
        actor="USER:usr_dana"
    )

    nlp = evidence.nlp_extracted_entities
    assert "extracted_entities" in nlp
    assert len(nlp["extracted_entities"]) > 0


def test_unsupported_or_freeform_payload_graceful_fallback():
    """Test that arbitrary or freeform payloads fall back gracefully without failing."""
    case = case_service.create_dispute_case(
        transaction_id="txn_freeform_005",
        cardholder_id="usr_eve",
        dispute_reason=DisputeReason.PRODUCT_DAMAGED_OR_DEFECTIVE,
        disputed_amount=95.00
    )
    dispute_id = case.header.dispute_id

    freeform_payload = {
        "notes": "Custom unstructured merchant notes with no standard schema.",
        "arbitrary_flag": True
    }

    evidence = case_service.attach_evidence(
        dispute_id=dispute_id,
        evidence_type=EvidenceType.REFUND_POLICY_TERMS,
        source=EvidenceSource.MERCHANT,
        raw_payload=freeform_payload,
        actor="MERCHANT:m_apex"
    )

    # Should succeed with valid hash and raw_payload preserved
    assert evidence.evidence_id.startswith("evi_")
    assert evidence.sha256_checksum is not None
    assert evidence.raw_payload == freeform_payload
    assert evidence.nlp_extracted_entities == {}


def test_dispatcher_query_methods():
    """Test query helpers on the EvidenceParserDispatcher."""
    assert evidence_dispatcher.is_supported(EvidenceType.RECEIPT_INVOICE) is True
    assert evidence_dispatcher.is_supported(EvidenceType.COURIER_TRACKING) is True
    assert evidence_dispatcher.is_supported(EvidenceType.COMMUNICATION_LOG) is True
    assert evidence_dispatcher.is_supported(EvidenceType.BANK_STATEMENT) is True
    assert evidence_dispatcher.is_supported(EvidenceType.SYSTEM_AUDIT_PROOF) is False

    supported = evidence_dispatcher.get_supported_types()
    assert len(supported) == 4
