#!/usr/bin/env python3
"""Analyze the labeled NYT releases CSV and produce comprehensive statistics."""
import csv
from collections import Counter, defaultdict

OUT = '/Users/ryanrestivo/Sites/releases/nyt_urls_with_paragraphs_removed_duplicates_labeled.csv'
REF1 = '/Users/ryanrestivo/Sites/releases/references/labeling_test.csv'

# Load data
data = list(csv.DictReader(open(OUT, encoding='utf-8')))
print(f"TOTAL: {len(data)} labeled rows\n")

cat_dist = Counter(r['Category'] for r in data)
type_dist = Counter(r['Type'] for r in data)
cont_dist = Counter(r['Controversial (Y/N)'] for r in data)
rel_dist = Counter(r['Relevant (Y/N)'] for r in data)

cat_type_xtab = defaultdict(lambda: defaultdict(int))
for r in data:
    cat_type_xtab[r['Category']][r['Type']] += 1

cont_by_cat = defaultdict(lambda: Counter())
rel_by_cat = defaultdict(lambda: Counter())
for r in data:
    co = r['Controversial (Y/N)']
    re_ = r['Relevant (Y/N)']
    cont_by_cat[r['Category']][co] += 1
    rel_by_cat[r['Category']][re_] += 1

months = Counter()
dates_out = []
title_lens_by_cat = defaultdict(list)
ft_lens_by_cat = defaultdict(list)
url_prefixes = defaultdict(int)

for r in data:
    dp = r.get('datePublished', '')
    if len(dp) >= 7:
        m = dp[:7]
        months[m] += 1
        dates_out.append(dp[:10])
    
    t = r.get('storyTitle', '')
    title_lens_by_cat[r['Category']].append(len(t))
    ft = r.get('fullText', '')
    ft_lens_by_cat[r['Category']].append(len(ft) if ft else 0)

# URL slug analysis by category
url_cats = defaultdict(Counter)
for r in data:
    u = r.get('urls', '')
    cat = r['Category']
    if 'press/' in u:
        slug = u.split('/press/')[-1].lower()
        if 'promot' in slug:
            url_cats[cat]['promo'] += 1
        elif 'win' in slug or 'award' in slug:
            url_cats[cat]['award-slug'] += 1
        elif 'joins' in slug or 'hire' in slug or 'hired' in slug:
            url_cats[cat]['joins-hire'] += 1
        elif 'return' in slug:
            url_cats[cat]['returns'] += 1
        else:
            # Count by first word after press
            parts = slug.split('-')[:4]
            if len(parts) >= 2:
                first_two = parts[-2] + '-' + parts[-1]
                url_cats[cat][first_two] += 1

# Word frequency per category (top words in fullText)
word_cnt_c = defaultdict(lambda: Counter())
for r in data:
    text = (r.get('storyTitle','') + ' ' + r.get('fullText','')).lower()
    for w in text.split():
        w2 = w.strip(".,;:'\"-()/")
        if len(w2) > 3 and not any(c.isdigit() for c in w2):
            word_cnt_c[r['Category']][w2] += 1

# Stop words to filter out
STOP = {'the', 'and', 'for', 'new', 'new york', 'times', 'press', 'of', 'a', 'to', 
        'in', 'is', 'on', 'that', 'with', 'as', 'by', 'at', 'this', 'from', 'its',
        'ny', 'co', 'com', 'not', 'we', 'our'}

# Month distribution sorted
print("--- CATEGORY DISTRIBUTION ---\n")
for c in sorted(cat_dist.keys(), key=lambda x:-cat_dist[x]):
    pct = cat_dist[c]/len(data)*100
    bar = '#' * int(pct/2)
    print(f"{c:25s} {cat_dist[c]:>4d}  {pct:5.1f}%  {bar}")

