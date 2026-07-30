#!/usr/bin/env python3
"""
Complete labeling pipeline for NYT press releases.
Reads BOTH reference CSVs to learn taxonomy rules from fullText analysis.
Applies learned patterns to ALL 3,390 rows. Outputs labeled CSV.
"""
import csv
import re
from collections import defaultdict

def normalize(s):
    if not s: return ''
    s = str(s).lower().strip()
    s = re.sub(r'[^\w\s]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

# Load main CSV
with open('/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv', 
          encoding='utf-8-sig') as f:
    MAIN = list(csv.DictReader(f))
print(f"Loaded {len(MAIN)} rows to label")

# Load reference data
REF_CAT = {}  # title_norm -> {Category, Type}  
with open('/Users/ryanrestivo/Downloads/labeling_test.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f, skipinitialspace=True):
        t = (row.get('Title') or '').strip()
        if not t: continue  
        REF_CAT[normalize(t)] = {
            'Category': (row.get('Category') or '').strip(),
            'Type': (row.get('Type') or '').strip()  
        }

REF_CR = {}  # title_norm -> {Controversial, Relevant}
with open('/Users/ryanrestivo/Downloads/releases_labeling.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f, skipinitialspace=True):
        t = (row.get('Title') or '').strip()  
        if not t: continue
        c = (row.get('Controversial (Y/N)') or '').strip().upper()  
        r = (row.get('Relevant (Y/N)') or '').strip().upper() 
        c = 'N' if not c else c
        r = 'N' if not r else r
        REF_CR[normalize(t)] = {'Controversial': c, 'Relevant': r}

print(f"References: {len(REF_CAT)} Cat.Type, {len(REF_CR)} C/R")

# ============================================================
# STEP 1: Find reference items in main CSV for fullText analysis
# ============================================================  
matched_examples = {}  # match_key -> {Category, Type, Contr, Rel, fulltext}  

for row in MAIN:
    title_norm = normalize(row.get('storyTitle', ''))
    
    for ref_t, labels in REF_CAT.items():
        if title_norm == ref_t or (ref_t and (ref_t in title_norm or title_norm in ref_t)):
            ft = (row.get('fullText') or '').strip()[:800]  
            key = 'cat:' + ref_t[:30]
            matched_examples[key] = {
                'Category': labels['Category'], 'Type': labels['Type'],
                'Controversial': REF_CR.get(ref_t, {}).get('Controversial', ''),
                'Relevant': REF_CR.get(ref_t, {}).get('Relevant', ''),
                'fulltext': ft
            }
            
    for ref_t, labels in REF_CR.items():  
        if title_norm == ref_t or (ref_t and (ref_t in title_norm or title_norm in ref_t)):
            ft = (row.get('fullText') or '').strip()[:800]
            key = 'cr:' + ref_t[:30] 
            existing = matched_examples.get(key, {})
            if not existing:
                # Try to find Category from same match
                for r in MAIN:  
                    s = normalize(r.get('storyTitle','')) 
                    if s == ref_t or (ref_t and (ref_t in s or s in ref_t)):
                        for rt in REF_CAT:
                            if s == rt or (rt and (rt in s or s in rt)):
                                existing['Category'] = REF_CAT[rt]['Category']
                                existing['Type'] = REF_CAT[rt]['Type']  
                                break
            if key not in matched_examples or not any(matched_examples[key].get('Title') for k2, matched_examples[key] in matched_examples.items()):
                matched_examples[key] = {
                    'fulltext': ft,
                    'Category': existing.get('Category', ''),
                    'Type': existing.get('Type', ''),  
                    'Controversial': labels['Controversial'],
                    'Relevant': labels['Relevant']
                }

# Actually just build matched_examples properly per-item
matched_examples = {}  
for row in MAIN:
    title_norm = normalize(row.get('storyTitle', ''))
    
    for ref_t, cat_labels in REF_CAT.items():
        if (title_norm == ref_t) or (ref_t and (ref_t in title_norm or title_norm in ref_t)):
            match_key = 'c:' + ref_t[:40]
            matched_examples[match_key] = {
                'storyTitle': row.get('storyTitle',''),
                'Category': cat_labels['Category'],  
                'Type': cat_labels['Type'],
                'fulltext': (row.get('fullText') or '')[:800],
                'source': 'labeling_test'
            }
            break
                
    for ref_t, cr_labels in REF_CR.items():
        if (title_norm == ref_t) or (ref_t and (ref_t in title_norm or title_norm in ref_t)):
            match_key = 'r:' + ref_t[:40]
            existing = None  
            for k2, v2 in matched_examples.items():  
                if normalize(v2['storyTitle']) == ref_t or normalize(v2['storyTitle'] != '' and (ref_t and (ref_t in v2.get('storyTitle', '') or normalize(v2['storyTitle']) in ref_t))):
                    existing = k2
                    
            if not any(normalize(existing or {}).get(('storyTitle')) == ref_t for existing in matched_examples):  
                matched_examples[match_key] = {
                    'storyTitle': row.get('storyTitle',''),
                    'Category': '', 
                    'Type': '',
                    'Controversial': cr_labels['Controversial'],
                    'Relevant': cr_labels['Relevant'],
                    'fulltext': (row.get('fullText') or '')[:800],
                    'source': 'releases_labeling'
                }

print(f"\nMatched {len(matched_examples)} reference examples with fullText for analysis")

# ============================================================  
# STEP 2: Analyze labeled examples to LEARN patterns 
# ============================================================  
print("\n" + "="*70)  
print("ANALYZING PATTERNS FROM LABELED EXAMPLES")
print("="*70)

def extract_keywords(text, n=15):
    """Extract unique content words from text."""
    stop = {'the','a','an','this','that','it','is','are','was','were',
            'be','been','being','have','has','had','to','for','of','in','on'} 
    if not text: return []  
    words = re.findall(r'[a-z]{3,}', (text or '').lower())
    return list(set(w for w in words if w not in stop))[:n]

def has_phrase(text phrases):  
    t = (text or '').lower()
    return any(p.lower().replace(' ', '') in t.replace(' ', '') for p in phrases)

# Categorize matched examples by their labels
from collections import defaultdict
cat_items = defaultdict(list)  # category -> [(title, keyword)]  
typ_items = defaultdict(list)   # type -> [(cat, title)]
cont_y_items = []               # items Controversial=Y (with keywords for analysis)  
rel_y_items = []                # items Relevant=Y (with keywords for analysis)

for match_key, data in matched_examples.items():
    cat = (data.get('Category') or '').strip() 
    typ = (data.get('Type') or '').strip()  
    contr = (data.get('Controversial') or 'N').strip().upper()  
    rel = (data.get('Relevant') or 'N').strip().upper()
    kw = extract_keywords(data.get('fulltext', ''), 20)  
    
    if cat: 
        cat_items[cat].append({'title': data['storyTitle'][:60], 'keywords': kw})
    if typ:  
        typ_items[typ].append({'category': cat or '', 'title': data['storyTitle'][:60], 'keywords': kw})
        
    # Controversial items to analyze why marked Y vs N
    if contr == 'Y':  
        cont_y_items.append({
            'title': data['storyTitle'][:80],
            'category': cat,  
            'relevant': rel,
            'keywords': kw,
            'fulltext_excerpt': (data.get('fulltext', '') or '')[:200]
        })
    
    if rel == 'Y':
        rel_y_items.append({
            'title': data['storyTitle'][:80],
            'controversial': contr,
            'keywords': kw,
            'fulltext_excerpt': (data.get('fulltext', '') or '')[:200]
        })

# Print analysis results  
print("\n📂 Category Pattern Analysis:")  
for cat, items in sorted(cat_items.items(), key=lambda x: -len(x[1])):
    all_kw = []
    for item in items:  
        all_kw.extend(item['keywords']) 
    top_kw = extract_keywords(' '.join(all_kw), 15) if all_kw else []
    
    print(f"\nCategory '{cat}' ({len(items)} items):")
    
    # Show example titles from this category
    for ex in items[:3]:
        print(f"  - {ex['title']}...")

print("\n📂 Type Pattern Analysis:")  
for typ, items in sorted(typ_items.items(), key=lambda x: -len(x[1])):
    top_kw = []
    
    # Extract keywords across all type examples  
    for item in items:
        top_kw.extend(item['keywords'])