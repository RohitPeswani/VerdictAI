# VerdictAI — Evidence Parsing & NLP Pipeline Architecture

**Author:** Achyut Pathak (AI/NLP Engineer — Evidence Parsing)
**Date:** September 2026
**Version:** 1.0

---

## 1. Overview

The Evidence Parsing Pipeline is responsible for ingesting, validating, and
extracting structured information from multi-modal dispute evidence submitted
by cardholders, merchants, and payment gateways. It feeds normalised data into
the Case Builder service and the Fair-Weighing ML scoring model.

### Design Goals

| Goal | Implementation |
|------|---------------|
| **Deterministic Parsing** | Rule-based & regex extraction ensures reproducible results across runs |
| **Polymorphic Evidence** | Single `EvidenceParser` interface handles transactions, receipts, tracking, and communication logs |
| **Anomaly Detection** | Each parser identifies evidence-specific red flags (amount mismatches, address discrepancies, unsigned deliveries) |
| **Claim Alignment** | Automated assessment of whether evidence SUPPORTS_CARDHOLDER, SUPPORTS_MERCHANT, or is NEUTRAL |
| **Testability** | No external service dependencies; 100% unit-testable without network or model downloads |
| **spaCy Compatibility** | Interface mirrors spaCy pipeline patterns for future upgrade to transformer models |

---

## 2. Evidence JSON Schema Design

### 2.1 Input Contract

All parsers consume the `raw_payload` dictionary from `EvidencePayloadModel`
(defined in `database/mongodb/models.py`). Each parser type expects specific
keys:

#### Transaction Evidence
```json
{
  "merchant_name": "Apex Electronics Direct",
  "amount": 1249.50,
  "currency": "USD",
  "transaction_date": "2026-08-20T14:32:00Z",
  "card_last_four": "4242",
  "mcc_code": "5411",
  "merchant_location": "San Francisco, CA",
  "payment_method": "VISA_CREDIT",
  "transaction_id": "txn_abc123",
  "authorization_code": "AUTH-789",
  "description": "APEX ELECTRONICS *ONLINE SAN FRANCISCO CA"
}
```

#### Receipt / Invoice Evidence
```json
{
  "merchant_name": "Apex Electronics Direct",
  "total": 1249.50,
  "currency": "USD",
  "receipt_number": "INV-2026-08-001",
  "receipt_date": "2026-08-20",
  "subtotal": 1178.30,
  "tax": 71.20,
  "payment_method": "VISA ****4242",
  "line_items": [
    {"description": "Wireless Noise-Cancelling Headphones", "quantity": 1, "unit_price": 299.99},
    {"description": "USB-C Charging Cable (3-pack)", "quantity": 2, "unit_price": 19.99}
  ],
  "transaction_amount": 1249.50
}
```

#### Courier Tracking Evidence
```json
{
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
  "delivery_address_match": true,
  "status_history": [
    {"status": "SHIPPED", "timestamp": "2026-08-20T16:00:00Z"},
    {"status": "IN_TRANSIT", "timestamp": "2026-08-21T08:00:00Z"},
    {"status": "DELIVERED", "timestamp": "2026-08-22T10:30:00Z"}
  ]
}
```

#### Communication Log Evidence
```json
{
  "channel": "EMAIL",
  "messages": [
    {
      "sender": "Alice Smith",
      "role": "CARDHOLDER",
      "timestamp": "2026-08-21T09:00:00Z",
      "content": "I ordered product X but never received it. Please refund."
    },
    {
      "sender": "Apex Support",
      "role": "MERCHANT",
      "timestamp": "2026-08-21T14:00:00Z",
      "content": "Our tracking shows it was delivered and signed for."
    }
  ]
}
```

### 2.2 Output Contract — `ParsedEvidence`

Every parser returns a `ParsedEvidence` dataclass:

