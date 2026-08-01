#!/usr/bin/env python3
"""Comprehensive classifier for NYT press releases using taxonomy learned from reference CSVs."""

import csv
import html
from collections import Counter

###############################################################################
# STEP 1: Load reference materials and build the decision rules
###############################################################################

# Load ref1 (Category + Type) with fullText lookup capability
ref1_rows = []
with open('/Users/ryanrestivo/Sites/releases/references/labeling_test.csv', newline='', encoding='utf-8') as f:
    ref1_rows = list(csv.DictReader(f))

# Load ref2 (Controversial + Relevant) 
ref2_rows = []
with open('/Users/ryanrestivo/Sites/releases/references/releases_labeling.csv', newline='', encoding='utf-8') as f:
    ref2_rows = list(csv.DictReader(f))

# Load target data
target_rows = []
with open('/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates.csv', newline='', encoding='utf-8') as f:
    target_raw = list(csv.DictReader(f))

print(f"Reference 1 (Cat+Type): {len(ref1_rows)} labeled\nReference 2 (Cont+Rel): {len(ref2_rows)} labeled\nTarget: {len(target_rows)} to label")

# Build keyword/rule lists from references
# --- Categories ---
fact_check_kw = ['Fact-Checking', 'false claims', 'claims about our', 'claims regarding our',
                 'tracking misinformation']
award_kw = ['wins', 'winning', 'award', 'pulitzer', 'emmy', 'honor', 'honored', 
            'polk', 'webby', 'nlgja', 'sopaa', 'recognition', 'won', 'granted',
            'osborn elliott', 'inaugural best new']
feature_kw = ['celebrates', 'anniversary', '175th']
statement_kw = ['supports campaign', 'response to the lawsuit', 'responds to lawsuit']
cooking_patterns = ['cooking', 'christmas cookies', 'menu', 'food editorial director']
games_patterns = ['wordle', 'crossword', 'connections', 'nyt games', 'games app',
                  'puzzle', 'midi', 'number puzzle', 'the 1,000th', 'crossplay']
audio_patterns = ['the daily', 'hard fork', 'serial productions', 'sunday episodes']
athletic_kw_list = ['the athletic', 'nfl draft', 'world cup coverage', 'football desk']

###############################################################################
# STEP 2: Classify function
###############################################################################

def classify(row):
    title = row.get('storyTitle', '').strip()
    text = (row.get('fullText', '') or '').replace('\n', ' ')[:5000]
    
    # Handle unicode entities in text 
    combined = html.unescape(f"{title} {text}")
    lower_combined = combined[:4000].lower()
    lower_title = title.lower()
    
    # --- Category classification (prioritized order) ---
    cat = None
    
    # 1. Fact check - very distinctive title pattern
    for kw in fact_check_kw:
        if kw.lower() in lower_combined or kw in title:
            cat = 'fact check'
            break
    
    # 2. Award 
    if not cat:
        for kw in award_kw:
            if kw.lower() in lower_combined:
                cat = 'award'
                break
    
    # 3. Statement - distinctive patterns
    if not cat:
        for kw in statement_kw:
            if kw.lower() in lower_combined:
                cat = 'statement'
                break
    
    # 4. Feature - distinctive patterns (celebrations/anniversaries)
    if not cat:
        for kw in feature_kw:
            if kw.lower() in lower_combined:
                cat = 'feature'
                break
    
    # 5. Company update - content/product announcements that are NOT staff changes
    if not cat:
        company_specific = ['launch', 'debuts', 'expands', 'partnership', 'collaboration',
                           '"today"', 'app ', 'feature', 'product', 'crossplay', 'midi',
                           'best seller lists', 'networking', 'invitational', 'reimagined']
        for kw in company_specific:
            if kw.lower() in lower_combined:
                # Check it's NOT really a staff announcement first
                is_staff = any(s in lower_combined for s in ['joins', 'named ', 'hired', 
                                                               'new hire', 'promotion', 
                                                               'receiving a new appointment'])
                if not is_staff:
                    cat = 'company update'
                    break
    
    # 6. Staff announcement - default for personnel changes
    if not cat:
        staff_signals = ['joins', 'named ', 'appointed', 'hire', 'promotion', 'returning to the times',
                        'takes on a new role', 'assumes the role', 'to return', 'new appointment']
        if any(s in lower_combined for s in staff_signals):
            cat = 'staff announcement'
    
    # 7. Default fallback - majority class in ref data is staff announcement
    if not cat:
        # Check remaining context clues
        if any(kw.lower() in lower_combined for kw in award_kw):
            cat = 'award'
        else:
            # Default to staff announcement (it's ~80% of training data)
            cat = 'staff announcement'
    
    # --- Type classification ---
    type_val = None
    
    # Athletic first (highly specific)
    if any(kw.lower() in lower_combined for kw in athletic_kw_list):
        type_val = 'the athletic'
    # Cooking
    elif any(kw.lower() in lower_combined for kw in cooking_patterns):
        type_val = 'cooking'
    # Games
    else:
        for kw in games_patterns:
            if kw.lower() in lower_combined:
                type_val = 'games'
                break
    
    # Audio
    if not type_val:
        for kw in audio_patterns:
            if kw.lower() in lower_combined:
                type_val = 'audio'
                break
    
    # Opinion
    if not type_val and ('opinion' in lower_title or 'op-ed' in lower_combined):
        type_val = 'opinion'
    
    # Newsroom (default for desk/editor/reporter content)
    if not type_val:
        for kw in ['desk', 'newsroom', 'editor', 'correspondent']:
            if kw.lower() in title or len(text) < 50:
                # If title has these words, it's newsroom-focused
                pass
        
        # More specific checks - if text is mainly about desks/departments
        staff_words_in_text = sum(1 for w in ['desk', 'newsroom', 'editorial department', 'correspondent', 'reporter', 'bureau chief'] 
                                  if w.lower() in lower_combined)
        if staff_words_in_text >= 1:
            type_val = 'newsroom'
    
    # Final fallback for types from ref data
    if not type_val:
        type_val = 'other/don\'t know'
    
    return cat, type_val

