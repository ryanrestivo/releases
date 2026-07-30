#!/usr/bin/env python3
"""Analyze ALL reference samples from BOTH CSVs, reading fullText to understand labeling patterns.
This creates a 'ruleset' that we'll apply to label all 3,390 rows."""
import csv
import re
from collections import Counter

def normalize(s):
    s = str(s or '').strip().lower()
    s = re.sub(r'[^\w\s]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

# ============================================================
# PART 1: Load labeling_test.csv → learn Category + Type patterns
# ============================================================
test_labels = []
cat_type_map = {}

with open('/Users/ryanrestivo/Downloads/labeling_test.csv', encoding='utf-8-sig') as f:
    raw = f.read()
reader = csv.DictReader(raw.strip().splitlines(False), skipinitialspace=True)
for row in reader:
    title = (row.get('Title') or '').strip()
    category = (row.get('Category') or '').strip()
    ntype = (row.get('Type') or '').strip()
    if not title: continue
    norm = normalize(title)
    cat_type_map[norm] = (category, ntype)
    test_labels.append({
        'title_norm': norm,
        'raw_title': title,
        'category': category,
        'type': ntype
    })

# ============================================================
# PART 2: Load releases_labeling.csv → learn Controversial + Relevant patterns
# ============================================================
release_labels = []
cont_rel_map = {}

with open('/Users/ryanrestivo/Downloads/releases_labeling.csv', encoding='utf-8-sig') as f:
    raw = f.read()
reader = csv.DictReader(raw.strip().splitlines(False), skipinitialspace=True)
for row in reader:
    title = (row.get('Title') or '').strip()
    cont = (row.get('Controversial (Y/N)') or 'N').strip().upper() if (row.get('Controversial (Y/N)') or 'N').strip() else 'N'
    rel = (row.get('Relevant (Y/N)') or 'N').strip().upper() if (row.get('Relevant (Y/N)') or 'N').strip() else 'N'
    if not title: continue
    norm = normalize(title)
    cont_rel_map[norm] = (cont, rel)
    release_labels.append({
        'title_norm': norm,
        'raw_title': title,
        'controversial': cont,
        'relevant': rel
    })

print("=" * 70)
print("REF DATA SUMMARY")
print("=" * 70)
print(f"Reference file 1 (labeling_test.csv): {len(test_labels)} rows with Category/Type labels")
print(f"Reference file 2 (releases_labeling.csv): {len(release_labels)} rows with Controversial/Relevant labels")

# ============================================================
# PART 3: Learn labeling patterns/rules
# ============================================================
print("\n" + "=" * 70)
print("PATTERN ANALYSIS - Category Labels")
print("=" * 70)

cat_patterns = {}  # category -> list of example titles
for item in test_labels:
    c = item['category']
    if c not in cat_patterns:
        cat_patterns[c] = []
    cat_patterns[c].append(item['title_norm'])

print("\n📂 Category Patterns from labeling_test.csv:")
cat_dist = Counter(c for c, _ in [(i['category'], i['type']) for i in test_labels])

for cat, count in cat_dist.most_common():
    examples = cat_patterns[cat][:5]  # First 5 examples
    print(f"\n  🏷️ '{cat}' ({count} items):")
    for ex in examples:
        print(f"     • {ex}")
# Add note about more if needed

print("\n" + "=" * 70)
print("PATTERN ANALYSIS - Type Labels")  
print("=" * 70)

print("\n📂 Type Patterns from labeling_test.csv:")
type_dist = Counter(t for _, t in [(i['category'], i['type']) for i in test_labels])
for typ, count in type_dist.most_common():
    examples = [item['title_norm'] for item in test_labels if item['type'] == typ][:5]
    print(f"\n  🏷️ '{typ}' ({count} items):")
    for ex in examples:
        print(f"     • {ex}")

print("\n" + "=" * 70)
print("PATTERN ANALYSIS - Controversial + Relevant Labels")
print("=" * 70)

cr_patterns = {}
for item in release_labels:
    key = f"C={item['controversial']}_R={item['relevant']}"
    if key not in cr_patterns:
        cr_patterns[key] = []
    cr_patterns[key].append(item['raw_title'])

print("\n📂 Controversial/Relevant Patterns from releases_labeling.csv:")
cr_dist = Counter((item['controversial'], item['relevant']) for item in release_labels)
for (cont, rel), count in CR_dist.most_common():
    examples = cr_patterns[f"C={cont}_R={rel}"][:5]
    print(f"\n  🏷️ C={cont}, R={rel} ({count} items):")
    for ex in examples:
        print(f"     • {ex}")

# ============================================================
# PART 4: Save structured ruleset for later use
# ============================================================
output = f"""
============================================================
REFERENCE LABELING RULESET - Generated from BOTH CSVs
Total reference rows analyzed: {len(test_labels) + len(release_labels)}
============================================================

CATEGORY PATTERNS (from labeling_test.csv):
{chr(10).join([f"  [{cat}]: {count} items - {', '.join(examples[:3])}" for cat, count in cat_dist.most_common() for examples in [cat_patterns[cat]][:1]])}

TYPE PATTERNS (from labeling_test.csv):  
{chr(10).join([f"  [{typ}]: {count} items - {', '.join(examples[:3])}" for typ, count in type_dist.most_common() if (examples := [item['title_norm'] for item in test_labels if item['type'] == typ]])}

CONTROVERSIAL/RELEVANT PATTERNS (from releases_labeling.csv):
{chr(10).join([f"  C={cont}, R={rel}: {count} items" for (cont, rel), count in cr_dist.most_common()])}

COMPLETE REFERENCE DATA:
"""

for i, item in enumerate(test_labels + release_labels):
    if 'category' in item:
        output += f"\n  [{i+1}] Category={item['category']}, Type={item['type']}, Title={item['raw_title'] or item.get('title_norm','')}"
    else:
        output += f"\n  [{i-len(test_labels)+1}] Controversial={item['controversial']}, Relevant={item['relevant']}, Title={item['raw_title']}"

# Write to file for later use
with open('/Users/ryanrestivo/Sites/releases/references/labeling_ruleset.md', 'w') as f:
    f.write(output.strip())

print("\n✅ Detailed labeling ruleset saved to refs/labeling_ruleset.md")
print("\n" + "=" * 70)  
print("NEXT: Apply learned patterns to all 3,390 rows...")
print("=" * 70)
