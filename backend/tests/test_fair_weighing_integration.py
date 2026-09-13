"""
VerdictAI Fair-Weighing ML Model Integration & Fairness Test Suite
Author: Akshay Purohit (202512033) - ML Engineer (Fair-Weighing Model)
Phase: Phase 5 (Integration) & Phase 6 (Testing & Optimization)
Coverage: SRS FR-15, FR-16, FR-17, FR-18, FR-19, FR-20, FR-21, SIR-07, AC-08 to AC-11, NFR-14
"""

import os
import json
import time
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.db import db_manager
from backend.app.models.schemas import DisputeStatus, DisputeReason, ResolutionOutcome
from backend.app.services.case_builder.service import case_service
from backend.app.services.fair_weighing.scoring_service import fair_weighing_service
from backend.app.services.audit_engine.audit import audit_engine
from database.mongodb.models import EvidenceType, EvidenceSource
from akshay_ml_fairweighing.phase3_model.fair_weighing_model import FairWeighingModel


@pytest.fixture(autouse=True)
def reset_in_memory_db():
    """Reset test database tables before each test case."""
    db_manager.pg_tables = {
        "users": {},
        "merchants": {},
        "transactions": {},
        "disputes": {},
        "case_files": {},
        "audit_logs": {},
        "dispute_resolutions": {},
    }
    db_manager.mongo_collections = {
        "evidence_payloads": {},
        "case_documents": {},
    }
    yield


@pytest.fixture
def client():
    return TestClient(app)


# ─── 1. SIR-07 & AC-08: Synchronous Inference & High Confidence Resolution ──────

def test_synchronous_scoring_merchant_win(client):
    """
    SRS SIR-07 & AC-08:
    Verify synchronous execution of fair-weighing scoring within latency budget (< 30s)
    and correct outcome resolution when merchant evidence is complete and verified.
    """
    # 1. Create a dispute for Item Not Received
    create_resp = client.post("/api/v1/disputes", json={
        "transaction_id": "txn_test_sir07_01",
        "cardholder_id": "usr_akshay_01",
        "dispute_reason": DisputeReason.PRODUCT_NOT_RECEIVED.value,
        "disputed_amount": 3499.00,
        "cardholder_statement": "I never received the parcel at my apartment."
    })
    assert create_resp.status_code == 201
    dispute_id = create_resp.json()["header"]["dispute_id"]

    # 2. Attach Merchant Delivery Evidence (Carrier Tracking confirms delivery)
    ev_resp = client.post("/api/v1/evidence/payload", json={
        "dispute_id": dispute_id,
        "evidence_type": EvidenceType.COURIER_TRACKING.value,
        "source": EvidenceSource.MERCHANT.value,
        "raw_payload": {
            "tracking_number": "DEL123456789",
            "carrier": "BlueDart Express",
            "delivery_status": "DELIVERED",
            "signed_by": "Security Desk"
        },
        "actor": "MERCHANT:apex_store"
    })
    assert ev_resp.status_code == 201

    # 3. Synchronous Scoring Inference (SIR-07)
    t0 = time.time()
    score_resp = client.post(f"/api/v1/disputes/{dispute_id}/score")
    latency = time.time() - t0

    assert score_resp.status_code == 200
    assert latency < 30.0  # P95 latency SLA per SIR-07

    case_file = score_resp.json()
    assert case_file["resolution"] is not None
    res = case_file["resolution"]

    # In CAT-01, present verified delivery confirmation favours Merchant
    assert res["outcome"] == ResolutionOutcome.FAVOR_MERCHANT.value
    assert res["confidence_score"] >= 0.50
    assert "Delivered" in res["justification_summary"] or "Merchant" in res["justification_summary"]

    # Verify lifecycle advanced to AUTO_RESOLVED
    assert case_file["header"]["current_status"] == DisputeStatus.AUTO_RESOLVED.value


# ─── 2. FR-17 & AC-09: Auto-Escalation for Confidence < 50% ─────────────────────

def test_scoring_auto_escalates_when_primary_evidence_missing(client):
    """
    SRS FR-17 & AC-09:
    Cases where confidence is below 50% (e.g. missing primary delivery evidence in CAT-01)
    must automatically transition to the Dispute-Ops admin review queue (MANUAL_REVIEW_QUEUE).
    """
    # 1. Create dispute with missing delivery tracking
    create_resp = client.post("/api/v1/disputes", json={
        "transaction_id": "txn_test_escalate_01",
        "cardholder_id": "usr_akshay_02",
        "dispute_reason": DisputeReason.PRODUCT_NOT_RECEIVED.value,
        "disputed_amount": 1850.00,
        "cardholder_statement": "Merchant has not provided any tracking link or updates."
    })
    dispute_id = create_resp.json()["header"]["dispute_id"]

    # 2. Trigger AI scoring without merchant delivery confirmation
    score_resp = client.post(f"/api/v1/disputes/{dispute_id}/score")
    assert score_resp.status_code == 200

    case_file = score_resp.json()
    # Confidence must incur primary evidence penalty and drop below 50%
    assert case_file["resolution"]["reasoning_payload"]["confidence_score_pct"] < 50.0

    # Must be routed to MANUAL_REVIEW_QUEUE per FR-17 / AC-09
    assert case_file["header"]["current_status"] == DisputeStatus.MANUAL_REVIEW_QUEUE.value

    # Verify case appears in the admin review queue
    queue_resp = client.get("/api/v1/admin/queue")
    assert queue_resp.status_code == 200
    queue_items = queue_resp.json()["items"]
    assert any(item["header"]["dispute_id"] == dispute_id for item in queue_items)


