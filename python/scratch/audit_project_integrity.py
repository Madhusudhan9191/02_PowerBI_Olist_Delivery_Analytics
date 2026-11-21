import os
import re
import glob
import pandas as pd

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

print("=== 3. CHECKING IMAGE PATHS IN README AND DOCS ===")
for root, dirs, files in os.walk(base_dir):
    for f in files:
        if f.endswith('.md'):
            fp = os.path.join(root, f)
            with open(fp, 'r', encoding='utf-8', errors='ignore') as md_file:
                content = md_file.read()
                # find markdown images: ![alt](path)
                imgs = re.findall(r'!\[.*?\]\((.*?)\)', content)
                for img in imgs:
                    # Resolve relative to the file directory
                    img_path = os.path.normpath(os.path.join(root, img))
                    if not os.path.exists(img_path):
                        print(f"BROKEN IMAGE: In {os.path.relpath(fp, base_dir)} -> {img} (resolved: {img_path})")
                    else:
                        print(f"VALID IMAGE: In {os.path.relpath(fp, base_dir)} -> {img}")

print("\n=== 4. CHECKING SCREENSHOT FILES ON DISK ===")
screenshots_dir = os.path.join(base_dir, "screenshots")
if os.path.exists(screenshots_dir):
    for s in os.listdir(screenshots_dir):
        sp = os.path.join(screenshots_dir, s)
        sz = os.path.getsize(sp)
        print(f"Screenshot: {s} (size: {sz:,} bytes)")
else:
    print("screenshots/ directory DOES NOT EXIST!")

print("\n=== 5. CHECKING PYTHON SCRIPTS SYNTAX AND IMPORTS ===")
import py_compile
python_files = glob.glob(os.path.join(base_dir, "python", "*.py"))
for pf in python_files:
    rel_pf = os.path.relpath(pf, base_dir)
    try:
        py_compile.compile(pf, doraise=True)
        print(f"SYNTAX OK: {rel_pf}")
    except py_compile.PyCompileError as e:
        print(f"SYNTAX ERROR in {rel_pf}: {e}")

print("\n=== 6. CHECKING SQL SCRIPTS EXISTENCE AND SYNTAX ===")
sql_files = glob.glob(os.path.join(base_dir, "sql", "*.sql")) + glob.glob(os.path.join(base_dir, "sql", "queries", "*.sql"))
for sf in sql_files:
    rel_sf = os.path.relpath(sf, base_dir)
    size = os.path.getsize(sf)
    print(f"SQL file: {rel_sf} ({size:,} bytes)")

print("\n=== 7. CHECKING KEY METRIC CONSISTENCY ACROSS FILES ===")
# Let's inspect AL, MA, RJ mix-adjusted gaps and repeat rates in README, interview notes, etc.
files_to_check = [
    "README.md",
    "documentation/data_dictionary.md",
    "documentation/interview_defense_notes.md",
    "documentation/three_way_reconciliation_report.md",
    "powerbi/specifications/page3_regional_and_seller.md",
    "powerbi/specifications/page4_customer_satisfaction.md"
]

for fc in files_to_check:
    fp = os.path.join(base_dir, fc)
    if os.path.exists(fp):
        with open(fp, 'r', encoding='utf-8') as f:
            text = f.read()
            print(f"\n--- Checking {fc} ---")
            # check AL gap mentions
            al_matches = re.findall(r'.{0,50}AL.{0,50}', text)
            for m in al_matches:
                if any(x in m for x in ['gap', '78.', 'mix-adjusted', '-11.', '-14.']):
                    print(f"  AL: {m.strip()}")
            # check 12.56 vs 12.61
            cycle_matches = re.findall(r'.{0,40}12\.(?:56|61).{0,40}', text)
            for m in cycle_matches:
                print(f"  Cycle: {m.strip()}")
