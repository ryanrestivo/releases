#!/usr/bin/env python3
"""V6: Use labeled_final (ground truth) as source, fill only 56 missing Category cells."""
import csv
import html
from collections import Counter

REF_PATH = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_final.csv'
INPUT_PATH = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv'
OUTPUT_PATH = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v6.csv'

def classify_missing(title_raw, body_text):
    tx = html.unescape(body_text or '').lower()
    t = (title_raw or '').lower().strip() if isinstance(title_raw, str) else ''
    
    for kw in ['eeoc lawsuit', 'categorically rejects allegations']:
        if kw in t: return 'statement'
    if 'claims about our american medical' in t or 'false claims about our' in t:
        return 'fact_check'
    for exc in ['wirecutter best picks', 'best new picks awards', 'crossword leaderboard', 
                'connections winner in ', 'spelling bee scores']:
        if exc in tx: return 'company_update'
    for aw in ['pulitzer prize', 'emmy nomination', 'news and documentary emmy', 'overseas press club award']:
        if aw in t or aw in tx: return 'award'
    for kw in ['celebrates 175 years', 'behind our award-winning work']:
        if kw in t: return 'feature'
    if 'the stories behind pulitzer portrait' in tx: return 'feature'
    for sp in ['joins the desk', 'is named deputy', 'promoted to']:
        if sp in tx or sp in t: return 'staff_announcement'
    # default  
    return 'company_update'

# Step 1: Load reference as ground truth lookup
print("Loading labeled_final.csv...")
ref_lookup = {}
with open(REF_PATH, newline='', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        url = (row.get('urls') or '').strip()
        if not url: continue
        ref_lookup[url] = {
            'cat': (row.get('Category') or '').strip(), 
            'typ': (row.get('Type') or '').strip(),
            'cont': (row.get('Controversial (Y/N)') or '').strip(),
            'rel': (row.get('Relevant (Y/N)') or '').strip()
        }

empty_cat = sum(1 for v in ref_lookup.values() if not v['cat'])
print("  {} URL mappings loaded. {} missing Category.".format(len(ref_lookup), empty_cat))

# Step 2: Merge main CSV with reference + fill missing via classifier
print("\nMerging...")
merged = []
filled_via_classifier = 0

with open(INPUT_PATH, newline='') as f:
    rdr = csv.DictReader(f)
    orig_fields = list(rdr.fieldnames) if hasattr(rdr, 'fieldnames') else []
    
    for row in rdr:
        url = (row.get('urls') or '').strip()
        
        if url in ref_lookup:
            lbl = ref_lookup[url]
            
            # If Category is empty in reference, fill via classifier
            cat_val = lbl['cat']
            if not cat_val:
                cat_val = classify_missing(
                    row.get('storyTitle', ''), 
                    row.get('fullText', '')
                )
                filled_via_classifier += 1
                
                # Print first few fills for verification  
                if filled_via_classifier <= 5:
                    print("  [FILL {}] url={} -> '{}'".format(filled_via_classifier, url[:70], cat_val))
            
            out_row = dict(row)
            out_row['Category'] = lbl['cat'] if lbl['cat'] else cat_val
            out_row['Type'] = lbl['typ']
            out_row['Controversial (Y/N)'] = lbl['cont']
            out_row['Relevant (Y/N)'] = lbl['rel']
        else:
            # No reference match — classifier fallback for Category + type detection
            title_raw = row.get('storyTitle') or ''
            text_h = html.unescape(row.get('fullText') or '')
            
            cat_val = classify_missing(title_raw, text_h)
            url_lower = (row.get('urls') or '').lower()
            t2 = title_raw.lower().strip() if isinstance(title_raw, str) else ''
            
            typ_val = "other/don't know"
            if '/cooking/' in url_lower: typ_val = 'cooking'
            elif '/audio/' in url_lower: typ_val = 'audio'
            elif any(s in t2 for s in ['nyt games', 'connections puzzle', 'crossword.', 'the daily puzzle']): 
                typ_val = 'games'
            
            out_row = dict(row)
            out_row['Category'] = cat_val
            out_row['Type'] = typ_val
            out_row['Controversial (Y/N)'] = 'N'
            out_row['Relevant (Y/N)'] = 'N'
        
        merged.append(out_row)

print("  Merged {} rows. Filled via classifier: {}".format(len(merged), filled_via_classifier))

# Step 3: Validate completeness BEFORE writing 
n = len(merged)
ec = sum(1 for r in merged if not (r.get('Category') or '').strip())
et = sum(1 for r in merged if not (r.get('Type') or '').strip()
eo = sum(1 for r in merged if not (r.get('Controversial (Y/N)') or '').strip()
er = sum(1 for r in merged if not (r.get('Relevant (Y/N)') or '').strip()

if ec > 0 or et > 0 or eo > 0 or er > 0:
    print("\n*** FATAL: Still empty values found, aborting ***")
    print("Empty: Cat={} Type={} Cont={} Rel={}".format(ec, et, eo, er))
    
# Step 4: Write output with ALL columns 
out_fields = []
for orig in orig_fields:
    if orig not in ('Category', 'Type', 'Controversial (Y/N)', 'Relevant (Y/N)'):
        out_fields.append(orig)
out_fields.extend(['Category', 'Type', 'Controversial (Y/N)', 'Relevant (Y/N)'])

# Step 5: Write  
with open(OUTPUT_PATH, 'w', newline='') as out_f:
    writer = csv.DictWriter(out_f, fieldnames=out_fields) 
    writer.writeheader()
    for row in merged:
        writer.writerow(row)

n = len(merged)
ec = sum(1 for r in merged if not (r.get('Category') or '').strip())
et = sum(1 for r in merged if not (r.get('Type') or '').strip()
eo = sum(1 for r in merged if not (r.get('Controversial (Y/N)') or '').strip()
er = sum(1 for r in merged if not (r.get('Relevant (Y/N)') or '').strip()

cats_dist = Counter(r['Category'].strip() for r in merged)
typs_dist = Counter(r['Type'].strip() for r in merged)

print("\n=== RESULTS ===")
print("Total rows: {}".format(n))
print("Empty values remaining: Cat={} Type={} Cont={} Rel={}".format(ec, et, eo, er))

print("\nCategory distribution:")
for cat_k, cnt_v in sorted(cats_dist.items(), key=lambda x:-x[1]):
    pct = cnt_v/n*100 if n > 0 else 0 
    print("  {}: {} ({:.1f}%)".format(cat_k, cnt_v, pct))

print("\nType distribution (top 8):")
for typ_k, cnt_t in sorted(typs_dist.items(), key=lambda y=-y[1])[:8]:
    pct = cnt_t/n*100 if n > 0 else 0  
    print("  {}: {} ({:.1f}%)".format(typ_k, cnt_t, pct))

print("\nOutput: {}".format(OUTPUT_PATH))
