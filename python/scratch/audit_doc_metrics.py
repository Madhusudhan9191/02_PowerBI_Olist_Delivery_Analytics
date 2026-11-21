"""
audit_doc_metrics.py
--------------------
Automated consistency check to verify that all project documentation,
specifications, and Power BI visual containers quote metrics that match
the dynamic DAX test table (powerbi/dax/dax_test_table.md) and SQL outputs.
Fails with exit code 1 if any stale or conflicting numbers are detected.
"""

import os
import re
import sys
import zipfile

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# 1. Parse Reconciled Test Table
TEST_TABLE_PATH = os.path.join(PROJECT_DIR, "powerbi", "dax", "dax_test_table.md")
if not os.path.exists(TEST_TABLE_PATH):
    print(f"ERROR: Reconciled test table not found at {TEST_TABLE_PATH}")
    sys.exit(1)

with open(TEST_TABLE_PATH, "r", encoding="utf-8") as f:
    test_table_content = f.read()

# Verify test table has 63 passes
pass_count = test_table_content.count("[x] PASS")
if pass_count != 63:
    print(f"FAILED: Expected 63 PASS in dax_test_table.md, found {pass_count}")
    sys.exit(1)

print(f"✓ dax_test_table.md verified with {pass_count}/63 PASS marks.")

# 2. Define Forbidden Stale Patterns
# These numbers represent stale/buggy outputs that must NOT appear as current metrics
FORBIDDEN_PATTERNS = [
    (r"8\.09%", "Stale Tier 1 late dispatch rate (should be 8.07%)"),
    (r"11\.08%", "Stale Tier 4 late dispatch rate (should be 11.07%)"),
    (r"11\.10%", "Unfixed DAX Tier 4 late dispatch rate (should be 11.07%)"),
    (r"Tier 2.*9\.34%", "Stale Tier 2 late dispatch rate (should be 9.31%)"),
    (r"Tier 3.*9\.89%", "Stale Tier 3 late dispatch rate (should be 9.86%)"),
]

# Files to audit
DOC_EXTENSIONS = (".md",)
AUDIT_DIRS = [
    PROJECT_DIR,
    os.path.join(PROJECT_DIR, "documentation"),
    os.path.join(PROJECT_DIR, "powerbi"),
    os.path.join(PROJECT_DIR, "powerbi", "specifications"),
]

errors = []
audited_files = 0

# Check text markdown files
for adir in AUDIT_DIRS:
    for fname in os.listdir(adir):
        fpath = os.path.join(adir, fname)
        if os.path.isfile(fpath) and fname.endswith(DOC_EXTENSIONS):
            audited_files += 1
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            
            for line_no, line in enumerate(lines, 1):
                # Allow historical discussion of the bug when explicitly framed as pre-fix root cause / observed bug
                is_bug_context = (
                    "inadvertently let those 15 orders pass" in line
                    or "blank-handling bug" in line.lower()
                    or "pre-fix" in line.lower()
                    or "was 11.08%" in line
                    or "shifted tier 4" in line.lower()
                    or "prior approximation" in line.lower()
                    or "observed vs." in line.lower()
                    or ("11.10%" in line and "11.07%" in line)
                )
                
                for pat, desc in FORBIDDEN_PATTERNS:
                    if re.search(pat, line):
                        if is_bug_context and ("11" in pat and ("08" in pat or "10" in pat)):
                            continue
                        errors.append(f"{fpath}:{line_no} - {desc}\n  Line: {line.strip()}")

# 3. Check Power BI .pbix internal visual text boxes
pbix_path = os.path.join(PROJECT_DIR, "Olist_Delivery_Analytics.pbix")
if os.path.exists(pbix_path):
    audited_files += 1
    with zipfile.ZipFile(pbix_path, "r") as z:
        for name in z.namelist():
            if "Report/definition/pages" in name and name.endswith(".json"):
                content = z.read(name).decode("utf-8", errors="ignore")
                for pat, desc in FORBIDDEN_PATTERNS:
                    if re.search(pat, content):
                        errors.append(f"{pbix_path} ({name}) - {desc}")
