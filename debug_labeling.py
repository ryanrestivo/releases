#!/usr/bin/env python3
"""Analyze what's being misclassified as company_update — find patterns to add."""

import csv
import io
import re

def load_source_csv(path):
    rows = []
    with open(path, 'r', encoding='utf-8-sig') as f:
        content = f.read().replace('\r\n', '\n').replace('\r', '\n')
    lines = content.split('\n')
    if not lines or not lines[0].strip():
        return []
    header = [h.strip() for h in lines[0].split(',')]
    source_keys = list(header)

    col_urls = 'urls'
    col_fulltext = 'fullText'
    col_storytitle = 'storyTitle'
    
    # Map column positions from header
    col_idx = {h: i for i, h in enumerate(header)}
    
    for line in lines[1:]:
        if not line.strip():
            continue
        row = {}
        i = 0
        current_field = []
        in_quotes = False
        fields = []
        chars = list(line)
        while i < len(chars):
            c = chars[i]
            if c == '"':
                if in_quotes and i + 1 < len(chars) and chars[i+1] == '"':
                    current_field.append('"')
                    i += 2
                    continue
                else:
                    in_quotes = not in_quotes
                    current_field.append(c)
            elif c == ',' and not in_quotes:
                fields.append(''.join(current_field).strip().replace('""', '"'))
                current_field = []
            else:
                current_field.append(c)
            i += 1
        fields.append(''.join(current_field).strip().replace('""', '"'))
        
        for j, h in enumerate(header):
            if j < len(fields):
                row[h] = fields[j].strip() if fields[j] else ''
            else:
                row[h] = ''
        
        if row.get(col_urls, '').strip():
            rows.append(row)
    return rows

def load_csv_clean(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        content = f.read().replace('\r\n', '\n').replace('\r', '\n')
    reader = csv.DictReader(io.StringIO(content))
    rows = []
    for row in reader:
        clean = {}
        for k, v in row.items():
            if k is not None: clean[k.strip()] = v.strip() if v else ''
        if any(v for v in clean.values()):
            rows.append(clean)
    return rows

source_rows = load_source_csv('/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv')
test_rows = load_csv_clean('/Users/ryanrestivo/Downloads/labeling_test.csv')

# Build URL->row lookup 
url_map = {str(r.get('urls','')).strip().rstrip('/') : r for r in source_rows}  

# Look at ground truth categories and find their titles in source
print("=== GROUNDF TRUTH EXAMPLES (first 5 per category) ===\n")

test_cats = {}
for r in test_rows:
    c = (r.get('Category') or '').strip().lower() or '(blank)'
    if c not in test_cats:
        test_cats[c] = []
    test_cats[c].append(r)

for cat, items in sorted(test_cats.items(), key=lambda x: -len(x[1]))[:6]:
    print(f"\n>>> {cat} ({len(items)} total):")
    for r in items[:5]:
        title = (r.get('Title') or '').strip()
        art_num = (r.get('Article Number') or '').replace(' ', '')
        print(f"  Art#{art_num}: {title[:80]}")

# Now: show first 30 company_update rows from output, including their titles and fullText snippets
print("\n" + "=" * 80)
print("=== FIRST 40 ROWS OF SOURCE CSV (titles + first 200 chars of fullText) ===\n")
for i, row in enumerate(source_rows[:40]):
    title = (row.get('storyTitle') or '')[:90]
    ft = str(row.get('fullText') or '')[:300].replace('\n', ' ')
    url = (row.get('urls') or '')[:60]
    print(f"\n[{i+1:2d}] TITLE: {title}")
    print(f"    URL:      {url}")
    sample_lines = ft.split('.')[0][:250] if ft else '(empty)'
    print(f"    FullText: {sample_lines}")

# Also show ALL ground truth test items with their matched source fullText snippets
print("\n\n" + "=" * 80)
print("=== GROUND TRUTH MATCHES (title → source first paragraph snippet) ===\n")

for r in test_rows[:15]:
    title = (r.get('Title') or '').strip()
    cat = (r.get('Category') or '').strip().lower()
    
    # Try to find this in source by looking for URL match via releases_labeling
    art_num = (r.get('Article Number') or '').replace(' ', '')
    
    best_match_title = None
    matched_art_num = None
    
    # Check rl_articles first
    import csv as csv_mod, io as io_mod
    with open('/Users/ryanrestivo/Downloads/releases_labeling.csv', 'r', encoding='utf-8-sig') as f:
        rl_content = f.read().replace('\r\n', '\n').replace('\r', '\n')
    rl_reader = csv_mod.DictReader(io.StringIO(rl_content))
    for r2 in rl_reader:
        art_id = (r2.get('Article Number') or '').strip()
        if str(art_id).replace(' ','') == art_num:
            src_url = (r2.get('Source URL') or '').strip().rstrip('/')
            if src_url and src_url in url_map:
                matched_row = url_map[src_url]
                best_match_title = str(matched_row.get('storyTitle', '') or '')[:80]
                ft_snippet = str(matched_row.get('fullText', '') or '')[:200].replace('\n',' ')
                print(f"\n[{cat}] Art#{art_num}: {title[:70]}")
                print(f"   Title in source: {best_match_title}")
                print(f"   FullText snippet: {ft_snippet}")
            break
    
    if not best_match_title and title:
        # Fuzzy title match  
        norm_target = re.sub(r'\s+', ' ', title.lower())
        for url_key, sr in url_map.items():
            src_title = (sr.get('storyTitle') or '').lower()
            sim = 0.0
            s1 = re.sub(r'[^a-z0-9]', ' ', norm_target)
            s2 = re.sub(r'[^a-z0-9]', ' ', src_title)
            from difflib import SequenceMatcher as SM
            sim = SM(None, s1, s2).ratio()
            if sim > 0.7:
                ft_snippet = str(sr.get('fullText', '') or '')[:200].replace('\n',' ')
                print(f"\n[{cat}] Art#{art_num}: {title[:70]}")
                print(f"   Fuzzy match (conf={sim:.2f}): {(sr.get('storyTitle') or '')[:80]}")
                print(f"   FullText snippet: {ft_snippet}")
                break
