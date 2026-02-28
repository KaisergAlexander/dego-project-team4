"""
[DEPRECATED] data_quality_assessment.py
The primary deliverable is now: notebooks/data_quality_assessment.ipynb
This script is kept for reference only and should not be used.
----------------------------------------------------------------------
data_quality_assessment.py
Data Engineer – DEGO Project Team 4

Pipeline (following session3_mongodb_governance_audit.ipynb style):
  1. load_data               – read raw JSON from Data/
  2. profile_data            – basic counts and field overview
  3. check_missing_values    – completeness: absent / empty fields
  4. check_duplicates        – uniqueness: duplicate SSNs
  5. validate_types_and_ranges – consistency + validity checks
  6. clean_data              – standardize gender, normalize dates
  7. save_outputs            – cleaned JSON → data/processed/, report → reports/

Run from project root (dego-project-team4/dego-project-team4/):
  python src/data_quality_assessment.py
  python -m src.data_quality_assessment
"""

import json
import os
import re
import sys
from collections import Counter
from datetime import datetime

import pandas as pd

# Ensure UTF-8 output on Windows (console defaults to CP1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------

# Relative to project root (resolved at runtime via __file__)
RAW_DATA_RELPATH = os.path.join("Data", "raw_credit_applications.json")
PROCESSED_RELDIR = os.path.join("data", "processed")
REPORTS_RELDIR   = "reports"

