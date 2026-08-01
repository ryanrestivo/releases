#!/usr/bin/env python3
"""Compare v5 labels vs labeled_final ground truth to find mismatches."""
import csv
import html
from collections import Counter

v5 = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v5.csv'
ref = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_final.csv'

print("Loading labeled_final...")
with open(ref, newline='', encoding='utf-8-sig') as f:
    ref_rows = list(csv.DictReader(f))
    
# Get ref distribution for labels
ref_cats = Counter(r['Category'].strip() for r in ref_rows)
ref_conts = Counter(r['Controversial (Y/N)'].strip().upper() for r in ref_rows)
refrels = Counter(r['Relevant (Y/N)'].strip().upper() for r in ref_rows)
print(f"\nRef category distribution: {sorted(ref_cats.items(), key=lambda x:-x[1])}")

# Check empty Category values in labeled_final
ref_empty_cat = sum(1 for r in ref_rows if not r['Category'].strip())
print(f"Reference rows with empty Category: {ref_empty_cat}")

print("\nLoading v5...")
with open(v5, newline='') as f:
    v5_rows = list(csv.DictReader(f))
    
v5_cats = Counter(r['Category'].strip() for r in v5_rows)
v5_conts = Counter(r['Controversial (Y/N)'].strip().upper() for r in v5_rows)
print("V5 category distribution: %s" % dict(sorted(v5_cats.items(), key=lambda x:-x[1])))

# Compare by URL bridge  
ref_by_url = {}
for r in ref_rows:
    url = r.get('urls') or ''
    if url:
        ref_by_url[url] = {'cat': r['Category'].strip(), 'cont': r['Controversial (Y/N)'].strip()}

v5_by_url = {}  
for r in v5_rows:
    url = r.get('urls') or ''
    if url:
        v5_by_url[url] = {'cat': r['Category'].strip(), 'cont': r['Controversial (Y/N)'].strip()}

# Find mismatches
mismatches = 0
matches = 0
for url in ref_by_url:
    if url in v5_by_url:
        ref_c = ref_by_url[url]['cat']
        v5_c = v5_by_url[url]['cat']
        if ref_c.lower() != v5_c.lower():
            mismatches += 1
    
print(f"\nComparison results:")
print(f"  Total labeled_final rows: {len(ref_rows)}")
print(f"  V5 rows matching by URL: {len(set(ref_by_url.keys()) & set(v5_by_url.keys()))} ({matches + mismatches}/{len(ref_by_url)})")
print(f"  Mismatches (category differs): {mismatches}")
print(f"  Matches (same labels): {mismatches + matches - mismatches}")

# Show first few mismatches to understand patterns  
if mismatches > 0:
    print("\nFirst 15 mismatches:")
    count = 0
    for url in ref_by_url:
        if url in v5_by_url and ref_by_url[url]['cat'].lower() != v5_by_url[url]['cat'].lower():
            count += 1
            print(f"  Ref={ref_by_url[url]['cat']} -> V5={v5_by_url[url]['cat']} (URL: {url[:80]})")
            if count >= 15: break

# Compare Controversial/Y/N distribution  
if ref_conts and v5_conts:
    print(f"\nRef Controversial: Y={ref_conts.get('Y',0)}, N={ref_conts.get('N',0)}")
    print(f"V5 Controversial: Y={v5_conts.get('Y',0)}, N={v5_conts.get('N',0)}")
    
    if ref_conts != v5_conts:
        print("  WARNING: Controversial distribution differs!")

# Check Relevant  
import sys
sys.exit(0)
