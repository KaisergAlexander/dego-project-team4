# Data-Ecosystems — NovaCred Credit Application Governance Analysis

Group assignment — Data Ecosystems and Governance in Organizations (DEGO 2606)
Nova School of Business and Economics — MSc Business Analytics

---

## Repository Structure

```
Data/
  raw_credit_applications.json          Raw dataset — never modified (Bronze layer)
data/
  processed/
    cleaned_credit_applications.json    Cleaned dataset for team use (Silver layer)
notebooks/
  01_data_quality_assessment.ipynb      Data Engineer primary deliverable
  02_bias_analysis.ipynb                Data Scientist primary deliverable
Assignment_information/                 Lecture code and project brief
reports/
  findings.md                           Detailed data quality findings
  figures.md                            Key figures selected for the presentation
src/                                    Reusable utility code (optional)
```

## Data Layers

| Layer | File | Description |
|---|---|---|
| **Raw (Bronze)** | `Data/raw_credit_applications.json` | Original dataset — never modified |
| **Cleaned (Silver)** | `data/processed/cleaned_credit_applications.json` | Gender standardised, dates normalised, impossible values nulled, deduped (500 records) — for team consumption |

**For teammates:** load the cleaned dataset at the start of your notebook:
```python
import json
with open("data/processed/cleaned_credit_applications.json", encoding="utf-8") as f:
    records = json.load(f)
```

---

## Data Quality Assessment (Data Engineer)

**Notebook:** `notebooks/01_data_quality_assessment.ipynb`
**Dataset:** `Data/raw_credit_applications.json` — 502 credit applications, 21 fields (nested JSON)

**Full findings:** [`reports/findings.md`](reports/findings.md)
**Presentation figures:** [`reports/figures.md`](reports/figures.md)

### Key Findings Summary

| Dimension | Worst Issue | Records Affected | Severity |
|---|---|---|---|
| Completeness | Missing `processing_timestamp` — GDPR audit trail | 440 (87.6%) | Critical |
| Accuracy | Approved loans with zero or missing income | 3 | Critical |
| Completeness | Missing `loan_purpose` | 452 (90.0%) | High |
| Uniqueness | Duplicate SSN groups (2 involve different people) | 3 groups / 6 records | High |
| Uniqueness | Duplicate application IDs | 4 records | High |
| Completeness | Blank strings masking true missingness | ~14 records | Medium |
| Consistency | Non-standard gender encoding (`M`, `F`, empty) | 114 (22.7%) | Medium |
| Consistency | Non-ISO date-of-birth formats | 162 (32.3%) | Medium |
| Consistency | Mixed Python types in `annual_income` | ~9 records | Medium |
| Validity | Schema split: `annual_income` vs `annual_salary` | 5 records | Medium |
| Validity | Negative `credit_history_months` + `savings_balance` | 3 records | Medium |
| Accuracy | Implausible ages (< 18 or > 100) | 0 — no violations | — |

**Overall risk: Moderate–High.** See [`reports/findings.md`](reports/findings.md) for full detail.

### Cleaning Applied (in-memory, notebook Sections 3.1–3.5)

| Step | Action | Records Affected |
|---|---|---|
| 3.1 | Gender standardised (`M/F` → `Male/Female`) | 111 corrected |
| 3.1 | Gender set to `Unknown` (empty/unrecognised) | 3 set |
| 3.2 | Date-of-birth normalised to ISO 8601 | 157 corrected |
| 3.3 | Negative `credit_history_months` + `savings_balance` → null | 3 nulled |
| 3.4 | Invalid email format → null | 1 nulled |
| 3.5 | Duplicate application IDs deduplicated | 2 removed |

**Final record count: 500** (raw: 502)

---

## Bias & Fairness Analysis (Data Scientist)

**Notebook:** `notebooks/02_bias_analysis.ipynb`
**Dataset:** `data/processed/cleaned_credit_applications.json` — 500 records (Silver layer)
**Analysis type:** Audit of historical credit decision outcomes — not a trained ML model
**Protected attributes:** Gender · Age (derived from `date_of_birth`, reference date 2024-01-01)
**Regulatory framework:** Regulation (EU) 2016/679 (GDPR) · EU AI Act Annex III

**Full findings:** [`reports/findings.md`](reports/findings.md)
**Presentation figures:** [`reports/figures.md`](reports/figures.md)

### Overall Fairness Risk Classification: Elevated–High

### Key Findings Summary

| Domain | Finding | Evidence | Severity |
|---|---|---|---|
| Gender — Baseline | Female approval rate 50.6% vs. Male 66.0% | DI = 0.767 (below 0.80 threshold) · χ² p = 0.0007 | **High** |
| Gender — Conditional | Gender disparity persists after controlling for all financial risk factors | Logistic regression OR = 2.01 · p = 0.0003 | **Critical** |
| Intersectional — Female ×  <30 | Young female applicants approved at 31.2% vs. male peers at 52.7% | DI = 0.591 — well below 0.80 threshold | **High** |
| Intersectional — Female × 40–49 | Female applicants aged 40–49 also below threshold | DI = 0.780 | **High** |
| Age — Baseline | Applicants under 30 face lowest approval rate of any age group | DI = 0.601 vs. highest-rate group · χ² p < 0.001 | **Moderate** |
| Age — Conditional | Age not independently significant after financial controls | p(age) = 0.642 in logistic model | **Low** |
| Proxy — ZIP code | ZIP prefix near-perfectly correlated with gender | χ² p = 8×10⁻⁷² · Condition 2 not confirmed (p = 0.842) | **Moderate** |
| Proxy — Spending data | Sensitive spending categories (Gambling, Alcohol, Adult Entertainment) collected without demonstrated credit-decision necessity | GDPR Art. 5(1)(c) data minimisation · Art. 9 scrutiny | **Moderate** |
| Pricing — Gender | No significant interest rate difference by gender among approved applicants | Mann–Whitney p = 0.326 · OLS p = 0.298 | **Low** |

### Critical Finding — Conditional Gender Discrimination

The most serious finding is that **gender remains a highly significant predictor of approval after controlling for income, debt-to-income ratio, credit history, and savings** (OR = 2.01, p = 0.0003). Male applicants with an identical financial profile are twice as likely to be approved as female applicants. This cannot be explained by legitimate risk-based reasoning and constitutes a conditional discrimination finding. Under Regulation (EU) 2016/679 (GDPR), Art. 22, credit applicants have the right not to be subject to solely automated decisions with significant effects — this finding directly engages that obligation.

### Governance Actions Required

| Priority | Action | Basis |
|---|---|---|
| **Immediate** | Legal review of gender-based approval gap — conditional disparity cannot be explained by financial risk | GDPR Art. 22 · EU AI Act Annex III |
| **Immediate** | Audit underwriting criteria for any gender-correlated decision rules | Conditional logistic regression finding |
| **Short-term** | Exclude ZIP code from all automated decision inputs — near-perfect gender proxy | GDPR Art. 5(1)(c) data minimisation |
| **Short-term** | Deploy disaggregated fairness monitoring dashboards by gender × age sub-group | Intersectional DI violations |
| **Short-term** | Implement fairness constraints in any future automated underwriting model | EU AI Act Annex III |
| **Short-term** | DPO review of sensitive spending categories — document lawful basis or remove | GDPR Art. 5(1)(c) · Art. 9 |
| **Ongoing** | Annual bias audits covering baseline, conditional, pricing, and intersectional dimensions | EU AI Act Art. 9 |
| **Ongoing** | Re-test spending proxy when per-category sample size reaches n ≥ 30 | Inconclusive proxy test |

