# Fair-Weighing Scoring Rubric v0
**Project:** Frictionless Dispute & Chargeback Resolution  
**Author:** Akshay Purohit (202512033) — ML Engineer – Fair-Weighing Model  
**Phase:** Phase 1 – Discovery & Design  
**Date:** August 15, 2026  
**Version:** 0.1 (Initial)

---

## 1. Overview

This document defines the scoring criteria used to evaluate the relative strength of Card Member and Merchant evidence in a dispute case. The fair-weighing model produces:

- A **Confidence Score** (0–100) representing the system's certainty in the resolution.
- A **Recommended Resolution** (`CARD_MEMBER_FAVOUR`, `MERCHANT_FAVOUR`, `ESCALATE`).
- A **Factor Breakdown** listing the weight and contribution of each evidence item.

Cases with Confidence Score < 50 are automatically routed to the Admin Review Queue and are NOT auto-resolved (per FR-16 / AC-09).

---

## 2. Dispute Categories

The scoring rubric is applied per dispute category. Categories and their primary evidence type:

| Category ID | Category Name | Primary Evidence |
|---|---|---|
| CAT-01 | Item Not Received | Delivery/tracking confirmation |
| CAT-02 | Item Not as Described | Merchant product listing + photos |
| CAT-03 | Unauthorized Transaction | Transaction metadata + biometric/auth logs |
| CAT-04 | Duplicate Charge | Transaction records (two matching charges) |
| CAT-05 | Cancelled Subscription | Cancellation communication log |
| CAT-06 | Refund Not Processed | Merchant refund confirmation |
| CAT-07 | Service Not Rendered | Service booking + communication logs |

---

## 3. Evidence Types & Base Scores

Each evidence item is evaluated independently and assigned a **Base Score** (0–10) and a **Weight** (%) that reflects its importance for the dispute category.

| Evidence ID | Evidence Type | Max Base Score | Description |
|---|---|---|---|
| EV-01 | Transaction Record | 10 | Official transaction metadata from card network |
| EV-02 | Merchant Receipt/Invoice | 9 | Proof of sale issued by merchant |
| EV-03 | Delivery/Tracking Confirmation | 10 | Carrier-confirmed delivery with timestamp |
| EV-04 | Merchant Communication Log | 7 | Emails/chats between merchant and card member |
| EV-05 | Card Member Communication Log | 7 | Card member's side of communications |
| EV-06 | Product/Service Description | 6 | Merchant's advertised listing or service terms |
| EV-07 | Refund/Cancellation Record | 9 | Formal refund or cancellation confirmation |
| EV-08 | Authentication/Auth Log | 8 | Login, OTP, or biometric auth records |
| EV-09 | Dispute Reason Statement | 5 | Card member's written dispute description |
| EV-10 | Photographic Evidence | 7 | Images of received item or damaged goods |

---

## 4. Scoring Formula

### 4.1 Evidence Presence Score

For each evidence item present in the case:

```
Presence_Score(EV-i) = Base_Score(EV-i) × Weight(category, EV-i)
```

### 4.2 Side Weighted Score

Each piece of evidence favours either the Card Member (CM) or Merchant (MR):

```
CM_Raw_Score  = Σ [ Presence_Score(EV-i) × Favour_Factor_CM(EV-i) ]
MR_Raw_Score  = Σ [ Presence_Score(EV-i) × Favour_Factor_MR(EV-i) ]
```

### 4.3 Normalised Confidence Score

```
Total = CM_Raw_Score + MR_Raw_Score
CM_Score_Norm = (CM_Raw_Score / Total) × 100
MR_Score_Norm = (MR_Raw_Score / Total) × 100

Confidence_Score = max(CM_Score_Norm, MR_Score_Norm)
```

### 4.4 Resolution Recommendation

```
IF Confidence_Score >= 70:
    IF CM_Score_Norm > MR_Score_Norm → CARD_MEMBER_FAVOUR
    ELSE                              → MERCHANT_FAVOUR
ELIF 50 <= Confidence_Score < 70:
    Recommend with lower confidence (same logic)
ELSE (Confidence_Score < 50):
    → ESCALATE (route to Admin Review Queue)
```

---

## 5. Category-Specific Evidence Weight Table

### CAT-01: Item Not Received

| Evidence Type | Weight (%) | Favours |
|---|---|---|
| EV-03 Delivery Confirmation | 35% | Merchant (if delivered) / CM (if not) |
| EV-01 Transaction Record | 20% | Neutral |
| EV-04 Merchant Communication | 15% | Context-dependent |
| EV-05 CM Communication | 15% | Context-dependent |
| EV-02 Receipt | 10% | Merchant |
| EV-09 Dispute Statement | 5% | Card Member |

### CAT-03: Unauthorized Transaction

| Evidence Type | Weight (%) | Favours |
|---|---|---|
| EV-08 Auth Log | 40% | Merchant (if auth present) / CM (if absent) |
| EV-01 Transaction Record | 25% | Neutral |
| EV-05 CM Communication | 15% | Card Member |
| EV-04 Merchant Communication | 10% | Merchant |
| EV-09 Dispute Statement | 10% | Card Member |

### CAT-04: Duplicate Charge

| Evidence Type | Weight (%) | Favours |
|---|---|---|
| EV-01 Transaction Record (×2) | 50% | Card Member (if duplicate confirmed) |
| EV-02 Receipt | 25% | Neutral |
| EV-07 Refund Record | 15% | Merchant (if refund issued) |
| EV-09 Dispute Statement | 10% | Card Member |

---

## 6. Missing Evidence Handling

Per AC-06: Unavailable evidence is labelled "Missing" and does NOT block scoring.

- Missing **optional** evidence: no deduction applied.
- Missing **primary** evidence: confidence score is penalised by 15 points (soft cap floor at 30).
- If ALL primary evidence is missing: `Confidence_Score = 0` → force ESCALATE.

---

## 7. Output Format

The model returns a structured scoring result:

```json
{
  "case_id": "CAS-20260901-001",
  "dispute_category": "CAT-01",
  "confidence_score": 82,
  "recommended_resolution": "CARD_MEMBER_FAVOUR",
  "cm_score": 82,
  "mr_score": 18,
  "factor_breakdown": [
    {
      "evidence_id": "EV-03",
      "evidence_type": "Delivery/Tracking Confirmation",
      "status": "Missing",
      "contribution": 0,
      "favours": "CARD_MEMBER"
    },
    {
      "evidence_id": "EV-01",
      "evidence_type": "Transaction Record",
      "status": "Present",
      "contribution": 20,
      "favours": "NEUTRAL"
    }
  ],
  "plain_language_summary": "The delivery confirmation was not available, and the transaction record confirms a charge was made. Based on the available evidence, the case is resolved in favour of the Card Member."
}
```

---

## 8. Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| v0.1 | Aug 15, 2026 | Akshay Purohit | Initial rubric draft |
