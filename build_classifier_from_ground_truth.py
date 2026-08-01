#!/usr/bin/env python3
"""
STEP 1: Data Analysis — Load all CSVs and understand the structure.
Maps ground truth (labeling_test.csv) to NYT source releases via shared titles/URLs.
Extracts signal patterns per label category for classifier training.
"""

import csv
import io
import re
import html
from collections import Counter
from difflib import SequenceMatcher


def load_csv_as_list(path):
    """Load CSV and return clean list of dicts, handling encoding quirks."""
    with open(path, 'r', encoding='utf-8-sig') as f:
        content = f.read().replace('\r\n', '\n').replace('\r', '\n')
    
    reader = csv.DictReader(io.StringIO(content))
    rows = []
    for row in reader:
        clean = {}
        for k, v in row.items():
            if k is not None:
                clean[k.strip()] = v.strip() if v else ''
        if any(v for v in clean.values()):  # skip completely empty rows
            rows.append(clean)
    return rows


def load_source_csv_comprehensive(path):
    """
    Load source CSV specially — fullText has embedded commas and quotes
    that break standard csv parsing. We use the header to know how many 
    fields we expect after 'urls' (which is always the first field).
    """
    rows = []
    with open(path, 'r', encoding='utf-8-sig') as f:
        content = f.read().replace('\r\n', '\n').replace('\r', '\n')
    
    lines = content.split('\n')
    if not lines or not lines[0].strip():
        return []
    
    # Parse header
    header = [h.strip() for h in lines[0].split(',')]
    # The fields we need are: urls, fullText, storyTitle, datePublished, dateModified
    
    for line in lines[1:]:
        if not line.strip():
            continue
        
        # Split on first comma to get URL (always field 0), then everything else is a mess
        first_comma = line.find(',')
        if first_comma == -1:
            continue
        
        rest_of_line = line[first_comma + 1:]
        
        # Now we need to split the rest properly. The fullText column may contain
        # commas and quotes (since it's CSV-escaped), so we parse field by field
        remaining = rest_of_line
        fields_after_urls = []
        
        next_field_start = 0
        for expected_idx in range(len(header) - 1):  # skip 'urls' which is already parsed
            if not remaining:
                break
            
            is_quoted = remaining.startswith('"')
            
            if is_quoted:
                # Find the closing quote (handling escaped quotes "")
                i = 1
                while i < len(remaining):
                    if remaining[i] == '"':
                        if i + 1 < len(remaining) and remaining[i + 1] == '"':
                            i += 2  # skip escaped quote
                            continue
                        else:
                            break  # closing quote
                    i += 1
                field_value = remaining[1:i].replace('""', '"')  # unescape
                fields_after_urls.append(field_value)
                remaining = remaining[i + 1:].lstrip(',')  # skip comma after closing quote if any
            else:
                # Unquoted field — simple split on comma
                next_comma = remaining.find(',')
                if next_comma == -1:
                    fields_after_urls.append(remaining)
                    remaining = ''
                else:
                    fields_after_urls.append(remaining[:next_comma])
                    remaining = remaining[next_comma + 1:]
            next_field_start += 1
        
        if len(fields_after_urls) >= len(header) - 1:
            full_fields = [header[0]] + header[1:]  # all headers, skip parsing urls since it's not in rest
            # We need exactly the same number of fields as headers  
            # But 'urls' is field 0 and we got rest_of_line starting after first comma
            # So combine: urls=first_field_value, rest=fields_after_urls
        else:
            continue
        
        row = {
            header[0]: line[:first_comma].strip(),  # urls
        }
        for i, h in enumerate(header[1:]):
            if i < len(fields_after_urls):
                row[h] = fields_after_urls[i]
            else:
                row[h] = ''
        
        # Only keep rows that have a valid URL
        if row.get('urls', '').strip():
            rows.append(row)
    
    return rows


def title_similarity(t1, t2):
    """Normalized similarity ratio between two strings (lowercase, normalized whitespace)."""
    s1 = re.sub(r'[^a-z0-9]', ' ', str(t1 or '').lower().strip())
    s2 = re.sub(r'[^a-z0-9]', ' ', str(t2 or '').lower().strip())
    return SequenceMatcher(None, s1, s2).ratio()


