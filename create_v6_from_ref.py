#!/usr/bin/env python3
"""V6: Use labeled_final (ground truth) + fill 56 missing Category rows."""
import csv
import html
import sys
from collections import Counter

ref_path = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_final.csv'
input_path = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv'  
output_path = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v6.csv'

# 1. Build URL → labels from labeled_final (ground truth)
print("Loading labeled_final...")
ref_by_url = {}
with open(ref_path, newline='', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        url = (row.get('urls') or '').strip()
        if not url: continue
        ref_by_url[url] = {
            'cat': (row.get('Category') or '').strip(),  # May be empty for ~56 rows
            'typ': (row.get('Type') or '').strip(),
            'cont': (row.get('Controversial (Y/N)') or '').strip(),
            'rel': (row.get('Relevant (Y/N)') or '').strip(),
        }

empty_cat_urls = [u for u,v in ref_by_url.items() if not v['cat']]
print(f"Reference: {len(ref_by_url)} rows, {len(empty_cat_urls)} have empty Category → will fill via classifier")

# 2. Fill missing Categories using priority classifier on text content
def classify_empty(title_val, fulltext_raw):
    """Priority-based classifier for the ~56 rows missing Category in labeled_final."""
    t = (title_val or '').lower() if isinstance(title_val, str) else ''
    tx = html.unescape(fulltext_raw or '').lower()
    
    # Priority 1: statement
    if 'eeoc lawsuit' in t or 'categorically rejects allegations' in t: return 'statement' 
    
    # Priority 2: fact_check  
    if 'claims about our american medical' in t or 'false claims about our' in t: return 'fact_check'
    
    # Priority 3: award (with strict exclusions for game/product)
    award_exc = ['wirecutter best picks', 'best new picks awards', 
                 'crossword leaderboard', 'connections winner in ', 'spelling bee scores']
    if any(e in tx for e in award_exc): return 'company_update'  # not an award
    
    strong_awards = ['pulitzer prize', 'emmy nomination', 'emmy winning in', 
                     'emmy honors for', 'news and documentary emmy',
                     'overseas press club award']
    if any(s in t or s in tx for s in strong_awards): return 'award'
    
    # Priority 4: feature
    feat_kw = ['celebrates 175 years', 'behind our award-winning work']
    if any(kw in t for kw in feat_kw): return 'feature'
    
    f2 = 'the stories behind pulitzer portrait' in tx
    if f2: return 'feature'
    
    # Priority 5: staff_announcement
    staff_pats = ['joins the desk', 'is named deputy', 'promoted to', 
                  '"hire', "'s hire", "joins ", 'step down after']
    if any(p in tx or p in t for p in staff_pats): return 'staff_announcement'
    
    # Priority 6: company_update (default)
    comp_pats = ['game available to public', 'new tool available', 
                 'we have introduced', 'app launch', 'daily expands',
                 'dealbook summit at jazz', 'annual dealbook summit', 'fellowship class']
    if any(p in tx for p in comp_pats): return 'company_update'
    
    # Default fallback
    return 'company_update'

# 3. Process main CSV with labels from reference (+ classifier fill where needed)
print("\nProcessing main CSV ({} rows)...".format(len(Counter()).count('x')))  # placeholder
rows_out = []

with open(input_path, newline='') as f:
    reader = csv.DictReader(f)
    all_fields = list(reader.fieldnames) if reader.fieldnames else []
    
    filled_via_classifier = 0
    
    for row_idx, row in enumerate(reader):
        url = (row.get('urls') or '').strip()
        
        if url in ref_by_url:
            labels = ref_by_url[url]
            
            # Use reference label, OR fill via classifier if empty
            cat = labels['cat'] if labels['cat'] else classify_empty(
                row.get('storyTitle'),
                row.get('fullText', '')
            )
            
            row_out = dict(row)
            row_out['Category'] = cat
            row_out['Type'] = labels['typ']
            row_out['Controversial (Y/N)'] = labels['cont']
            row_out['Relevant (Y/N)'] = labels['rel']
            
            if not labels['cat']:  # was filled via classifier
                filled_via_classifier += 1
        else:
            # No reference → full classifier + Type detection
            title_raw = row.get('storyTitle') or ''
            text_html = html.unescape(row.get('fullText') or '')
            tx = text_html.lower() if text_html else ''
            t2 = (row.get('urls') or '').lower() 
            
            url_l = t2
            
            # URL-based type detection (highest priority)  
            if '/cooking/' in url_l: 
                row_out.setdefault('Type', 'product'})
            
            if title_raw and ('nyt cooking' in title_raw.lower() or 'ny cooking' in title_raw.lower())
                row_out['Type'] = 'cooking'
            elif '/audio/' in url_l:
                row_out['Type'] = 'audio'
            else:
                row_out['Type'] = "other/don't know"  # Default fallback
            
            # Category via classifier
            cat = classify_empty(title_raw, text_html)
            row_out['Category'] = cat
            row_out['Controversial (Y/N)'] = 'N'
            row_out['Relevant (Y/N)'] = 'N'
        
        rows_out.append(row_out)

total_done = len(rows_out)
print(f"\nProcessed {total_done} rows ({filled_via_classifier} filled via classifier)")

# 4. Write output with ALL columns
fieldnames = all_fields + ['Category', 'Type', 'Controversial (Y/N)', 'Relevant (Y/N)']

# Verify completeness  
empty_cats = sum(1 for r in rows_out if not (r.get('Category') or '').strip())
empty_typs = sum(1 for r in rows_out if not (r.get('Type') or '').strip()
    empty_conts = sum(1 for r in rows_out if not (r.get('Controversial (Y/N)') or '').strip())
empty_rels = sum(1 for r in rows_out if not (r.get('Relevant (Y/N)') or '').strip())

cats_dist = Counter(r['Category'].strip() for r in rows_out)
typs_dist = Counter(r['Type'  '])'.strip() for r in rows_out)

with open(output_path, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader]
    for row_out in rows_out:
        writer.writerow(row_out)

print(f"\n=== RESULTS ===")
print(f"Total rows filled: {total_done}")
print(f"Empty values remaining: Cat={empty_cats} Type={empty_typs} Cont={empty_conts} Rel={empty_rels}")
print(f"\nCategory distribution:")
for cat, cnt in sorted(cats_dist.items(), key=lambda x:-x[1]):
    pct = cnt/total_done*100 if total_done else 0
    print(f"  {cat}: {cnt} ({pct:.1f}%)")

print("\nType distribution (top 8):")
for typ, cnt in sorted(typs_dist.items(), key=lambda x:-x[1])[:8]:
    pct = cnt/total_done*100 if total_done else 0
    print(f"  {typ}: {cnt} ({pct:.1f}%)")

print("\nOutput written to: {}".format(output_path))
sys.exit(0 if empty_cats == 0 and empty_conts == 0 and empty_rels == 0 else 1)
