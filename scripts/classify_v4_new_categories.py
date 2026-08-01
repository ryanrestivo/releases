#!/usr/bin/env python3
"""
1. Sample 50 items from v3 for manual inspection
2. Analyze ALL rows content to find new category patterns
3. Create new categories found in the sample and apply to all rows
4. Save as v4 and commit/push
"""

import csv
import random
import re
from collections import Counter, defaultdict

random.seed(29)

# Read v3 labeled CSV
all_rows = []
with open('/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v3.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames_read = list(reader.fieldnames)
    for row in reader:
        all_rows.append(dict(row))

print(f"Total rows in v3: {len(all_rows)}")
print(f"V3 fieldnames: {fieldnames_read}")

cat_counts = Counter(r.get('Category', '').strip() for r in all_rows)
print(f"\nCurrent categories: {dict(cat_counts)}")

##############################################
# STEP 1: Sample 50 items with full context
##############################################
sample_indices = random.sample(range(len(all_rows)), 50)

print("\n" + "=" * 80)
print("SAMPLE OF 50 ITEMS — analyzing for new category patterns")
print("=" * 80)

for idx in sample_indices:
    row = all_rows[idx]
    title = (row.get('storyTitle') or '')[:90]
    cat = row.get('Category', '').strip()
    typ = row.get('Type', '').strip()
    body = row.get('fullText') or ''
    url = row.get('urls', '')[:100]
    
    print(f"\n{'='*60}")
    print(f"[{idx+1}] Category={cat}  Type={typ}")
    print(f"Title: {title}")
    print(f"URL slug part: .../press/{url.split('/press/ ')[-1][:60] if '/press/' in url else url[:60]}")
    
    # Show key content for pattern detection
    body_lines = [l.strip() for l in body.replace('\n', ' ').split('.') if len(l.strip()) > 20]
    snippet = '. '.join(body_lines[:3]) + '.'
    print(f"Content: {snippet[:250]}")

##############################################
# STEP 2: Identify patterns that suggest new categories
##############################################
print("\n\n" + "=" * 80)
print("PATTERN ANALYSIS OF ALL 3,390 ROWS")
print("=" * 80)

text_by_idx = {}
for i, row in enumerate(all_rows):
    text_by_idx[i] = (row.get('fullText') or '') + ' ' + (row.get('storyTitle') or '')

# Define search patterns for new categories by examining what DOESN'T fit existing categories:
# Existing: award, staff announcement, company update, fact check, feature, statement
# 
# Looking for items that currently say "company update" but are actually:
# 1. Product/Tool launches (a new tool, app, feature)
# 2. Content expansion (new newsletter, podcast season, show)  
# 3. Partnership/collaboration announcements
# 4. Event/conference attendance hosting

product_launch_count = 0
content_addition_count = 0
partnership_count = 0
event_announcement_count = 0

for i, row in enumerate(all_rows):
    text_lower = text_by_idx[i].lower()
    title_text = (row.get('storyTitle') or '').lower()
    cat = (row.get('Category') or '').strip()
    
    # Skip items already clearly categorized
    if cat in ('fact check', 'statement'):
        continue
    
    # Product launch patterns - new tools, apps, features being introduced
    product_patterns = [
        'introducing our' in text_lower,  # "Introducing Our Q1..." is a quarterly report
        'we have launched' in text_lower,
        'just launched a' in text_lower,
        'launching the next phase' in text_lower,
        'new tool for' in text_lower,
        'roll-out of our' in text_lower,
        'expanding access to' in text_lower,
        'announcing our new' in (title_text + text_lower),
    ]
    
    # Content addition/subscription expansion patterns
    content_patterns = [
        'adding a new' in text_lower or 'adding our first' in text_lower,
        'expanding our daily with' in text_lower,
        'expanding our coverage to' in text_lower,
        'expansions for the 2025-26 season' in text_lower,
        'launches a new newsletter' in text_lower,
    ] + [p for p in ['new-and-hot-roster', 'nytdigital-productivity-tool-march'] if p not in (row.get('urls') or '').lower()]
    
    # Partnership/collaboration
    partnership_patterns = [
        ('partner and co' in text_lower),
    ]
    
    # Event/summit announcements
    event_patterns = [
        'annual dealbook summit' in text_lower,
        'festival of literature' in text_lower,
    ]

print("\nSearching through all rows for new category patterns...")

# Better approach: look at what's currently miscategorized by examining title patterns
print("\nLooking at items categorized as 'company update' to see which might be other types:")
cu_rows = [r for r in all_rows if (r.get('Category') or '').strip() == 'company update']
print(f"  company update count: {len(cu_rows)}")

# Look at what these company updates actually contain
for row in cu_rows[:5]:
    body_preview = ((row.get('fullText') or '')).replace('\n', ' ')[:300]
    print(f"  CU example: {row.get('storyTitle','')}"[:60])
    print(f"           Body begins: {body_preview}...")

# Look at award items to understand what the classifier is doing there
award_rows = [r for r in all_rows if (r.get('Category') or '').strip() == 'award']
print(f"\n  award count: {len(award_rows)}")
for row in award_rows[:5]:
    print(f"  Award example: {row.get('storyTitle','')}"[:80])

# Look at feature items
feature_rows = [r for r in all_rows if (r.get('Category') or '').strip() == 'feature']
print(f"\n  feature count: {len(feature_rows)}")
for row in feature_rows[:5]:
    print(f"  Feature example: {row.get('storyTitle','')"[:80]}

# Look at fact check items  
fc_rows = [r for r in all_rows if (r.get('Category') or '').strip() == 'fact check']
print(f"\n  fact check count: {len(fc_rows)}")
for row in fc_rows[:5]:
    print(f"  Fact check example: {row.get('storyTitle','')"[:80]}

# Look at staff announcement items
sa_rows = [r for r in all_rows if (r.get('Category') or '').strip() == 'staff announcement']
print(f"\n  staff announcement count: {len(sa_rows)}")
for row in sa_rows[:5]:
    print(f"  Staff example: {row.get('storyTitle','')"[:80]}

# Key question: what are the most common patterns in company update items that might suggest a new category?
print("\n\nSearching for 'partnership'/'collaboration' mentions across all rows:")
partnership_text_idx = []
for i, row in enumerate(all_rows):
    body_lower = ((row.get('fullText') or '') + ' ' + (row.get('storyTitle') or '')).lower()
    if 'our partnership with' in body_lower or 'partner and co' in (body_lower) or ('in partnership with the' in body_lower):
        print(f"  [{i}] {row.get('storyTitle','')}")
        print(f"     Current cat: {row.get('Category')}, Type: {row.get('Type')}")
        partnership_text_idx.append(i)

print("\n\nSearching for 'new tool', 'introducing our new', 'just launched' patterns:")
product_text_idx = []
for i, row in enumerate(all_rows):
    body_lower = ((row.get('fullText') or '') + ' ' + (row.get('storyTitle') or '')).lower()
    if any(w in body_lower for w in ['our new productivity tool', 'announcing our first', 
                                       'we have introduced', 'introducing our new']):
        print(f"  [{i}] {row.get('storyTitle','')"[:80]}")
        print(f"     Current cat: {row.get('Category')}, Type: {row.get('Type')}")
        product_text_idx.append(i)

print("\n\nSearching for 'annual dealbook', 'summit', 'festival' patterns:")
event_text_idx = []
for i, row in enumerate(all_rows):
    body_lower = ((row.get('fullText') or '') + ' ' + (row.get('storyTitle') or '')).lower()
    if any(w in body_lower for w in ['annual dealbook summit', 'festival of literature 20']):
        print(f"  [{i}] {row.get('storyTitle','')"[:80]}")
        event_text_idx.append(i)

print("\n\nSearching for newsletter/subscription launches:")
newsletter_text_idx = []
for i, row in enumerate(all_rows):
    body_lower = ((row.get('fullText') or '') + ' ' + (row.get('storyTitle') or '')).lower()
    if any(w in body_lower for w in ['announcing our next edition', 'revenue and reader numbers']):
        print(f"  [{i}] {row.get('storyTitle','')"[:80]}")
        newsletter_text_idx.append(i)

print("\n\n=== SUMMARY ===")
print(f"Partnership-text items: {len(partnership_text_idx)} at indices {partnership_text_idx}")
print(f"Product-text items: {len(product_text_idx)} at indices {product_text_idx}")
print(f"Event-text items: {len(event_text_idx)} at indices {event_text_idx}")
print(f"Newsletter revenue items: {len(newsletter_text_idx)} at indices {newsletter_text_idx}")
