# Data-Ecosystems — NovaCred Credit Application Governance Analysis

Group assignment — Data Ecosystems and Governance in Organizations (DEGO 2606)
Nova School of Business and Economics — MSc Business Analytics

---

## Repository Structure

```
Data/
  raw_credit_applications.json     Raw dataset — never modified (Bronze layer)
data/
  processed/
    cleaned_credit_applications.json  Cleaned dataset for team use (Silver layer)
notebooks/
  data_quality_assessment.ipynb    Data Engineer primary deliverable
Assignment_information/            Lecture code and project brief
src/
  data_quality_assessment.py       (deprecated — superseded by the notebook)
```

## Data Layers

| Layer | File | Description |
|---|---|---|
| **Raw (Bronze)** | `Data/raw_credit_applications.json` | Original dataset — never modified |
| **Cleaned (Silver)** | `data/processed/cleaned_credit_applications.json` | Gender standardised, dates normalised to ISO 8601 — for team consumption |

**For teammates:** load the cleaned dataset at the start of your notebook:
```python
import json
with open("data/processed/cleaned_credit_applications.json", encoding="utf-8") as f:
    records = json.load(f)
```

---

## Data Quality Assessment (Data Engineer)

**Notebook:** `notebooks/data_quality_assessment.ipynb`
**Dataset:** `Data/raw_credit_applications.json` — 502 credit applications, 21 fields (nested JSON)

### Dataset Overview

| Metric | Value |
|---|---|
| Total records | 502 |
| Approved loans | 292 (58.2%) |
| Rejected loans | 210 (41.8%) |
| Flattened columns | 21 |

---

### Quality Findings

#### 2.1 Completeness — Missing and Empty Fields

| Field | Missing | % |
|---|---|---|
| `applicant_info.full_name` | 0 | 0.0% |
| `applicant_info.ssn` | 5 | 1.0% |
| `applicant_info.gender` | 3 | 0.6% |
| `applicant_info.date_of_birth` | 5 | 1.0% |
| `applicant_info.email` | 7 | 1.4% |
| `financials.annual_income` | 5 | 1.0% |
| `financials.debt_to_income` | 0 | 0.0% |
| `decision.loan_approved` | 0 | 0.0% |
| `processing_timestamp` *(governance)* | 440 | **87.6%** |
| `loan_purpose` *(governance)* | 452 | **90.0%** |

> The near-total absence of `processing_timestamp` is a significant GDPR audit-trail gap.

---

#### 2.2 Uniqueness — Duplicate Records

**Duplicate SSN groups: 3** (6 records involved)

| SSN | Records | Names |
|---|---|---|
| 937-72-8731 | 2 | Sandra Smith, Samuel Hill |
| 780-24-9300 | 2 | Susan Martinez, Gary Wilson |
| 652-70-5530 | 2 | Joseph Lopez, Joseph Lopez |

Two SSN groups involve **different people sharing one SSN** — a potential fraud or data-entry error.

**Duplicate application IDs: 2 groups** (`app_042` × 2, `app_001` × 2)

---

#### 2.3 Consistency — Encoding and Format Issues

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

#### 2.4 Validity — Type and Range Issues

- **Schema inconsistency:** 5 records use `annual_salary` instead of `annual_income` — two field names for the same concept.
- **Range violations:**

| Rule | Violations |
|---|---|
| Zero `annual_income` | 1 |
| Negative `savings_balance` | 1 |
| Negative `credit_history_months` | 2 |
| `debt_to_income` > 1 | 1 |

---

#### 2.5 Accuracy — Age Sanity Check

Age was derived from the 340 ISO-format `date_of_birth` values (the only ones parseable without cleaning). All derived ages fall within the plausible 18–100 range.

| Metric | Value |
|---|---|
| ISO dates checked | 340 |
| Derived age range | 23 – 67 years |
| Implausible ages (< 18 or > 100) | 0 |

> Full accuracy verification requires an external ground-truth source (e.g. credit bureau data). Internal consistency checks find no violations.

---

#### 2.6 Timeliness — Processing Timestamp Coverage

| Metric | Value |
|---|---|
| Records with `processing_timestamp` | 62 (12.4%) |
| Records missing `processing_timestamp` | 440 (87.6%) |
| Earliest timestamp present | 2024-01-15 |
| Latest timestamp present | 2027-01-20 |

> With 87.6% of timestamps absent, dataset recency cannot be meaningfully assessed. This also constitutes a GDPR audit-trail gap.

---

### Cleaning Applied

Cleaning runs in-memory inside the notebook. The final cleaned dataset is also written to `data/processed/cleaned_credit_applications.json` for team use (Section 6 of the notebook).

| Step | Action | Records affected |
|---|---|---|
| Gender standardisation | `M` → `Male`, `F` → `Female` | 111 corrected |
| Gender fallback | Empty / unrecognised → `Unknown` | 3 set |
| Date normalisation | Non-ISO formats parsed to `YYYY-MM-DD` | 157 corrected |
| Date unparseable | Left as null (empty source) | 0 |

### Before vs. After

| Metric | Before | After |
|---|---|---|
| Gender distinct values | 5 | 3 |
| Non-standard gender records | 114 | 3 |
| Non-ISO date-of-birth records | 162 | 5 |

After cleaning: `Female` 251 · `Male` 248 · `Unknown` 3
After cleaning: 497 ISO dates · 5 null/empty (no source data to infer from)