###############################################################################
# STEP 3: Validate against known labels
###############################################################################

print("\n=== VALIDATING CLASSIFIER AGAINST REF1 DATA ===")
correct_cat = 0
total_validated = len(ref1_rows)

category_mismatches = []
for r in ref1_rows:
    expected_cat = r.get('Category', '').strip().lower()
    expected_type = r.get('Type', '').strip().lower().rstrip()
    
    test_row = {'storyTitle': r.get('Title', ''), 'fullText': ''}
    predicted_cat, predicted_type = classify(test_row)
    
    if predicted_cat == expected_cat:
        correct_cat += 1
    else:
        category_mismatches.append({
            'expected': expected_cat, 
            'predicted': predicted_cat, 
            'title': r.get('Title', '')[:80],
            'type_expected': expected_type,
            'type_predicted': predicted_type
        })

print(f"\nCorrect categories on ref1: {correct_cat}/{total_validated} ({correct_cat/total_validated*100:.1f}%)")

if category_mismatches:
    print("\nMISMATCHES:")
    for mm in category_mismatches[:20]:
        print(f"  Expected='{mm['expected']}' vs Got='{mm['predicted']}' | '{mm['title'][:60]}'")
    
    # Also check type mismatches separately  
    correct_type = sum(1 for r in ref1_rows 
                       if classify({'storyTitle': r.get('Title', ''), 'fullText': ''})[1] == 
                          r.get('Type', '').strip().lower().rstrip())
    print(f"\nCorrect types on ref1: {correct_type}/{total_validated} ({correct_type/total_validated*100:.1f}%)")

###############################################################################
# STEP 4: Apply to all target rows and write output
###############################################################################

print("\n=== APPLYING TO ALL 3,390 TARGET ROWS ===")

results = []
cat_counts = Counter()
type_counts = Counter()
controversial_counts = {'Y': 0, 'N': 0}
relevant_counts = {'Y': 0, 'N': 0}

for i, row in enumerate(target_raw):
    cat, type_val = classify(row)
    
    # Controversial (Y/N) - same rules from ref2
    lower_combined = (html.unescape(f"{row.get('storyTitle', '')} {row.get('fullText', '')}")[:4000]).lower()
    if any(kw in lower_combined for kw in ['sues', 'lawsuit', 'eeoc', 'e-e-o-c']):
        controversial = 'Y'
    elif any(kw.lower() in lower_combined or kw in row.get('storyTitle', '') 
             for kw in ['press freedom', 'free press', 'threaten', 'intimidation']):
        controversial = 'Y'  
    else:
        controversial = 'N'
    
    # Relevant (Y/N) - strategic/leadership/vision = Y, operational = N
    relevant = 'N'  # default
    # Leadership pieces are relevant (from ref2 examples)
    if any(kw.lower() in lower_combined for kw in ['ambition', 'future of journalism', 
                                                     'core values', 'press freedom', 'strategic',
                                                     'independent reporting']):
        relevant = 'Y'
    
    # CEO/Publisher/Editor-in-Chief titles are relevant
    title_lower = row.get('storyTitle', '').lower()
    if any(kw in title_lower for kw in ['ceo', 'publisher', 'editor in chief', 'deputy editor',
                                          's.v.p.', 'senior vice president']):
        relevant = 'Y'
    
    # Staff announcements with executive titles are relevant (from ref2)  
    if cat == 'staff announcement':
        if any(kw in lower_combined for kw in ['editor in chief', 'deputy editor', 's.v.p.', 
                                                 'senior vice president', 'ceo', 'managing editor']):
            relevant = 'Y'
    
    # Also check text for strategic/ambition language
    if cat == 'staff announcement':
        if any(kw.lower() in lower_combined for kw in ['vision', 'core team', 'newsroom development']):
            relevant = 'Y'
    
    results.append({
        'urls': row.get('urls', ''),
        'fullText': row.get('fullText', ''),
        'storyTitle': row.get('storyTitle', ''),
        'datePublished': row.get('datePublished', ''),
        'dateModified': row.get('dateModified', ''),
        'Category': cat,
        'Type': type_val,
        'Controversial (Y/N)': controversial,
        'Relevant (Y/N)': relevant,
    })
    
    cat_counts[cat] += 1
    type_counts[type_val] += 1
    controversial_counts[controversial] += 1
    relevant_counts[relevant] += 1

print(f"\nLabel distribution:")
print(f"  Category: {dict(cat_counts)}")
print(f"  Type: {dict(type_counts)}")
print(f"  Controversial Y: {controversial_counts['Y']}, N: {controversial_counts['N']}")
print(f"  Relevant Y: {relevant_counts['Y']}, N: {relevant_counts['N']}")

# Write output CSV
output_path = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v3.csv'
fieldnames = ['urls', 'fullText', 'storyTitle', 'datePublished', 'dateModified',
              'Category', 'Type', 'Controversial (Y/N)', 'Relevant (Y/N)']

with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    
    # Write header row + data
    for r in results[:3]:  # first 3 rows
        print(f"\nFirst labeled row (sample):")
        print(f"  Title: {r['storyTitle'][:80]}")
        print(f"  Category={r['Category']} Type={r['Type']} Controversial={r['Controversial (Y/N)']} Relevant={r['Relevant (Y/N)']}")
    
    # Actually write all rows  
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print(f"\nLabeled CSV written to: {output_path}")
print("DONE")
