import os
import re
import glob

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# 1. Search for hardcoded machine paths
print("=== 1. CHECKING FOR HARDCODED MACHINE PATHS ===")
machine_patterns = [r"Users\\[A-Za-z0-9_-]+"]  # Generic user folder check
excluded_dirs = [".git", "scratch", ".system_generated", "query_results"]

found_paths = []
for root, dirs, files in os.walk(base_dir):
    dirs[:] = [d for d in dirs if d not in excluded_dirs]
    for file in files:
        if file.endswith(('.py', '.sql', '.md', '.dax', '.ps1', '.json')):
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, base_dir)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        for pat in machine_patterns:
                            if re.search(pat, line, re.IGNORECASE):
                                # ignore harmless comments or expected documentation of machine differences
                                found_paths.append((relpath, line_num, line.strip()))
            except Exception as e:
                print(f"Error reading {filepath}: {e}")

for p, l, text in found_paths[:30]:
    print(f"  {p}:{l} -> {text[:100]}")
print(f"Total hardcoded machine path matches: {len(found_paths)}")

# 2. Search for causal words in documentation and specs
print("\n=== 2. CHECKING FOR CAUSAL / FORBIDDEN WORDS ===")
causal_words = [
    r"\bcaused\b", r"\bcauses\b", r"\bcausing\b",
    r"\bproves\b", r"\bproving\b", r"\bproven\b",
    r"\bconfirms\b", r"\bconfirming\b",
    r"exclusively because",
    r"\brestored\b",
    r"congestion caused",
    r"severe carrier congestion",
    r"peak anger",
    r"transit silence",
    r"economically challenging"
]

found_causal = []
doc_files = glob.glob(os.path.join(base_dir, "documentation", "*.md")) + \
            glob.glob(os.path.join(base_dir, "powerbi", "specifications", "*.md")) + \
            [os.path.join(base_dir, "README.md")]

for filepath in doc_files:
    relpath = os.path.relpath(filepath, base_dir)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            # Skip lines that explicitly talk about avoiding causal language or quoting past text
            for cw in causal_words:
                if re.search(cw, line, re.IGNORECASE):
                    found_causal.append((relpath, line_num, cw, line.strip()))

for p, l, cw, text in found_causal:
    print(f"  {p}:{l} [{cw}] -> {text[:120]}")
print(f"Total causal occurrences: {len(found_causal)}")

