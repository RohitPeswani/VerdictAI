"""
VerdictAI REST API Request & Response Schemas
Author: Darshan Prajapati (Backend Engineer - Reasoning & APIs)
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from backend.app.models.schemas import (
    DisputeStatus,
    DisputeReason,
    ResolutionOutcome,
    UnifiedCaseFile,
    TransactionSummary
)
from database.mongodb.models import EvidenceType, EvidenceSource, EvidencePayloadModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DisputeCreateRequest(BaseModel):
    transaction_id: str = Field(..., description="ID of the disputed transaction", json_schema_extra={"example": "txn_001"})
    cardholder_id: str = Field(..., description="ID of the cardholder filing the dispute", json_schema_extra={"example": "usr_alice_01"})
    dispute_reason: DisputeReason = Field(..., description="Categorized reason for dispute", json_schema_extra={"example": DisputeReason.PRODUCT_NOT_RECEIVED})
    disputed_amount: float = Field(..., gt=0, description="Amount contested in dispute", json_schema_extra={"example": 1249.50})
    cardholder_statement: Optional[str] = Field(None, description="Free-text narrative from the cardholder", json_schema_extra={"example": "Package never delivered to residence."})
    merchant_sla_hours: int = Field(48, ge=1, le=168, description="Merchant evidence window in hours (default 48h)")


class StateTransitionRequest(BaseModel):
    target_status: DisputeStatus = Field(..., description="Desired lifecycle status")
    actor: str = Field(..., description="Identity of the actor triggering the transition", json_schema_extra={"example": "DISPUTE_OPS_ANALYST:alex"})
    reason: str = Field(..., min_length=3, description="Reason for status transition", json_schema_extra={"example": "Evidence collection completed, starting AI scoring."})


class StructuredEvidenceRequest(BaseModel):
    dispute_id: str = Field(..., description="Target dispute ID")
    evidence_type: EvidenceType = Field(..., description="Category of evidence")
    source: EvidenceSource = Field(..., description="Submitting party")
    raw_payload: Dict[str, Any] = Field(default_factory=dict, description="Structured metadata/evidence payload")
    actor: str = Field(default="SYSTEM", description="Actor attaching the evidence")
    file_name: Optional[str] = Field(None, description="Original filename if applicable")


class StatementSubmissionRequest(BaseModel):
    dispute_id: str = Field(..., description="Target dispute ID")
    statement_type: str = Field(..., description="CARDHOLDER or MERCHANT", json_schema_extra={"example": "CARDHOLDER"})
    statement_text: str = Field(..., min_length=5, description="Full text statement")
    author: str = Field(..., description="Author of the statement", json_schema_extra={"example": "Alice Smith"})

    @field_validator("statement_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v_upper = v.upper()
        if v_upper not in ["CARDHOLDER", "MERCHANT"]:
            raise ValueError("statement_type must be either 'CARDHOLDER' or 'MERCHANT'")
        return v_upper


class AdminOverrideRequest(BaseModel):
    override_decision: ResolutionOutcome = Field(..., description="Overridden outcome", json_schema_extra={"example": ResolutionOutcome.FAVOR_CARDHOLDER})
    mandatory_reason: str = Field(
        ...,
        min_length=10,
        description="Mandatory written justification for override (SRS FR-27, AC-13)",
        json_schema_extra={"example": "Carrier GPS confirms parcel was delivered to incorrect geographic coordinate 0.4 miles away."}
    )
    admin_id: str = Field(..., description="ID of the Dispute-Ops Administrator", json_schema_extra={"example": "adm_marcus_01"})
    admin_name: str = Field(default="Dispute-Ops Admin", description="Name of the administrator")


class AssignCaseRequest(BaseModel):
    analyst_id: str = Field(..., description="ID of the analyst assigned to this case", json_schema_extra={"example": "ana_elena_02"})
    analyst_name: str = Field(..., description="Name of the analyst", json_schema_extra={"example": "Elena Vance"})


class DisputeListResponse(BaseModel):
    total_count: int = Field(..., description="Total matching disputes")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=20, description="Items per page")
    total_pages: int = Field(..., description="Total pages")
    items: List[UnifiedCaseFile] = Field(default_factory=list, description="List of case files")


class SystemStatusResponse(BaseModel):
    status: str = "operational"
    service: str = "VerdictAI REST API Gateway"
    version: str = "1.0.0"
    active_disputes_count: int = 0
    uptime_status: str = "99.5%+"
    timestamp: datetime = Field(default_factory=utc_now)
