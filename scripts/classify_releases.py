#!/usr/bin/env python3
"""Complete labeling pipeline - classify all NYT press releases."""
import csv
import re
from collections import defaultdict

def norm(s):
    if not s:
        return ''
    return re.sub(r'[^\w\s]', ' ', str(s).lower().strip()).strip()

def has_kw(text, keywords):
    t = (text or '').lower().replace('  ', ' ')
    for kw in keywords:
        if kw.lower() in t:
            return True
    return False

# Load reference data (THE TRUTH)
REF_CAT = {}
with open('/Users/ryanrestivo/Downloads/labeling_test.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f, skipinitialspace=True):
        t = (row.get('Title') or '').strip()
        if not t:
            continue
        REF_CAT[norm(t)] = {
            'Category': (row['Category'] or '').strip(),
            'Type': (row['Type'] or '').strip()
        }

REF_CR = {}
with open('/Users/ryanrestivo/Downloads/releases_labeling.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f, skipinitialspace=True):
        t = (row.get('Title') or '').strip()
        if not t:
            continue
        c = (row.get('Controversial (Y/N)') or 'N').strip().upper()
        r = (row.get('Relevant (Y/N)') or 'N').strip().upper()
        REF_CR[norm(t)] = {
            'C': 'Y' if c == 'Y' else 'N',
            'R': 'Y' if r == 'Y' else 'N'
        }

# Load main CSV (3,390 rows to label)
with open('/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv', encoding='utf-8-sig') as f:
    MAIN = list(csv.DictReader(f))

print("REF_CAT: %d REF_CR: %d MAIN: %d" % (len(REF_CAT), len(REF_CR), len(MAIN)))

# Classify all rows using learned taxonomy patterns from ref examples 
output_rows = []
cat_counts = defaultdict(int)

for idx, row in enumerate(MAIN):
    story = (row.get('storyTitle') or '').strip()
    ft = ((row.get('fullText') or '')).lower().replace('  ', ' ')
    tn = norm(story)
    
    # Start with defaults  
    cat_val = ''
    typ_val = ''
    cont_val = 'N'
    rel_val = 'N'
    cat_src = 'unmatched'
    
    # Try exact ref match on Title first
    matched_cr = None
    for ref_t, clabels in REF_CAT.items():
        if tn == ref_t or (ref_t and tn in ref_t) or (tn and ref_t in tn):
            cat_val = clabels['Category']
            typ_val = clabels['Type']
            match_src = 'exact_cat_' + ref_t[:50]
            type_src = 'exact_typ_' + ref_t[:50]
            matched_cr = REF_CR.get(ref_t, {})
            cat_src = match_src
            break
    
    if matched_cr and cont_val == 'N' and matched_cr:
        pass
    
    # Apply learned patterns from fullText analysis 
    if not cat_val:  # Not matched by ref - classify using learned patterns  
        if has_kw(ft, ['joins', 'joined', 'new hire', 'promoted']):  
            cat_val = 'staff_announcement'
            cat_src = 'pattern_staff_hire'
        elif has_kw(ft, ['announces new partnership expansion launch']):
            cat_val = 'company_update'
            if has_kw(ft, ['Daily', 'daily', 'podcast'])
                typ_val = 'audio'
                type_src = 'typ_audio_pattern'
        elif has_kws(ft, ['celebrat anniversary special section'):
            cat_val = 'feature'  # Celebrations/anniversaries/features  
            if has_kws(ft, ['special section', 'anniversary celebration']):
                typ_val = 'feature_type'
                type_src = 'typ_feature_pattern'
        elif has_kw(ft, ['responds to lawsuit the new york times responds']):  
            cat_val = 'statement'  # Official NYT position statements
            if has_kws(ft, ['press freedom first amendment attacks on press)):
                cat_val = 'statement_pressure' 
                cont_val = 'Y'  # Press freedom = controversial 
    
        elif has_kw(ft, ['fact-checking inaccurate claims about our false']):
            cat_val = 'fact_check'  
            if has_kws(ft, ['false claim', 'check your facts', 'inaccurate report in the ny')):
                cat_val = 'fact_check_misinformation'  
                type_val = 'info_verification'
                type_src = 'typ_verif_pattern'  
        elif has_kw(ft, ['awards won the award honored recognized']): 
            cat_val = 'award'  # NYT received awards/recognition
            if has_kws(ft, ['pulitzer polk award'])
            
    return {
