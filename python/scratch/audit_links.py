import os
import re

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

print("=== CHECKING ALL MARKDOWN LINKS FOR BROKEN TARGETS ===")
md_files = []
for root, dirs, files in os.walk(base_dir):
    for f in files:
        if f.endswith('.md'):
            md_files.append(os.path.join(root, f))

broken_links = []
for mdf in md_files:
    rel_mdf = os.path.relpath(mdf, base_dir)
    with open(mdf, 'r', encoding='utf-8', errors='ignore') as fp:
        content = fp.read()
        # Match [text](target) but ignore http, https, mailto, and anchor # links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        for text, target in links:
            if target.startswith(('http://', 'https://', 'mailto:', '#')):
                continue
            # Handle anchor in path: path.md#anchor
            clean_target = target.split('#')[0]
            if not clean_target:
                continue
            # target is relative to the directory of the markdown file
            target_path = os.path.normpath(os.path.join(os.path.dirname(mdf), clean_target))
            if not os.path.exists(target_path):
                broken_links.append((rel_mdf, text, target, target_path))

for r_mdf, txt, tgt, full_tgt in broken_links:
    print(f"BROKEN LINK in {r_mdf}: [{txt}]({tgt}) -> not found at {full_tgt}")

print(f"Total broken markdown file links: {len(broken_links)}")
