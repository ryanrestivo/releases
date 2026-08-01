#!/usr/bin/env python3
"""Spot-check validation for v5: pick every 100th row and verify all 4 columns.
Also count any empty/missing values per column."""
import csv
import html
import sys

INPUT = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled_v5.csv'

valid_categories = {"statement", "fact_check", "award", "feature", "staff_announcement", "company_update"}
valid_types = {"cooking", "audio", "games", "opinion", "newsroom", "product", "feature", "other/don't know", "the_athletic"}
valid_controversial = {"Y", "N"}
valid_relevant = {"Y", "N"}

print(f"Checking: {INPUT}...\n")

with open(INPUT, newline='') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

total = len(rows)
print(f"Total rows: {total}")

errors = []
for i, r in enumerate(rows):
    cat = r.get('Category','').strip()
    typ = r.get('Type','').strip()
    cont = r.get('Controversial (Y/N)','').strip()
    rel = r.get('Relevant (Y/N)','').strip()
    
    issues = []
    if not cat: issues.append("EMPTY Category")
    elif cat not in valid_categories: issues.append(f"UNKNOWN_CATEGORY={cat}")
    
    if not typ: issues.append("EMPTY Type")
    elif typ not in valid_types: issues.append(f"UNKNOWN_TYPE={typ}")
    
    if cont not in valid_controversial: issues.append(f"BAD_Controversial='{cont}'")
    if rel not in valid_relevant: issues.append(f"BAD_Relevant='{rel}'")
    
    if cat == 'award':
        t = r.get('storyTitle','').lower()
        tx = html.unescape(r.get('fullText','')).lower()
        exc = ['crossword leaderboard', 'spelling bee scores', 'wirecutter best picks', 'connections winner in ', 'best new picks awards']
        if any(e in tx for e in exc):
            issues.append("FALSE_POS_AWARD - matches exclusion")
    
    if issues:
        errors.append((i+1, r.get('storyTitle','')[:60], issues))

print(f"\nValidation complete:")
print(f"  Total rows checked: {total}")
print(f"  Rows with errors:   {len(errors)}")

if len(errors) <= 20:
    print("\n=== ERROR DETAILS ===")
    for i, title, iss in errors[:15]:
        print(f"  Row {i+1}: '{title}' -> {iss}")
else:
    print(f"\n=== FIRST 20 ERRORS (showing out of {len(errors)} total) ===")
    for i, title, iss in errors[:20]:
        print(f"  Row {i+1}: '{title}' -> {iss}")
    remaining = len(errors) - 20
    if remaining > 0:
        print(f"  ... and {remaining} more\n")

# Category/Type distribution summary
from collections import Counter
cats = Counter(r['Category'].strip() for r in rows)
typs = Counter(r['Type'].strip() for r in rows)
conts = Counter(r['Controversial (Y/N)'].strip() for r in rows)
rels = Counter(r['Relevant (Y/N)'].strip() for r in rows)

print(f"\n=== DISTRIBUTIONS ===")
print("Categories: %s" % {k:v for k,v in sorted(cats.items(), key=lambda x:-x[1])})
print("Types (top 8): %s" % dict(sorted(typs.items(), key=lambda x:-x[1])[:8]))
print(f"Controversial: Y={conts.get('Y',0)}, N={conts.get('N',0)}, others={sum(v for k,v in conts.items() if k not in ('Y','N'))}")
print("Relevant:   Y=%d, N=%d, others=%d" % (rels.get('Y',0), rels.get('N',0), sum(v for k,v in rels.items() if k not in ('Y','N'))))

sys.exit(1 if len(errors) > 10 else 0)
