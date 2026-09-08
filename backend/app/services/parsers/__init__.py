"""
VerdictAI Evidence Parsing Pipeline
Author: Achyut Pathak (AI/NLP Engineer — Evidence Parsing)

Public API for the parsers sub-package.
"""

from backend.app.services.parsers.base_parser import (
    AnomalyLevel,
    ClaimAlignment,
    DetectedAnomaly,
    EvidenceParser,
    ExtractedEntity,
    ParsedEvidence,
)
from backend.app.services.parsers.transaction_parser import TransactionParser
from backend.app.services.parsers.receipt_parser import ReceiptParser
from backend.app.services.parsers.courier_tracking_parser import CourierTrackingParser

__all__ = [
    # Base
    "EvidenceParser",
    "ParsedEvidence",
    "ExtractedEntity",
    "DetectedAnomaly",
    "ClaimAlignment",
    "AnomalyLevel",
    # Parsers
    "TransactionParser",
    "ReceiptParser",
    "CourierTrackingParser",
]
