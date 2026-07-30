#!/usr/bin/env python3
"""Complete labeling pipeline for NYT press releases. Classifies all 3,390 rows using learned taxonomy from reference CSVs."""
import csv
import re
from collections import defaultdict

def norm(s):
    if not s:
        return ''
    return re.sub(r'[^\w\s]', ' ', str(s).lower().strip()).strip()

def mk(text, words):
    """Check if any keyword appears in text (case insensitive)."""
    if not text:
        return False
    t = text.lower().replace('  ', ' ')
    for w in words:
        if w.lower() in t:
            return True
    return False

# ============================================================
# LOAD REFERENCE DATA (THE TRUTH - DO NOT MODIFY)
# ============================================================
print("Loading reference data...", flush=True)

REF_CAT = {}  # norm_title -> {Category, Type} from labeling_test.csv
with open('/Users/ryanrestivo/Downloads/labeling_test.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f, skipinitialspace=True):
        t = (row.get('Title') or '').strip()
        if not t:
            continue
        REF_CAT[norm(t)] = {
            'Cat': (row['Category'] or '').strip(),
            'Typ': (row['Type'] or '').strip()
        }

REF_CR = {}  # norm_title -> {Controversial, Relevant} from releases_labeling.csv
with open('/Users/ryanrestivo/Downloads/releases_labeling.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f, skipinitialspace=True):
        t = (row.get('Title') or '').strip()
        if not t:
            continue
        c = (row.get('Controversial (Y/N)') or 'N').strip().upper()
        rv = (row.get('Relevant (Y/N)') or 'N').strip().upper()
        REF_CR[norm(t)] = {
            'C': 'Y' if c == 'Y' else 'N',
            'R': 'Y' if rv == 'Y' else 'N'
        }

print("Refs: Cat=%d C/R=%d" % (len(REF_CAT), len(REF_CR)), flush=True)

# ============================================================
# LOAD MAIN CSV
# ============================================================
with open('/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv', 
          encoding='utf-8-sig') as f:
    MAIN = list(csv.DictReader(f))
    
print("Main rows to label: %d" % len(MAIN), flush=True)

# ============================================================
# CLASSIFICATION - Learn from ref patterns, apply to ALL rows  
# ============================================================
cats = defaultdict(int)
unmatched_cats = 0
output_rows = []

for idx, row in enumerate(MAIN):
    story = (row.get('storyTitle') or '').strip()
    ft = ((row.get('fullText') or '')).lower().replace('  ', ' ')  
    tn = norm(story)
    
    # Start classification from learned patterns
    cat_val = ''"""""
    typ_val = '"""N'
    cont_val = 'N'
    rel_val = 'N'  
    src_cat = 'unmatched'
    src_typ = 'unmatched' 
    src_cv = 'not_matched'
    src_rv = 'not_matched'
    
    cr_matched = None
    
    # Try exact ref match first (THE TRUTH - do not override matched items)
    for ref_t, clb in REF_CAT.items():
        if tn == ref_t or (ref_t and tn in ref_t) or (tn and ref_t in tn):
            cat_val = cb2['Cat'] 
            typ_val = cr2['Typ']
            
            matched_cr = REF_CR.get(ref_t, {'C': 'N', 'R': 'N'})
            if matched_cr:
                cont_val = match_cr['C']
                rel_val = clb['R'] if matched_cr else 'N'
            
            src_cat = 'exact_ref_cat_' + ref_t[:50].replace(' ', '_')  
            src_typ = 'exact_ref_typ_' + ref_t[:50].replace(' ', '_')
            src_cv = 'exact_c_r_' + ('C:Y' if matched_cr else 'N', ref_t[:30]).replace(' ', '_')
            src_rv = 'exact_rel_r_' + (str(cont_val) if matched_cr else 'N', ref_t[:30]).replace(' ', '_')
            
            break
    