def fuzzy_title_match(target_title, candidate_titles_dict):
    """
    Find the best matching source row for a given title.
    Returns (row, similarity_score) or (None, 0).
    """
    if not target_title:
        return None, 0
    
    target = re.sub(r'\s+', ' ', target_title.lower().strip())
    
    # Exact match first
    for key in candidate_titles_dict:
        if key.strip() == target.strip():
            return candidate_titles_dict[key], 1.0
    
    # Fuzzy match
    best_score = 0
    best_row = None
    best_key = ''
    for key, val in candidate_titles_dict.items():
        score = title_similarity(target, key)
        if score > best_score:
            best_score = score
            best_row = val
            best_key = key
    
    threshold = 0.6  # minimum similarity to count as a match
    if best_score >= threshold and best_row:
        return best_row, round(best_score, 3)
    
    return None, 0


# ============================================================================
# STEP 1: Load all data files
# ============================================================================

print("=" * 70)
print("STEP 1: Loading and analyzing ALL data files")  
print("=" * 70)

# 1a: Ground truth labels from labeling_test.csv (has actual categories!)
test_rows = load_csv_as_list('/Users/ryanrestivo/Downloads/labeling_test.csv')
print(f"\n\n[1] labeling_test.csv — GROUND TRUTH LABELS")
print(f"    Rows: {len(test_rows)}")
if test_rows:
    print(f"    Columns: {list(test_rows[0].keys())}")
    
# Category distribution in labeling_test  
cat_counter = Counter()
for r in test_rows:
    c = r.get('Category') or r.get('Category of Release', '')
    if not c:
        c = ''
    cat_counter[c.strip()] += 1
    
print(f"\n    Categories:")
for c, count in sorted(cat_counter.items(), key=lambda x: -x[1]):
    print(f"      {c or '(blank)':<30} → {count}")

# Check for blanks
blank_count = sum(1 for r in test_rows if not (r.get('Category') or '').strip())
print(f"    Blank categories: {blank_count} / {len(test_rows)}")

# 1b: Source releases with fullText from NYT
source_rows = load_source_csv_comprehensive('/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv')
print(f"\n\n[2] NYT source CSV (with fullText)")
print(f"    Rows: {len(source_rows)}")
if source_rows:
    print(f"    Columns: {list(source_rows[0].keys())}")

# 1c: Releases labeling (has Source URLs + Titles, but blank categories)
rl_rows = load_csv_as_list('/Users/ryanrestivo/Downloads/releases_labeling.csv')
print(f"\n\n[3] releases_labeling.csv — UNLABELED (Source URLs available!)")
print(f"    Rows: {len(rl_rows)}")
if rl_rows:
    print(f"    Columns: {list(rl_rows[0].keys())}")

# 1d: labeled_final baseline 
lf_rows = load_csv_as_list('/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_final.csv')
print(f"\n\n[4] labeled_final.csv (PREVIOUS attempt baseline)")
print(f"    Rows: {len(lf_rows)}")
if lf_rows:
    # Count categories vs blanks  
    cat_counts = Counter()
    for r in lf_rows:
        c = r.get('Category') or ''
        cat_counts[c.strip()] += 1
    
    print(f"    Categories:")
    blank_in_lf = 0
    for c, count in sorted(cat_counts.items(), key=lambda x: -x[1])[:10]:
        total_cats = sum(v for v in cat_counts.values() if v > 0)
        actual_total = total_cats + (len(lf_rows) - total_cats)
        print(f"      {c or '(blank)':<30} → {count}")
    blank_in_lf = cat_counts.get('', 0)
    print(f"    Blank/empty categories: {blank_in_lf} / {len(lf_rows)}")

print("\n\n" + "=" * 70)
print("STEP 1 COMPLETE — Data loaded successfully")
print("=" * 70)


# ============================================================================  
# STEP 2: Build lookup maps 
# ============================================================================

print("\n\n" + "=" * 70)
print("STEP 2: Building title/URL lookup maps for cross-referencing")
print("=" * 70)

# Map source titles → rows (normalize for matching)
title_map = {}
for row in source_rows:
    title = row.get('storyTitle') or ''
    if title.strip():
        norm_key = re.sub(r'\s+', ' ', title.lower().strip())
        if norm_key not in title_map:
            title_map[norm_key] = row

