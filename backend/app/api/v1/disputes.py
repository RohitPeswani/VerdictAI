"""
VerdictAI Dispute Lifecycle & Case Management REST Endpoints
Author: Darshan Prajapati (Backend Engineer - Reasoning & APIs)
"""

import math
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.models.schemas import (
    UnifiedCaseFile,
    DisputeStatus,
    DisputeReason
)
from backend.app.models.api_schemas import (
    DisputeCreateRequest,
    DisputeListResponse,
    StateTransitionRequest,
    utc_now
)
from backend.app.services.case_builder.service import case_service
from backend.app.services.state_machine.state_machine import (
    DisputeStateMachine,
    InvalidStateTransitionError
)
from backend.app.services.audit_engine.audit import audit_engine
from backend.app.core.db import db_manager

router = APIRouter(prefix="/disputes", tags=["Disputes"])


@router.post(
    "",
    response_model=UnifiedCaseFile,
    status_code=status.HTTP_201_CREATED,
    summary="File a new dispute"
)
async def create_dispute(payload: DisputeCreateRequest):
    """
    Creates a new cardholder dispute case file, registers transaction records,
    calculates SLA deadlines, and establishes the cryptographic audit trail (SRS FR-06, FR-09, UC-01).
    """
    try:
        case_file = case_service.create_dispute_case(
            transaction_id=payload.transaction_id,
            cardholder_id=payload.cardholder_id,
            dispute_reason=payload.dispute_reason,
            disputed_amount=payload.disputed_amount,
            cardholder_statement=payload.cardholder_statement,
            merchant_sla_hours=payload.merchant_sla_hours
        )
        return case_file
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create dispute: {str(e)}"
        )


@router.get(
    "",
    response_model=DisputeListResponse,
    summary="List and filter disputes"
)
async def list_disputes(
    status: Optional[DisputeStatus] = Query(None, description="Filter by current dispute status"),
    cardholder_id: Optional[str] = Query(None, description="Filter by cardholder user ID"),
    merchant_id: Optional[str] = Query(None, description="Filter by merchant ID"),
    reason: Optional[DisputeReason] = Query(None, description="Filter by dispute reason category"),
    search: Optional[str] = Query(None, description="Search by case ID or reference number"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Retrieves a paginated list of unified case files with multi-criteria filtering (SRS FR-22, FR-25).
    """
    all_dispute_records = list(db_manager.pg_tables.get("disputes", {}).values())
    filtered_cases = []

    for dispute_rec in all_dispute_records:
        d_id = dispute_rec["id"]
        case_file = case_service.get_unified_case_file(d_id)
        if not case_file:
            continue

        # Status filter
        if status and case_file.header.current_status != status:
            continue

        # Cardholder filter
        if cardholder_id and case_file.transaction.cardholder_id != cardholder_id:
            continue

        # Merchant filter
        if merchant_id and case_file.transaction.merchant_id != merchant_id:
            continue

        # Reason filter
        if reason and case_file.header.dispute_reason != reason:
            continue

        # Keyword search
        if search:
            q = search.lower()
            ref = case_file.header.case_reference_number.lower()
            cid = case_file.header.case_file_id.lower()
            did = case_file.header.dispute_id.lower()
            mname = case_file.transaction.merchant_name.lower()
            cname = case_file.transaction.cardholder_name.lower()
            if not any(q in field for field in [ref, cid, did, mname, cname]):
                continue

        filtered_cases.append(case_file)

    # Sort descending by creation date
    filtered_cases.sort(key=lambda c: c.header.created_at, reverse=True)

    total_count = len(filtered_cases)
    total_pages = max(1, math.ceil(total_count / page_size))
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_items = filtered_cases[start_idx:end_idx]

    return DisputeListResponse(
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=paginated_items
    )


@router.get(
    "/{dispute_id}",
    response_model=UnifiedCaseFile,
    summary="Get Unified Case File details"
)
async def get_dispute(dispute_id: str):
    """
    Retrieves the complete, tamper-evident case file combining PostgreSQL transactional data
    and MongoDB polymorphic evidence items (SRS FR-26, SIR-01).
    """
    case_file = case_service.get_unified_case_file(dispute_id)
    if not case_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute with ID '{dispute_id}' not found."
        )
    return case_file


@router.patch(
    "/{dispute_id}/status",
    summary="Transition dispute lifecycle status"
)
async def transition_status(dispute_id: str, payload: StateTransitionRequest):
    """
    Validates and performs deterministic state transitions across the dispute lifecycle (SRS FR-30, FR-32).
    """
    dispute_rec = db_manager.get_pg_record("disputes", dispute_id)
    if not dispute_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute with ID '{dispute_id}' not found."
        )

    current_status = DisputeStatus(dispute_rec["current_status"])
    try:
        new_status = DisputeStateMachine.execute_transition(
            dispute_id=dispute_id,
            current_status=current_status,
            target_status=payload.target_status,
            actor=payload.actor,
            reason=payload.reason
        )
        dispute_rec["current_status"] = new_status.value
        dispute_rec["updated_at"] = utc_now().isoformat()
        db_manager.update_pg_record("disputes", dispute_id, dispute_rec)
        return {
            "dispute_id": dispute_id,
            "previous_status": current_status.value,
            "current_status": new_status.value,
            "transitioned_by": payload.actor,
            "reason": payload.reason
        }
    except InvalidStateTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{dispute_id}/audit-trail",
    summary="Get cryptographic audit trail"
)
async def get_dispute_audit_trail(dispute_id: str):
    """
    Returns the full audit log chain and cryptographic integrity verification status (SRS FR-21, FR-32).
    """
    dispute_rec = db_manager.get_pg_record("disputes", dispute_id)
    if not dispute_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute with ID '{dispute_id}' not found."
        )

    trail = audit_engine.get_audit_trail(dispute_id)
    is_valid = audit_engine.verify_integrity(dispute_id)

    return {
        "dispute_id": dispute_id,
        "is_chain_intact": is_valid,
        "total_events": len(trail),
        "audit_logs": trail
    }
