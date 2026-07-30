#!/usr/bin/env python3
"""Label NYT Press Releases CSV using reference samples."""
import csv
import re

def normalize_title(s):
    if not s: return ""
    # Lowercase, strip punctuation except apostrophe, collapse whitespace  
    s = re.sub(r'[^\w\s\d\']', ' ', s.strip().lower())
    return re.sub(r'\s+', ' ', s).strip()

# Load reference samples
labeling_test = '/Users/ryanrestivo/Sites/releases/references/labeling_test.csv'
releases_label = '/Users/ryanrestivo/Sites/releases/references/releases_labeling.csv'
main_csv = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv'

cat_type_map = {}  # norm_title -> (Category, Type)
with open(labeling_test, newline='', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        title = row.get('Title', '').strip()
        if not title: continue
        key = normalize_title(title)
        cat_type_map[key] = (
            row.get('Category', '').strip(),
            row.get('Type', '').strip()
        )

cont_rel_map = {}  # norm_title -> (Controversial, Relevant)  
with open(releases_label, newline='', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        title = row.get('Title', '').strip()
        if not title: continue
        key = normalize_title(title)
        cont_rel_map[key] = (
            row.get('Controversial (Y/N)', '').strip().upper(),
            row.get('Relevant (Y/N)', '').strip().upper()
        )

print(f"Loaded refs: {len(cat_type_map)} Category/Type, {len(cont_rel_map)} Controversial/Relevant")

# Process and label all rows
result_path = main_csv.replace('.csv', '_labeled.csv')
stats = {'perfect': 0, 'partial': 0, 'none': 0}
unmatched_titles = []

with open(main_csv, newline='', encoding='utf-8-sig') as infile, \
     open(result_path, 'w', newline='', encoding='utf-8-sig') as outfile:
    
    reader = csv.DictReader(infile)
    fieldnames = list(reader.fieldnames or []) + ['Category', 'Type', 'Controversial (Y/N)', 'Relevant (Y/N)']
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()
    
    for row in reader:
        story_title = normalize_title(row.get('storyTitle') or '')
        category, stype, cont, rel = '', '', '', ''
        
        # Try perfect match first
        if story_title and story_title in cat_type_map:
            category, stype = cat_type_map[story_title]
            stats['perfect'] += 1
        if story_title and story_title in cont_rel_map:
            cont, rel = cont_rel_map[story_title]
        
        # Try partial matches (substring) for close variants  
        if not category and not cont:
            all_refs = set(list(cat_type_map.keys()) + list(cont_rel_map.keys()))
            for ref_key in all_refs:
                if story_title and (story_title in ref_key or ref_key in story_title):
                    if ref_key in cat_type_map:
                        category, stype = cat_type_map[ref_key]
                    if ref_key in cont_rel_map:
                        cont, rel = cont_rel_map[ref_key]
                    stats['partial'] += 1
                    break
        
        out_row = {f: row.get(f, '') or '' for f in fieldnames}
        if category: out_row['Category'] = category
        if stype: out_row['Type'] = stype  
        if cont: out_row['Controversial (Y/N)'] = cont
        if rel: out_row['Relevant (Y/N)'] = rel
        
        writer.writerow(out_row)
        
        if not any([category or stype, cont or rel]):
            unmatched_titles.append(row.get('storyTitle', 'UNKNOWN')[:80])

print(f"\nResults:")
print(f"  Perfect matches: {stats['perfect']}")
print(f"  Partial matches: {stats['partial']}")
print(f"  No match (unmatched): {len(unmatched_titles)}")

if unmatched_titles:
    print(f"\nFirst 5 unmatched titles:")
    for title in unmatched_titles[:5]:
        print(f'  "{title}"')
