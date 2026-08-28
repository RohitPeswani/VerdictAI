# Mock-Data Schema Alignment Notes
**Project:** Frictionless Dispute & Chargeback Resolution  
**Author:** Akshay Purohit (202512033) — ML Engineer – Fair-Weighing Model  
**Phase:** Phase 2 – Evidence Pipeline & Mock Data  
**Date:** September 6, 2026

---

## 1. Overview

This document specifies how the synthetic dataset (`mock_disputes_dataset.json`) aligns with:
1. **Achyut Pathak's (AI/NLP Engineer)** evidence-parsing JSON output schema.
2. **Darshan Prajapati's (Backend Engineer)** REST API case payloads (`openapi.yaml`).
3. **Akshay Purohit's (ML Engineer)** fair-weighing scoring input model.

---

## 2. Shared Evidence Interface Schema

To ensure seamless integration in Phase 5, the mock data complies with the following unified JSON schema structure agreed upon in Phase 1:

```json
{
  "case_id": "string (UUID or CAS-YYYYMMDD-XXX)",
  "dispute_category_id": "string (CAT-01 to CAT-07)",
  "dispute_category_name": "string",
  "amount": "number",
  "currency": "string (INR/USD)",
  "created_at": "ISO-8601 timestamp",
  "evidence_items": [
    {
      "evidence_id": "string (EV-01 to EV-10)",
      "evidence_type": "string",
      "status": "string (Present | Missing | Pending)",
      "quality_score": "number (0.0 to 1.0)",
      "favours": "string (CARD_MEMBER | MERCHANT | NEUTRAL)",
      "details": "object (type-specific metadata)"
    }
  ],
  "ground_truth_resolution": "string (CARD_MEMBER | MERCHANT | ESCALATE)",
  "expected_confidence_target": "number (0 to 100)"
}
```

---

## 3. Data Mapping Verification

| Field | Source Module (Owner) | ML Model Usage | Validation Status |
|---|---|---|---|
| `case_id` | Case API (Darshan) | Case tracking & logging | ✅ Aligned |
| `dispute_category_id` | Case API (Nirav/Darshan) | Selects Weight Matrix `W(eᵢ, cat)` | ✅ Aligned |
| `evidence_items[].evidence_id` | NLP Ingestion (Achyut) | Lookup Base Score `S(eᵢ)` | ✅ Aligned |
| `evidence_items[].status` | Ingestion Service (Achyut) | Presence Multiplier `P(eᵢ)` (1 or 0) | ✅ Aligned |
| `evidence_items[].quality_score` | NLP Confidence (Achyut) | Quality Multiplier `Q(eᵢ)` (0.0-1.0) | ✅ Aligned |
| `evidence_items[].favours` | Evidence Classifier (Achyut) | Direction Vector `F(eᵢ)` (+1, -1, 0) | ✅ Aligned |
| `evidence_items[].details` | Parsed Extraction (Achyut) | Gemini Prompt Explanation context | ✅ Aligned |

---

## 4. Dataset Statistics

- **Total Cases Generated:** 56 cases (8 scenarios × 7 categories)
- **Category Coverage:** CAT-01 through CAT-07 fully represented
- **Outcome Distribution:**
  - `CARD_MEMBER`: 21 cases (~37.5%)
  - `MERCHANT`: 21 cases (~37.5%)
  - `ESCALATE`: 14 cases (~25.0%)
- **Confidence Tiers:**
  - High Confidence (>= 80): 28 cases
  - Medium Confidence (50 - 79): 14 cases
  - Low Confidence / Escalation (< 50): 14 cases

---

## 5. Next Steps for Phase 3

The synthetic dataset `mock_disputes_dataset.json` will serve as the benchmark suite for validating `fair_weighing_model.py` and calibrating the Gemini API prompt in Phase 3.
