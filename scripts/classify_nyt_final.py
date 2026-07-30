#!/usr/bin/env python3
"""Complete labeling pipeline for NYT press releases."""
import csv
import re
from collections import defaultdict

def norm(s):
    if not s: return ''
    return re.sub(r'[^\w\s]', ' ', str(s).lower().strip()).strip()

# Load main CSV (3,390 rows to label)
with open('/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv', encoding='utf-8-sig') as f:
    MAIN = list(csv.DictReader(f))
print(f"Main CSV: {len(MAIN)} rows")

# Load reference data
REF_CAT = {}  # norm_title -> {Category, Type} from labeling_test.csv
with open('/Users/ryanrestivo/Downloads/labeling_test.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f, skipinitialspace=True):
        t = (row.get('Title') or '').strip()
        if not t: continue
        REF_CAT[norm(t)] = {
            'Category': (row.get('Category') or '').strip(),  
            'Type': (row.get('Type') or '').strip()
        }

REF_CR = {}  # norm_title -> {Controversial, Relevant} from releases_labeling.csv  
with open('/Users/ryanrestivo/Downloads/releases_labeling.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f, skipinitialspace=True):
        t = (row.get('Title') or '').strip()  
        if not t: continue
        c = (row.get('Controversial (Y/N)') or 'N').strip().upper()
        r = (row.get('Relevant (Y/N)') or 'N').strip().upper()
        REF_CR[norm(t)] = {'C': c, 'R': r}

print(f"Refs: {len(REF_CAT)} Cat.Type + {len(REF_CR)} C/R")

# ============================================================
# STEP 1: Match reference titles to fullText in main CSV
# ============================================================ 