# ─── 3. FR-19, FR-20 & AC-10: Plain-Language Explanation & Contributing Factors ─

def test_plain_language_explanation_and_factors(client):
    """
    SRS FR-19, FR-20 & AC-10:
    Every decision must generate an objective plain-language explanation citing
    at least three contributing factors.
    """
    case = case_service.create_dispute_case(
        transaction_id="txn_test_ac10",
        cardholder_id="usr_akshay_03",
        dispute_reason=DisputeReason.DUPLICATE_PROCESSING,
        disputed_amount=899.00,
        cardholder_statement="Charged twice for the same order."
    )
    dispute_id = case.header.dispute_id

    # Attach bank statement showing duplicate charge
    case_service.attach_evidence(
        dispute_id=dispute_id,
        evidence_type=EvidenceType.BANK_STATEMENT,
        source=EvidenceSource.CARDHOLDER,
        raw_payload={"duplicate_reference": "txn_test_ac10_second"},
        actor="USER:usr_akshay_03"
    )

    # Evaluate scoring
    updated_case = fair_weighing_service.evaluate_dispute_case(dispute_id)
    res = updated_case.resolution

    assert res is not None
    explanation = res["justification_summary"]
    factors = res["reasoning_payload"]["contributing_factors"]

    # Plain language explanation is non-empty and accessible
    assert isinstance(explanation, str)
    assert len(explanation) > 20

    # AC-10: Cites at least three specific factors
    assert len(factors) >= 3


# ─── 4. FR-18, FR-21 & AC-11: Cryptographic Audit Trail & Persistence ──────────

def test_audit_log_records_model_version_and_weights(client):
    """
    SRS FR-18, FR-21 & AC-11:
    Case audit trail must record the model version, all factor weights,
    and raw score delta, preserving cryptographic Merkle-chain integrity.
    """
    case = case_service.create_dispute_case(
        transaction_id="txn_test_audit_01",
        cardholder_id="usr_akshay_04",
        dispute_reason=DisputeReason.FRAUD_UNRECOGNIZED_CHARGE,
        disputed_amount=12000.00,
        cardholder_statement="Unrecognized midnight charge on my card."
    )
    dispute_id = case.header.dispute_id

    # Attach auth log showing 2FA verification
    case_service.attach_evidence(
        dispute_id=dispute_id,
        evidence_type=EvidenceType.IDENTITY_VERIFICATION,
        source=EvidenceSource.MERCHANT,
        raw_payload={"auth_success": True, "auth_type": "BIOMETRIC_3DS"},
        actor="SYSTEM:issuer_bank"
    )

    fair_weighing_service.evaluate_dispute_case(dispute_id)

    # Verify audit trail
    audit_resp = client.get(f"/api/v1/disputes/{dispute_id}/audit-trail")
    assert audit_resp.status_code == 200
    data = audit_resp.json()

    assert data["is_chain_intact"] is True

    # Find the AI_SCORING_EVALUATED audit event
    scoring_events = [
        event for event in data["audit_logs"]
        if event["action_type"] == "AI_SCORING_EVALUATED"
    ]
    assert len(scoring_events) == 1
    event = scoring_events[0]

    # Check model version, delta, and factor weights
    assert event["state_delta"]["model_version"] == "fair_weighing_v1.0"
    assert "score_delta" in event["state_delta"]
    assert len(event["state_delta"]["factor_breakdown"]) > 0

    # Verify GET /disputes/{id}/resolution endpoint
    res_resp = client.get(f"/api/v1/disputes/{dispute_id}/resolution")
    assert res_resp.status_code == 200
    assert res_resp.json()["dispute_id"] == dispute_id


# ─── 5. NFR-14: Model Validation & False Positive Rate Benchmark Test ──────────

def test_nfr_14_benchmark_dataset_accuracy_and_fpr():
    """
    SRS NFR-14:
    The scoring model must be validated against the synthetic dispute benchmark dataset
    to ensure False Positive Rate (FPR) <= 2.0% and high overall accuracy.
    """
    dataset_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "akshay_ml_fairweighing",
        "phase2_mockdata",
        "mock_disputes_dataset.json"
    )
    assert os.path.exists(dataset_path), f"Benchmark dataset not found at {dataset_path}"

    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    cases = dataset.get("cases", [])
    assert len(cases) >= 50

    model = FairWeighingModel()
    total_cases = len(cases)
    correct_matches = 0
    false_positives = 0

    for case in cases:
        output = model.evaluate_case(case)
        gt = case.get("ground_truth_resolution")
        rec = output.get("recommended_resolution")

        if rec == gt:
            correct_matches += 1
        elif rec != "ESCALATE" and rec != gt:
            false_positives += 1

    accuracy = (correct_matches / total_cases) * 100.0
    fpr = (false_positives / total_cases) * 100.0

    # NFR-14 Compliance: FPR <= 2.0%
    assert fpr <= 2.0, f"FPR ({fpr:.2f}%) exceeds maximum allowable threshold of 2.0%"
    assert accuracy >= 95.0, f"Accuracy ({accuracy:.2f}%) is below 95%"
