#!/usr/bin/env python3
"""Label NYT Press Releases CSV using ONLY the two reference files.
Taxonomy: Category, Type (from labeling_test.csv) + Controversial, Relevant (from releases_labeling.csv)
Unmatched rows get EMPTY strings for label fields - no defaults."""
import csv
import re

def normalize(s):
    s = str(s or '').strip().lower()
    s = re.sub(r'[^\w\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

# 1. Load labeling_test.csv → Category + Type maps
cat_type_map = {}
with open('/Users/ryanrestivo/Downloads/labeling_test.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f.read().strip().splitlines(False), skipinitialspace=True)
    for row in reader:
        title = (row.get('Title') or '').strip()
        if not title: continue
        norm = normalize(title)
        cat_type_map[norm] = (
            (row.get('Category') or '').strip(),
            (row.get('Type') or '').strip()
        )

print(f"✅ Loaded {len(cat_type_map)} Category/Type refs from labeling_test.csv")

# 2. Load releases_labeling.csv → Controversial + Relevant maps  
cont_rel_map = {}
with open('/Users/ryanrestivo/Downloads/releases_labeling.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f.read().strip().splitlines(False), skipinitialspace=True)
    for row in reader:
        title = (row.get('Title') or '').strip()
        if not title: continue
        norm = normalize(title)
        cont_rel_map[norm] = (
            (row.get('Controversial (Y/N)') or '').strip().upper(),
            (row.get('Relevant (Y/N)') or '').strip().upper()
        )

print(f"✅ Loaded {len(cont_rel_map)} Controversial/Relevant refs from releases_labeling.csv")

# 3. Read main CSV and label each row with EXACT match only
main_csv = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv'
output_csv = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled.csv'

match_stats = {'exact': 0, 'partial': 0, 'no_match': 0}

with open(main_csv, encoding='utf-8-sig') as fin, \
     open(output_csv, 'w', newline='', encoding='utf-8-sig') as fout:
    
    reader = csv.DictReader(fin)
    fieldnames = list(reader.fieldnames or []) + ['Category', 'Type', 'Controversial (Y/N)', 'Relevant (Y/N)']
    writer = csv.DictWriter(fout, fieldnames=fieldnames)
    writer.writeheader()
    
    for i, row in enumerate(reader, 1):
        main_title = normalize(row.get('storyTitle') or '')
        
        # Try Category/Type match
        category, ntype = '', ''
        
        # Exact first, then partial/nested substring
        if main_title and main_title in cat_type_map:
            category, ntype = cat_type_map[main_title]
            match_stats['exact'] += 1
        elif main_title:
            for ref_key in cat_type_map.keys():
                if (main_title in ref_key) or (ref_key in main_title):
                    category, ntype = cat_type_map[ref_key]
                    match_stats['partial'] += 1
                    break
        
        # Try Controversial/Relevant match
        cont, rel = '', ''
        if main_title and main_title in cont_rel_map:
            cont, rel = cont_rel_map[main_title]
            match_stats['exact'] += 1
        elif main_title:
            for ref_key in cont_rel_map.keys():
                if (main_title in ref_key) or (ref_key in main_title):
                    cont, rel = cont_rel_map[ref_key]
                    match_stats['partial'] += 1
                    break
        
        # Only add fields if they have actual values from references
        out_row = {f: (row.get(f) or '') for f in fieldnames}
        
        if category:
            out_row['Category'] = category
        if ntype:
            out_row['Type'] = ntype
        
        if cont == 'Y' or cont == 'N':  # Only set if we found a match
            out_row['Controversial (Y/N)'] = cont
        if rel == 'Y' or rel == 'N':  # Only set if we found a match
            out_row['Relevant (Y/N)'] = rel
        
        writer.writerow(out_row)

print(f"\n📊 MATCHING RESULTS:")
print(f"  ✅ Exact matches: {match_stats['exact']}")
print(f"  🔄 Partial matches: {match_stats['partial']}")
print(f"  ❌ No match: {match_stats['no_match']}")
print(f"  Total rows processed: {match_stats['exact'] + match_stats['partial'] + match_stats['no_match']}")

# Show what labels are available in refs
cat_dist = {}
type_dist = {}
for (c, t) in cat_type_map.values():
    if c: cat_dist[c] = cat_dist.get(c, 0) + 1
    if t: type_dist[t] = type_dist.get(t, 0) + 1

print(f"\n📋 Available labels:")
for k, v in sorted(cat_dist.items(), key=lambda x: -x[1]):
    print(f"  Category='{k}': {v}")
for k, v in sorted(type_dist.items(), key=lambda x: -x[1]):
    print(f"  Type='{k}': {v}")

# Show first few fully-labeled rows as verification
with open(output_csv, encoding='utf-8-sig') as f:
    labeled = csv.DictReader(f)
    labeled_rows = list(labeled)

labeled_count = sum(1 for r in labeled_rows if (r.get('Category','').strip() or r.get('Controversial (Y/N)','').strip()))
print(f"\n📌 Rows with at least one label: {labeled_count}/{len(labeled_rows)}")

print("\n🔍 Sample matched rows:")
match_shown = 0
for i, r in enumerate(labeled_rows):
    if (r.get('Category','').strip() or (r.get('Controversial (Y/N)','').strip()).strip()):
        print(f"  Row {i+1}: '{r.get('storyTitle','')[:70]}...'")
        print(f"       → Cat={r.get('Category','')}, Type={r.get('Type','')}, Controversial={r.get('Controversial (Y/N)','')}, Relevant={r.get('Relevant (Y/N)','')}")
        match_shown += 1
        if match_shown >= 10:
            break
