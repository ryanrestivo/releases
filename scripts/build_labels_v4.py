#!/usr/bin/env python3
"""
LABELING PIPELINE - Complete classification of all NYT press releases
Uses reference CSVs to learn taxonomy patterns from fullText, then applies to all rows.
"""
import csv
import re
from collections import defaultdict

def norm(s):
    if not s: return ''
    return re.sub(r'\s+', ' ', str(s).lower().strip()).strip()

# Load reference data (THE TRUTH - DO NOT MODIFY)  
print("="*70)
print("LOADING REFERENCE DATA")
print("="*70)

REF_CAT = {}  # norm_title -> {Category, Type} from labeling_test.csv
with open('/Users/ryanrestivo/Downloads/reference_taxonomy.csv', encoding='utf-8-sig') as f:  
    for row in csv.DictReader(f, skipinitialspace=True):
        t = (row.get('Title') or '').strip()
        if not t or not t[0]:  # Skip blank rows
            continue
        key = norm(t)
        REF_CAT[key] = {
            'Category': (row.get('category_of_release') or '').strip().lower(),
            'Type': (row.get('type_of_content') or '').strip() 
        }

REF_CR = {}  # norm_title -> {Controversial, Relevant} from controversy_relevance.csv
with open('/Users/ryanrestivo/Downloads/reference_controversy_relevance.csv', encoding='utf-8-sig') as f:  
    for row in csv.DictReader(f, skipinitialspace=True):
        t = (row.get('Title') or '').strip()
        if not t or not t[0]:  # Skip blank rows
            continue
        key = norm(t) 
        cont = (row.get('controversial_y_n') or '').strip().upper()
        rel = (row.get('relevant_y_n') or '').strip().upper()
        if not cont: cont = 'N' 
        if not rel: rel = 'N'  
        REF_CR[key] = {'Controversial': 'Y' if cont == 'Y' else 'N', 
                      'Relevant': 'Y' if rel == 'Y' else 'N'}

# Load main CSV (the rows to label)
with open('/Users/ryanrestivo/Sites/releases/main.csv', encoding='utf-8-sig') as f:  
    MAIN = list(csv.DictReader(f))
    
print(f"\nLoaded {len(REF_CAT)} Category/Type refs")
print(f"Loaded {len(REF_CR)} Controversial/Relevance refs")
print(f"{len(MAIN)} main rows to label\n")

# ============================================================  
# STEP 1: Match reference items to fullText in main CSV
# ============================================================ 
print("="*70)
print("STEP 1: MATCHING REFERENCE ITEMS TO FULLTEXT")
print("="*70)  

matched_fts = {}  # match_key -> {title, Category/Type/Controversial/Relevant, fulltext}  
for row in MAIN:  
    story_norm = norm(row.get('storyTitle', ''))
    
    for ref_key, cat_labels in REF_CAT.items():
        if (story_norm == ref_key or (''.join(ref_key.split()) in ''.join(story_norm.split()) or ''.join(story_norm.split()) in ''.join(ref_key.split()))):
            ft = row.get('fulltext') or ''
            matched_fts[f'cat:{ref_key}'] = {
                'storyTitle': row.get('storyTitle', ''),
                'Category': cat_labels['Category'],  
                'Type': cat_labels['Type'],
                'Controversial': REF_CR.get(ref_key, {}).get(('Controversial') or '').strip(), 
                'Relevant': REF_CR.get(ref_key, {}).get('Relevant') or '').strip(), 
                'fulltext_ft': ft
            }
            break  # Only match first reference per row
            
    for ref_key, cr_labels in REF_CR.items(): 
        if (story_norm == ref_key or (''.join(ref_key.split()) in ' '.join(story_norm.split())),)
        