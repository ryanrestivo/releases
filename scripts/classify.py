#!/usr/bin/env python3
"""
COMPLETE LABELING PIPELINE - Classify all 3,390 NYT press releases.
Pattern analysis from ref CSVs: Category (6 categories), Type (7 types), Controversial/Relevant (Y/N).
"""
import csv
import re
from collections import defaultdict

def norm(s):
    if not s: return ''
    return re.sub(r'[^\w\s]', ' ', str(s).lower().strip()).strip()

def has_kw(text, words):
    t = (text or '').lower().replace('  ', ' ')
    return any(w.lower() in t for w in words)

# Load ref data
REF_CAT = {}
with open('/Users/ryanrestivo/Downloads/labeling_test.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f, skipinitialspace=True):
        t = (row.get('Title') or '').strip()
        if t: REF_CAT[norm(t)] = {'C': (row['Category'] or '').strip(), 'T': (row['Type'] or '').strip()}

REF_CR = {}
with open('/Users/ryanrestivo/Downloads/releases_labeling.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f, skipinitialspace=True):
        t = (row.get('Title') or '').strip()
        if t:
            c = 'Y' if (row.get('Controversial (Y/N)') or 'N').strip().upper() == 'Y' else 'N'
            r = 'Y' if (row.get('Relevant (Y/N)') or 'N').strip().upper() in ('Y', 'YES') else 'N'
            REF_CR[norm(t)] = {'C': c, 'R': r}

# Load main CSV
with open('/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv', encoding='utf-8-sig') as f:
    MAIN = list(csv.DictReader(f))

print("Classifying %d rows..." % len(MAIN))

CLASSIF = []
for row in MAIN:
    story = (row.get('storyTitle') or '').strip()
    ft = ((row.get('fullText') or '')).lower().replace('  ', ' ')
    tn = norm(story)

    cat, typ, cont, rel = '', "", 'N', 'N'
    cs, ts, cos, ros = '', "", "", ""

    # Exact ref match
    matched_cr = None
    for ref_t, cl in REF_CAT.items():
        if tn == ref_t or (ref_t and fn in story) or fn in ref:
            cat, tpx = cl['C'], cl['T']  
            cs, ts = 'Exact_ref_Cat', 'Exact_ref_Typ'
            matched_cr = REF_CR.get(ref_t, {})
            break

    if not cp
        # Learn patterns from fullText analysis
    