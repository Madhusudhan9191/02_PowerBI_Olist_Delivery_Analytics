import re

dax_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "powerbi", "dax", "measures.dax"))

with open(dax_file, "r", encoding="utf-8") as f:
    text = f.read()

# Pattern for measure definition: Measure Name = \n ...
# Measure names start at beginning of line or after comments, followed by ' ='
measures = re.findall(r'^[ \t]*([A-Za-z0-9 _%★\-()]+?)\s*=\s*\n', text, re.MULTILINE)

# Filter out VAR assignments (e.g., VAR Something =)
actual_measures = [m.strip() for m in measures if not m.strip().startswith(('VAR', 'RETURN'))]

print(f"Total measure headers matched: {len(actual_measures)}")
for i, m in enumerate(actual_measures, 1):
    print(f"{i:2d}. {m}")

# Check for duplicates
seen = set()
dups = []
for m in actual_measures:
    if m in seen:
        dups.append(m)
    seen.add(m)

print(f"\nDuplicates found: {dups}")