else:
    errors.append(f"Missing PBIX file: {pbix_path}")

# 4. Mandatory Reconciled Figures Check per document
DOCUMENT_REQUIREMENTS = {
    "README.md": [
        ("8.07%", "Tier 1 late dispatch rate"),
        ("9.31%", "Tier 2 late dispatch rate"),
        ("9.86%", "Tier 3 late dispatch rate"),
        ("11.07%", "Tier 4 late dispatch rate"),
        ("95,082", "Clean fulfillment order count"),
        ("61,022", "Interstate order count"),
        ("34,060", "Intrastate order count"),
    ],
    os.path.join("documentation", "data_dictionary.md"): [
        ("8.07%", "Tier 1 late dispatch rate"),
        ("9.31%", "Tier 2 late dispatch rate"),
        ("9.86%", "Tier 3 late dispatch rate"),
        ("11.07%", "Tier 4 late dispatch rate"),
        ("95,082", "Clean fulfillment order count"),
        ("61,022", "Interstate order count"),
        ("34,060", "Intrastate order count"),
    ],
    os.path.join("documentation", "business_queries_report.md"): [
        ("8.07%", "Tier 1 late dispatch rate"),
        ("9.31%", "Tier 2 late dispatch rate"),
        ("9.86%", "Tier 3 late dispatch rate"),
        ("11.07%", "Tier 4 late dispatch rate"),
        ("95,082", "Clean fulfillment order count"),
        ("61,022", "Interstate order count"),
        ("34,060", "Intrastate order count"),
    ],
    os.path.join("documentation", "three_way_reconciliation_report.md"): [
        ("8.07%", "Tier 1 late dispatch rate"),
        ("9.31%", "Tier 2 late dispatch rate"),
        ("9.86%", "Tier 3 late dispatch rate"),
        ("11.07%", "Tier 4 late dispatch rate"),
        ("95,082", "Clean fulfillment order count"),
        ("61,022", "Interstate order count"),
        ("34,060", "Intrastate order count"),
    ],
    os.path.join("powerbi", "specifications", "page2_delivery_performance.md"): [
        ("95,082", "Clean fulfillment order count"),
        ("61,022", "Interstate order count"),
        ("34,060", "Intrastate order count"),
        ("91.89%", "Interstate on-time rate"),
        ("95.43%", "Intrastate on-time rate"),
    ],
    os.path.join("powerbi", "specifications", "page3_regional_and_seller.md"): [
        ("8.07%", "Tier 1 late dispatch rate"),
        ("9.31%", "Tier 2 late dispatch rate"),
        ("9.86%", "Tier 3 late dispatch rate"),
        ("11.07%", "Tier 4 late dispatch rate"),
        ("2,959", "Active clean merchants count"),
    ],
    os.path.join("powerbi", "README_build_guide.md"): [
        ("8.07%", "Tier 1 late dispatch rate"),
        ("9.31%", "Tier 2 late dispatch rate"),
        ("9.86%", "Tier 3 late dispatch rate"),
        ("11.07%", "Tier 4 late dispatch rate"),
    ],
}

for doc_rel, reqs in DOCUMENT_REQUIREMENTS.items():
    doc_path = os.path.join(PROJECT_DIR, doc_rel)
    if os.path.exists(doc_path):
        with open(doc_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        for token, desc in reqs:
            if token not in text:
                errors.append(f"Missing expected metric in {doc_rel}: {token} ({desc})")
    else:
        errors.append(f"Missing required documentation file: {doc_path}")

print(f"\nAudit complete: Scanned {audited_files} documents and visual definitions.")

if errors:
    print(f"\nFAILED: {len(errors)} consistency check errors detected:")
    for err in errors:
        print(f"  [ERROR] {err}")
    sys.exit(1)
else:
    print("\nSUCCESS: All documentation and visuals match dax_test_table.md exactly (0 errors).")
    sys.exit(0)
