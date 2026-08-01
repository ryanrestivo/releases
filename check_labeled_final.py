#!/usr/bin/env python3
"""Verify labeled_final.csv has ALL 3,390 rows with all 4 columns fully populated."""
import csv
import sys

ref_path = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_final.csv'

with open(ref_path, newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Total rows: {len(rows)}")
print(f"Columns: {list(rows[0].keys())}")

# Check all 4 label columns
label_cols = ['Category', 'Type', 'Controversial (Y/N)', 'Relevant (Y/N)']
empty_counts = {}
for col in label_cols:
    empty = sum(1 for r in rows if not (r.get(col, '').strip()))
    non_empty = len(rows) - empty
    empty_counts[col] = empty
    print(f"\n{col}: {non_empty}/{len(rows)} populated ({empty} empty)")
    
# Show category distribution 
from collections import Counter
cats = Counter()
typs = Counter()
conts = Counter()
rels = Counter()

for r in rows:
    c = (r.get('Category') or '').strip().lower()
    cats[c] += 1
    t2 = (r.get('Type') or '').strip().lower()
    typs[t2] += 1
    co = (r.get('Controversial (Y/N)') or '').strip()
    conts[co.upper()] += 1
    re = (r.get('Relevant (Y/N)') or '').strip()
    rels[re.upper()] += 1

print(f"\n=== DISTRIBUTIONS ===")
print(f"Categories: {sorted(cats.items(), key=lambda x:-x[1])}")
print(f"Types: {sorted(typs.items(), key=lambda x:-x[1])[:8]}")
print(f"Controversial: Y={conts.get('Y',0)}, N={conts.get('N',0)} ({sum(v for k,v in conts.items() if k not in ('Y','N'))} bad)")
print(f"Relevant:   Y={rels.get('Y',0)}, N={rels.get('N',0)} ({sum(v for k,v in rels.items() if k not in ('Y','N'))} bad)")

all_ok = all(empty_counts[col] == 0 for col in label_cols)
print(f"\nAll labels complete: {all_ok}")
sys.exit(0 if all_ok else 1)