print("\n--- TYPE DISTRIBUTION ---\n")
for t in sorted(type_dist.keys(), key=lambda x:-type_dist[x]):
    pct = type_dist[t]/len(data)*100
    bar = '#' * int(pct/2)
    print(f"{t:35s} {type_dist[t]:>4d}  {pct:5.1f}%  {bar}")

print("\n--- CROSS-TAB: CATEGORY × TYPE ---\n")
for cat in sorted(cat_type_xtab.keys(), key=lambda x:-sum(cat_type_xtab[x].values())):
    total = sum(cat_type_xtab[cat].values())
    print(f"  {cat} (n={total}):")
    for tp in sorted(cat_type_xtab[cat].keys(), key=lambda x:-cat_type_xtab[cat][x]):
        cnt = cat_type_xtab[cat][tp]
        pct = cnt/total*100
        print(f"    → {tp:25s}: {cnt:>4d} ({pct:.0f}%)")

print("\n--- C/R BY CATEGORY ---\n")
for cat in sorted(cont_by_cat.keys(), key=lambda x:-sum(cont_by_cat[x].values())):
    total = sum(cont_by_cat[cat].values())
    co_y = cont_by_cat[cat].get('Y',0)
    co_n = cont_by_cat[cat].get('N','')
    re1y = rel_by_cat[cat].get('Y',0)
    re1n = rel_by_cat[cat].get('N',0)
    pct_c = co_y/total*100 if total else 0
    pct_r = re1y/total*100 if total else 0
    print(f"  {cat} (n={total}):")
    print(f"    Controversial: Y={co_y:>3d}, N={co_n:>3d} ({pct_c:.0f}% Y)")
    print(f"    Relevant:      Y={re1y:>3d}, N={re1n:>3d} ({pct_r:.0f}% Y)")

# Date range
if dates_out:
    d_min = min(dates_out)
    d_max = max(dates_out)
    unique_months = sorted(months.keys())
    print(f"\n--- DATE RANGE ---\n")
    print(f"Date range: {d_min} → {d_max}")
    print(f"Total months covered: {len(unique_months)}")
    print("\nMonthly distribution:")
    for m in sorted(months.keys()):
        pct = months[m]/len(data)*100
        bar = '#' * int(pct/2)
        print(f"  {m}: {months[m]:>4d}  {pct:5.1f}%  {bar}")

# Title length stats
print("\n--- TITLE LENGTH (chars by category ---\n")
for cat in sorted(title_lens_by_cat.keys(), key=lambda x:-sum(title_lens_by_cat[x])/len(title_lens_by_cat[x])):
    lens = title_lens_by_cat[cat]
    avg = sum(lens)/len(lens)
    mx = max(lens)
    mn = min(lens)
    print(f"  {cat}: avg={avg:.0f} (min={mn}, max={mx})")

# Top words per category
print("\n--- TOP KEYWORDS PER CATEGORY (in fullText, excluding stop words) ---\n")
for cat in sorted(word_cnt_c.keys(), key=lambda x:-sum(word_cnt_c[x].values())):
    top_words = [(w,c) for w,c in word_cnt_c[cat].most_common(10)]
    meaningful = [(w,c) for w,c in top_words if w not in STOP and len(w) > 3]
    print(f"  {cat}:")
    if meaningful:
        for w,c in meaningful[:6]:
            print(f"    {w}: {c}")
    else:
        print("    (no meaningful words)")

# URL slug patterns by category
print("\n--- URL SLUG PATTERNS BY CATEGORY ---\n")
for cat in sorted(url_cats.keys(), key=lambda x:-sum(url_cats[x].values())):
    total_urls = sum(url_cats[cat].values())
    print(f"  {cat} (total URLs with detectable patterns: {total_urls}):")
    for prefix, cnt in sorted(url_cats[cat].items(), key=lambda x:-x[1])[:5]:
        pct = cnt/total_urls*100 if total_urls else 0
        print(f"    → {prefix}: {cnt} ({pct:.0f}%)")
