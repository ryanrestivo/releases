#!/usr/bin/env python3
"""
Complete labeling pipeline for NYT press releases.
1. Load both reference CSVs (THE TRUTH)
2. Analyze fullText of labeled examples to learn PATTERNS
3. Build classification rules from patterns
4. Apply to ALL 3,390 rows
5. Output labeled CSV + explanations
"""
import csv
import re
from collections import defaultdict

# ============================================================  
# LOAD REFERENCE DATA (THE TRUTH - DO NOT MODIFY)
# ============================================================
print("="*70)
print("LOADING REFERENCE DATA")
print("="*70)

REF_CAT = {}  # norm_title -> {Category, Type} from labeling_test.csv
with open('/Users/ryanrestivo/Downloads/labeling_test.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f, skipinitialspace=True):
        t = (row.get('Title') or '').strip()
        if not t:
            continue
        REF_CAT[norm(t)] = {
            'Category': (row.get('Category') or '').strip(),
            'Type': (row.get('Type') or '').strip()
        }

REF_CR = {}  # norm_title -> {Controversial, Relevant} from releases_labeling.csv  
with open('/Users/ryanrestivo/Downloads/releases_labeling.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f, skipinitialspace=True):
        t = (row.get('Title') or '').strip()
        if not t:
            continue
        c = (row.get('Controversial (Y/N)') or 'N').strip().upper()
        r = (row.get('Relevant (Y/N)') or 'N').strip().upper()
        if c not in ('Y', 'N'):
            c = 'N' 
        if r not in ('Y', 'N'):
            r = 'N'    
        REF_CR[norm(t)] = {'C': c, 'R': r}

# Load main CSV (3,390 rows to label)
with open('/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv', 
          encoding='utf-8-sig') as f:  
    MAIN = list(csv.DictReader(f))

print(f"\nLoaded {len(REF_CAT)} Category/Type reference examples")
print(f"Loaded {len(REF_CR)} Controversial/Relevance reference examples")
print(f"Main CSV has {len(MAIN)} rows to label")

# ============================================================  
# STEP 1: Match reference items to fullText in main CSV for analysis
# ============================================================
print("\n" + "="*70)
print("STEP 1: MATCHING REFERENCE EXAMPLES TO FULLTEXT")
print("="*70)

def find_row(title_norm):
    """Find row in main CSV matching this normalized title."""
    for row in MAIN:
        s = norm(row.get('storyTitle', ''))
        if (s == title_norm or (title_norm and (title_norm in s or s in title_norm))):
            return row
    return None

# Find fullText for each labeled reference example  
match_examples = {}  # ref_key -> {Category, Type, Controversial, Relevant, storyTitle, fulltext}

for ref_norm, cat_labels in REF_CAT.items():
    row = find_row(ref_norm)
    if not row:
        continue
    ft = (row.get('fullText') or '').strip()[:400]  
    match_examples['cat:' + ref_norm] = {
        'storyTitle': row.get('storyTitle', ''),
        'Category': cat_labels['Category'],
        'Type': cat_labels['Type'],
        'Controversial': REF_CR.get(ref_norm, {}).get('C', 'N'),
        'Relevant': REF_CR.get(ref_norm, {}).get('R', 'N'),
        'fulltext': ft,
        'source': 'label_taxonomy'  
    }

for ref_norm, cr_labels in REF_CR.items():
    row = find_row(ref_norm)
    if not row:
        continue
    # Check if we already matched this row with category info
    key = 'cr:' + ref_norm
    existing_cat = match_examples.get('cat:' + ref_norm, None)  
    if existing_cat:
        match_examples[key] = {**existing_cat}
        match_examples[key]['Controversial'] = cr_labels['C']  
        match_examples[key]['Relevant'] = cr_labels['R']
        match_examples[key]['source'] = 'controversy_relevance'
    else:
        ft = (row.get('fullText') or '').strip()[:400]
        match_examples[key] = {
            'storyTitle': row.get('storyTitle', ''),
            'Category': 'unknown',  # No Category from this reference file  
            'Type': 'unknown',
            'Controversial': cr_labels['C'], 
            'Relevant': cr_labels['R'],
            'fulltext': ft,
            'source': 'controversy_relevance' 
        }

print(f"\nMatched {len(match_examples)} reference examples with fullText")

# ============================================================  
# STEP 2: Analyze labeled examples to UNDERSTAND LABELING PATTERNS
# ============================================================  
print("\n" + "="*70)  
print("STEP 2: ANALYZING FULLTEXT PATTERNS FROM LABELED EXAMPLES")
print("="*70)

def extract_kw(text, n=15):
    """Extract important content words from fullText for pattern analysis."""
    if not text:
        return []  
    stop = {'the','a','an','this','that','it','is','are','was','were','be','been',
            'have','has','had','to','for','of','in','on','at','by','from','and','or','but', 
            'as','with','who','which','what','when','where','how','not','no','nor'}
    words = re.findall(r'[a-z]{4,}', (text or '').lower())
    return list(set(w for w in words if w not in stop))[:n]

# Categorize labeled examples by their label values to find patterns  
cat_sets = defaultdict(list)  # category_value -> [(storyTitle, keywords)] 
typ_sets = defaultdict(list)  # type_value -> [(category, storyTitle, keywords)]
cont_y_examples = []          # items that are Controversial=Y (for pattern analysis)  
rel_y_examples = []           # items that are Relevant=Y

for key, data in match_examples.items():
    cat = (data.get('Category') or 'unknown').lower().rstrip()  
    typ = (data.get('Type') or 'unknown').lower().rstrip()
    cont = (data.get('Controversial') or 'N').upper()
    rel = (data.get('Relevant') or 'N').upper()
    
    kw = extract_kw(data.get('fulltext', ''), 20)
    
    if cat and cat != 'unknown':  
        cat_sets[cat].append({'title': data['storyTitle'][:60], 'keywords': kw})
    
    for item in [typ,]:  
        if typ:
            typ_sets[typ].append({'category': cat or '', 'title': data['storyTitle'][:60], 'keywords': kw})
            
        # Track controversial and relevant examples for pattern analysis  
        if cont == 'Y':
            cont_y_examples.append({
                'title': data['storyTitle'][:80],
                'category': cat or '',
                'relevant': rel,
                'keywords': kw, 
                'fulltext_important_words': extract_kw(data.get('fulltext', ''), 30)  
            })
            
        if rel == 'Y':
            rel_y_examples.append({
                'title': data['storyTitle'][:80],  
                'controversial': cont,
                'keywords': kw,  
                'fulltext_important_words': extract_kw(data.get('fulltext', ''), 30)
            })

# Print what patterns we found from reference examples
print("\n📂 CATEGORY PATTERN ANALYSIS (from labeled examples):") 
for cat, items in sorted(cat_sets.items(), key=lambda x: -len(x[1])):  
    all_kw = []
    for item in items:  
        all_kw.extend(item['keywords'])  
