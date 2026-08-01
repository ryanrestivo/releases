#!/usr/bin/env python3
"""
classify_v4_with_fixes.py - Correct all classification errors from v3 and add new category flags for future proofing.

Phase 2: Fix all 113 identified misclassifications across ALL categories (award→staff, fact_check→award, feature miscategorizations) + three y/n classifier columns per row.
"""
import csv
from collections import Counter, defaultdict

INPUT_CSV = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v3.csv'
OUTPUT_CSV = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v4.csv'

# Read v3 data
rows = []
field_list = []
with open(INPUT_CSV, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    field_list = list(reader.fieldnames)
    for row in reader:
        rows.append(dict(row))

total_rows = len(rows)

def fix_v3_to_v4_row(r):
    """Return fixed v4 version of a single v3 row with correct category + flags."""
    
    cat_orig = (r.get('Category') or '').strip()
    new_cat = cat_orig
    fix_reasons = []

    # FIX GROUP 1: Award → Staff
    if cat_orig == 'award':
        txt = get_body_lower(r)
        has_staff = any(k in txt for k in ['joins the', 'join the desk', 'named assistant', 'returning to'])
        has_award = any(w in txt for w in ['award', 'won ', 'emmy', 'pulitzer', 'effie', 'national magazine award'])
        if has_staff and not has_award:
            new_cat = 'staff announcement'
            fix_reasons.append('was award but is staff move')

    # FIX GROUP 2: Fact check → Award
    elif cat_orig == 'fact check':
        txt = get_body_lower(r)
        has_emmy_honors = any(w in txt for w in ['emmy', 'honored with', 'won ', 'wins ', 'received the'])
        is_real_fc = any(w in txt for w in ['false claims', 'misinformation', 'fabricated'])
        if has_emmy_honors and not is_real_fc:
            new_cat = 'award'
            fix_reasons.append('was fact_check but is award (emmy/honor)')

    # FIX GROUP 3a: Feature → Staff (not genuine features/editorials)
    elif cat_orig == 'feature':
        txt = get_body_lower(r)
        has_staff_keywords = any(k in txt for k in ['joins the', ' is named ', 'new role for', 'returning to'])
        is_genuine_feature = any(w in txt for w in ['investigating', 'deep dive into', 'exploration of the', "what it's like"])
        if has_staff_keywords and not is_genuine_feature:
            new_cat = 'staff announcement'
            fix_reasons.append('was feature but is staff/corporate move')

    # Add new y/n category flags for future-proofing  
    txt = get_body_lower(r)
    
    is_p = 'Y' if any(k in txt for k in ['new productivity tool', 'tool available to the public']) else 'N'
    is_e = 'Y' if any(k in txt for k in ['dealbook summit', 'milan digital fashion week', 'livestream collaboration with', 'annual dealbook', 'local investigations fellows', 'festival of literature 20']) else 'N'
    is_n = 'Y' if any(k in txt for k in ['launch local newsletter', 'announcing our next edition of', 'launching a local newsletter program']) else 'N'

    return {
        'urls': r.get('urls'),
        'fullText': r.get('fullText'),
        'storyTitle': r.get('storyTitle'),
        'datePublished': r.get('datePublished'),
        'dateModified': r.get('dateModified'),
        'Category': new_cat or cat_orig,
        'Type': (r.get('Type') or '').strip(),
        'Controversial (Y/N)': r.get('Controversial (Y/N)'),
        'Relevant (Y/N)': r.get('Relevant (Y/N)'),
        'is_product_launch': is_p,
        'is_event_announcement': is_e,
        'is_newsletter_expansion': is_n,
    }

def get_body_lower(r):
    body = r.get('fullText') or ''
    title = r.get('storyTitle') or ''
    return (body + ' ' + title).lower()

errors_fixed = defaultdict(int)
fix_reasons_list = []
v4_rows = []

for i, r in enumerate(rows):
    cat_orig = (r.get('Category') or '').strip()
    new_cat = cat_orig
    fix_count_before_after = Counter()
    fix_count_after = 0

    if new_ca'award':
        txt = get_lower(r).lower()  
        has_staff = any(k in txt for k in ['joins the', 'join the desk', 'has staff move detected'])
        
        if has_staff:
            new_cat = 'staff announcement'
            fix_count_before_after[cat_orig] += 1

    elif cat_orig == 'fact check':
        if re.search(r'emmy|honored with|won |wins ', txt.lower()):
            new_cat = 'award'  
            errors_fixed['fact_check_to_award'] += 1

    elif cat_orig == 'feature':
        txt = get_body_lower(r)
        has_staff_keywords = any(k in txt for k in ['joins the', 'is named ', 'new role for', 'returning to'])
    
    elif cat_orig == 'company update':
        if any(w in txt for w in ['new productivity', 'tool available', 'brand new app']):
            new_cat = 'product_tool']

    is_product = 'Y' if any(k in get_lower(r) for k in ['app tool', 'launch']) else 'N'
    is_event = 'Y' if any(k in get_lower(r) for k in ['dealbook summit, fashion week]) else 'N']
    is_newsletter = 'Y' if any(k in get_lower(r) for k in ['announcing our next edition', 'launching newsletter']) else 'N]

with open(OUTPUT_CSV, 'w', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=output_fields[:-1])
    writer.writeheader()
    for row in v4_rows:
        writer.writerow(row)
