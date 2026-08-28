# Mathematical Weight Distribution for Dispute Evidence Types
**Project:** Frictionless Dispute & Chargeback Resolution  
**Author:** Akshay Purohit (202512033) — ML Engineer – Fair-Weighing Model  
**Phase:** Phase 1 – Discovery & Design  
**Date:** August 15, 2026

---

## 1. Purpose

This document formalises the mathematical framework behind the fair-weighing model. It defines:
- Evidence weight functions per dispute category
- Score aggregation formulas
- Confidence normalisation
- Penalty and bonus adjustment rules

---

## 2. Notation

| Symbol | Meaning |
|---|---|
| `E = {e₁, e₂, ..., eₙ}` | Set of all evidence items in the case |
| `eᵢ` | A single evidence item |
| `S(eᵢ)` | Base score of evidence item eᵢ ∈ [0, 10] |
| `W(eᵢ, cat)` | Weight of eᵢ for dispute category `cat` ∈ [0, 1] |
| `F(eᵢ)` | Favour direction: +1 (CM), -1 (MR), 0 (Neutral) |
| `P(eᵢ)` | Presence indicator: 1 if available, 0 if missing |
| `Q(eᵢ)` | Quality score of evidence ∈ [0, 1] (from NLP parser) |
| `C` | Final Confidence Score ∈ [0, 100] |

---

## 3. Core Scoring Formula

### Step 1 — Effective Score per Evidence Item

```
ES(eᵢ) = S(eᵢ) × W(eᵢ, cat) × P(eᵢ) × Q(eᵢ)
```

Where:
- `S(eᵢ)` is the base reliability score for that evidence type (see Section 4)
- `W(eᵢ, cat)` is the category-specific weight (see Section 5)
- `P(eᵢ)` = 1 (present) or 0 (missing)
- `Q(eᵢ)` = quality/confidence signal from the NLP parser (0.0 – 1.0)

### Step 2 — Side Attribution

```
CM_contribution(eᵢ) = ES(eᵢ)    if F(eᵢ) = +1 (CM favours)
MR_contribution(eᵢ) = ES(eᵢ)    if F(eᵢ) = -1 (MR favours)
Neutral(eᵢ)         = ES(eᵢ)/2  if F(eᵢ) =  0 (split equally)
```

### Step 3 — Aggregate Raw Scores

```
CM_raw = Σ CM_contribution(eᵢ)  +  Σ Neutral(eᵢ)   for all eᵢ ∈ E
MR_raw = Σ MR_contribution(eᵢ)  +  Σ Neutral(eᵢ)   for all eᵢ ∈ E
```

### Step 4 — Normalise to [0, 100]

```
Total = CM_raw + MR_raw

CM_score = (CM_raw / Total) × 100    if Total > 0
MR_score = (MR_raw / Total) × 100    if Total > 0

C = max(CM_score, MR_score)
```

If `Total = 0` (no evidence): `C = 0`, Resolution = `ESCALATE`

### Step 5 — Apply Adjustments (Section 6)

```
C_adj = C + Bonus_adjustments - Penalty_adjustments
C_final = clamp(C_adj, 0, 100)
```

### Step 6 — Resolution Decision

```
IF   C_final >= 70  AND  CM_score > MR_score  →  CARD_MEMBER_FAVOUR
ELIF C_final >= 70  AND  MR_score > CM_score  →  MERCHANT_FAVOUR
ELIF 50 <= C_final < 70                        →  (same as above, flagged low-confidence)
ELSE C_final < 50                              →  ESCALATE
```

---

## 4. Base Scores S(eᵢ) — Evidence Type Reliability

These are static reliability weights representing how trustworthy each evidence type is intrinsically:

| Evidence ID | Evidence Type | S(eᵢ) | Rationale |
|---|---|---|---|
| EV-01 | Transaction Record | 10 | Authoritative card-network record |
| EV-02 | Merchant Receipt/Invoice | 9 | Formal merchant-issued document |
| EV-03 | Delivery/Tracking Confirmation | 10 | Carrier-verified, timestamped |
| EV-04 | Merchant Communication Log | 7 | Relevant but subjective |
| EV-05 | Card Member Communication | 7 | Relevant but self-reported |
| EV-06 | Product/Service Description | 6 | Public listing, can be edited |
| EV-07 | Refund/Cancellation Record | 9 | Formal record with timestamp |
| EV-08 | Authentication Log | 8 | System-generated, hard to forge |
| EV-09 | Dispute Reason Statement | 5 | Subjective self-declaration |
| EV-10 | Photographic Evidence | 7 | Verifiable but can be staged |

---

## 5. Category-Specific Weight Matrix W(eᵢ, cat)

Each cell is the fractional weight `W(eᵢ, cat)` for that evidence in that category. Row sums = 1.0.

| Evidence | CAT-01 | CAT-02 | CAT-03 | CAT-04 | CAT-05 | CAT-06 | CAT-07 |
|---|---|---|---|---|---|---|---|
| EV-01 | 0.20 | 0.15 | 0.25 | 0.50 | 0.10 | 0.20 | 0.15 |
| EV-02 | 0.10 | 0.15 | 0.05 | 0.25 | 0.05 | 0.15 | 0.10 |
| EV-03 | 0.35 | 0.05 | 0.00 | 0.00 | 0.00 | 0.00 | 0.05 |
| EV-04 | 0.10 | 0.10 | 0.10 | 0.05 | 0.20 | 0.15 | 0.20 |
| EV-05 | 0.10 | 0.10 | 0.15 | 0.05 | 0.20 | 0.10 | 0.15 |
| EV-06 | 0.00 | 0.20 | 0.00 | 0.00 | 0.10 | 0.05 | 0.10 |
| EV-07 | 0.00 | 0.05 | 0.00 | 0.15 | 0.25 | 0.30 | 0.10 |
| EV-08 | 0.00 | 0.00 | 0.40 | 0.00 | 0.00 | 0.00 | 0.00 |
| EV-09 | 0.10 | 0.15 | 0.05 | 0.00 | 0.10 | 0.05 | 0.10 |
| EV-10 | 0.05 | 0.05 | 0.00 | 0.00 | 0.00 | 0.00 | 0.05 |

---

## 6. Adjustment Rules

### 6.1 Penalty: Missing Primary Evidence

For each dispute category, one evidence type is designated **Primary**. If it is missing (`P(eᵢ) = 0`):

```
Penalty = -15 points applied to C (floor: 30)
```

| Category | Primary Evidence |
|---|---|
| CAT-01 | EV-03 (Delivery Confirmation) |
| CAT-02 | EV-06 (Product Description) + EV-10 (Photo) |
| CAT-03 | EV-08 (Auth Log) |
| CAT-04 | EV-01 (Transaction Record ×2) |
| CAT-05 | EV-07 (Cancellation Record) |
| CAT-06 | EV-07 (Refund Record) |
| CAT-07 | EV-04 + EV-05 (Communication Logs) |

### 6.2 Bonus: High-Quality Evidence

If `Q(eᵢ) > 0.9` for any primary evidence item:

```
Bonus = +5 points applied to C (ceiling: 100)
```

### 6.3 Contradiction Penalty

If CM communication log (EV-05) **contradicts** the dispute statement (EV-09) as detected by the NLP parser:

```
Contradiction_Penalty = -10 points
```

---

## 7. Calibration Summary

Initial calibration targets (validated in Phase 3 against 200 labelled disputes):

| Metric | Target |
|---|---|
| Accuracy (correct side wins) | ≥ 85% |
| False Positive Rate (FPR) | ≤ 2% |
| Escalation Rate | ≤ 20% |
| Mean Confidence (auto-resolved) | ≥ 72 |

---

## 8. Version History

| Version | Date | Author | Notes |
|---|---|---|---|
| v0.1 | Aug 15, 2026 | Akshay Purohit | Initial mathematical framework |