url_map = {}
for row in source_rows:
    raw_url = row.get('urls') or ''
    url = str(raw_url).strip().rstrip('/').lower() if isinstance(raw_url, str) else str(raw_url).strip().rstrip('/')
    # Skip empty/non-string
    if isinstance(url, str) and url.strip():
        clean_url = url.lower().rstrip('/')
        url_map[clean_url] = row

print(f"  title_map: {len(title_map)} unique titles")  
print(f"  url_map: {len(url_map)} unique URLs")


# Map releases_labeling Articles → rows + Source URLs  
rl_articles = {}
for row in rl_rows:
    art_num = (row.get('Article Number') or '').strip().replace(' ', '')
    if art_num:
        rl_articles[art_num] = row

print(f"\n  articles from releases_labeling: {len(rl_articles)}")


# ============================================================================
# STEP 3: Map ground truth (labeling_test) items to NYT source fullText
# ============================================================================

print("\n\n" + "=" * 70)  
print("STEP 3: Mapping ground truth labels → fullText in NYT source CSV")
print("=" * 70)

all_matched = []  # (category, title, source_title, fullText, url, article_num, similarity)

# Method A: Use Article Number from labeling_test to find Source URL in releases_labeling, then match that URL to source
for row in test_rows:
    art_num = (row.get('Article Number') or row.get('article_number', '')).strip().replace(' ', '')
    cat_label = (row.get('Category') or '').strip().lower()  
    title = (row.get('Title') or '').strip()
    
    if not art_num and not title:
        continue
    
    matched_row = None
    method = ''
    score = 0.0
    
    # Method A1: Article Number → Source URL in releases_labeling → find that URL in source CSV
    if art_num and art_num in rl_articles:
        src_url = (rl_articles[art_num].get('Source URL') or '').strip().rstrip('/')
        if src_url:
            for url_key, src_row in url_map.items():
                clean_src_url = src_url.lower()
                # Direct URL comparison  
                if clean_src_url == url_key or clean_src_url in url_key:
                    matched_row = src_row
                    method = 'artnum+url'
                    score = 1.0
                    break
    
    # Method A2: Title match from labeling_test → source by title
    if not matched_row and title:
        matched_row, score = fuzzy_title_match(title, title_map)
        method = 'title_fuzzy'
    
    # If still unmatched, try articles_labeling titles too 
    if not matched_row and title:
        rl_url_for_title = None  
        for art_num2 in rl_articles:
            if (re.sub(r'\s+', ' ', (rl_articles[art_num2].get('Title') or '').lower().strip()) == 
                re.sub(r'\s+', ' ', title.lower().strip())):
                rl_url_for_title = (rl_articles[art_num2].get('Source URL') or '').rstrip('/')
                break
        
        if rl_url_for_title:
            for url_key, src_row in url_map.items():
                if rl_url_for_title.lower() in url_key or url_key in rl_url_for_title.lower():
                    matched_row = src_row
                    method = 'rltitle+url'
                    score = 1.0
                    break
    
    if matched_row and (matched_row.get('fullText') or '').strip():
        all_matched.append({
            'category': cat_label,
            'title': title[:120],
            'source_title': (matched_row.get('storyTitle') or '')[:120],
            'fullText_first500': (matched_row.get('fullText') or '')[:500].strip(),
            'url': matched_row.get('urls', '')[:80],
            'article_num': art_num,
            'method': method,
            'similarity': score,
        })
    elif matched_row:
        all_matched.append({
            'category': cat_label,
            'title': title[:120],
            'source_title': (matched_row.get('storyTitle') or '')[:120],
            'fullText_first500': '(empty/fullText not available)',
            'url': matched_row.get('urls', '')[:80],
            'article_num': art_num,
            'method': method + '_(text_empty)',
            'similarity': score,
        })

matched_with_text = sum(1 for m in all_matched if not m['fullText_first500'].startswith('('))
print(f"\n  Total ground truth items: {len(test_rows)}")
print(f"  Successfully mapped to source rows: {len(all_matched)} of {len(test_rows)} ({len(all_matched)/len(test_rows)*100:.0f}%)")
print(f"  With fullText available: {matched_with_text}")