```python
@dataclass
class ParsedEvidence:
    parser_name: str
    parsed_at: datetime
    structured_data: Dict[str, Any]       # Normalised extracted fields
    extracted_entities: List[ExtractedEntity]  # NLP entities
    anomalies: List[DetectedAnomaly]      # Red-flags detected
    confidence_score: float               # 0.0 – 1.0
    claim_alignment: ClaimAlignment       # SUPPORTS_CARDHOLDER | SUPPORTS_MERCHANT | NEUTRAL
    raw_text_content: Optional[str]
    metadata: Dict[str, Any]
```

---

## 3. NLP Tool Selection Rationale

### Why Rule-Based + Regex (not pure spaCy / HF Transformers)?

| Criterion | Rule-Based (Selected) | spaCy / HF Transformers |
|-----------|----------------------|------------------------|
| **Determinism** | ✅ Identical output every run | ❌ Stochastic model inference |
| **CI/CD Compatibility** | ✅ No model downloads | ❌ Requires ~500MB models |
| **Latency** | ✅ Sub-millisecond | ⚠ 10–100ms per document |
| **Testability** | ✅ Pure unit tests | ⚠ Requires model fixtures |
| **Domain Coverage** | ✅ Tailored to dispute vocabulary | ⚠ Generic NER models |
| **Upgrade Path** | ✅ Interface is spaCy-compatible | N/A |

The `EntityExtractor` class is designed with the same method signature as
`spaCy.nlp()` output, making it a drop-in replacement when production
spaCy/HF models become available.

---

## 4. Pipeline Data Flow

```
┌────────────────────┐
│  Evidence Payload   │  (EvidencePayloadModel.raw_payload)
│  (JSON dict)        │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  Parser Selection   │  TransactionParser / ReceiptParser /
│  (by EvidenceType)  │  CourierTrackingParser / CommunicationLogParser
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  Validation         │  _require_fields() checks
│                     │  validate() pre-check
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  Entity Extraction  │  Regex patterns → ExtractedEntity objects
│  (EntityExtractor)  │  DATE, MONEY, PERSON, ORDER_ID, TRACKING_NUMBER
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  Anomaly Detection  │  Cross-referencing, validation rules
│                     │  Amount mismatches, address issues, etc.
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  Confidence &       │  Heuristic scoring + penalty for anomalies
│  Claim Alignment    │  SUPPORTS_CARDHOLDER / SUPPORTS_MERCHANT / NEUTRAL
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  ParsedEvidence     │  → Case Builder
│  Output             │  → Fair-Weighing ML Model
└────────────────────┘
```

---

## 5. Module Inventory

| Module | Path | Description |
|--------|------|-------------|
| `base_parser` | `backend/app/services/parsers/base_parser.py` | ABC, shared dataclasses |
| `transaction_parser` | `backend/app/services/parsers/transaction_parser.py` | Bank/card transaction parsing |
| `receipt_parser` | `backend/app/services/parsers/receipt_parser.py` | Invoice/receipt parsing |
| `courier_tracking_parser` | `backend/app/services/parsers/courier_tracking_parser.py` | Carrier tracking parsing |
| `entity_extractor` | `backend/app/services/nlp/entity_extractor.py` | Rule-based NER engine |
| `communication_parser` | `backend/app/services/nlp/communication_parser.py` | Communication log NLP |

---

## 6. Integration Points

- **Case Builder** (`backend/app/services/case_builder/service.py`):
  `CaseService.attach_evidence()` calls parsers to enrich `EvidencePayloadModel.nlp_extracted_entities`.
- **Evidence API** (`backend/app/api/v1/evidence.py`):
  Structured evidence payloads routed through parser pipeline.
- **Fair-Weighing Model** (`akshay_ml_fairweighing/`):
  `ParsedEvidence.claim_alignment` and `confidence_score` feed into scoring inputs.
- **Audit Engine** (`backend/app/services/audit_engine/`):
  Parser execution logged as `EVIDENCE_PARSED` audit events.
