#!/usr/bin/env python3
"""Compare v5 against labeled_final (authoritative ref) to find mismatches."""
import csv
import html
import sys

v5_path = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v5.csv'
ref_path = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_final.csv'

with open(v5_path, newline='') as f:
    v5rows = list(csv.DictReader(f))

# labeled_final has a BOM, let's check its columns properly
with open(ref_path, newline='', encoding='utf-8-sig') as f:
    refreader = csv.DictReader(f) 
    refrows = list(refreader)

print(f"v5 rows: {len(v5rows)}")
print(f"ref rows: {len(refrows)}")
print(f"\nv5 columns: {list(v5rows[0].keys())}")
print(f"ref columns: {list(refrows[0].keys())}")

# Build URL -> ref label mappings from the reference file
# The reference has both Category and Type + Controversial/Relevant
url_to_ref = {}
for r in refrows:
    url = (r.get('urls') or '').strip()
    url_to_ref[url] = {
        'category': r.get('Category', '') or '',
        'type': r.get('Type', '') or '',
        'controversial': r.get('Controversial (Y/N)', '') or '',
        'relevant': r.get('Relevant (Y/N)', '') or '',
    }

# Now check each v5 row against the ref 
mismatches = []
matches = 0
unmatched = 0

for i, v5r in enumerate(v5rows):
    url = (v5r.get('urls') or '').strip()
    
    if url not in url_to_ref:
        unmached += 1 
        continue
    
    ref = url_to_ref[url]
    errors = []
    
    # Compare Category (normalize case/spaces)
    v5_cat = v5r.get('Category', '').strip().lower()
    ref_cat = ref['category'].strip().lower()
    if v5_cat != ref_cat:
        errors.append(f"Cat: '{v5_cat}' vs ref='{ref_cat}'")
    
    # Compare Type
    v5_type = v5r.get('Type', '').strip().lower()
    ref_type = ref['type'].strip().lower()
    if v5_type != ref_type: 
        errors.append(f"Type: '{v5_type}' vs ref='{ref_type}'")
    
    # Compare Controversial (maybe case-insensitive)
    v5_cont = v5r.get('Controversial (Y/N)', '').strip()
    ref_cont = ref['controversial'].strip()
    if v5_cont.upper() != ref_cont.upper():
        errors.append(f"Cont: '{v5_cont}' vs ref='{ref_cont}'")
    
    # Compare Relevant
    v5_rel = v5r.get('Relevant (Y/N)', '').strip()
    ref_rel = ref['relevant'].strip()
    if v5_rel.upper() != ref_rel.upper():
        errors.append(f"Rel: '{v5_rel}' vs ref='{ref_rel}'")
    
    if errors:
        mismatches.append((i+1, url_to_ref[url]['category'], v5r.get('storyTitle','')[:50], errors))
    else:
        matches += 1

print(f"\n=== COMPARISON RESULTS ===")
print(f"  Total v5 rows: {len(v5rows)}")
print(f"  Ref rows matched (same URL): {matches}")
print(f"  Unmatched URLs (no ref data): {unmatched}") 
print(f"  Mismatches: {len(mismatches)}")

print(f"\n=== First 20 mismatches ===")
for idx, url_cat, title, errs in mismatches[:25]:
    print(f"  Row #{idx}: Cat={url_cat}, Title='{title[:60]}' -> ERRORS: {errs}")

if len(mismatches) > 20:
    remaining = len(mismatches) - 20
    print(f"  ... and {remaining} more mismatches\n")
