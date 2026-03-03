# Data Quality Assessment — Detailed Findings

**Course:** Data Ecosystems and Governance in Organizations (DEGO 2606)
**Institution:** Nova School of Business and Economics — MSc Business Analytics
**Notebook:** `notebooks/01_data_quality_assessment.ipynb`
**Dataset:** `Data/raw_credit_applications.json`

---

## Dataset Overview

| Metric | Value |
|---|---|
| Total records | 502 |
| Approved loans | 292 (58.2%) |
| Rejected loans | 210 (41.8%) |
| Flattened columns | 21 |

---

## Pre-check: Empty String Normalisation

Before any quality checks, all whitespace-only strings were replaced with NaN.
`isna()` alone does not catch fields that are present but blank — these represent hidden gaps.

| Field | Blank strings (hidden gaps) |
|---|---|
| `applicant_info.gender` | ~2–3 |
| `applicant_info.date_of_birth` | ~4 |
| `applicant_info.email` | ~7 |
| `applicant_info.zip_code` | ~1 |

> Total hidden gaps not caught by standard null checks: ~14. Normalised to NaN before analysis.

---

## 2.1 Completeness — Missing and Empty Fields

| Field | Missing | % | Status |
|---|---|---|---|
| `applicant_info.full_name` | 0 | 0.0% | OK |
| `applicant_info.ssn` | 5 | 1.0% | ISSUE |
| `applicant_info.gender` | 3 | 0.6% | ISSUE |
| `applicant_info.date_of_birth` | 5 | 1.0% | ISSUE |
| `applicant_info.email` | 7 | 1.4% | ISSUE |
| `financials.annual_income` | 5 | 1.0% | ISSUE |
| `financials.debt_to_income` | 0 | 0.0% | OK |
| `decision.loan_approved` | 0 | 0.0% | OK |
| `processing_timestamp` *(governance)* | 440 | **87.6%** | CRITICAL |
| `loan_purpose` *(governance)* | 452 | **90.0%** | CRITICAL |

> The near-total absence of `processing_timestamp` is a significant GDPR audit-trail gap.

### 2.1b Decision Field Integrity (Conditional Completeness)

Each loan outcome implies specific field requirements:
- **Approved** → must have `approved_amount` + `interest_rate`, must not have `rejection_reason`
- **Rejected** → must have `rejection_reason`, must not have `approved_amount` or `interest_rate`

Violations of these rules indicate structural incoherence between the decision and its supporting data.
*(Run notebook to see exact violation counts.)*

---

## 2.2 Uniqueness — Duplicate Records

**Duplicate SSN groups: 3** (6 records involved)

| SSN | Records | Names | Risk |
|---|---|---|---|
| 937-72-8731 | 2 | Sandra Smith, Samuel Hill | Different people — potential fraud |
| 780-24-9300 | 2 | Susan Martinez, Gary Wilson | Different people — potential fraud |
| 652-70-5530 | 2 | Joseph Lopez, Joseph Lopez | Same name — likely duplicate entry |

Two SSN groups involve **different people sharing one SSN** — potential fraud or data-entry error.

**Duplicate application IDs: 2 groups** (`app_042` × 2, `app_001` × 2)

---

## 2.3 Consistency — Encoding and Format Issues

**Gender encoding — 5 distinct values (expected: 2)**

| Value | Count | Standard? |
|---|---|---|
| `Male` | 195 | Yes |
| `Female` | 193 | Yes |
| `F` | 58 | No |
| `M` | 53 | No |
| *(empty)* | 3 | No |

→ 114 records (22.7%) use non-standard gender encoding.

**Date-of-birth formats — 162 records with non-ISO format**

| Format | Count |
|---|---|
| `YYYY-MM-DD` (ISO) | 340 |
| `DD/MM/YYYY` or `MM/DD/YYYY` | 101 |
| `YYYY/MM/DD` | 56 |
| empty | 5 |

---

## 2.4 Validity — Type and Range Issues

**2.4a Schema inconsistency:** 5 records use `annual_salary` instead of `annual_income` — two field names for the same concept.

**Range violations:**

| Rule | Violations |
|---|---|
| Zero `annual_income` | 1 |
| Negative `savings_balance` | 1 |
| Negative `credit_history_months` | 2 |
| `debt_to_income` > 1 | 1 |

