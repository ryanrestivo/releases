#!/usr/bin/env python3
"""
COMPLETE LABELING PIPELINE FOR NYT PRESS RELEASES
===================================================
Goal: Classify ALL 3,390 rows using learned taxonomy from two reference CSVs.
TAXONOMY (from ref files - DO NOT MODIFY):
- Category: staff_announcement|company_update|feature|statement|fact_check|award  
- Type: newsroom|audio|opinion|games|the_athletic|cooking|other/don't_know
- Controversial/Relevant: Y/N (from releases_labeling.csv)
"""
import csv
import re
from collections import defaultdict, OrderedDict

def normalize(s):
    if not s: return ''
    return re.sub(r'[\s\W]+', ' ', str(s).lower().strip()).strip()

# ============================================================
# STEP 1: Load ALL reference data from both CSVs (THE "TRUTH")
# ============================================================
print("="*70)
print("LOADING REFERENCE DATA FROM BOTH CSVs\n" + "="*70)

REF_CAT_TYPE = {}  # norm_title -> {Category, Type}  
with open('/Users/ryanrestivo/Downloads/labeling_test.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, skipinitialspace=True)
    for row in reader:
        title = (row.get('Title') or '').strip()
        if not title: continue
        norm = normalize(title)
        REF_CAT_TYPE[norm] = {
            'Category': (row.get('Category') or '').strip().lower(),
            'Type': (row.get('Type') or '').strip().lower(),
            'RawTitle': title  
        }

REF_CONT_REL = {}  # norm_title -> {Controversial, Relevant} 
with open('/Users/ryanrestivo/Downloads/releases_labeling.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, skipinitialspace=True)
    for row in reader:
        title = (row.get('Title') or '').strip()  
        if not title: continue
        norm = normalize(title)
        cont = (row.get('Controversial (Y/N)') or '').strip().upper()
        rel = (row.get('Relevant (Y/N)') or '').strip().upper()
        cont = 'N' if not cont else cont  
        rel = 'N' if not rel else rel  
        REF_CONT_REL[norm] = {
            'Controversial': cont,
            'Relevant': rel,
            'RawTitle': title
        }

# Load main CSV (the rows to label)
with open('/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv', encoding='utf-8-sig') as f:
    MAIN_ROWS = list(csv.DictReader(f))

print(f"\n✅ {len(REF_CAT_TYPE)} Category/Type refs from labeling_test.csv")
print(f"✅ {len(REF_CONT_REL)} Controversial/Relevant refs from releases_labeling.csv")
print(f"✅ {len(MAIN_ROWS)} rows to label in main CSV")

# ============================================================
# STEP 2: Analyze labeled examples' fullText to UNDERSTAND LABELING PATTERNS
# ============================================================ 
print("\n" + "="*70)  
print("STEP 2: ANALYZING FULLTEXT OF LABELED EXAMPLES TO LEARN PATTERNS")
print("="*70)

# Map reference items to their fullText in main CSV to extract patterns
def find_match_in_main(title_norm):
    """Find row in MAIN_ROWS matching this normalized title."""
    for row in MAIN_ROWS:
        story = normalize(row.get('storyTitle', ''))
        if story == title_norm or (title_norm and (title_norm in story or story in title_norm)):
            return row  
    return None

# Analyze labeled examples' fullText to understand WHY each was assigned its label
category_examples = defaultdict(list)  # category -> [(fulltext_excerpt, raw_title)] 
type_examples = defaultdict(list)      # type -> [(fulltext_excerpt, category)]
controversial_yes_items = []            # items marked Y as controversial (title + fulltext)
relevant_yes_items = []                 # items marked Y as relevant  
matched_count = 0

# Match Category/Type reference examples to main CSV and analyze their fullText
print("\nAnalyzing categorized examples from labeling_test.csv:")
for ref_norm, ref_labels in REF_CAT_TYPE.items():
    row_match = find_match_in_main(ref_norm) or None  
    if not row_match: continue
    
    fulltext = (row_match.get('fullText') or '')[:500]  # First 500 chars of fullText for analysis
    cat_val = ref_labels['Category']
    typ_val = ref_labels['Type']
    
    category_examples[cat_val].append({
        'title': ref_labels['RawTitle'],
        'fulltext_important_words': extract_keywords(fulltext),  # Key content words
        'excerpt': fulltext[:300]
    })
    type_examples[typ_val].append({  
        'category': cat_val,
        'title': ref_labels['RawTitle'],
        'fulltext_key_info': extract_keywords(fulltext) 
    })
    matched_count += 1

# Match Controversial/Relevant reference examples to main CSV  
print(f"\nAnalyzing {matched_count} labeled examples with fullText...")
for ref_norm, ref_labels in REF_CONT_REL.items():
    row_match = find_match_in_main(ref_norm) or None
    if not row_match: continue
    
    fulltext = (row_match.get('fullText') or '')[:500]
    
    if ref_labels['Controversial'] == 'Y':  
        controversial_yes_items.append({
            'title': ref_labels['RawTitle'],
            'relevant': ref_labels['Relevant'],  
            'fulltext_excerpt': fulltext[:300],
            'key_indicators': find_controversial_indicators(fulltext)
        })
    
    if ref_labels['Relevant'] == 'Y':
        relevant_yes_items.append({
            'title': ref_labels['RawTitle'],
            'controversial': ref_labels['Controversial'],
            'fulltext_excerpt': fulltext[:300],  
            'key_indicators': find_relevance_indicators(fulltext)
        })

def extract_keywords(text):
    """Extract important content words from text for pattern analysis."""
    if not text: return []
    common_stop = {'the', 'a', 'an', 'this', 'that', 'it', 'is', 'are', 'was', 'were', 
                   'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
                   'to', 'for', 'of', 'in', 'on', 'at', 'by', 'from', 'and', 'or', 'but',
                   'as', 'with', 'who', 'which', 'what', 'when', 'where', 'how'}
    words = re.findall(r"[a-z]{3,}", (text or '').lower())
    return list(set(w for w in words if w not in common_stop))[:15]

def find_controversial_indicators(text):
    """Find text features that indicate controversial content."""
    lower_text = (text or '').lower().replace('  ', ' ')  
    indicators = []
    
    # Check for legal/lawsuit/sue language patterns  
    if any(kw in lower_text for kw in ['laws', 'sues', 'legislat', 'legal']):
        indicators.append('legal_action')
    if any(kw in lower_text for kw in ['threatens', 'threatening', 'attacking']):
        indicators.append('threat_language')  
    if any(kw in lower_text for kw in ['court', 'lawsuit filed', 'litigation']):
        indicators.append('court_reference')
        
    return indicators if indicators else ['no_controversial_signals']

def find_relevance_indicators(text):
    """Find text features that indicate high relevance content."""
    lower_text = (text or '').lower().replace('  ', ' ')
    indicators = []  
    
    if any(kw in lower_text for kw in ['strategic', 'ambition', 'vision', 'future of journalism',
                                       'mission', 'innovation in']:
        indicators.append('strategic_content')
    
    if any(kw in lower_text for kw in ['ceo', 'president', 'chief executive', 'publisher', 
                                       'new york timestime':  # Catch leadership signals  
        indicators.append('leadership_reference')