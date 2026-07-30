#!/usr/bin/env python3
"""
LABEL NYT PRESS RELEASES - COMPLETE PIPELINE
================================================
Goals:
1. Load BOTH reference CSVs (labeling_test.csv + releases_labeling.csv)  
2. Read EACH labeled example's fullText from main CSV to UNDERSTAND WHY labels were assigned
3. Extract labeling RULES from fullText analysis of labeled examples
4. Apply learned taxonomy to ALL 3,390+ remaining rows
5. Output labeled CSV with explanations
6. Support step-by-step commit batches

TAXONOMY (from reference CSVs - DO NOT CHANGE):
Category values: staff_announcement, company_update, feature, statement, fact_check, award  
Type values: newsroom, audio, opinion, games, the_athletic, cooking, other_dont_know
Controversial: Y or N (based on litigation/legal/press_freedom signals)  
Relevant: Y or N (based on strategic/vision/mission language)
"""
import csv
import re
from collections import defaultdict, OrderedDict

# ============================================================
# STEP 1: LOAD REFERENCE CSVs (THE "TRUTH" - DO NOT MODIFY VALUES)
# ============================================================
print("="*70)
print("STEP 1: LOADING REFERENCE CSVs")  
print("="*70)

REF_CAT_TYPE = {}  # normalized_title -> {Category, Type} from labeling_test.csv  
with open('/Users/ryanrestivo/Downloads/reference_label_taxonomy.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        title = (row.get('Title') or '').strip()
        if not title or not title[0]:
            continue
        cat_key = re.sub(r"[^a-z0-9\s']", '', normalize_title(title)).lower()
        REF_CAT_TYPE[cat_key] = {
            'title': title,  
            'Category': (row.get('category_of_release') or '').strip() or 'unlabeled',
            'Type': (row.get('type_of_content') or '').strip() or 'unknown'
        }

REF_CONTREL = {}  # normalized_title -> {Controversial, Relevant} from controversy_relevance.csv
with open('/Users/ryanrestivo/Downloads/reference_controversy_relevance.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f) 
    for row in reader:
        title = (row.get('Title') or '').strip()
        if not title or not title[0]:
            continue
        cat_key = re.sub(r"[^a-z0-9\s']", '', normalize_title(title)).lower()  
        REF_CONTREL[cat_key] = {
            'title': title,
            'Controversial': (row.get('controversial_y_n') or '').strip().upper() or 'N',
            'Relevant': (row.get('relevant_y_n') or '').strip().upper() or 'N'
        }

# Load main CSV (the 3,390+ rows to label)
with open('/Users/ryanrestivo/Sites/releases/main.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    main_rows = list(reader)
    
print(f"Loaded {len(REF_CAT_TYPE)} Category-Type reference examples")
print(f"Loaded {len(REF_CONTREL)} Controversial-Relevance reference examples")
print(f"Main CSV has {len(main_rows)} rows to label\n")

# ============================================================
# STEP 2: ANALYZE FULLTEXT OF LABELED EXAMPLES TO LEARN LABELING RULES
# ============================================================ 
print("="*70)
print("STEP 2: LEARNING LABELING PATTERNS FROM FULLTEXT ANALYSIS")
print("="*70)

def normalize_title(s):  
    """Normalize titles for comparison - lowercases, removes punctuation."""
    if not s: return ''
    s = re.sub(r"[^a-z0-9\s']", '', str(s).lower().strip())
    s = re.sub(r"\s+", ' ', s).strip()
    return s

# Match reference items to their fullText in main CSV 
reference_fulltexts = {}  # ref_title -> {"fulltext": "...", "labels": {...}}
matched_titles = set()   # Track which titles we've found with fullText

for row in main_rows:
    story_norm = normalize_title(row.get('storyTitle', ''))
    if not story_norm: continue
    
    for cat_key, ref_labels in REF_CAT_TYPE.items():  
        norm_ref = normalize_title(ref_labels['title'])
        # Check for match using multiple strategies
        is_match = (cat_key == story_norm or norm_ref == story_norm) \
                    or (cat_key and (cat_key in story_norm or story_norm in cat_key)) \
                    or (norm_ref and (norm_ref in story_norm or story_norm in norm_ref))
        
        fulltext = (row.get('fullText') or '').strip()  
        if is_match and not REF_CAT_TYPE[cat_key]['title'] in matched_titles:
            reference_fulltexts[f'CAT:{REF_CAT_TYPE[cat_key]["title"][:40]}'] = {
                'Category': ref_labels['Category'],
                'Type': ref_labels['Type'],
                'fulltext': fulltext,
                'storyTitle': ref_labels['title'],
                'source': 'label_taxonomy'  
            }
            matched_titles.add(REF_CAT_TYPE[cat_key]['title'])
            break
    
    for cr_key, ref_labels in REF_CONTREL.items():
        norm_ref = normalize_title(ref_labels['title'])
        # Check for match using multiple strategies
        is_match = (cr_key == story_norm or norm_ref == story_norm) \
                    or (cr_key and (cr_key in story_norm or story_norm in cr_key)) \
                    or (norm_ref and (norm_ref in story_norm or story_norm in norm_ref))
                
        fulltext = (row.get('fullText') or '').strip()  
        if is_match and not REF_CONTREL[cr_key]['title'] in matched_titles:
            reference_fulltexts[f'CR:{REF_CONTREL[cr_key]["title"][:40]}'] = {
                'Controversial': ref_labels['Controversial'],
                'Relevant': ref_labels['Relevant'],
                'fulltext': fulltext, 
                'storyTitle': ref_labels['title'],
                'source': 'controversy_relevance'  
            }
            matched_titles.add(REF_CONTREL[cr_key]['title'])
            break

# Now analyze the FULLTEXT of labeled examples to UNDERSTAND THE PATTERNS 
print(f"\nFound {len(reference_fulltexts)} reference examples with fullText")

category_examples = defaultdict(list)  # category_value -> [(storyTitle, short_fulltext)]
type_examples = defaultdict(list)      # type_value -> [(storyTitle, short_fulltext)]
controversial_y = []  # items marked controversial=Y  
controversial_n = []  # items marked controversial=N 
relevant_y = []       # items marked relevant=Y
relevant_n = []       # items marked relevant=N

for key, data in reference_fulltexts.items():
    if ref.get('storyTitle'):
        story_title = (ref.get('storyTitle', '') or ref.key.split(':')[-1] if ':' in ref.key else '')  # Extract title from key  
        short_text = ((ref.fulltext or '')[:300]).strip()  
        
        # Category patterns  
        cat_val = data.get('Category', 'unknown')
        category_examples[cat_val].append({'title': story_title, 'excerpt': short_text})
        
        typ_val = data.get('Type', 'unknown')
        type_examples[typ_val].append({'title': story_title, 'category': cat_val, 'excerpt': short_text})  
        
        # Controversial/Relevant patterns
        cont_val = data.get('Controversial', '')  
        rel_val = data.get('Relevant', '')
        
        if cont_val == 'Y':
            controversial_y.append({'title': story_title, 'excerpt': short_text, 'category': cat_val})
        else:
            controversial_n.append({'title': story_title, 'excerpt': short_text, 'category': cat_val})  
        
        if rel_val == 'Y':
            relevant_y.append({'title': story_title, 'excerpt': short_text, 'controversial': cont_val})
        else:
            relevant_n.append({'title': story_title, 'excerpt': short_text, 'controversial': cont_val})

# Print learned patterns for verification  
print("\n📂 CATEGORY PATTERNS from reference examples:")
for cat, exs in sorted(category_examples.items(), key=lambda x: -len(x[1])): 
    print(f"\n  📛 '{cat}' ({len(exs)} items)")
    for ex in exs[:3]:  
        excerpt = (ex.get('excerpt', '') or str[:80]).strip()
        story_title = (ex.get('title', '') or 'unknown')[:60]
        print(f"     Title: {story_title}")
        print(f"     ...{excerpt}...")

print("\n📂 TYPE PATTERNS from reference examples:")
for typ, exs in sorted(type_examples.items(), key=lambda x: -len(x[1])):
    print(f"\n  📛 '{typ}' ({len(exs)} items)")  
    for ex in exs[:3]:
        excerpt = (ex.get('excerpt', '') or str[:80]).strip()
        story_title = (ex.get('title', '') or 'unknown')[:60]
        
        print(f"     Title: {story_title}")  
        print(f"     ...{excerpt}...")

# Analyze controversial items to extract KEY SIGNALS that make something controversial
print("\n📂 CONTROVERSIAL=Y examples analysis:") 
print(f"   Total marked Y: {len(controversial_y)}")
for ex in controversial_y[:5]:  # Show first 5  
    story_title = (ex.get('title', '') or 'unknown')[:70]
    excerpt = (ex.get('excerpt', '') or str[:200]).strip() 
    cat_val = ex.get('category', '')
    print(f"\n   Title: '{story_title}' ({cat_val})")
    
    text_lower = ((ex.get('excerpt', '') or '').lower()).replace('\n', ' ')
    
    # Look for signals in the fullText that explain WHY it's controversial
    if ('lawsuit' in text_lower):
        print("       Signal: litigation/lawsuit language detected")
    if any(kw in text_lower for kw in ['press freedom', 'first amendment']):
        print("       Signal: press_freetext in ex.get('excerpt', '') or '').lower():