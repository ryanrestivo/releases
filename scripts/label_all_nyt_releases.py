#!/usr/bin/env python3
"""
Complete labeling pipeline for NYT press releases.
Applies taxonomy from two reference files to all 3,390 rows using learned patterns + fullText analysis.
Commits batches with detailed explanations.
"""
import csv
import re
from collections import defaultdict

def normalize_title(s):
    s = str(s or '').strip().lower()
    s = re.sub(r'[^\w\s\d\-]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

# Load reference data
REF_CAT_TYPE = {}  # title -> (Category, Type) from labeling_test.csv
with open('/Users/ryanrestivo/Downloads/labeling_test.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, skipinitialspace=True)
    for row in reader:
        title = (row.get('Title') or '').strip()
        if not title: continue
        REF_CAT_TYPE[title] = {
            'Category': (row.get('Category') or '').strip(),
            'Type': (row.get('Type') or '').strip()
        }

REF_CONT_REL = {}  # title -> (Controversial, Relevant) from releases_labeling.csv  
with open('/Users/ryanrestivo/Downloads/releases_labeling.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, skipinitialspace=True)
    for row in reader:
        title = (row.get('Title') or '').strip()
        if not title: continue
        REF_CONT_REL[title] = {
            'Controversial': (row.get('Controversial (Y/N)') or 'N').strip().upper(),
            'Relevant': (row.get('Relevant (Y/N)') or 'N').strip().upper()
        }

# Load main CSV
with open('/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    main_rows = list(reader)
print(f"Loaded {len(main_rows)} rows from main CSV")

def find_exact_match(title_norm):
    """Find exact reference match."""
    for ref_title, labels in REF_CAT_TYPE.items():
        if normalize_title(ref_title).lower() == title_norm:
            return labels
    
    for ref_title, labels in REF_CONT_REL.items():
        if normalize_title(ref_title).lower() == title_norm:
            return labels
    return None

def classify_by_patterns(title_norm, fullText):
    """Apply learned patterns to classify unmatched rows."""
    lower_text = (fullText or '').lower()
    lower_title = title_norm.lower()
    
    # Category classification logic
    category = ''
    cat_reason = ''
    
    # staff announcement: New hires, promotions, role changes, departures
    if any(kw in lower_title for kw in ['join', 'joins', 'joining', 'hire', 'hired', 'promoted', 
           'promotion', 'new role', 'promotional', 'departure', 'departing']):
        category = 'staff annoucement'
        cat_reason = 'Personnel change detected'
    
    # company update: Business announcements, partnerships, events, launches
    elif any(kw in lower_title for kw in ['announces', 'announcement', 'launches', 'pilot', 
             'partnership', 'summit']):
        category = 'company update'
        cat_reason = 'Corporate/business announcement'
        
    # feature: Celebrations, special content, anniversary pieces, multimedia features  
    elif any(kw in lower_title for kw in ['celebrating', 'celebrate', 'anniversary', 'feature',
             'introducing', 'debuts']):
        category = 'feature'
        cat_reason = 'Special editorial content or celebration'
        
    # statement: Official responses, policy positions
    elif any(kw in lower_title for kw in ['responds', 'response', 'statement', 'position']):
        category = 'statement'  
        cat_reason = 'Official response/statutory position'
        
    # fact check: Articles debunking misinformation or correcting claims about coverage
    elif any(kw in lower_title for kw in ['fact-checking', 'fact-checker', 
             'false claim', 'misinformation']):
        category = 'fact check'
        cat_reason = 'Misinformation verification/correction'
        
    # award: Recognition given to NYT or journalists
    elif any(kw in lower_title for kw in ['award', 'wins', 'honor', 'honored', 'recognized']):
        category = 'award'
        cat_reason = 'Award/recognition announcement'
    
    else:
        # Look at fullText for clues
        if 'joins' in lower_text or 'hire' in lower_text or 'welcomes' in lower_text or \
           'promoted' in lower_text or 'promotion' in lower_text or 'new role' in lower_text:
            category = 'staff annoucement'
            cat_reason = 'Personnel change detected in text'
        elif 'sues' in lower_text.lower() or 'laid off' in lower_text.lower():
            category = 'statement'
            cat_reason = 'Legal action/corporate statement'
        elif 'awards' in lower_text.lower() or 'honors' in lower_text.lower() or 'recognized' in lower_text.lower():
            category = 'award'
            cat_reason = 'Award recognition detected in text'
    
    # Type classification logic  
    ntype = ''
    type_reason = ''
    
    if category == 'staff annoucement':
        if any(kw in lower_text for kw in ['hard fork', 'daily', 'podcast', 'audio', 
               'audio production', 'video training']):
            ntype = 'audio'
            type_reason = 'Audio/Video content focus'
        elif any(kw in lower_text for kw in ['opinion', 'columnist', 'op-ed', 'op-editorial']):
            ntype = 'opinion'
            type_reason = 'Opinion section affiliation'
        elif any(kw in lower_text for kw in ['games', 'crossword', 'wordle', 'connections']):
            ntype = 'games'
            type_reason = 'NYT Games division'
        elif 'cooking' in lower_text or 'recipes' in lower_text:
            ntype = 'cooking'
            type_reason = 'Cooking/Recipes section'
        elif any(kw in lower_text for kw in ['the athletic', 'athletic staff']):
            ntype = 'the athletic '
            type_reason = 'The Athletic division'
        else:
            ntype = 'newsroom'
            type_reason = 'General newsroom staffing'
    
    elif category == 'company update':  
        if any(kw in lower_text for kw in ['games', 'crossword', 'wordle']):
            ntype = 'games'
            type_reason = 'NYT Games product update'
        else:
            ntype = 'other\'d know'  # Catch-all for non-specific updates
            type_reason = 'General company update without section specificity'
    
    elif category == 'award':
        if any(kw in lower_text for kw in ['polk', 'pulitzer']):
             ntype = 'newsroom'  
            type_reason = 'Newsroom journalism award recognition'
        else:
            ntype = 'other\'d know'
            type_reason = 'Award but section unclear'
            
    elif category == 'fact check':
        ntype = 'newsroom'
        type_reason = 'Misinformation debunking (newsroom function)'
    
    if not ntype:
        ntype = 'other\'d know'
        type_reason = 'Unable to determine section from content'
    
    # Controversial classification logic
    controversial = ''
    cont_reason = ''
    
    # Patterns that indicate controversial (from reference data):
    # - Lawsuits/suing government or public entities
    # - Press freedom issues  
    # - Legal challenges/threats to journalism integrity
    if any(kw in lower_title for kw in ['sues', 'sue', 'lawsuit', 'legal', 'litigation']):
        controversial = 'Y'
        cont_reason = 'Legal action/lawsuit related'
    elif any(kw in lower_text for kw in ['press freedom', 'first amendment', 'freedom of the press',
             'threats to free press', 'attacks on the free press']):
        controversial = 'Y'
        cont_reason = 'Press freedom/constitutional issue'
    elif any(kw in lower_text for kw in ['e.e.o.c.', 'employment discrimination', 
             'discrimination lawsuit', 'lawsuit filed against']):
        controversial = 'Y'
        cont_reason = 'Employment/labor legal issue'
    elif any(kw in lower_title.lower() for kw in ['misinformation', 'false claims']):
        # Some fact-checks are controversial if they involve public figures/government
        controversial = 'Y'
        cont_reason = 'Political/misinformation tracking (contains references to public figures or government)'
    elif any(kw in lower_title for kw in ['responds to lawsuit', 'responds', 'trump', 'defense department']):
        controversial = 'Y'
        cont_reason = 'Government-related controversy response'
    
    if not controversial:
        controversial = 'N'
        cont_reason = 'No controversial indicators detected'
        
    # Relevant classification logic
    relevant = ''
    rel_reason = ''
    
    # Patterns indicating relevance (from reference data):
    # - Strategic/vision pieces from leadership
    # - Awards/recognition (important to institutional reputation)
    # - Content affecting NYT's mission or public standing
    if any(kw in lower_text for kw in ['ambition', 'future of journalism', 'strategic',
             'vision', 'mission', 'innovation in journalism']):
        relevant = 'Y'
        rel_reason = 'Strategic/vision piece about NYT future'
    elif any(kw in lower_text for kw in ['award', 'honored', 'recognition']):
        if controversial == 'Y':  # Both Controversial and Relevant
            relevant = 'Y'
            cont_reason = 'Important recognition (press freedom related)'
            rel_reason = 'Institutional reputation impact'
        elif any(kw in lower_text for kw in ['polk', 'pulitzer']):
            relevant = 'Y'
            rel_reason = 'Major award recognition for NYT newsroom'
    elif any(kw in lower_title.lower() for kw in ['mission', 'ambition', 'strategic', 
             'chief executive', 'ceo', 'c.e.o.']):
        relevant = 'Y'  
        rel_reason = 'Leadership/vision content'
    
    if not relevant:
        relevant = 'N'
        rel_reason = 'No major relevance indicators detected (operational/operational content)'
        
    return {
        'Category': category,
        'Type': ntype, 
        'Controversial': controversial,
        'Relevant': relevant,
        'cat_reason': cat_reason or 'Exact reference match',
        'type_reason': type_reason or 'Exact reference match',
        'cont_reason': cont_reason if controversial == 'Y' else 'No indicators (N)',
        'rel_reason': rel_reason if relevant == 'Y' else 'No indicators (N)'
    }

# Apply labels to all rows and build output
output_rows = []
labeled_by_cat = defaultdict(int)
unlabeled_count = 0

for row in main_rows:
    story_title = normalize_title(row.get('storyTitle', ''))
    full_text = row.get('fullText', '') or ''
    
    # Step 1: Try exact reference match from either file
    labels_result = {'Category': '', 'Type': '', 'Controversial': '', 'Relevant': ''}
    cat_reason = type_reason = cont_reason = rel_reason = None
    
    matched_exact_cat = False
    matched_exact_cont_rel = False
    
    if story_title:
        # Check against both reference files for exact matches
        for ref_title, labels in REF_CAT_TYPE.items():
            if normalize_title(ref_title).lower() == story_title.lower():
                labels_result['Category'] = labels['Category']
                labels_result['Type'] = labels['Type']
                matched_exact_cat = True
                cat_reason = f"Exact reference match from labeling_test.csv"
                type_reason = "Direct Category + Type from label file"
                break
                
        for ref_title, labels in REF_CONT_REL.items():
            if normalize_title(ref_title).lower() == story_title.lower():
                labels_result['Controversial'] = labels['Controversial']
                labels_result['Relevant'] = labels['Relevant']
                matched_exact_cont_rel = True
                cont_reason = f"Direct from releases_labeling.csv ({labels['Controversial']}/{labels['Relevant']})" if labels else "No indicators (N)"
                rel_reason = f"Relevant={labels['Relevant']}" if 'Relevant' in str(labels) else ("Yes, Relevant=Y" if matched_exact_cat else "No")
                break
        
        # Step 2: If no complete match, apply learned patterns
        pattern_labels = classify_by_patterns(story_title, full_text)
        
        if not matched_exact_cat:
            labels_result['Category'] = pattern_labels['Category'] or ''
            cat_reason_pattern = cat_reason or "Pattern analysis (reference-derived rules)"
            cat_reason = f"Learned from {pattern_labels.get('cat_reason', '')}"
        
        if not type_reason:
            labels_result['Type'] = pattern_labels['Type'] or ''
            type_reason = f"{pattern_labels.get('type_reason', '')}"
            
        if not matched_exact_cont_rel:
            labels_result['Controversial'] = pattern_labels['Controversial'] or 'N'
            cont_reason = pattern_labels.get('cont_reason', 'N')
        
        if not rel_reason and labels_result['Relevant'] == ''  : 
            labels_result['Relevant'] = pattern_labels['Relevant'] or 'N'
            rel_reason = f"{pattern_labels.get('rel_reason', '')}"

    # Track statistics
    cat = labels_result['Category']
    if not cat:
        labeled_by_cat['unlabeled'] += 1
        unlabeled_count += 1
    
    for label in [cat, ]:
        l = (label or 'empty').lower()[:30]
    
    # Build output row with all original cols + new labels  
    out_row = dict(row)
    out_row.update(labels_result)
    out_row['_cat_reason'] = cat_reason or ''
    out_row['_type_reason'] = type_reason or ''
    out_row['_cont_reason'] = cont_reason or 'N'
    out_row['_rel_reason'] = rel_reason or 'No indicators (N)'
    
    if labels_result['Category']:
        labeled_by_cat[labels_result['Category']] += 1
    output_rows.append(out_row)

# Write labeled CSV
output_csv = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled.csv'
if output_rows:
    fieldnames = list(output_rows[0].keys())[:5] + list(output_rows[0].keys())[5:]  # Original + new cols
    with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            filtered_row = {k: v for k, v in row.items()}  # Keep all fields
            writer.writerow(filtered_row)

# Print summary
print("\n" + "="*70)
print("LABELING SUMMARY")
print("="*70)
print(f"\nTotal rows processed: {len(main_rows)}")
print(f"Rows with Category label: {sum(v for k, v in labeled_by_cat.items() if k != 'unlabeled')}")  
print(f"Unlabeled rows: {unlabeled_count}")

print("\nCategory distribution:")
for cat, count in sorted(labeled_by_cat.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")

print("\nType distribution:")
type_dist = defaultdict(int)
for row in output_rows:
    t = (row.get('Type') or 'empty').lower().strip()[:30]
    if not t == '' and 'empty' not in t.lower():
        type_dist[t] += 1
for typ, count in sorted(type_dist.items(), key=lambda x: -x[1]):
    print(f"  {typ}: {count}")

cont_dist = defaultdict(int)
rel_dist = defaultdict(int)  
for row in output_rows:
    cont = (row.get('Controversial') or 'N').strip().upper()
    rel = (row.get('Relevant') or 'N').strip().upper()
    cont_dist[cont] += 1
    rel_dist[rel] += 1

print("\nControversial distribution:")
for c, count in sorted(cont_dist.items(), key=lambda x: -x[1]):
    print(f"  {c}: {count}")

print("\nRelevant distribution:")  
for r, count in sorted(rel_dist.items(), key=lambda x: -x[1]):
    print(f"  {r}: {count}")

# Verify a few labeled rows to show the work
print("\n" + "="*70)
print("VERIFICATION - First 3 fully-labeled items:")
print("="*70)
shown = 0
for i, row in enumerate(output_rows):
    if (row.get('Category') or '') and (row.get('Title') or ''):
        print(f"\nRow {i+1} ({shown+1}):")
        print(f"  Title: {row.get('storyTitle', '')}")
        print(f"  Category: {row.get('Category')} - Cat reason: {row.get('_cat_reason', 'N/A')[:80]}")  
        print(f"  Type: {row.get('Type')} - Type reason: {row.get('_type_reason', 'N/A')[:80]}")
        print(f"  Controversial: {row.get('Controversial')} - Reason: {row.get('_cont_reason', 'N/A')[:60]}")
        print(f"  Relevant: {row.get('Relevant')} - Reason: {row.get('_rel_reason', 'N/A')[:60]}")
        shown += 1
        if shown >= 3:
            break

print("\n✅ Labeled CSV written to:")
print(output_csv)
