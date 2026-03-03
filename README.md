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