# Show per-category breakdown with matching rate
cat_stats = {}
for m in all_matched:
    c = m['category']
    if c not in cat_stats:
        cat_stats[c] = {'total': 0, 'with_url_or_method': len([m2 for m2 in test_rows if (m2.get('Category') or '').strip().lower() == c])}
    cat_stats[c]['count'] += 1

print(f"\n  Category → # mapped:")
for c, stats in sorted(cat_stats.items(), key=lambda x: -x[1]['count']):
    print(f"    {c:<40} → {stats['count']}")


# ============================================================================
# STEP 4: Extract signal patterns from ground truth examples with fullText
# ============================================================================

print("\n\n" + "=" * 70)
print("STEP 4: Extracting SIGNATURE PATTERNS from matched examples")  
print("=" * 70)

pattern_examples = {}  # category → list of (title, first_sentence_of_fulltext, key_signals)

for m in all_matched:
    c = m['category']
    if not c or c == '(blank)':
        continue
    
    ft_preview = m['fullText_first500']
    sigs = []
    
    # Extract the FIRST sentence/paragraph from fullText as a signature
    sentences = split_into_sentences(ft_preview) if has_text else [(ft_preview[:300])]
    first_sentence = sentences[0] if sentences else '(no text)'
    
    pattern_examples.setdefault(c, []).append({
        'title': m['title'],
        'article_num': m['article_num'] or '',
        'method': m['method'],
        'first_fifteen_words': ft_preview[:60] if ft_preview else '(empty)',
        'fullText_sample': ft_preview[:300],
    })

# Also show some key signals found in fullText per category
cat_key_signals = {}  # For each category, what common phrases appear?
for m in all_matched:
    c = m['category']
    if not c or c == '(blank)':
        continue
    
    ft = (match_row.get('fullText') or '') if match_row else ''
    
    # Extract key patterns from fullText for this category
    common_phrases = [
        'joins', 'named', 'hired', 'promotion', 'returns to', 'new role for',
        'award', 'honored', 'won', 'pulitzer', 'emmy',  # Award signals
        'responds', 'statement', 'position', 'claims', 'false claims',  # Statement/FC
    ]
    
    found = [p for p in common_phrases if p.lower() in ft.lower()]
    if found:
        cat_key_signals.setdefault(c, {}).update({k: v for k, v in Counter(found).items()})

print(f"\n  Pattern examples by category:")
for c, items in sorted(pattern_examples.items()):
    print(f"\n    {c} ({len(items)} matched):")
    for item in items[:5]:
        sample = item['first_fifteen_words'] or item.get('fullText_sample', '')[0:60] if 'fullText_sample' in item else ''
        method_note = f" [method: {item['method']}]" if item.get('method') != '' else ''
        print(f"      Art#{item['article_num']}: {item['title'][0:90]}")
        if sample:
            clean_sample = sample.replace('\n', ' ')
            if len(clean_sample) > 80:
                clean_sample = clean_sample[:80] + '...'
            print(f"        → FullText snippet: {clean_sample}")


# ============================================================================
# STEP 5: Analyze — what do we need from the classifier?
# ============================================================================

print("\n\n" + "=" * 70)
print("STEP 5: Analysis summary — deriving requirements for the full classifier")
print("=" * 70)

# Count of each category that we have ground truth for
gt_distribution = Counter()
for row in test_rows:
    c = (row.get('Category') or '').strip().lower()
    gt_distribution[c] += 1  

blank_gt = gt_distribution.pop('(blank)', 0) if 'blank' in gt_distribution else 0

print(f"\n  Ground truth distribution (from labeling_test): ")
for c, count in sorted(gt_distribution.items(), key=lambda x: -x[1]):
    label = c or '(blank)'  
    print(f"    {label:<30} → {count}")
if blank_gt:
    print(f"    {'(blank)':<30} → {blank_gt} [BLANK — needs labeling]")

print(f"\n  Matched to source fullText: {len([m for m in all_matched if not m['fullText_first500'].startswith('(')])} / {len(all_matched)}")

print("\n" + "=" * 70)
print("STEP 1-5 COMPLETE — ready for STEP 6 (build classifier)")  
print("=" * 70)
