import csv
from collections import Counter, defaultdict

INPUT_CSV = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v3.csv'
OUTPUT_CSV = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v4.csv'

print('\n=== PHASE 2: Classification Fixes + New Category Flags ===\n')

rows = []
with open(INPUT_CSV, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    field_list = list(reader.fieldnames)
    for row in reader:
        rows.append(dict(row))

total_rows = len(rows)
print(f'Reads v3: {total_rows}')

def get_lower(r):
    return (r.get('fullText') or '') + ' ' + (r.get('storyTitle') or '')

errors_fixed = defaultdict(int)
fix_reasons_list = []  # collect reasons for documentation
v4_rows = []

for i, r in enumerate(rows):
    cat_orig = (r.get('Category') or '').strip()
    new_cat = cat_orig

    if cat_orig == 'award':
        txt = get_lower(r).lower()
        has_staff = any(k in txt for k in ['joins the', 'join the desk', 'named assistant', 'returning to'])
        has_award = any(w in txt for w in [
            'award', 'won ', 'emmy', 'pulitzer',
            'effie', 'national magazine award'
        ])
        if has_staff and not has_award:
            new_cat = 'staff announcement'

    elif cat_orig == 'fact check':
        txt = get_lower(r).lower()
        has_emmy_honors = any(w in txt for w in [
            'emmy', 'honored with', 'won ', 
            'wins ', 'received the'
        ])
        is_real_fc = any(w in txt for w in [
            'false claims', 'misinformation', 'fabricated'
        ])
        if has_emmy_honors and not is_real_fc:
            new_cat = 'award'

    elif cat_orig == 'feature':
        txt = get_lower(r).lower()
        has_staff_keywords = any(k in txt for k in [
            'joins the', ' is named ', 'new role for', 'returning to'
        ])
        is_genuine_feature = any(w in txt for w in [
            'investigating', 'deep dive into',
            'exploration of the', "what it's like"
        ])
        if has_staff_keywords and not is_genuine_feature:
            new_cat = 'staff announcement'

    elif cat_orig == 'company update':
        txt = get_lower(r).lower()
        if any(w in txt for w in [
            'new productivity tool', 'tool available to the public'
        ]):
            new_cat = 'product_tool'

    # Add new category flags  
    txt = get_lower(r).lower()
    
    is_p = 'Y' if any(k in txt for k in [
        'new productivity tool', 'tool available to the public',
        'we have launched', 'brand new app', 'just launched a tool'
    ]) else 'N'

    is_e = 'Y' if any(k in txt for k in [
        'dealbook summit', 'milan digital fashion week', 
        'livestream collaboration with', 'annual dealbook',
        'local investigations fellows', 'festival of literature 20'
    ]) else 'N'

    is_n = 'Y' if any(k in txt for k in [
        'launch local newsletter', 'announcing our next edition of',
        'launching a local newsletter program'
    ]) else 'N'

    v4_rows.append({
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
    })

output_fields = [
    'urls', 'fullText', 'storyTitle', 
    'datePublished', 'dateModified',
    'Category', 'Type',
    'Controversial (Y/N)', 'Relevant (Y/N)',
    'is_product_launch', 'is_event_announcement',
    'is_newsletter_expansion',
]

with open(OUTPUT_CSV, 'w', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=output_fields[:-1])
    writer.writeheader()
    for row in v4_rows:
        writer.writerow(row)

print('\nPhase 2 Complete! All fixes applied.')
for cat_orig, count in errors_fixed.items():
    print(f"  {cat_orig}: {count} rows corrected")
print(f"\nv4 file written to: {OUTPUT_CSV}")
