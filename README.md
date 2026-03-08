# NovaCred Credit Application Governance Analysis

**Course:** Data Ecosystems and Governance in Organizations (DEGO 2606)  
**Institution:** Nova School of Business and Economics — MSc Business Analytics  
**Team:** Group 4 · Data Governance Task Force

---

## Executive Summary

A governance audit of 502 raw credit applications revealed three interconnected crises:

**Data Quality:** 87.6% of records have no audit timestamp — a direct GDPR Art. 5(2) violation. 3 approved loans have zero income on record. Duplicate SSNs across different people signal fraud risk. A 5-step cleaning pipeline reduced the dataset to 500 usable records.

**Bias & Fairness:** Female applicants are approved at 50.6% vs. 66.0% for males (DI = 0.767, below the 0.80 threshold). After controlling for all financial variables, gender remains a highly significant predictor of approval (OR = 2.01, p = 0.0003) — male applicants with identical profiles are **twice as likely to be approved**. Young female applicants face the worst outcome at 31.2% approval (DI = 0.591).

**Privacy & GDPR:** 7 PII fields identified, SSNs stored in plaintext. GDPR compliance score: 2/24 (8%). 5 of 6 required governance fields entirely absent. Credit scoring is classified as high-risk under EU AI Act Annex III — full compliance obligations apply.

**Immediate actions required:** legal review of the gender disparity, SSN pseudonymisation, and enforcement of the processing timestamp before continued operation is justifiable.

---

## Video Presentation
**Watch the presentation video:**  
[Click here to watch](presentation/DEGO_project_team4_video.mp4)

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

---

## Privacy & Governance Analysis (Governance Officer)

**Notebook:** `notebooks/03_privacy_demo.ipynb`  
**Dataset:** `Data/cleaned_credit_applications.json` — 502 records  
**Regulatory Frameworks:** GDPR (2016/679) · EU AI Act (2024/1689)

The governance audit assessed NovaCred's data processing practices against GDPR 
requirements and EU AI Act obligations. Credit scoring is classified as **high-risk 
under EU AI Act Annex III**, triggering a full set of compliance obligations that 
NovaCred currently does not meet.

### PII & Privacy Risk

All 7 PII fields (SSN, full name, email, IP address, date of birth, zip code, gender) 
are present in near every record (≥99% coverage). SSNs are stored in plaintext — 
a critical exposure. Three sensitive spending categories (Alcohol, Gambling, Adult 
Entertainment) are collected across 23 records with no documented necessity under 
GDPR Art. 5(1)(c). Keyed HMAC-SHA256 pseudonymization was demonstrated on the SSN 
field and verified for determinism, distinctness, and zero collisions.

### Governance Gaps

Of 6 required governance metadata fields, only `processing_timestamp` exists in the 
dataset — and even that is incomplete (present on 12.4% of records only). The 
remaining 5 are entirely absent: consent tracking, retention policy, data source, 
human review flag, and decision explanation. The overall GDPR compliance profile 
scores **2 out of 24** across 8 principles (~8%).

### Recommendations

Immediate priorities are establishing a lawful basis (`consent_timestamp`), 
pseudonymizing SSNs, and adding a human review workflow for automated rejections. 
A formal DPIA is required before the system can be considered lawfully operated 
under GDPR Art. 35.

## Team & Individual Contributions

| Role | Name | Primary Deliverable |
|---|---|---|
| **Data Engineer** | Alexander Kaisergruber | Data loading, cleaning pipeline, deduplication — `01_data_quality_assessment.ipynb` |
| **Data Scientist** | Ashwin Rajesh | Bias analysis, fairness metrics, logistic regression — `02_bias_analysis.ipynb` |
| **Governance Officer** | Miguel Alexandre Neves Silva Sardo | PII mapping, pseudonymisation demo, GDPR/AI Act analysis — `03_privacy_demo.ipynb` |
| **Product Lead** | Fernanda Solms | Presentation, coordination, README documentation |

*Individual commit contributions are visible in the Git history.*