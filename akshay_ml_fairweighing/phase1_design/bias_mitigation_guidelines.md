# Bias Mitigation Guidelines — Fair-Weighing Model
**Project:** Frictionless Dispute & Chargeback Resolution  
**Author:** Akshay Purohit (202512033) — ML Engineer – Fair-Weighing Model  
**Phase:** Phase 1 – Discovery & Design  
**Date:** August 15, 2026

---

## 1. Purpose

The fair-weighing model must not introduce or amplify bias based on user demographics, merchant size, transaction history, or any protected attribute. This document defines guidelines to prevent, detect, and mitigate bias in the scoring model, aligned with NFR-14 (FPR ≤ 2%).

---

## 2. Types of Bias Identified

| Bias Type | Description | Risk Level |
|---|---|---|
| **Historical Bias** | Model trained on past outcomes that may have been biased | High |
| **Merchant Size Bias** | Large merchants with more evidence may win unfairly | Medium |
| **Evidence Availability Bias** | Card members with fewer documents may score lower | Medium |
| **Category Bias** | Certain dispute categories may structurally favour one side | Medium |
| **Language Bias** | NLP models may perform worse on non-English communications | Low |
| **Recency Bias** | Recent disputes treated differently than older ones | Low |

---

## 3. Bias Mitigation Strategies

### 3.1 Evidence-Only Scoring

**Rule:** The model scores ONLY on evidence quality and presence. The following attributes are **explicitly excluded** from the scoring formula:

- Card Member's dispute history (number of past disputes filed)
- Merchant's size, revenue, or transaction volume
- Card Member's account tier or credit limit
- Geographic location of either party
- Device type used to file dispute

**Implementation:** The `fair_weighing_model.py` must filter these fields before passing data to the Gemini API prompt.

### 3.2 Symmetric Weight Application

**Rule:** The same weight matrix `W(eᵢ, cat)` is applied regardless of which side submitted the evidence. A delivery confirmation submitted by the merchant receives the same base weight as one auto-collected by the system.

### 3.3 Missing Evidence Neutrality

**Rule:** Missing evidence is treated as **absence of support**, not as negative evidence against the party who was supposed to provide it, UNLESS:
- A deadline was set and passed (merchant deadline for evidence submission)
- In that case, a time-expired flag is logged but the penalty is capped at -10 points

### 3.4 LLM Prompt Bias Controls

When using Gemini API for reasoning/explanation generation, the prompt must:

1. **Never include** party names, account IDs, merchant names, or demographics.
2. Use **role labels only**: "Party A (Card Member)" and "Party B (Merchant)".
3. Include an explicit instruction: *"Evaluate evidence objectively. Do not assume either party is more trustworthy based on any factor other than the provided evidence."*
4. Instruct the model to **list at least 3 specific evidence factors** in its explanation (per AC-10).

### 3.5 Calibration Against Protected Groups

During Phase 3 validation, the dataset of 200+ labelled disputes must be checked for:

```
FPR_overall  = FP / (FP + TN)  ≤ 2%
FPR_per_cat  = per-category FPR  ≤ 5%
```

If any category's FPR exceeds 5%, the weight matrix for that category must be recalibrated.

---

## 4. Fairness Metrics to Track

| Metric | Formula | Target |
|---|---|---|
| False Positive Rate (FPR) | FP / (FP + TN) | ≤ 2% |
| False Negative Rate (FNR) | FN / (FN + TP) | ≤ 5% |
| Escalation Rate | Escalated / Total | ≤ 20% |
| CM Win Rate (legitimate disputes) | Should reflect ground truth | Balanced |
| MR Win Rate (legitimate defences) | Should reflect ground truth | Balanced |
| Confidence Score Mean | Mean of auto-resolved scores | ≥ 72 |

---

## 5. Audit & Explainability Requirements

Per NFR-13 and FR-27:

- Every model decision must store: model version, all factor weights, confidence score, evidence IDs used.
- Decisions must be **100% reproducible** from the stored audit log.
- Admin override must always be available (no decision is irreversible by design).

### Audit Log Schema

```json
{
  "audit_id": "AUD-20260901-001",
  "case_id": "CAS-20260901-001",
  "model_version": "fair_weighing_v0.1",
  "timestamp": "2026-09-01T10:30:00Z",
  "actor": "SYSTEM",
  "confidence_score": 82,
  "recommended_resolution": "CARD_MEMBER_FAVOUR",
  "factor_weights_used": { "EV-03": 0.35, "EV-01": 0.20 },
  "evidence_quality_scores": { "EV-03": 0.0, "EV-01": 0.95 },
  "bias_exclusions_applied": ["dispute_history", "merchant_size"],
  "llm_model_used": "gemini-2.0-flash",
  "prompt_template_version": "v1.0"
}
```

---

## 6. Review & Update Schedule

| Milestone | Action |
|---|---|
| Phase 3 (Sep 22–28) | Run calibration against 200 labelled disputes; check FPR per category |
| Phase 6 (Nov 3–6) | Final fairness & accuracy testing; confirm FPR ≤ 2% |
| Post-submission | Quarterly bias review if system is extended to production |

---

## 7. Version History

| Version | Date | Author | Notes |
|---|---|---|---|
| v0.1 | Aug 15, 2026 | Akshay Purohit | Initial bias mitigation guidelines |