**2.4b Email format:** 1 record has a syntactically invalid email address (missing `@`). Present but unusable for communication or identity verification.

**2.4c Mixed Python types in `annual_income`:** The column contains a mix of `int`, `str`, and `float` values. Non-numeric string entries coerce silently to NaN and corrupt aggregations. *(Exact count from notebook run.)*

**2.4d Approved loans with zero or missing income — CRITICAL**
3 approved loans have zero or missing income. This is a **process control failure**: the algorithm approved applications without a key underwriting input. Post-hoc cleaning cannot substitute for this governance gap.

---

## 2.5 Accuracy — Age Sanity Check

| Metric | Value |
|---|---|
| ISO dates checked | 340 |
| Derived age range | 23 – 67 years |
| Implausible ages (< 18 or > 100) | 0 |

> Full accuracy verification requires an external ground-truth source (e.g. credit bureau data). Internal consistency checks find no violations.

---

## 2.6 Timeliness — Processing Timestamp Coverage

| Metric | Value |
|---|---|
| Records with `processing_timestamp` | 62 (12.4%) |
| Records missing `processing_timestamp` | 440 (87.6%) |
| Earliest timestamp present | 2024-01-15 |
| Latest timestamp present | 2027-01-20 |

> With 87.6% of timestamps absent, dataset recency cannot be meaningfully assessed. This constitutes a GDPR audit-trail gap (Art. 5(2) Accountability).

---

## Cleaning Applied (Steps 3.1 – 3.5)

| Step | Action | Records affected |
|---|---|---|
| 3.1 Gender standardisation | `M` → `Male`, `F` → `Female` | 111 corrected |
| 3.1 Gender fallback | Empty / unrecognised → `Unknown` | 3 set |
| 3.2 Date normalisation | Non-ISO formats parsed to `YYYY-MM-DD` | 157 corrected |
| 3.3 Impossible values → null | Negative `credit_history_months` + `savings_balance` | 3 nulled |
| 3.4 Invalid email → null | Email failing format check | 1 nulled |
| 3.5 Deduplication | Duplicate `_id` removed (keep highest field coverage) | 2 removed |

**Final record count: 500** (down from 502 raw records)

## Before vs. After

| Metric | Before | After |
|---|---|---|
| Total records | 502 | 500 |
| Gender distinct values | 5 | 3 |
| Non-standard gender records | 114 | 3 |
| Non-ISO date-of-birth records | 162 | 5 |
| Negative credit_history_months | 2 | 0 |
| Negative savings_balance | 1 | 0 |
| Invalid email format | 1 | 0 |
| Duplicate application IDs | 4 | 0 |

After cleaning: `Female` 251 · `Male` 248 · `Unknown` 3

---

## Consolidated Risk Summary

| Dimension | Finding | Records | Severity |
|---|---|---|---|
| Completeness | Missing `processing_timestamp` | 440 (87.6%) | Critical |
| Accuracy | Approved loans with zero/missing income | 3 | Critical |
| Timeliness | GDPR audit trail — timestamp absent | 440 (87.6%) | Critical |
| Completeness | Missing `loan_purpose` | 452 (90.0%) | High |
| Uniqueness | Duplicate SSN — different applicants | 2 groups | High |
| Uniqueness | Duplicate application IDs | 4 records | High |
| Completeness | Blank strings masking missingness | ~14 | Medium |
| Consistency | Non-standard gender encoding | 114 records | Medium |
| Consistency | Non-ISO date formats | 162 records | Medium |
| Consistency | Mixed types in `annual_income` | ~9 records | Medium |
| Validity | Schema split: income vs salary fields | 5 records | Medium |
| Validity | Negative `credit_history_months` | 2 records | Medium |
| Validity | `debt_to_income` > 1 | 1 record | Medium |
| Completeness | Missing SSN | 5 records | Medium |
| Validity | Negative `savings_balance` | 1 record | Low |
| Validity | Invalid email format | 1 record | Low |
| Completeness | Missing email | 7 records | Low |
| Accuracy | Implausible ages (< 18 or > 100) | 0 | — |

**Overall risk level: Moderate–High.** Dataset must not be used as sole basis for automated credit decisions until P1 controls are in place.
