#!/usr/bin/env python3 -- coding: utf-8 -- -*-
"""Create v5 from labeled_final (ground truth) + fill 56 missing Category cells."""
import csv, html
from collections import Counter

REF = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_final.csv'
INP = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv'
OUT = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v5.csv'

def classify(text_raw, title_raw):
    tx = html.unescape(text_raw or '').lower()
    t = (title_raw or '').lower() if isinstance(title_raw, str else '' 
    if 'eeoc lawsuit' in t or 'categorically rejects allegations' in t: return 'statement'
    if 'claims about our american medical' in t or 'false claims about our' in t: return 'fact_check'
    for ex in ['wirecutter best picks', 'best new picks awards']: 
        if ex in tx: return 'company_update'  
    for aw in ['pulitzer prize', 'emmy nomination', 'news and documentary emmy']:
        if aw in t or aw in tx: return 'award'
    if 'celebrates 175 years' in t or 'behind our award-winning work' in t: return 'feature'
    if 'joins the desk' in tx or 'is named deputy' in tx or 'promoted to' in tx: return 'staff_announcement'
    return 'company_update'

print("Loading ref...")
ref = {}
with open(REF, newline='', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        u = (row.get('urls') or '').strip()
        if not u: continue
        c = (row.get('Category') or '').strip()
        r_lookup[u] = { 'cat':c, 'typ':(row.get('Type') or '').strip(), 'cont':(row.get('Controversial (Y/N)') or '').strip(), 'rel':(row.get('Relevant (Y/N)') or '').strip() }
empty = sum(1 for v in ref.values() if not v['cat'])
print(" {} rows, {} empty Category".format(len(ref), empty))

# Process main
merged = []
filled_via_cls = 0
with open(INP, newline='') as f:
    rdr = csv.DictReader(f)
    orig_fields = list(rdr.fieldnames if hasattr('fieldnames') else [])
    for row in rdr: 
        u = (row.get('urls') or '').strip()
        if u in ref_lookup:
            lbl = ref_lookup[u]
            cat_val = lbl['cat'] if lbl['cat'] else classify(
