"""
VerdictAI Evidence Parsing Pipeline — Dispatcher & Orchestration Bridge
Author: Nirav Kachhiya (Project Lead / Backend Engineer)

Wires polymorphic evidence types to their dedicated parsing engines,
providing automated schema validation, entity extraction, and anomaly detection.
"""

import logging
from typing import Any, Dict, List, Optional

from database.mongodb.models import EvidenceType
from backend.app.services.parsers.base_parser import EvidenceParser, ParsedEvidence
from backend.app.services.parsers.transaction_parser import TransactionParser
from backend.app.services.parsers.receipt_parser import ReceiptParser
from backend.app.services.parsers.courier_tracking_parser import CourierTrackingParser
from backend.app.services.nlp.communication_parser import CommunicationLogParser

logger = logging.getLogger(__name__)


class EvidenceParserDispatcher:
    """
    Central dispatcher that inspects the evidence type and delegates parsing
    to the appropriate domain-specific parser engine.
    """

    def __init__(self):
        self._parsers: Dict[EvidenceType, EvidenceParser] = {
            EvidenceType.RECEIPT_INVOICE: ReceiptParser(),
            EvidenceType.COURIER_TRACKING: CourierTrackingParser(),
            EvidenceType.COMMUNICATION_LOG: CommunicationLogParser(),
            EvidenceType.BANK_STATEMENT: TransactionParser(),
        }

    def register_parser(self, evidence_type: EvidenceType, parser: EvidenceParser) -> None:
        """Register or override a parser for a specific evidence type."""
        self._parsers[evidence_type] = parser

    def get_parser(self, evidence_type: EvidenceType) -> Optional[EvidenceParser]:
        """Returns the parser registered for the given evidence type, if any."""
        return self._parsers.get(evidence_type)

    def is_supported(self, evidence_type: EvidenceType) -> bool:
        """Checks if a dedicated parser exists for the evidence type."""
        return evidence_type in self._parsers

    def get_supported_types(self) -> List[EvidenceType]:
        """Returns a list of all evidence types that have registered parsers."""
        return list(self._parsers.keys())

    def dispatch_and_parse(
        self,
        evidence_type: EvidenceType,
        raw_payload: Dict[str, Any]
    ) -> Optional[ParsedEvidence]:
        """
        Validates and parses a raw evidence payload using the registered parser.

        Parameters
        ----------
        evidence_type : EvidenceType
            The classification of the evidence payload.
        raw_payload : Dict[str, Any]
            The raw JSON payload submitted by the user/integration.

        Returns
        -------
        Optional[ParsedEvidence]
            The structured extraction result with entities, anomalies, and confidence score,
            or None if no parser exists or if parsing cannot proceed.
        """
        parser = self.get_parser(evidence_type)
        if not parser:
            logger.debug("No parser registered for evidence type %s", evidence_type)
            return None

        if not isinstance(raw_payload, dict):
            logger.warning("Raw payload for %s is not a dictionary", evidence_type)
            return None

        # Check if the payload passes minimum validation requirements
        if not parser.validate(raw_payload):
            logger.info(
                "Payload for %s failed parser validation; skipping automated parsing",
                evidence_type
            )
            return None

        try:
            parsed = parser.parse(raw_payload)
            logger.info(
                "Successfully parsed %s evidence with %s (confidence: %.2f, anomalies: %d)",
                evidence_type.value,
                parser.parser_name,
                parsed.confidence_score,
                len(parsed.anomalies)
            )
            return parsed
        except Exception as e:
            logger.warning(
                "Parser %s raised exception for %s: %s",
                parser.parser_name,
                evidence_type.value,
                str(e),
                exc_info=True
            )
            return None


evidence_dispatcher = EvidenceParserDispatcher()