# Gender normalisation map (fixes "M" → "Male", "F" → "Female", etc.)
GENDER_MAP = {
    "male":   "Male",
    "m":      "Male",
    "female": "Female",
    "f":      "Female",
}


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _project_root() -> str:
    """Return the absolute path to the project root (parent of src/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _abs(relpath: str) -> str:
    """Resolve a project-root-relative path to an absolute path."""
    return os.path.join(_project_root(), relpath)


def _print_and_collect(line: str, buf: list) -> None:
    """Print a line and append it to the report buffer."""
    print(line)
    buf.append(line)


# ---------------------------------------------------------------------------
# 1. LOAD DATA
# ---------------------------------------------------------------------------

def load_data(path: str):
    """
    Load raw JSON file and return (records_list, flat_DataFrame).

    pd.json_normalize flattens the nested document structure so we can
    inspect column-level coverage – same approach used in the Data Lake
    exercise (DataLakeExercisev2.ipynb).
    """
    with open(path, "r", encoding="utf-8") as f:
        records = json.load(f)

    df = pd.json_normalize(records)
    print(f"[LOAD] {len(records)} records loaded from '{path}'")
    return records, df


# ---------------------------------------------------------------------------
# 2. PROFILE DATA
# ---------------------------------------------------------------------------

def profile_data(records: list, df: pd.DataFrame) -> list:
    """Basic dataset overview: total records, loan outcome split, columns."""
    buf = []

    approved = sum(
        1 for r in records
        if r.get("decision", {}).get("loan_approved") is True
    )

    lines = [
        "=" * 60,
        "DATA QUALITY REPORT – NovaCred Credit Applications",
        f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
        "",
        "── 0. DATASET PROFILE ──────────────────────────────────",
        f"  Total records   : {len(records)}",
        f"  Approved loans  : {approved}",
        f"  Rejected loans  : {len(records) - approved}",
        f"  Flattened cols  : {df.shape[1]}",
        "",
    ]

    for line in lines:
        _print_and_collect(line, buf)

    return buf


# ---------------------------------------------------------------------------
# 3. CHECK MISSING VALUES  (Completeness)
# ---------------------------------------------------------------------------

def check_missing_values(records: list) -> list:
    """
    Flag absent or empty fields across all records.

    Pattern mirrors session3 governance check:
      collection.count_documents({field: {"$exists": False}})
    Here we replicate that logic in Python over the loaded list.
    """
    buf = []
    total = len(records)

    _print_and_collect(
        "── 1. COMPLETENESS (Missing / Empty Fields) ─────────────", buf
    )

    # Fields that every record is expected to have
    required = [
        ("applicant_info.full_name",
         lambda r: bool(r.get("applicant_info", {}).get("full_name", "").strip())),
        ("applicant_info.ssn",
         lambda r: bool(r.get("applicant_info", {}).get("ssn", "").strip())),
        ("applicant_info.gender",
         lambda r: bool(r.get("applicant_info", {}).get("gender", "").strip())),
        ("applicant_info.date_of_birth",
         lambda r: bool(r.get("applicant_info", {}).get("date_of_birth", "").strip())),
        ("applicant_info.email",
         lambda r: bool(r.get("applicant_info", {}).get("email", "").strip())),
        ("financials.annual_income",
         lambda r: "annual_income" in r.get("financials", {})),
        ("financials.debt_to_income",
         lambda r: "debt_to_income" in r.get("financials", {})),
        ("decision.loan_approved",
         lambda r: "loan_approved" in r.get("decision", {})),
    ]

    for label, check_fn in required:
        missing = sum(1 for r in records if not check_fn(r))
        pct    = missing / total * 100
        status = "✅" if missing == 0 else "🔴"
        _print_and_collect(
            f"  {status} {label:<42} missing: {missing:>3}  ({pct:.1f}%)", buf
        )

    # Optional / governance fields (GDPR-style completeness, session3 pattern)
    _print_and_collect("", buf)
    _print_and_collect("  Optional / governance fields:", buf)
    for field in ("processing_timestamp", "loan_purpose"):
        missing = sum(1 for r in records if field not in r)
        pct    = missing / total * 100
        _print_and_collect(
            f"     {field:<42} missing: {missing:>3}  ({pct:.1f}%)", buf
        )

    _print_and_collect("", buf)
    return buf


# ---------------------------------------------------------------------------
# 4. CHECK DUPLICATES  (Uniqueness)
# ---------------------------------------------------------------------------

def check_duplicates(records: list) -> list:
    """
    Detect duplicate SSNs (and duplicate application IDs).

    Mirrors session3 pipeline:
      $group by SSN → $match count > 1 → $sort
    """
    buf = []
    _print_and_collect(
        "── 2. UNIQUENESS (Duplicate SSNs) ──────────────────────", buf
    )

    ssn_counter = Counter(
        r.get("applicant_info", {}).get("ssn", "") for r in records
    )
    duplicates = {
        ssn: cnt
        for ssn, cnt in ssn_counter.items()
        if cnt > 1 and ssn
    }

    if duplicates:
        _print_and_collect(
            f"  🔴 {len(duplicates)} duplicate SSN(s) detected:", buf
        )
        for ssn, cnt in sorted(duplicates.items(), key=lambda x: -x[1]):
            names = [
                r["applicant_info"]["full_name"]
                for r in records
                if r.get("applicant_info", {}).get("ssn") == ssn
            ]
            _print_and_collect(f"     SSN {ssn}: {cnt} records – {names}", buf)
    else:
        _print_and_collect("  ✅ No duplicate SSNs found", buf)

    # Check application ID uniqueness
    id_dups = sum(
        1 for cnt in Counter(r.get("_id") for r in records).values()
        if cnt > 1
    )
    _print_and_collect(f"  Duplicate application IDs: {id_dups}", buf)

    _print_and_collect("", buf)
    return buf


# ---------------------------------------------------------------------------
# 5. VALIDATE TYPES AND RANGES  (Consistency + Validity)
# ---------------------------------------------------------------------------

def validate_types_and_ranges(records: list) -> list:
    """
    Check encoding consistency and numeric validity.

    Follows the two-part session3 audit:
      • Consistency – categorical fields with unexpected encodings
      • Validity    – numeric range rule violations
    """
    buf = []
    iso_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    # ── Consistency: gender encoding ──────────────────────────────────────
    _print_and_collect(
        "── 3. CONSISTENCY (Gender Encoding) ────────────────────", buf
    )
    gender_counts = Counter(
        r.get("applicant_info", {}).get("gender", "") for r in records
    )
    _print_and_collect(
        f"  Distinct gender values found: {len(gender_counts)}  (expected: 2)", buf
    )
    for val, cnt in sorted(gender_counts.items(), key=lambda x: -x[1]):
        flag = "" if val in ("Male", "Female") else "  ← non-standard"
        _print_and_collect(f"     '{val}': {cnt}{flag}", buf)

    _print_and_collect("", buf)

    # ── Consistency: date_of_birth formats ───────────────────────────────
    _print_and_collect(
        "── 4. CONSISTENCY (Date-of-Birth Formats) ──────────────", buf
    )
    fmt_counts: Counter = Counter()
    for r in records:
        dob = r.get("applicant_info", {}).get("date_of_birth", "")
        if iso_re.match(dob):
            fmt_counts["YYYY-MM-DD (ISO ✅)"] += 1
        elif re.match(r"^\d{4}/\d{2}/\d{2}$", dob):
            fmt_counts["YYYY/MM/DD"] += 1
        elif re.match(r"^\d{2}/\d{2}/\d{4}$", dob):
            fmt_counts["DD/MM/YYYY or MM/DD/YYYY"] += 1
        elif dob == "":
            fmt_counts["empty"] += 1
        else:
            fmt_counts["other"] += 1

    non_iso = sum(cnt for fmt, cnt in fmt_counts.items() if "ISO" not in fmt)
    _print_and_collect(
        f"  Records with non-ISO date_of_birth: {non_iso}", buf
    )
    for fmt, cnt in sorted(fmt_counts.items(), key=lambda x: -x[1]):
        _print_and_collect(f"     {fmt}: {cnt}", buf)

    _print_and_collect("", buf)

    # ── Validity: numeric range rules (mirrors session3 validity_rules) ───
    _print_and_collect(
        "── 5. VALIDITY (Numeric Range Checks) ──────────────────", buf
    )

    def _num(record, *keys, default=0):
        """Safely extract a numeric value, returning default for missing/non-numeric."""
        val = record
        for k in keys:
            val = val.get(k, {}) if isinstance(val, dict) else {}
        try:
            return float(val) if val != {} else default
        except (TypeError, ValueError):
            return default

    validity_rules = [
        ("Negative annual_income",
         lambda r: _num(r, "financials", "annual_income") < 0),
        ("Zero annual_income",
         lambda r: _num(r, "financials", "annual_income", default=1) == 0),
        ("Debt-to-income ratio > 1  (suspicious)",
         lambda r: _num(r, "financials", "debt_to_income") > 1),
        ("Negative savings_balance",
         lambda r: _num(r, "financials", "savings_balance") < 0),
        ("Negative credit_history_months",
         lambda r: _num(r, "financials", "credit_history_months") < 0),
    ]

    for rule_name, check_fn in validity_rules:
        violations = sum(1 for r in records if check_fn(r))
        status     = "✅" if violations == 0 else "🔴"
        _print_and_collect(
            f"  {status} {rule_name:<44} violations: {violations}", buf
        )

    _print_and_collect("", buf)
    return buf


# ---------------------------------------------------------------------------
# 6. CLEAN DATA  (Silver-layer transformation)
# ---------------------------------------------------------------------------

def _parse_date(dob: str):
    """
    Try multiple date formats; return ISO 'YYYY-MM-DD' string or None.

    Formats encountered in this dataset:
      YYYY/MM/DD  →  1990/07/26
      DD/MM/YYYY  →  14/02/1982   (tried first; fails when day > 12 disambiguates)
      MM/DD/YYYY  →  03/20/1968   (US format – handles when day-first would fail)
    """
    for fmt in ("%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(dob, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def clean_data(records: list) -> tuple:
    """
    Apply basic cleaning (mirrors DataLakeExercisev2 silver-layer steps):
      • Standardise gender  → 'Male' / 'Female' / 'Unknown'
      • Normalise date_of_birth → ISO 8601 (YYYY-MM-DD) where possible

    Returns (cleaned_records, stats_dict).
    """
    iso_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    stats  = {
        "gender_standardized": 0,
        "gender_unknown":      0,
        "dob_normalized":      0,
        "dob_unparseable":     0,
    }
    cleaned = []

    for rec in records:
        # Deep-copy without external library (json round-trip)
        r = json.loads(json.dumps(rec))

        # ── Gender standardisation ────────────────────────────────────────
        raw    = r.get("applicant_info", {}).get("gender", "")
        normed = GENDER_MAP.get(raw.strip().lower(), "")
        if normed:
            if raw != normed:
                r["applicant_info"]["gender"] = normed
                stats["gender_standardized"] += 1
        else:
            r["applicant_info"]["gender"] = "Unknown"
            stats["gender_unknown"] += 1

        # ── Date-of-birth normalisation ───────────────────────────────────
        dob = r.get("applicant_info", {}).get("date_of_birth", "")
        if dob and not iso_re.match(dob):
            parsed = _parse_date(dob)
            if parsed:
                r["applicant_info"]["date_of_birth"] = parsed
                stats["dob_normalized"] += 1
            else:
                r["applicant_info"]["date_of_birth"] = None
                stats["dob_unparseable"] += 1

        cleaned.append(r)

    return cleaned, stats


# ---------------------------------------------------------------------------
# 7. SAVE OUTPUTS
# ---------------------------------------------------------------------------

def save_outputs(
    cleaned_records: list,
    report_lines:    list,
    stats:           dict,
    processed_dir:   str,
    reports_dir:     str,
) -> None:
    """
    Write cleaned JSON and text report to disk; print cleaning summary.
    Creates output directories if they do not exist.
    """
    cleaned_file = os.path.join(processed_dir, "cleaned_credit_applications.json")
    report_file  = os.path.join(reports_dir,   "data_quality_report.txt")

    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(reports_dir,   exist_ok=True)

    # Save cleaned JSON
    with open(cleaned_file, "w", encoding="utf-8") as f:
        json.dump(cleaned_records, f, indent=2, ensure_ascii=False)

    # Append cleaning summary to report
    cleaning_section = [
        "── 6. CLEANING SUMMARY ─────────────────────────────────",
        f"  Gender values standardised (M/F → Male/Female) : {stats['gender_standardized']}",
        f"  Gender set to 'Unknown' (empty / unrecognised)  : {stats['gender_unknown']}",
        f"  Date-of-birth normalised to ISO 8601            : {stats['dob_normalized']}",
        f"  Date-of-birth unparseable (set to null)         : {stats['dob_unparseable']}",
        "",
        "=" * 60,
        "END OF REPORT",
        "=" * 60,
    ]
    report_lines.extend(cleaning_section)

    # Save report
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    # Console output
    print("\n".join(cleaning_section))
    print(f"\n[SAVE] Cleaned data   → {cleaned_file}  ({len(cleaned_records)} records)")
    print(f"[SAVE] Quality report → {report_file}")


# ---------------------------------------------------------------------------
# PIPELINE ENTRY POINT
# ---------------------------------------------------------------------------

def run_pipeline() -> None:
    """Execute the full data quality assessment pipeline."""
    root = _project_root()

    raw_path      = os.path.join(root, RAW_DATA_RELPATH)
    processed_dir = os.path.join(root, PROCESSED_RELDIR)
    reports_dir   = os.path.join(root, REPORTS_RELDIR)

    print("\n" + "=" * 60)
    print("DATA QUALITY ASSESSMENT PIPELINE – NovaCred")
    print("=" * 60)

    # 1. Load
    records, df = load_data(raw_path)

    # 2–5. Quality checks (accumulate report lines)
    report = []
    report.extend(profile_data(records, df))
    report.extend(check_missing_values(records))
    report.extend(check_duplicates(records))
    report.extend(validate_types_and_ranges(records))

    # 6. Clean
    cleaned_records, stats = clean_data(records)

    # 7. Save
    save_outputs(cleaned_records, report, stats, processed_dir, reports_dir)


if __name__ == "__main__":
    run_pipeline()
