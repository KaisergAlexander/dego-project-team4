# MongoDB Governance Queries - Quick Reference
## Session 3: Data & AI Governance

Copy these directly into MongoDB Compass → Aggregations tab

---

## 1. Find Duplicates (Uniqueness)

```javascript
[
  { "$group": { "_id": "$applicant_info.ssn", "count": { "$sum": 1 }, "names": { "$push": "$applicant_info.full_name" } } },
  { "$match": { "count": { "$gt": 1 } } },
  { "$sort": { "count": -1 } }
]
```

**Expected:** Empty result = no duplicates ✅

---

## 2. Check Consistency (Gender)

```javascript
[
  { "$group": { "_id": "$applicant_info.gender", "count": { "$sum": 1 } } },
  { "$sort": { "count": -1 } }
]
```

**Expected:** 2 values (Male, Female)  
**Problem:** 4 values (Male, M, Female, F) = inconsistent encoding 🔴

---

## 3. Find Missing Consent (Completeness)

```javascript
[
  { "$match": { "consent_timestamp": { "$exists": false } } },
  { "$count": "missing_consent" }
]
```

**Expected:** 0 missing  
**Problem:** Any count > 0 = GDPR violation 🔴

---

## 4. Find Invalid Values (Validity)

```javascript
[
  { "$match": { "financials.annual_income": { "$lt": 0 } } },
  { "$count": "negative_income" }
]
```

**Expected:** 0 negative incomes  
**Problem:** Any negative values = invalid data 🔴

---

## 5. Detect Bias (Fairness)

```javascript
[
  { "$group": { "_id": "$applicant_info.gender", "total": { "$sum": 1 }, "approved": { "$sum": { "$cond": ["$decision.loan_approved", 1, 0] } } } },
  { "$addFields": { "approval_rate": { "$divide": ["$approved", "$total"] } } },
  { "$sort": { "approval_rate": -1 } }
]
```

**80% Rule:** If lowest rate < 80% of highest rate → investigate discrimination 🔴

---

## Quick Summary

| Query | Checks | GDPR/AI Act |
|-------|--------|-------------|
| Group by SSN | Duplicates | Data Quality |
| Group by gender values | Consistency | Data Quality |
| Match exists: false | Missing fields | GDPR Art. 5, 6 |
| Match < 0 | Invalid values | Data Quality |
| Group + approval rate | Bias | AI Act High Risk |

---

## Project Task

Use these queries on the credit dataset → Document findings → Map to regulations → Propose fixes
