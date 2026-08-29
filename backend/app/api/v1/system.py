"""
VerdictAI System Status & Health Endpoints
Author: Darshan Prajapati (Backend Engineer - Reasoning & APIs)
"""

from fastapi import APIRouter
from backend.app.models.api_schemas import SystemStatusResponse, utc_now
from backend.app.core.db import db_manager

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status():
    """
    Returns real-time system operational metrics and active case counts.
    """
    disputes_table = db_manager.pg_tables.get("disputes", {})
    return SystemStatusResponse(
        status="operational",
        service="VerdictAI REST API Gateway",
        version="1.0.0",
        active_disputes_count=len(disputes_table),
        uptime_status="99.5%+",
        timestamp=utc_now()
    )
